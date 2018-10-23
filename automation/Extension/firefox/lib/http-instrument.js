// TODO: doesn't work with e10s -- be sure to launch nightly disabling remote tabs
// import { Cc, Ci, CC, Cu, Cr, components } from 'chrome';

// import events from 'sdk/system/events';
// import { data } from 'sdk/self';
import * as httpPostParser from './http-post-parser.js';

/*
var BinaryInputStream = CC('@mozilla.org/binaryinputstream;1',
    'nsIBinaryInputStream', 'setInputStream');
var BinaryOutputStream = CC('@mozilla.org/binaryoutputstream;1',
    'nsIBinaryOutputStream', 'setOutputStream');
var StorageStream = CC('@mozilla.org/storagestream;1',
    'nsIStorageStream', 'init');
const ThirdPartyUtil = Cc["@mozilla.org/thirdpartyutil;1"].getService(
                       Ci.mozIThirdPartyUtil);
var cryptoHash = Cc["@mozilla.org/security/hash;1"]
         .createInstance(Ci.nsICryptoHash);
var converter = Cc["@mozilla.org/intl/scriptableunicodeconverter"]
         .createInstance(Ci.nsIScriptableUnicodeConverter);
converter.charset = "UTF-8";
Cu.import("resource://gre/modules/XPCOMUtils.jsm");
*/

let loggingDB;
export const setLoggingDB = function($loggingDB) {
  loggingDB = $loggingDB;
};

/*
 * HTTP Request Handler and Helper Functions
 */

function get_stack_trace_str() {
  // return the stack trace as a string
  // TODO: check if http-on-modify-request is a good place to capture the stack
  // In the manual tests we could capture exactly the same trace as the
  // "Cause" column of the devtools network panel.
  var stacktrace = [];
  var frame = components.stack;
  if (frame && frame.caller) {
    // internal/chrome callers occupy the first three frames, pop them!
    frame = frame.caller.caller.caller;
    while (frame) {
      // chrome scripts appear as callers in some cases, filter them out
      var scheme = frame.filename.split("://")[0];
      if ( ["resource", "chrome", "file"].indexOf(scheme) === -1 ) {  // ignore chrome scripts
        stacktrace.push(frame.name + "@" + frame.filename + ":" +
            frame.lineNumber + ":" + frame.columnNumber + ";" + frame.asyncCause);
      }
      frame = frame.caller || frame.asyncCaller;
    }
  }
  return stacktrace.join("\n");
}

