import { HttpPostParser } from "../lib/http-post-parser";
import ResourceType = browser.webRequest.ResourceType;
import UploadData = browser.webRequest.UploadData;
import HttpHeaders = browser.webRequest.HttpHeaders;
import { escapeString } from "../lib/string-utils";
import { HttpRedirect, HttpRequest, HttpResponse } from "../types/schema";

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

/*
 * Attach handlers to event monitor
 */

export class HttpInstrument {
  private readonly dataReceiver;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID, saveJavascript, saveAllContent) {
    console.log(
      "HttpInstrument",
      HttpPostParser,
      crawlID,
      escapeString,
      saveJavascript,
      saveAllContent,
      escapeString,
      this.dataReceiver,
    );

    const allTypes: ResourceType[] = [
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

    const requestStemsFromExtension = details => {
      return (
        details.originUrl && details.originUrl.indexOf("moz-extension://") > -1
      );
    };

    /*
     * Attach handlers to event listeners
     */

    browser.webRequest.onBeforeRequest.addListener(
      details => {
        // Ignore requests made by extensions
        if (requestStemsFromExtension(details)) {
          return;
        }
        return this.onBeforeRequestHandler(
          details,
          crawlID,
          saveJavascript,
          saveAllContent,
        );
      },
      { urls: ["http://*/*", "https://*/*"], types: allTypes },
      saveJavascript || saveAllContent
        ? ["requestBody", "blocking"]
        : ["requestBody"],
    );

    browser.webRequest.onBeforeSendHeaders.addListener(
      details => {
        // Ignore requests made by extensions
        if (requestStemsFromExtension(details)) {
          return;
        }
        return this.onBeforeSendHeadersHandler(details, crawlID);
      },
      { urls: ["http://*/*", "https://*/*"], types: allTypes },
      ["requestHeaders"],
    );

    browser.webRequest.onBeforeRedirect.addListener(
      details => {
        // Ignore requests made by extensions
        if (requestStemsFromExtension(details)) {
          return;
        }
        return this.onBeforeRedirectHandler(details, crawlID);
      },
      { urls: ["http://*/*", "https://*/*"], types: allTypes },
      ["responseHeaders"],
    );

    browser.webRequest.onCompleted.addListener(
      details => {
        // Ignore requests made by extensions
        if (requestStemsFromExtension(details)) {
          return;
        }
        return this.onCompletedHandler(
          details,
          crawlID,
          saveJavascript,
          saveAllContent,
        );
      },
      { urls: ["http://*/*", "https://*/*"], types: allTypes },
      ["responseHeaders"],
    );
  }

  /*
   * HTTP Request Handler and Helper Functions
   */

  private get_stack_trace_str() {
    /*
    // return the stack trace as a string
    // TODO: check if http-on-modify-request is a good place to capture the stack
    // In the manual tests we could capture exactly the same trace as the
    // "Cause" column of the devtools network panel.
    const stacktrace = [];
    let frame = components.stack;
    if (frame && frame.caller) {
      // internal/chrome callers occupy the first three frames, pop them!
      frame = frame.caller.caller.caller;
      while (frame) {
        // chrome scripts appear as callers in some cases, filter them out
        const scheme = frame.filename.split("://")[0];
        if (["resource", "chrome", "file"].indexOf(scheme) === -1) {
          // ignore chrome scripts
          stacktrace.push(
            frame.name +
              "@" +
              frame.filename +
              ":" +
              frame.lineNumber +
              ":" +
              frame.columnNumber +
              ";" +
              frame.asyncCause,
          );
        }
        frame = frame.caller || frame.asyncCaller;
      }
    }
    return stacktrace.join("\n");
    */
  }

  private onBeforeSendHeadersHandler(
    details: {
      /**
       * The ID of the request. Request IDs are unique within a browser session. As a result, they could be used to
       * relate different events of the same request.
       */
      requestId: string;
      url: string;
      /** Standard HTTP method. */
      method: string;
      /**
       * The value 0 indicates that the request happens in the main frame; a positive value indicates the ID of a
       * subframe in which the request happens. If the document of a (sub-)frame is loaded (`type` is `main_frame` or
       * `sub_frame`), `frameId` indicates the ID of this frame, not the ID of the outer frame. Frame IDs are unique
       * within a tab.
       */
      frameId: number;
      /** ID of frame that wraps the frame which sent the request. Set to -1 if no parent frame exists. */
      parentFrameId: number;
      /** URL of the resource that triggered this request. */
      originUrl?: string;
      /** URL of the page into which the requested resource will be loaded. */
      documentUrl?: string;
      /** The ID of the tab in which the request takes place. Set to -1 if the request isn't related to a tab. */
      tabId: number;
      /** How the requested resource will be used. */
      type: ResourceType;
      /** The time when this signal is triggered, in milliseconds since the epoch. */
      timeStamp: number;
      /** The HTTP request headers that are going to be sent out with this request. */
      requestHeaders?: HttpHeaders;
    },
    crawlID,
  ) {
    console.log(
      "onBeforeSendHeadersHandler (previously httpRequestHandler)",
      details,
      crawlID,
      this.get_stack_trace_str,
    );

    // http_requests table schema:
    // id [auto-filled], crawl_id, url, method, referrer,
    // headers, visit_id [auto-filled], time_stamp
    const update = {} as HttpRequest;

    update.crawl_id = crawlID;

    // requestId is a unique identifier that can be used to link requests and responses
    update.channel_id = details.requestId;

    // const stacktrace_str = get_stack_trace_str();
    // update.req_call_stack = escapeString(stacktrace_str);

    const url = details.documentUrl;
    update.url = escapeString(url);

    const requestMethod = details.method;
    update.method = escapeString(requestMethod);

    // let referrer = "";
    // if (details.referrer) {
    //   referrer = details.referrer.spec;
    // }
    // update.referrer = escapeString(referrer);

    const current_time = new Date();
    update.time_stamp = current_time.toISOString();

    // let encodingType = "";
    const headers = [];
    const isOcsp = false;
    details.requestHeaders.map(requestHeader => {
      console.log("requestHeader", requestHeader);
    });
    /*
    details.visitRequestHeaders({
      visitHeader(name, value) {
        const header_pair = [];
        header_pair.push(escapeString(name));
        header_pair.push(escapeString(value));
        headers.push(header_pair);
        if (name === "Content-Type") {
          encodingType = value;
          if (encodingType.indexOf("application/ocsp-request") !== -1) {
            isOcsp = true;
          }
        }
      },
    });
    */

    if (requestMethod === "POST" && !isOcsp) {
      // TODO: set up await requestBody info from the onBeforeRequestHandler
      // (with timeout after ~10s if no such event was received)
      /*
      // don't process OCSP requests
      reqEvent.subject.QueryInterface(components.interfaces.nsIUploadChannel);
      if (reqEvent.subject.uploadStream) {
        reqEvent.subject.uploadStream.QueryInterface(
          components.interfaces.nsISeekableStream,
        );
        const postParser = new HttpPostParser(
          reqEvent.subject.uploadStream,
          this.dataReceiver,
        );
        const postObj = postParser.parsePostRequest(encodingType);

        // Add (POST) request headers from upload stream
        if ("post_headers" in postObj) {
          // Only store POST headers that we know and need. We may misinterpret POST data as headers
          // as detection is based on "key:value" format (non-header POST data can be in this format as well)
          const contentHeaders = [
            "Content-Type",
            "Content-Disposition",
            "Content-Length",
          ];
          for (const name in postObj.post_headers) {
            if (contentHeaders.includes(name)) {
              const header_pair = [];
              header_pair.push(escapeString(name));
              header_pair.push(
                escapeString(postObj.post_headers[name]),
              );
              headers.push(header_pair);
            }
          }
        }
        // we store POST body in JSON format, except when it's a string without a (key-value) structure
        if ("post_body" in postObj) {
          update.post_body = postObj.post_body;
        }
      }
      */
    }

    update.headers = JSON.stringify(headers);

    /*
    // Check if xhr
    let isXHR;
    try {
      const callbacks = details.notificationCallbacks;
      const xhr = callbacks ? callbacks.getInterface(Ci.nsIXMLHttpRequest) : null;
      isXHR = !!xhr;
    } catch (e) {
      isXHR = false;
    }
    update.is_XHR = isXHR;

    // Check if frame OR full page load
    let isFrameLoad;
    let isFullPageLoad;
    if (details.loadFlags & Ci.nsIHttpChannel.LOAD_INITIAL_DOCUMENT_URI) {
      isFullPageLoad = true;
      isFrameLoad = false;
    } else if (details.loadFlags & Ci.nsIHttpChannel.LOAD_DOCUMENT_URI) {
      isFrameLoad = true;
      isFullPageLoad = false;
    }
    update.is_full_page = isFullPageLoad;
    update.is_frame_load = isFrameLoad;

    // Grab the triggering and loading Principals
    let triggeringOrigin;
    let loadingOrigin;
    if (details.loadInfo.triggeringPrincipal) {
      triggeringOrigin = details.loadInfo.triggeringPrincipal.origin;
    }
    if (details.loadInfo.loadingPrincipal) {
      loadingOrigin = details.loadInfo.loadingPrincipal.origin;
    }
    update.triggering_origin = escapeString(triggeringOrigin);
    update.loading_origin = escapeString(loadingOrigin);

    // loadingDocument's href
    // The loadingDocument is the document the element resides, regardless of
    // how the load was triggered.
    let loadingHref;
    if (
      details.loadInfo.loadingDocument &&
      details.loadInfo.loadingDocument.location
    ) {
      loadingHref = details.loadInfo.loadingDocument.location.href;
    }
    update.loading_href = escapeString(loadingHref);

    // contentPolicyType of the requesting node. This is set by the type of
    // node making the request (i.e. an <img src=...> node will set to type 3).
    // For a mapping of integers to types see:
    // TODO: include the mapping directly
    // http://searchfox.org/mozilla-central/source/dom/base/nsIContentPolicyBase.idl)
    update.content_policy_type = details.loadInfo.externalContentPolicyType;

    // Do third-party checks
    // These specific checks are done because it's what's used in Tracking Protection
    // See: http://searchfox.org/mozilla-central/source/netwerk/base/nsChannelClassifier.cpp#107
    try {
      const isThirdPartyChannel = ThirdPartyUtil.isThirdPartyChannel(details);
      const topWindow = ThirdPartyUtil.getTopWindowForChannel(details);
      const topURI = ThirdPartyUtil.getURIFromWindow(topWindow);
      if (topURI) {
        const topUrl = topURI.spec;
        const channelURI = details.URI;
        const isThirdPartyToTopWindow = ThirdPartyUtil.isThirdPartyURI(
          channelURI,
          topURI,
        );
        update.is_third_party_to_top_window = isThirdPartyToTopWindow;
        update.is_third_party_channel = isThirdPartyChannel;
        update.top_level_url = escapeString(topUrl);
      }
    } catch (anError) {
      // Exceptions expected for channels triggered or loading in a
      // NullPrincipal or SystemPrincipal. They are also expected for favicon
      // loads, which we attempt to filter. Depending on the naming, some favicons
      // may continue to lead to error logs.
      if (
        update.triggering_origin !== "[System Principal]" &&
        update.triggering_origin !== undefined &&
        update.loading_origin !== "[System Principal]" &&
        update.loading_origin !== undefined &&
        !update.url.endsWith("ico")
      ) {
        this.dataReceiver.logError(
          "Error while retrieving additional channel information for URL: " +
          "\n" +
          update.url +
          "\n Error text:" +
          JSON.stringify(anError),
        );
      }
    }
    */

    this.dataReceiver.saveRecord("http_requests", update);
  }

  private onBeforeRequestHandler(
    details: {
      /**
       * The ID of the request. Request IDs are unique within a browser session. As a result, they could be used to
       * relate different events of the same request.
       */
      requestId: string;
      url: string;
      /** Standard HTTP method. */
      method: string;
      /**
       * The value 0 indicates that the request happens in the main frame; a positive value indicates the ID of a
       * subframe in which the request happens. If the document of a (sub-)frame is loaded (`type` is `main_frame` or
       * `sub_frame`), `frameId` indicates the ID of this frame, not the ID of the outer frame. Frame IDs are unique
       * within a tab.
       */
      frameId: number;
      /** ID of frame that wraps the frame which sent the request. Set to -1 if no parent frame exists. */
      parentFrameId: number;
      /** URL of the resource that triggered this request. */
      originUrl?: string;
      /** URL of the page into which the requested resource will be loaded. */
      documentUrl?: string;
      /** Contains the HTTP request body data. Only provided if extraInfoSpec contains 'requestBody'. */
      requestBody?: {
        /** Errors when obtaining request body data. */
        error?: string;
        /**
         * If the request method is POST and the body is a sequence of key-value pairs encoded in UTF8, encoded as
         * either multipart/form-data, or application/x-www-form-urlencoded, this dictionary is present and for
         * each key contains the list of all values for that key. If the data is of another media type, or if it is
         * malformed, the dictionary is not present. An example value of this dictionary is {'key': ['value1',
         * 'value2']}.
         */
        formData?: object;
        /**
         * If the request method is PUT or POST, and the body is not already parsed in formData, then the unparsed
         * request body elements are contained in this array.
         */
        raw?: UploadData[];
      };
      /** The ID of the tab in which the request takes place. Set to -1 if the request isn't related to a tab. */
      tabId: number;
      /** How the requested resource will be used. */
      type: ResourceType;
      /** The time when this signal is triggered, in milliseconds since the epoch. */
      timeStamp: number;
    },
    crawlID,
    saveJavascript,
    saveAllContent,
  ) {
    console.log(
      "onBeforeRequestHandler (previously httpRequestHandler)",
      details,
      crawlID,
      saveJavascript,
      saveAllContent,
    );
  }

  private onBeforeRedirectHandler(
    details: {
      /**
       * The ID of the request. Request IDs are unique within a browser session. As a result, they could be used to
       * relate different events of the same request.
       */
      requestId: string;
      url: string;
      /** Standard HTTP method. */
      method: string;
      /**
       * The value 0 indicates that the request happens in the main frame; a positive value indicates the ID of a
       * subframe in which the request happens. If the document of a (sub-)frame is loaded (`type` is `main_frame` or
       * `sub_frame`), `frameId` indicates the ID of this frame, not the ID of the outer frame. Frame IDs are unique
       * within a tab.
       */
      frameId: number;
      /** ID of frame that wraps the frame which sent the request. Set to -1 if no parent frame exists. */
      parentFrameId: number;
      /** URL of the resource that triggered this request. */
      originUrl?: string;
      /** URL of the page into which the requested resource will be loaded. */
      documentUrl?: string;
      /** The ID of the tab in which the request takes place. Set to -1 if the request isn't related to a tab. */
      tabId: number;
      /** How the requested resource will be used. */
      type: ResourceType;
      /** The time when this signal is triggered, in milliseconds since the epoch. */
      timeStamp: number;
      /**
       * The server IP address that the request was actually sent to. Note that it may be a literal IPv6 address.
       */
      ip?: string;
      /** Indicates if this response was fetched from disk cache. */
      fromCache: boolean;
      /** Standard HTTP status code returned by the server. */
      statusCode: number;
      /** The new URL. */
      redirectUrl: string;
      /** The HTTP response headers that were received along with this redirect. */
      responseHeaders?: HttpHeaders;
      /**
       * HTTP status line of the response or the 'HTTP/0.9 200 OK' string for HTTP/0.9 responses (i.e., responses
       * that lack a status line) or an empty string if there are no headers.
       */
      statusLine: string;
    },
    crawlID,
  ) {
    console.log(
      "onBeforeRedirectHandler (previously httpRequestHandler)",
      details,
      crawlID,
    );

    // Save HTTP redirect events

    /*
    // Events are saved to the `http_redirects` table, and map the old
    // request/response channel id to the new request/response channel id.
    // Implementation based on: https://stackoverflow.com/a/11240627
    const oldNotifications = details.notificationCallbacks;
    let oldEventSink = null;
    details.notificationCallbacks = {
      QueryInterface: XPCOMUtils.generateQI([
        Ci.nsIInterfaceRequestor,
        Ci.nsIChannelEventSink,
      ]),

      getInterface(iid) {
        // We are only interested in nsIChannelEventSink,
        // return the old callbacks for any other interface requests.
        if (iid.equals(Ci.nsIChannelEventSink)) {
          try {
            oldEventSink = oldNotifications.QueryInterface(iid);
          } catch (anError) {
            this.dataReceiver.logError(
              "Error during call to custom notificationCallbacks::getInterface." +
                JSON.stringify(anError),
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

      asyncOnChannelRedirect(oldChannel, newChannel, flags, callback) {
        const isTemporary = !!(flags & Ci.nsIChannelEventSink.REDIRECT_TEMPORARY);
        const isPermanent = !!(flags & Ci.nsIChannelEventSink.REDIRECT_PERMANENT);
        const isInternal = !!(flags & Ci.nsIChannelEventSink.REDIRECT_INTERNAL);
        const isSTSUpgrade = !!(
          flags & Ci.nsIChannelEventSink.REDIRECT_STS_UPGRADE
        );

        newChannel.QueryInterface(Ci.nsIHttpChannel);

        const httpRedirect: HttpRedirect = {
          crawl_id: crawlID,
          old_channel_id: oldChannel.channelId,
          new_channel_id: newChannel.channelId,
          is_temporary: isTemporary,
          is_permanent: isPermanent,
          is_internal: isInternal,
          is_sts_upgrade: isSTSUpgrade,
          time_stamp: new Date().toISOString(),
        };
        this.dataReceiver.saveRecord("http_redirects", httpRedirect);

        if (oldEventSink) {
          oldEventSink.asyncOnChannelRedirect(
            oldChannel,
            newChannel,
            flags,
            callback,
          );
        } else {
          callback.onRedirectVerifyCallback(Cr.NS_OK);
        }
      },
    };
    */

    const httpRedirect: HttpRedirect = {
      crawl_id: crawlID,
      old_channel_id: null, // previously: oldChannel.channelId,
      new_channel_id: details.requestId, // previously: newChannel.channelId,
      is_temporary: null, // TODO: Check status code
      is_permanent: null, // TODO: Check status code
      is_internal: null, // TODO: Check status code
      is_sts_upgrade: null, // TODO
      time_stamp: new Date().toISOString(),
    };
    this.dataReceiver.saveRecord("http_redirects", httpRedirect);
  }

  /*
  * HTTP Response Handler and Helper Functions
  */

  /*
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
    reject: null,
  };
  this.deferredDone.promise = new Promise(
    function(resolve, reject) {
      this.resolve = resolve;
      this.reject = reject;
    }.bind(this.deferredDone),
  );
  Object.freeze(this.deferredDone);
  this.promiseDone = this.deferredDone.promise;




  console.log("blocking request listener", details);

  // Used to parse Response stream to log content
  const filter: any = browser.webRequest.filterResponseData(
    details.requestId,
  ) as any;

  const decoder = new TextDecoder("utf-8");
  // const encoder = new TextEncoder();

  filter.ondata = event => {
    let str = decoder.decode(event.data, { stream: true });
    console.log("blocking request listener ondata: event, str", event, str);
    filter.disconnect();
  };




}
TracingListener.prototype = {
  onDataAvailable(aRequest, aContext, aInputStream, aOffset, aCount) {
    const iStream = new BinaryInputStream(aInputStream);
    const sStream = new StorageStream(8192, aCount, null);
    const oStream = new BinaryOutputStream(sStream.getOutputStream(0));

    // Copy received data as they come.
    const data = iStream.readBytes(aCount);
    this.receivedChunks.push(data);
    oStream.writeBytes(data, aCount);

    this.originalListener.onDataAvailable(
      aRequest,
      aContext,
      sStream.newInputStream(0),
      aOffset,
      aCount,
    );
  },
  onStartRequest(aRequest, aContext) {
    this.originalListener.onStartRequest(aRequest, aContext);
  },
  onStopRequest(aRequest, aContext, aStatusCode) {
    this.responseBody = this.receivedChunks.join("");
    delete this.receivedChunks;
    this.responseStatus = aStatusCode;

    this.originalListener.onStopRequest(aRequest, aContext, aStatusCode);
    this.deferredDone.resolve();
  },
  QueryInterface(aIID) {
    if (aIID.equals(Ci.nsIStreamListener) || aIID.equals(Ci.nsISupports)) {
      return this;
    }
    throw Cr.NS_NOINTERFACE;
  },
};
*/

  /*
// Helper functions to convert hash data to hex
function toHexString(charCode) {
  return ("0" + charCode.toString(16)).slice(-2);
}
function binaryHashtoHex(hash) {
  return Array.from(hash, (c, i) => toHexString(hash.charCodeAt(i))).join("");
}

function logWithResponseBody(respEvent, update) {
  // log with response body from an 'http-on-examine(-cached)?-response' event
  const newListener = new TracingListener();
  respEvent.subject.QueryInterface(Ci.nsITraceableChannel);
  newListener.originalListener = respEvent.subject.setNewListener(newListener);
  newListener.promiseDone
    .then(
      function() {
        const respBody = newListener.responseBody; // get response body as a string
        const bodyBytes = converter.convertToByteArray(respBody); // convert to bytes
        cryptoHash.init(cryptoHash.MD5);
        cryptoHash.update(bodyBytes, bodyBytes.length);
        const contentHash = binaryHashtoHex(cryptoHash.finish(false));
        update.content_hash = contentHash;
        this.dataReceiver.saveContent(
          escapeString(respBody),
          escapeString(contentHash),
        );
        this.dataReceiver.saveRecord("http_responses", update);
      },
      function(aReason) {
        this.dataReceiver.logError(
          "Unable to retrieve response body." + JSON.stringify(aReason),
        );
        update.content_hash = "<error>";
        this.dataReceiver.saveRecord("http_responses", update);
      },
    )
    .catch(function(aCatch) {
      this.dataReceiver.logError(
        "Unable to retrieve response body." +
          "Likely caused by a programming error. Error Message:" +
          aCatch.name +
          aCatch.message +
          "\n" +
          aCatch.stack,
      );
      update.content_hash = "<error>";
      this.dataReceiver.saveRecord("http_responses", update);
    });
}

function isJS(details) {
  // Return true if this channel is loading javascript
  // We rely mostly on the content policy type to filter responses
  // and fall back to the URI and content type string for types that can
  // load various resource types.
  // See: http://searchfox.org/mozilla-central/source/dom/base/nsIContentPolicyBase.idl
  const contentPolicyType = details.loadInfo.externalContentPolicyType;
  if (contentPolicyType === 2) {
    // script
    return true;
  }
  if (
    contentPolicyType !== 5 && // object
    contentPolicyType !== 7 && // subdocument (iframe)
    contentPolicyType !== 11 && // XMLHTTPRequest
    contentPolicyType !== 16 && // websocket
    contentPolicyType !== 19
  ) {
    // beacon response
    return false;
  }

  let contentType;
  try {
    contentType = details.getResponseHeader("Content-Type");
  } catch (e) {
    // Content-Type may not be present
    contentType = "";
  }

  if (contentType && contentType.toLowerCase().includes("javascript")) {
    return true;
  }
  const path = details.URI.path;
  if (
    path &&
    path
      .split("?")[0]
      .split("#")[0]
      .endsWith(".js")
  ) {
    return true;
  }
  return false;
}
*/

  // Instrument HTTP responses
  private onCompletedHandler(
    details: {
      /**
       * The ID of the request. Request IDs are unique within a browser session. As a result, they could be used to
       * relate different events of the same request.
       */
      requestId: string;
      url: string;
      /** Standard HTTP method. */
      method: string;
      /**
       * The value 0 indicates that the request happens in the main frame; a positive value indicates the ID of a
       * subframe in which the request happens. If the document of a (sub-)frame is loaded (`type` is `main_frame` or
       * `sub_frame`), `frameId` indicates the ID of this frame, not the ID of the outer frame. Frame IDs are unique
       * within a tab.
       */
      frameId: number;
      /** ID of frame that wraps the frame which sent the request. Set to -1 if no parent frame exists. */
      parentFrameId: number;
      /** URL of the resource that triggered this request. */
      originUrl?: string;
      /** URL of the page into which the requested resource will be loaded. */
      documentUrl?: string;
      /** The ID of the tab in which the request takes place. Set to -1 if the request isn't related to a tab. */
      tabId: number;
      /** How the requested resource will be used. */
      type: ResourceType;
      /** The time when this signal is triggered, in milliseconds since the epoch. */
      timeStamp: number;
      /**
       * The server IP address that the request was actually sent to. Note that it may be a literal IPv6 address.
       */
      ip?: string;
      /** Indicates if this response was fetched from disk cache. */
      fromCache: boolean;
      /** Standard HTTP status code returned by the server. */
      statusCode: number;
      /** The HTTP response headers that were received along with this response. */
      responseHeaders?: HttpHeaders;
      /**
       * HTTP status line of the response or the 'HTTP/0.9 200 OK' string for HTTP/0.9 responses (i.e., responses
       * that lack a status line) or an empty string if there are no headers.
       */
      statusLine: string;
    },
    crawlID,
    saveJavascript,
    saveAllContent,
  ) {
    console.log(
      "onCompletedHandler (previously httpRequestHandler)",
      details,
      crawlID,
      saveJavascript,
      saveAllContent,
    );

    // http_responses table schema:
    // id [auto-filled], crawl_id, url, method, referrer, response_status,
    // response_status_text, headers, location, visit_id [auto-filled],
    // time_stamp, content_hash
    const update = {} as HttpResponse;

    update.crawl_id = crawlID;

    // requestId is a unique identifier that can be used to link requests and responses
    update.channel_id = details.requestId;

    const isCached = details.fromCache;
    update.is_cached = isCached;

    const url = details.documentUrl;
    update.url = escapeString(url);

    const requestMethod = details.method;
    update.method = escapeString(requestMethod);

    // let referrer = "";
    // if (details.referrer) {
    //   referrer = details.referrer.spec;
    // }
    // update.referrer = escapeString(referrer);

    const responseStatus = details.statusCode;
    update.response_status = responseStatus;

    const responseStatusText = details.statusLine;
    update.response_status_text = escapeString(responseStatusText);

    const current_time = new Date();
    update.time_stamp = current_time.toISOString();

    /*
    let location = "";
    try {
      location = details.getResponseHeader("location");
    } catch (e) {
      location = "";
    }
    update.location = escapeString(location);

    const headers = [];
    details.visitResponseHeaders({
      visitHeader(name, value) {
        const header_pair = [];
        header_pair.push(escapeString(name));
        header_pair.push(escapeString(value));
        headers.push(header_pair);
      },
    });
    update.headers = JSON.stringify(headers);
    */

    /*
    if (saveAllContent) {
      logWithResponseBody(respEvent, update);
    } else if (saveJavascript && isJS(details)) {
      logWithResponseBody(respEvent, update);
    } else {
      */
    this.dataReceiver.saveRecord("http_responses", update);
    /*
    }
    */
  }
}
