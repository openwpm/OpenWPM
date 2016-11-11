// TODO: doesn't work with e10s -- be sure to launch nightly disabling remote tabs
const {Cc, Ci, CC, Cu, components} = require("chrome");
var events = require("sdk/system/events");
const data = require("sdk/self").data;
var loggingDB = require("./loggingdb.js");
var timers = require("sdk/timers");
var pageManager = require("./page-manager.js");
Cu.import('resource://gre/modules/Services.jsm');

var BinaryInputStream = CC('@mozilla.org/binaryinputstream;1',
    'nsIBinaryInputStream', 'setInputStream');
var BinaryOutputStream = CC('@mozilla.org/binaryoutputstream;1',
    'nsIBinaryOutputStream', 'setOutputStream');
var StorageStream = CC('@mozilla.org/storagestream;1',
    'nsIStorageStream', 'init');
const ThirdPartyUtil = Cc["@mozilla.org/thirdpartyutil;1"].getService(
                       Ci.mozIThirdPartyUtil);

function get_stack_trace_str(){
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

exports.run = function(crawlID) {
  // Set up logging
  var createHttpRequestTable = data.load("create_http_requests_table.sql");
  loggingDB.executeSQL(createHttpRequestTable, false);

  var createHttpResponseTable = data.load("create_http_responses_table.sql");
  loggingDB.executeSQL(createHttpResponseTable, false);

  // Instrument HTTP requests
  events.on("http-on-modify-request", function(event) {
    var httpChannel = event.subject.QueryInterface(Ci.nsIHttpChannel);

    // http_requests table schema:
    // id [auto-filled], crawl_id, url, method, referrer,
    // headers, visit_id [auto-filled], time_stamp
    var update = {};

    update["crawl_id"] = crawlID;

    var stacktrace_str = get_stack_trace_str();
    update["req_call_stack"] = loggingDB.escapeString(stacktrace_str);

    var url = httpChannel.URI.spec;
    update["url"] = loggingDB.escapeString(url);

    var requestMethod = httpChannel.requestMethod;
    update["method"] = loggingDB.escapeString(requestMethod);

    var referrer = "";
    if(httpChannel.referrer)
      referrer = httpChannel.referrer.spec;
    update["referrer"] = loggingDB.escapeString(referrer);

    var current_time = new Date();
    update["time_stamp"] = current_time.toISOString();

    var headers = [];
    httpChannel.visitRequestHeaders({visitHeader: function(name, value) {
      var header_pair = [];
      header_pair.push(loggingDB.escapeString(name));
      header_pair.push(loggingDB.escapeString(value));
      headers.push(header_pair);
    }});
    update["headers"] = JSON.stringify(headers);

    //
    // Let's grab some extra information here
    //

    // Test if xhr
    var isXHR;
    try {
        var callbacks = httpChannel.notificationCallbacks;
        var xhr = callbacks ? callbacks.getInterface(Ci.nsIXMLHttpRequest) : null;
        isXHR = !!xhr;
    } catch (e) {
        isXHR = false;
    }
    update["is_XHR"] = isXHR;

    // Test if frame OR full page load
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

    // Triggering and loading Principal
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
    // http://searchfox.org/mozilla-central/source/dom/base/nsIContentPolicyBase.idl)
    // TODO: can we include the string types directly?
    var contentPolicyType;
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
        var isThirdPartyWindow = ThirdPartyUtil.isThirdPartyURI(channelURI, topURI);
        update["is_third_party_window"] = isThirdPartyWindow;
        update["is_third_party_channel"] = isThirdPartyChannel;
        update["top_level_url"] = loggingDB.escapeString(topUrl);
      }
    } catch (e) {
      //Exceptions expected for channels triggered by a NullPrincipal or SystemPrincipal
      //TODO probably a cleaner way to handle this
    }
    loggingDB.executeSQL(loggingDB.createInsert("http_requests_ext", update), true);
  }, true);


  function TracingListener() {
    this.receivedChunks = []; // array for incoming data. onStopRequest we combine these to get the full source
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
      var iStream = new BinaryInputStream(aInputStream) // binaryaInputStream
      var sStream = new StorageStream(8192, aCount, null);
      var oStream = new BinaryOutputStream(sStream.getOutputStream(0));

      // Copy received data as they come.
      var data = iStream.readBytes(aCount);
      this.receivedChunks.push(data);
      oStream.writeBytes(data, aCount);

      this.originalListener.onDataAvailable(aRequest, aContext, sStream.newInputStream(0), aOffset, aCount);
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

  // Instrument HTTP responses
  var httpResponseHandler = function(event, isCached) {
    var httpChannel = event.subject.QueryInterface(Ci.nsIHttpChannel);

    // http_responses table schema:
    // id [auto-filled], crawl_id, url, method, referrer, response_status,
    // response_status_text, headers, location, visit_id [auto-filled],
    // time_stamp, content_hash
    var update = {};

    update["crawl_id"] = crawlID;

    var url = httpChannel.URI.spec;
    update["url"] = loggingDB.escapeString(url);

    var requestMethod = httpChannel.requestMethod;
    update["method"] = loggingDB.escapeString(requestMethod);

    var referrer = "";
    if(httpChannel.referrer)
      referrer = httpChannel.referrer.spec;
    update["referrer"] = loggingDB.escapeString(referrer);

    var responseStatus = httpChannel.responseStatus;
    update["response_status"] = responseStatus;

    var responseStatusText = httpChannel.responseStatusText;
    update["response_status_text"] = loggingDB.escapeString(responseStatusText);

    // TODO: add "is_cached" boolean?

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

    var newListener = new TracingListener();
    event.subject.QueryInterface(Ci.nsITraceableChannel);
    newListener.originalListener = event.subject.setNewListener(newListener);
    newListener.promiseDone.then(
      function() {
        // no error happened
        update["content_hash"] = "testing";
        loggingDB.executeSQL(loggingDB.createInsert("http_responses_ext", update), true);

      },
      function(aReason) {
        // promise was rejected
      }
    ).catch(
      function(aCatch) {
        console.error('something went wrong, a typo by dev probably:', aCatch);
      }
    );


  };

  events.on("http-on-examine-response", function(event) {
    httpResponseHandler(event, false);
  }, true);

  // Instrument cached HTTP responses
  events.on("http-on-examine-cached-response", function(event) {
    httpResponseHandler(event, true);
  }, true);

};