var httpRequestHandler = function(reqEvent, crawlID) {
  var httpChannel = reqEvent.subject.QueryInterface(Ci.nsIHttpChannel);

  // Save HTTP redirect events. Requires FF 49+
  // Events are saved to the `http_redirects` table, and map the old
  // request/response channel id to the new request/response channel id.
  // Implementation based on: https://stackoverflow.com/a/11240627
  var oldNotifications = httpChannel.notificationCallbacks;
  var oldEventSink = null;
  httpChannel.notificationCallbacks = {
    QueryInterface: XPCOMUtils.generateQI([
        Ci.nsIInterfaceRequestor,
        Ci.nsIChannelEventSink]),

    getInterface: function(iid) {
      // We are only interested in nsIChannelEventSink,
      // return the old callbacks for any other interface requests.
      if (iid.equals(Ci.nsIChannelEventSink)) {
        try {
          oldEventSink = oldNotifications.QueryInterface(iid);
        } catch(anError) {
          loggingDB.logError(
              'Error during call to custom notificationCallbacks::getInterface.' +
              JSON.stringify(anError)
          );
        }
        return this;
      }

      if (oldNotifications) {
        return oldNotifications.getInterface(iid);
      } else {
        throw Cr.NS_ERROR_NO_INTERFACE;
      }
    },

    asyncOnChannelRedirect: function(oldChannel, newChannel, flags, callback) {
      var isTemporary = !!(flags & Ci.nsIChannelEventSink.REDIRECT_TEMPORARY);
      var isPermanent = !!(flags & Ci.nsIChannelEventSink.REDIRECT_PERMANENT);
      var isInternal = !!(flags & Ci.nsIChannelEventSink.REDIRECT_INTERNAL);
      var isSTSUpgrade = !!(flags & Ci.nsIChannelEventSink.REDIRECT_STS_UPGRADE);

      newChannel.QueryInterface(Ci.nsIHttpChannel);

      loggingDB.saveRecord("http_redirects", {
        'crawl_id': crawlID,
        'old_channel_id': oldChannel.channelId,
        'new_channel_id': newChannel.channelId,
        'is_temporary': isTemporary,
        'is_permanent': isPermanent,
        'is_internal': isInternal,
        'is_sts_upgrade': isSTSUpgrade,
        'time_stamp': new Date().toISOString()
      });

      if (oldEventSink) {
        oldEventSink.asyncOnChannelRedirect(oldChannel, newChannel, flags, callback);
      } else {
        callback.onRedirectVerifyCallback(Cr.NS_OK);
      }
    }
  };

  // http_requests table schema:
  // id [auto-filled], crawl_id, url, method, referrer,
  // headers, visit_id [auto-filled], time_stamp
  var update = {};

  update["crawl_id"] = crawlID;

  // ChannelId is a unique identifier that can be used to link requests and
  // responses. FF 49+
  update['channel_id'] = httpChannel.channelId;

  var stacktrace_str = get_stack_trace_str();
  update["req_call_stack"] = loggingDB.escapeString(stacktrace_str);

  var url = httpChannel.URI.spec;
  update["url"] = loggingDB.escapeString(url);

  var requestMethod = httpChannel.requestMethod;
  update["method"] = loggingDB.escapeString(requestMethod);

  var referrer = "";
  if (httpChannel.referrer)
    referrer = httpChannel.referrer.spec;
  update["referrer"] = loggingDB.escapeString(referrer);

  var current_time = new Date();
  update["time_stamp"] = current_time.toISOString();

  var encodingType = "";
  var headers = [];
  var isOcsp= false;
  httpChannel.visitRequestHeaders({visitHeader: function(name, value) {
    var header_pair = [];
    header_pair.push(loggingDB.escapeString(name));
    header_pair.push(loggingDB.escapeString(value));
    headers.push(header_pair);
    if (name == "Content-Type") {
      encodingType = value;
      if (encodingType.indexOf("application/ocsp-request") != -1)
        isOcsp = true;
    }
  }});

  if (requestMethod == 'POST' && !isOcsp) {  // don't process OCSP requests
    reqEvent.subject.QueryInterface(components.interfaces.nsIUploadChannel);
    if (reqEvent.subject.uploadStream) {
      reqEvent.subject.uploadStream.QueryInterface(components.interfaces.nsISeekableStream);
      var postParser = new httpPostParser.HttpPostParser(reqEvent.subject.uploadStream);
      var postObj = postParser.parsePostRequest(encodingType);

      // Add (POST) request headers from upload stream
      if ("post_headers" in postObj) {
        // Only store POST headers that we know and need. We may misinterpret POST data as headers
        // as detection is based on "key:value" format (non-header POST data can be in this format as well)
        var contentHeaders = ["Content-Type", "Content-Disposition", "Content-Length"];
        for (var name in postObj["post_headers"]) {
          if (contentHeaders.includes(name)){
            var header_pair = [];
            header_pair.push(loggingDB.escapeString(name));
            header_pair.push(loggingDB.escapeString(postObj["post_headers"][name]));
            headers.push(header_pair);
          }
        }
      }
      // we store POST body in JSON format, except when it's a string without a (key-value) structure
      if ("post_body" in postObj)
        update["post_body"] = postObj["post_body"];
    }
  }

  update["headers"] = JSON.stringify(headers);

  // Check if xhr
  var isXHR;
  try {
      var callbacks = httpChannel.notificationCallbacks;
      var xhr = callbacks ? callbacks.getInterface(Ci.nsIXMLHttpRequest) : null;
      isXHR = !!xhr;
  } catch (e) {
      isXHR = false;
  }
  update["is_XHR"] = isXHR;

  // Check if frame OR full page load
  var isFrameLoad;
  var isFullPageLoad;
  if (httpChannel.loadFlags & Ci.nsIHttpChannel.LOAD_INITIAL_DOCUMENT_URI) {
      isFullPageLoad = true;
      isFrameLoad = false;
  } else if (httpChannel.loadFlags & Ci.nsIHttpChannel.LOAD_DOCUMENT_URI) {
      isFrameLoad = true;
      isFullPageLoad = false;
  }
  update["is_full_page"] = isFullPageLoad;
  update["is_frame_load"] = isFrameLoad;

  // Grab the triggering and loading Principals
  var triggeringOrigin;
  var loadingOrigin;
  if (httpChannel.loadInfo.triggeringPrincipal)
    triggeringOrigin = httpChannel.loadInfo.triggeringPrincipal.origin
  if (httpChannel.loadInfo.loadingPrincipal)
    loadingOrigin = httpChannel.loadInfo.loadingPrincipal.origin
  update["triggering_origin"] = loggingDB.escapeString(triggeringOrigin);
  update["loading_origin"] = loggingDB.escapeString(loadingOrigin);

  // loadingDocument's href
  // The loadingDocument is the document the element resides, regardless of
  // how the load was triggered.
  var loadingHref;
  if (httpChannel.loadInfo.loadingDocument && httpChannel.loadInfo.loadingDocument.location)
    loadingHref = httpChannel.loadInfo.loadingDocument.location.href;
  update["loading_href"] = loggingDB.escapeString(loadingHref);

  // contentPolicyType of the requesting node. This is set by the type of
  // node making the request (i.e. an <img src=...> node will set to type 3).
  // For a mapping of integers to types see:
  // TODO: include the mapping directly
  // http://searchfox.org/mozilla-central/source/dom/base/nsIContentPolicyBase.idl)
  update["content_policy_type"] = httpChannel.loadInfo.externalContentPolicyType;

  // Do third-party checks
  // These specific checks are done because it's what's used in Tracking Protection
  // See: http://searchfox.org/mozilla-central/source/netwerk/base/nsChannelClassifier.cpp#107
  try {
    var isThirdPartyChannel = ThirdPartyUtil.isThirdPartyChannel(httpChannel);
    var topWindow = ThirdPartyUtil.getTopWindowForChannel(httpChannel);
    var topURI = ThirdPartyUtil.getURIFromWindow(topWindow);
    if (topURI) {
      var topUrl = topURI.spec;
      var channelURI = httpChannel.URI;
      var isThirdPartyToTopWindow = ThirdPartyUtil.isThirdPartyURI(channelURI, topURI);
      update["is_third_party_to_top_window"] = isThirdPartyToTopWindow;
      update["is_third_party_channel"] = isThirdPartyChannel;
      update["top_level_url"] = loggingDB.escapeString(topUrl);
    }
  } catch (anError) {
    // Exceptions expected for channels triggered or loading in a
    // NullPrincipal or SystemPrincipal. They are also expected for favicon
    // loads, which we attempt to filter. Depending on the naming, some favicons
    // may continue to lead to error logs.
    if (update["triggering_origin"] != '[System Principal]' &&
        update["triggering_origin"] != undefined &&
        update["loading_origin"] != '[System Principal]' &&
        update["loading_origin"] != undefined &&
        !update['url'].endsWith('ico')) {

      loggingDB.logError(
          'Error while retrieving additional channel information for URL: ' +
          '\n' + update['url'] +
          '\n Error text:' + JSON.stringify(anError)
      );
    }
  }

  loggingDB.saveRecord("http_requests", update);
};

/*
 * HTTP Response Handler and Helper Functions
 */

// Used to parse Response stream to log content
function TracingListener() {
  // array for incoming data.
  // onStopRequest we combine these to get the full source
  this.receivedChunks = [];
  this.responseBody;
  this.responseStatusCode;

  this.deferredDone = {
    promise: null,
    resolve: null,
    reject: null
  };
  this.deferredDone.promise = new Promise(function(resolve, reject) {
    this.resolve = resolve;
    this.reject = reject;
  }.bind(this.deferredDone));
  Object.freeze(this.deferredDone);
  this.promiseDone = this.deferredDone.promise;
}
TracingListener.prototype = {
  onDataAvailable: function(aRequest, aContext, aInputStream, aOffset, aCount) {
    var iStream = new BinaryInputStream(aInputStream);
    var sStream = new StorageStream(8192, aCount, null);
    var oStream = new BinaryOutputStream(sStream.getOutputStream(0));

    // Copy received data as they come.
    var data = iStream.readBytes(aCount);
    this.receivedChunks.push(data);
    oStream.writeBytes(data, aCount);

    this.originalListener.onDataAvailable(aRequest, aContext,
        sStream.newInputStream(0), aOffset, aCount);
  },
  onStartRequest: function(aRequest, aContext) {
    this.originalListener.onStartRequest(aRequest, aContext);
  },
  onStopRequest: function(aRequest, aContext, aStatusCode) {
    this.responseBody = this.receivedChunks.join("");
    delete this.receivedChunks;
    this.responseStatus = aStatusCode;

    this.originalListener.onStopRequest(aRequest, aContext, aStatusCode);
    this.deferredDone.resolve();
  },
  QueryInterface: function(aIID) {
    if (aIID.equals(Ci.nsIStreamListener) || aIID.equals(Ci.nsISupports)) {
      return this;
    }
    throw Cr.NS_NOINTERFACE;
  }
};

// Helper functions to convert hash data to hex
function toHexString(charCode) {
  return ("0" + charCode.toString(16)).slice(-2);
}
function binaryHashtoHex(hash) {
  return Array.from(hash, (c, i) => toHexString(hash.charCodeAt(i))).join("");
}

function logWithResponseBody(respEvent, update) {
  // log with response body from an 'http-on-examine(-cached)?-response' event
  var newListener = new TracingListener();
  respEvent.subject.QueryInterface(Ci.nsITraceableChannel);
  newListener.originalListener = respEvent.subject.setNewListener(newListener);
  newListener.promiseDone.then(function() {
    var respBody = newListener.responseBody; // get response body as a string
    var bodyBytes = converter.convertToByteArray(respBody); // convert to bytes
    cryptoHash.init(cryptoHash.MD5);
    cryptoHash.update(bodyBytes, bodyBytes.length);
    var contentHash = binaryHashtoHex(cryptoHash.finish(false));
    update["content_hash"] = contentHash;
    loggingDB.saveContent(loggingDB.escapeString(respBody),
                          loggingDB.escapeString(contentHash));
    loggingDB.saveRecord("http_responses", update);
  }, function(aReason) {
    loggingDB.logError("Unable to retrieve response body." + JSON.stringify(aReason));
    update["content_hash"] = "<error>";
    loggingDB.saveRecord("http_responses", update);
  }).catch(function(aCatch) {
    loggingDB.logError('Unable to retrieve response body.' +
        'Likely caused by a programming error. Error Message:' +
        aCatch.name + aCatch.message + '\n' + aCatch.stack);
    update["content_hash"] = "<error>";
    loggingDB.saveRecord("http_responses", update);
  });
}

function isJS(httpChannel) {
  // Return true if this channel is loading javascript
  // We rely mostly on the content policy type to filter responses
  // and fall back to the URI and content type string for types that can
  // load various resource types.
  // See: http://searchfox.org/mozilla-central/source/dom/base/nsIContentPolicyBase.idl
  var contentPolicyType = httpChannel.loadInfo.externalContentPolicyType;
  if (contentPolicyType == 2) // script
    return true;
  if (contentPolicyType != 5 && // object
      contentPolicyType != 7 && // subdocument (iframe)
      contentPolicyType != 11 && // XMLHTTPRequest
      contentPolicyType != 16 && // websocket
      contentPolicyType != 19) // beacon response
    return false;

  var contentType;
  try {
    contentType = httpChannel.getResponseHeader("Content-Type");
  }catch (e) {  // Content-Type may not be present
    contentType = "";
  }

  if (contentType && contentType.toLowerCase().includes('javascript'))
    return true;
  var path = httpChannel.URI.path;
  if (path && path.split('?')[0].split('#')[0].endsWith('.js'))
    return true;
  return false;
}

// Instrument HTTP responses
var httpResponseHandler = function(respEvent, isCached, crawlID,
                                   saveJavascript, saveAllContent) {
  var httpChannel = respEvent.subject.QueryInterface(Ci.nsIHttpChannel);

  // http_responses table schema:
  // id [auto-filled], crawl_id, url, method, referrer, response_status,
  // response_status_text, headers, location, visit_id [auto-filled],
  // time_stamp, content_hash
  var update = {};

  update["crawl_id"] = crawlID;

  // ChannelId is a unique identifier that can be used to link requests and
  // responses. FF 49+
  update['channel_id'] = httpChannel.channelId;

  update["is_cached"] = isCached;

  var url = httpChannel.URI.spec;
  update["url"] = loggingDB.escapeString(url);

  var requestMethod = httpChannel.requestMethod;
  update["method"] = loggingDB.escapeString(requestMethod);

  var referrer = "";
  if (httpChannel.referrer)
    referrer = httpChannel.referrer.spec;
  update["referrer"] = loggingDB.escapeString(referrer);

  var responseStatus = httpChannel.responseStatus;
  update["response_status"] = responseStatus;

  var responseStatusText = httpChannel.responseStatusText;
  update["response_status_text"] = loggingDB.escapeString(responseStatusText);

  var current_time = new Date();
  update["time_stamp"] = current_time.toISOString();

  var location = "";
  try {
    location = httpChannel.getResponseHeader("location");
  }
  catch (e) {
    location = "";
  }
  update["location"] = loggingDB.escapeString(location);

  var headers = [];
  httpChannel.visitResponseHeaders({visitHeader: function(name, value) {
    var header_pair = [];
    header_pair.push(loggingDB.escapeString(name));
    header_pair.push(loggingDB.escapeString(value));
    headers.push(header_pair);
  }});
  update["headers"] = JSON.stringify(headers);

  if (saveAllContent) {
    logWithResponseBody(respEvent, update);
  } else if (saveJavascript && isJS(httpChannel)) {
    logWithResponseBody(respEvent, update);
  } else {
    loggingDB.saveRecord("http_responses", update);
  }
};

/*
 * Attach handlers to event monitor
 */

export const run = function(crawlID, saveJavascript, saveAllContent) {

  const allTypes = [
    "beacon",
    "csp_report",
    "font",
    "image",
    "imageset",
    "main_frame",
    "media",
    "object",
    "object_subrequest",
    "ping",
    "script",
    // "speculative",
    "stylesheet",
    "sub_frame",
    "web_manifest",
    "websocket",
    "xbl",
    "xml_dtd",
    "xmlhttprequest",
    "xslt",
    "other",
  ];

  // request listener

  browser.webRequest.onBeforeRequest.addListener(
    function(details) {
      // Ignore requests made by extensions
      if (details.originUrl && details.originUrl.indexOf("moz-extension://") > -1) {
        return;
      }
      console.log("webRequest.onBeforeRequest listener", details);
    },
    { urls: ["http://*/*", "https://*/*"], types: allTypes },
    ["requestBody"],
  );

  browser.webRequest.onBeforeRequest.addListener(
    function(details) {
      // Ignore requests made by extensions
      if (details.originUrl && details.originUrl.indexOf("moz-extension://") > -1) {
        return;
      }
      console.log("webRequest.onBeforeRequest listener", details);
    },
    { urls: ["http://*/*", "https://*/*"], types: allTypes },
    ["requestBody"],
  );

  browser.webRequest.onBeforeSendHeaders.addListener(
    function(details) {
      // Ignore requests made by extensions
      if (details.originUrl && details.originUrl.indexOf("moz-extension://") > -1) {
        return;
      }
      console.log("webRequest.onBeforeSendHeaders listener", details);
    },
    { urls: ["http://*/*", "https://*/*"], types: allTypes },
    ["requestHeaders"],
  );

  browser.webRequest.onCompleted.addListener(
    function(details) {
      // Ignore requests made by extensions
      if (details.originUrl && details.originUrl.indexOf("moz-extension://") > -1) {
        return;
      }
      console.log("webRequest.onCompleted listener", details);
    },
    { urls: ["http://*/*", "https://*/*"], types: allTypes },
    ["responseHeaders"],
  );

  /*
  // Monitor http events
  events.on("http-on-modify-request", function(event) {
    httpRequestHandler(event, crawlID);
  }, true);

  events.on("http-on-examine-response", function(event) {
    httpResponseHandler(event, false, crawlID, saveJavascript, saveAllContent);
  }, true);

  events.on("http-on-examine-cached-response", function(event) {
    httpResponseHandler(event, true, crawlID, saveJavascript, saveAllContent);
  }, true);

  events.on("http-on-examine-merged-response", function(event) {
    httpResponseHandler(event, true, crawlID, saveJavascript, saveAllContent);
  }, true);
  */
};
