/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = "./content.js/index.js");
/******/ })
/************************************************************************/
/******/ ({

/***/ "./content.js/index.js":
/*!*****************************!*\
  !*** ./content.js/index.js ***!
  \*****************************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var openwpm_webext_instrumentation__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! openwpm-webext-instrumentation */ "./node_modules/openwpm-webext-instrumentation/build/module/index.js");


Object(openwpm_webext_instrumentation__WEBPACK_IMPORTED_MODULE_0__["injectJavascriptInstrumentPageScript"])();



/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/background/cookie-instrument.js":
/*!**************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/background/cookie-instrument.js ***!
  \**************************************************************************************************/
/*! exports provided: transformCookieObjectToMatchOpenWPMSchema, CookieInstrument */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "transformCookieObjectToMatchOpenWPMSchema", function() { return transformCookieObjectToMatchOpenWPMSchema; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CookieInstrument", function() { return CookieInstrument; });
/* harmony import */ var _lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../lib/extension-session-event-ordinal */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-event-ordinal.js");
/* harmony import */ var _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../lib/extension-session-uuid */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-uuid.js");
/* harmony import */ var _lib_string_utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../lib/string-utils */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/string-utils.js");



const transformCookieObjectToMatchOpenWPMSchema = (cookie) => {
    const javascriptCookie = {};
    // Expiry time (in seconds)
    // May return ~Max(int64). I believe this is a session
    // cookie which doesn't expire. Sessions cookies with
    // non-max expiry time expire after session or at expiry.
    const expiryTime = cookie.expirationDate; // returns seconds
    let expiryTimeString;
    const maxInt64 = 9223372036854776000;
    if (!cookie.expirationDate || expiryTime === maxInt64) {
        expiryTimeString = "9999-12-31T21:59:59.000Z";
    }
    else {
        const expiryTimeDate = new Date(expiryTime * 1000); // requires milliseconds
        expiryTimeString = expiryTimeDate.toISOString();
    }
    javascriptCookie.expiry = expiryTimeString;
    javascriptCookie.is_http_only = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["boolToInt"])(cookie.httpOnly);
    javascriptCookie.is_host_only = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["boolToInt"])(cookie.hostOnly);
    javascriptCookie.is_session = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["boolToInt"])(cookie.session);
    javascriptCookie.host = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(cookie.domain);
    javascriptCookie.is_secure = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["boolToInt"])(cookie.secure);
    javascriptCookie.name = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(cookie.name);
    javascriptCookie.path = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(cookie.path);
    javascriptCookie.value = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(cookie.value);
    javascriptCookie.same_site = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(cookie.sameSite);
    javascriptCookie.first_party_domain = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(cookie.firstPartyDomain);
    javascriptCookie.store_id = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(cookie.storeId);
    javascriptCookie.time_stamp = new Date().toISOString();
    return javascriptCookie;
};
class CookieInstrument {
    constructor(dataReceiver) {
        this.dataReceiver = dataReceiver;
    }
    run(crawlID) {
        // Instrument cookie changes
        this.onChangedListener = async (changeInfo) => {
            const eventType = changeInfo.removed ? "deleted" : "added-or-changed";
            const update = {
                record_type: eventType,
                change_cause: changeInfo.cause,
                crawl_id: crawlID,
                extension_session_uuid: _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__["extensionSessionUuid"],
                event_ordinal: Object(_lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__["incrementedEventOrdinal"])(),
                ...transformCookieObjectToMatchOpenWPMSchema(changeInfo.cookie),
            };
            this.dataReceiver.saveRecord("javascript_cookies", update);
        };
        browser.cookies.onChanged.addListener(this.onChangedListener);
    }
    async saveAllCookies(crawlID) {
        const allCookies = await browser.cookies.getAll({});
        await Promise.all(allCookies.map((cookie) => {
            const update = {
                record_type: "manual-export",
                crawl_id: crawlID,
                extension_session_uuid: _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__["extensionSessionUuid"],
                ...transformCookieObjectToMatchOpenWPMSchema(cookie),
            };
            return this.dataReceiver.saveRecord("javascript_cookies", update);
        }));
    }
    cleanup() {
        if (this.onChangedListener) {
            browser.cookies.onChanged.removeListener(this.onChangedListener);
        }
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY29va2llLWluc3RydW1lbnQuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvYmFja2dyb3VuZC9jb29raWUtaW5zdHJ1bWVudC50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxPQUFPLEVBQUUsdUJBQXVCLEVBQUUsTUFBTSx3Q0FBd0MsQ0FBQztBQUNqRixPQUFPLEVBQUUsb0JBQW9CLEVBQUUsTUFBTSwrQkFBK0IsQ0FBQztBQUNyRSxPQUFPLEVBQUUsU0FBUyxFQUFFLFlBQVksRUFBRSxNQUFNLHFCQUFxQixDQUFDO0FBSzlELE1BQU0sQ0FBQyxNQUFNLHlDQUF5QyxHQUFHLENBQUMsTUFBYyxFQUFFLEVBQUU7SUFDMUUsTUFBTSxnQkFBZ0IsR0FBRyxFQUFzQixDQUFDO0lBRWhELDJCQUEyQjtJQUMzQixzREFBc0Q7SUFDdEQscURBQXFEO0lBQ3JELHlEQUF5RDtJQUN6RCxNQUFNLFVBQVUsR0FBRyxNQUFNLENBQUMsY0FBYyxDQUFDLENBQUMsa0JBQWtCO0lBQzVELElBQUksZ0JBQWdCLENBQUM7SUFDckIsTUFBTSxRQUFRLEdBQUcsbUJBQW1CLENBQUM7SUFDckMsSUFBSSxDQUFDLE1BQU0sQ0FBQyxjQUFjLElBQUksVUFBVSxLQUFLLFFBQVEsRUFBRTtRQUNyRCxnQkFBZ0IsR0FBRywwQkFBMEIsQ0FBQztLQUMvQztTQUFNO1FBQ0wsTUFBTSxjQUFjLEdBQUcsSUFBSSxJQUFJLENBQUMsVUFBVSxHQUFHLElBQUksQ0FBQyxDQUFDLENBQUMsd0JBQXdCO1FBQzVFLGdCQUFnQixHQUFHLGNBQWMsQ0FBQyxXQUFXLEVBQUUsQ0FBQztLQUNqRDtJQUNELGdCQUFnQixDQUFDLE1BQU0sR0FBRyxnQkFBZ0IsQ0FBQztJQUMzQyxnQkFBZ0IsQ0FBQyxZQUFZLEdBQUcsU0FBUyxDQUFDLE1BQU0sQ0FBQyxRQUFRLENBQUMsQ0FBQztJQUMzRCxnQkFBZ0IsQ0FBQyxZQUFZLEdBQUcsU0FBUyxDQUFDLE1BQU0sQ0FBQyxR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

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/background/http-instrument.js":
/*!************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/background/http-instrument.js ***!
  \************************************************************************************************/
/*! exports provided: HttpInstrument */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "HttpInstrument", function() { return HttpInstrument; });
/* harmony import */ var _lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../lib/extension-session-event-ordinal */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-event-ordinal.js");
/* harmony import */ var _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../lib/extension-session-uuid */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-uuid.js");
/* harmony import */ var _lib_http_post_parser__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../lib/http-post-parser */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/http-post-parser.js");
/* harmony import */ var _lib_pending_request__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../lib/pending-request */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-request.js");
/* harmony import */ var _lib_pending_response__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../lib/pending-response */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-response.js");
/* harmony import */ var _lib_string_utils__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../lib/string-utils */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/string-utils.js");






/**
 * Note: Different parts of the desired information arrives in different events as per below:
 * request = headers in onBeforeSendHeaders + body in onBeforeRequest
 * response = headers in onCompleted + body via a onBeforeRequest filter
 * redirect = original request headers+body, followed by a onBeforeRedirect and then a new set of request headers+body and response headers+body
 * Docs: https://developer.mozilla.org/en-US/docs/User:wbamberg/webRequest.RequestDetails
 */
class HttpInstrument {
    constructor(dataReceiver) {
        this.pendingRequests = {};
        this.pendingResponses = {};
        this.dataReceiver = dataReceiver;
    }
    run(crawlID, saveJavascript, saveAllContent) {
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
        const filter = { urls: ["<all_urls>"], types: allTypes };
        const requestStemsFromExtension = details => {
            return (details.originUrl && details.originUrl.indexOf("moz-extension://") > -1);
        };
        /*
         * Attach handlers to event listeners
         */
        this.onBeforeRequestListener = details => {
            const blockingResponseThatDoesNothing = {};
            // Ignore requests made by extensions
            if (requestStemsFromExtension(details)) {
                return blockingResponseThatDoesNothing;
            }
            const pendingRequest = this.getPendingRequest(details.requestId);
            pendingRequest.resolveOnBeforeRequestEventDetails(details);
            const pendingResponse = this.getPendingResponse(details.requestId);
            pendingResponse.resolveOnBeforeRequestEventDetails(details);
            if (saveAllContent) {
                pendingResponse.addResponseResponseBodyListener(details);
            }
            else if (saveJavascript && this.isJS(details.type)) {
                pendingResponse.addResponseResponseBodyListener(details);
            }
            return blockingResponseThatDoesNothing;
        };
        browser.webRequest.onBeforeRequest.addListener(this.onBeforeRequestListener, filter, saveJavascript || saveAllContent
            ? ["requestBody", "blocking"]
            : ["requestBody"]);
        this.onBeforeSendHeadersListener = details => {
            // Ignore requests made by extensions
            if (requestStemsFromExtension(details)) {
                return;
            }
            const pendingRequest = this.getPendingRequest(details.requestId);
            pendingRequest.resolveOnBeforeSendHeadersEventDetails(details);
            this.onBeforeSendHeadersHandler(details, crawlID, Object(_lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__["incrementedEventOrdinal"])());
        };
        browser.webRequest.onBeforeSendHeaders.addListener(this.onBeforeSendHeadersListener, filter, ["requestHeaders"]);
        this.onBeforeRedirectListener = details => {
            // Ignore requests made by extensions
            if (requestStemsFromExtension(details)) {
                return;
            }
            this.onBeforeRedirectHandler(details, crawlID, Object(_lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__["incrementedEventOrdinal"])());
        };
        browser.webRequest.onBeforeRedirect.addListener(this.onBeforeRedirectListener, filter, ["responseHeaders"]);
        this.onCompletedListener = details => {
            // Ignore requests made by extensions
            if (requestStemsFromExtension(details)) {
                return;
            }
            const pendingResponse = this.getPendingResponse(details.requestId);
            pendingResponse.resolveOnCompletedEventDetails(details);
            this.onCompletedHandler(details, crawlID, Object(_lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__["incrementedEventOrdinal"])(), saveJavascript, saveAllContent);
        };
        browser.webRequest.onCompleted.addListener(this.onCompletedListener, filter, ["responseHeaders"]);
    }
    cleanup() {
        if (this.onBeforeRequestListener) {
            browser.webRequest.onBeforeRequest.removeListener(this.onBeforeRequestListener);
        }
        if (this.onBeforeSendHeadersListener) {
            browser.webRequest.onBeforeSendHeaders.removeListener(this.onBeforeSendHeadersListener);
        }
        if (this.onBeforeRedirectListener) {
            browser.webRequest.onBeforeRedirect.removeListener(this.onBeforeRedirectListener);
        }
        if (this.onCompletedListener) {
            browser.webRequest.onCompleted.removeListener(this.onCompletedListener);
        }
    }
    getPendingRequest(requestId) {
        if (!this.pendingRequests[requestId]) {
            this.pendingRequests[requestId] = new _lib_pending_request__WEBPACK_IMPORTED_MODULE_3__["PendingRequest"]();
        }
        return this.pendingRequests[requestId];
    }
    getPendingResponse(requestId) {
        if (!this.pendingResponses[requestId]) {
            this.pendingResponses[requestId] = new _lib_pending_response__WEBPACK_IMPORTED_MODULE_4__["PendingResponse"]();
        }
        return this.pendingResponses[requestId];
    }
    /*
     * HTTP Request Handler and Helper Functions
     */
    /*
    // TODO: Refactor to corresponding webext logic or discard
    private get_stack_trace_str() {
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
    }
    */
    async onBeforeSendHeadersHandler(details, crawlID, eventOrdinal) {
        /*
        console.log(
          "onBeforeSendHeadersHandler (previously httpRequestHandler)",
          details,
          crawlID,
        );
        */
        const tab = details.tabId > -1
            ? await browser.tabs.get(details.tabId)
            : { windowId: undefined, incognito: undefined, url: undefined };
        const update = {};
        update.incognito = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["boolToInt"])(tab.incognito);
        update.crawl_id = crawlID;
        update.extension_session_uuid = _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__["extensionSessionUuid"];
        update.event_ordinal = eventOrdinal;
        update.window_id = tab.windowId;
        update.tab_id = details.tabId;
        update.frame_id = details.frameId;
        // requestId is a unique identifier that can be used to link requests and responses
        update.request_id = details.requestId;
        // const stacktrace_str = get_stack_trace_str();
        // update.req_call_stack = escapeString(stacktrace_str);
        const url = details.url;
        update.url = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeUrl"])(url);
        const requestMethod = details.method;
        update.method = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(requestMethod);
        const current_time = new Date(details.timeStamp);
        update.time_stamp = current_time.toISOString();
        let encodingType = "";
        let referrer = "";
        const headers = [];
        let isOcsp = false;
        if (details.requestHeaders) {
            details.requestHeaders.map(requestHeader => {
                const { name, value } = requestHeader;
                const header_pair = [];
                header_pair.push(Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(name));
                header_pair.push(Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(value));
                headers.push(header_pair);
                if (name === "Content-Type") {
                    encodingType = value;
                    if (encodingType.indexOf("application/ocsp-request") !== -1) {
                        isOcsp = true;
                    }
                }
                if (name === "Referer") {
                    referrer = value;
                }
            });
        }
        update.referrer = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(referrer);
        if (requestMethod === "POST" && !isOcsp /* don't process OCSP requests */) {
            const pendingRequest = this.getPendingRequest(details.requestId);
            const resolved = await pendingRequest.resolvedWithinTimeout(1000);
            if (!resolved) {
                this.dataReceiver.logError("Pending request timed out waiting for data from both onBeforeRequest and onBeforeSendHeaders events");
            }
            else {
                const onBeforeRequestEventDetails = await pendingRequest.onBeforeRequestEventDetails;
                const requestBody = onBeforeRequestEventDetails.requestBody;
                if (requestBody) {
                    const postParser = new _lib_http_post_parser__WEBPACK_IMPORTED_MODULE_2__["HttpPostParser"](
                    // details,
                    onBeforeRequestEventDetails, this.dataReceiver);
                    const postObj = postParser
                        .parsePostRequest();
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
                                header_pair.push(Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(name));
                                header_pair.push(Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(postObj.post_headers[name]));
                                headers.push(header_pair);
                            }
                        }
                    }
                    // we store POST body in JSON format, except when it's a string without a (key-value) structure
                    if ("post_body" in postObj) {
                        update.post_body = postObj.post_body;
                    }
                }
            }
        }
        update.headers = JSON.stringify(headers);
        // Check if xhr
        const isXHR = details.type === "xmlhttprequest";
        update.is_XHR = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["boolToInt"])(isXHR);
        // Check if frame OR full page load
        const isFullPageLoad = details.frameId === 0;
        const isFrameLoad = details.type === "sub_frame";
        update.is_full_page = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["boolToInt"])(isFullPageLoad);
        update.is_frame_load = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["boolToInt"])(isFrameLoad);
        // Grab the triggering and loading Principals
        let triggeringOrigin;
        let loadingOrigin;
        if (details.originUrl) {
            const parsedOriginUrl = new URL(details.originUrl);
            triggeringOrigin = parsedOriginUrl.origin;
        }
        if (details.documentUrl) {
            const parsedDocumentUrl = new URL(details.documentUrl);
            loadingOrigin = parsedDocumentUrl.origin;
        }
        update.triggering_origin = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(triggeringOrigin);
        update.loading_origin = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(loadingOrigin);
        // loadingDocument's href
        // The loadingDocument is the document the element resides, regardless of
        // how the load was triggered.
        const loadingHref = details.documentUrl;
        update.loading_href = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(loadingHref);
        // resourceType of the requesting node. This is set by the type of
        // node making the request (i.e. an <img src=...> node will set to type "image").
        // Documentation:
        // https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/ResourceType
        update.resource_type = details.type;
        /*
        // TODO: Refactor to corresponding webext logic or discard
        const ThirdPartyUtil = Cc["@mozilla.org/thirdpartyutil;1"].getService(
                               Ci.mozIThirdPartyUtil);
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
        update.top_level_url = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeUrl"])(tab.url);
        update.parent_frame_id = details.parentFrameId;
        update.frame_ancestors = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(JSON.stringify(details.frameAncestors));
        this.dataReceiver.saveRecord("http_requests", update);
    }
    async onBeforeRedirectHandler(details, crawlID, eventOrdinal) {
        /*
        console.log(
          "onBeforeRedirectHandler (previously httpRequestHandler)",
          details,
          crawlID,
        );
        */
        // Save HTTP redirect events
        // Events are saved to the `http_redirects` table
        /*
        // TODO: Refactor to corresponding webext logic or discard
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
    
            newChannel.QueryInterface(Ci.nsIHttpChannel);
    
            const httpRedirect: HttpRedirect = {
              crawl_id: crawlID,
              old_request_id: oldChannel.channelId,
              new_request_id: newChannel.channelId,
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
        const responseStatus = details.statusCode;
        const responseStatusText = details.statusLine;
        const tab = details.tabId > -1
            ? await browser.tabs.get(details.tabId)
            : { windowId: undefined, incognito: undefined };
        const httpRedirect = {
            incognito: Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["boolToInt"])(tab.incognito),
            crawl_id: crawlID,
            old_request_url: Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeUrl"])(details.url),
            old_request_id: details.requestId,
            new_request_url: Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeUrl"])(details.redirectUrl),
            new_request_id: null,
            extension_session_uuid: _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__["extensionSessionUuid"],
            event_ordinal: eventOrdinal,
            window_id: tab.windowId,
            tab_id: details.tabId,
            frame_id: details.frameId,
            response_status: responseStatus,
            response_status_text: Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(responseStatusText),
            time_stamp: new Date(details.timeStamp).toISOString(),
        };
        this.dataReceiver.saveRecord("http_redirects", httpRedirect);
    }
    /*
    * HTTP Response Handlers and Helper Functions
    */
    async logWithResponseBody(details, update) {
        const pendingResponse = this.getPendingResponse(details.requestId);
        try {
            const responseBodyListener = pendingResponse.responseBodyListener;
            const respBody = await responseBodyListener.getResponseBody();
            const contentHash = await responseBodyListener.getContentHash();
            this.dataReceiver.saveContent(Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(respBody), Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(contentHash));
            this.dataReceiver.saveRecord("http_responses", update);
        }
        catch (err) {
            /*
            // TODO: Refactor to corresponding webext logic or discard
            dataReceiver.logError(
              "Unable to retrieve response body." + JSON.stringify(aReason),
            );
            update.content_hash = "<error>";
            dataReceiver.saveRecord("http_responses", update);
            */
            this.dataReceiver.logError("Unable to retrieve response body." +
                "Likely caused by a programming error. Error Message:" +
                err.name +
                err.message +
                "\n" +
                err.stack);
            update.content_hash = "<error>";
            this.dataReceiver.saveRecord("http_responses", update);
        }
    }
    /**
     * Return true if this request is loading javascript
     * We rely mostly on the content policy type to filter responses
     * and fall back to the URI and content type string for types that can
     * load various resource types.
     * See: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/ResourceType
     *
     * @param resourceType
     */
    isJS(resourceType) {
        return resourceType === "script";
    }
    // Instrument HTTP responses
    async onCompletedHandler(details, crawlID, eventOrdinal, saveJavascript, saveAllContent) {
        /*
        console.log(
          "onCompletedHandler (previously httpRequestHandler)",
          details,
          crawlID,
          saveJavascript,
          saveAllContent,
        );
        */
        const tab = details.tabId > -1
            ? await browser.tabs.get(details.tabId)
            : { windowId: undefined, incognito: undefined };
        const update = {};
        update.incognito = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["boolToInt"])(tab.incognito);
        update.crawl_id = crawlID;
        update.extension_session_uuid = _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__["extensionSessionUuid"];
        update.event_ordinal = eventOrdinal;
        update.window_id = tab.windowId;
        update.tab_id = details.tabId;
        update.frame_id = details.frameId;
        // requestId is a unique identifier that can be used to link requests and responses
        update.request_id = details.requestId;
        const isCached = details.fromCache;
        update.is_cached = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["boolToInt"])(isCached);
        const url = details.url;
        update.url = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeUrl"])(url);
        const requestMethod = details.method;
        update.method = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(requestMethod);
        // TODO: Refactor to corresponding webext logic or discard
        // (request headers are not available in http response event listener object,
        // but the referrer property of the corresponding request could be queried)
        //
        // let referrer = "";
        // if (details.referrer) {
        //   referrer = details.referrer.spec;
        // }
        // update.referrer = escapeString(referrer);
        const responseStatus = details.statusCode;
        update.response_status = responseStatus;
        const responseStatusText = details.statusLine;
        update.response_status_text = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(responseStatusText);
        const current_time = new Date(details.timeStamp);
        update.time_stamp = current_time.toISOString();
        const headers = [];
        let location = "";
        if (details.responseHeaders) {
            details.responseHeaders.map(responseHeader => {
                const { name, value } = responseHeader;
                const header_pair = [];
                header_pair.push(Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(name));
                header_pair.push(Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(value));
                headers.push(header_pair);
                if (name.toLowerCase() === "location") {
                    location = value;
                }
            });
        }
        update.headers = JSON.stringify(headers);
        update.location = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_5__["escapeString"])(location);
        if (saveAllContent) {
            this.logWithResponseBody(details, update);
        }
        else if (saveJavascript && this.isJS(details.type)) {
            this.logWithResponseBody(details, update);
        }
        else {
            this.dataReceiver.saveRecord("http_responses", update);
        }
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaHR0cC1pbnN0cnVtZW50LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2JhY2tncm91bmQvaHR0cC1pbnN0cnVtZW50LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBLE9BQU8sRUFBRSx1QkFBdUIsRUFBRSxNQUFNLHdDQUF3QyxDQUFDO0FBQ2pGLE9BQU8sRUFBRSxvQkFBb0IsRUFBRSxNQUFNLCtCQUErQixDQUFDO0FBQ3JFLE9BQU8sRUFBRSxjQUFjLEVBQXFCLE1BQU0seUJBQXlCLENBQUM7QUFDNUUsT0FBTyxFQUFFLGNBQWMsRUFBRSxNQUFNLHdCQUF3QixDQUFDO0FBQ3hELE9BQU8sRUFBRSxlQUFlLEVBQUUsTUFBTSx5QkFBeUIsQ0FBQztBQUkxRCxPQUFPLEVBQUUsU0FBUyxFQUFFLFlBQVksRUFBRSxTQUFTLEVBQUUsTUFBTSxxQkFBcUIsQ0FBQztBQVN6RTs7Ozs7O0dBTUc7QUFFSCxNQUFNLE9BQU8sY0FBYztJQWF6QixZQUFZLFlBQVk7UUFYaEIsb0JBQWUsR0FFbkIsRUFBRSxDQUFDO1FBQ0MscUJBQWdCLEdBRXBCLEVBQUUsQ0FBQztRQU9MLElBQUksQ0FBQyxZQUFZLEdBQUcsWUFBWSxDQUFDO0lBQ25DLENBQUM7SUFFTSxHQUFHLENBQUMsT0FBTyxFQUFFLGNBQWMsRUFBRSxjQUFjO1FBQ2hELE1BQU0sUUFBUSxHQUFtQjtZQUMvQixRQUFRO1lBQ1IsWUFBWTtZQUNaLE1BQU07WUFDTixPQUFPO1lBQ1AsVUFBVTtZQUNWLFlBQVk7WUFDWixPQUFPO1lBQ1AsUUFBUTtZQUNSLG1CQUFtQjtZQUNuQixNQUFNO1lBQ04sUUFBUTtZQUNSLGlCQUFpQjtZQUNqQixZQUFZO1lBQ1osV0FBVztZQUNYLGNBQWM7WUFDZCxXQUFXO1lBQ1gsS0FBSztZQUNMLFNBQVM7WUFDVCxnQkFBZ0I7WUFDaEIsTUFBTTtZQUNOLE9BQU87U0FDUixDQUFDO1FBRUYsTUFBTSxNQUFNLEdBQWtCLEVBQUUsSUFBSSxFQUFF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

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/background/javascript-instrument.js":
/*!******************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/background/javascript-instrument.js ***!
  \******************************************************************************************************/
/*! exports provided: JavascriptInstrument */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "JavascriptInstrument", function() { return JavascriptInstrument; });
/* harmony import */ var _lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../lib/extension-session-event-ordinal */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-event-ordinal.js");
/* harmony import */ var _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../lib/extension-session-uuid */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-uuid.js");
/* harmony import */ var _lib_string_utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../lib/string-utils */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/string-utils.js");



class JavascriptInstrument {
    constructor(dataReceiver) {
        this.dataReceiver = dataReceiver;
    }
    run(crawlID) {
        const processCallsAndValues = (data, sender) => {
            const update = {};
            update.crawl_id = crawlID;
            update.extension_session_uuid = _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__["extensionSessionUuid"];
            update.event_ordinal = Object(_lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__["incrementedEventOrdinal"])();
            update.page_scoped_event_ordinal = data.ordinal;
            update.window_id = sender.tab.windowId;
            update.tab_id = sender.tab.id;
            update.frame_id = sender.frameId;
            update.script_url = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeUrl"])(data.scriptUrl);
            update.script_line = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(data.scriptLine);
            update.script_col = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(data.scriptCol);
            update.func_name = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(data.funcName);
            update.script_loc_eval = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(data.scriptLocEval);
            update.call_stack = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(data.callStack);
            update.symbol = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(data.symbol);
            update.operation = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(data.operation);
            update.value = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(data.value);
            update.time_stamp = data.timeStamp;
            update.incognito = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["boolToInt"])(sender.tab.incognito);
            // document_url is the current frame's document href
            // top_level_url is the top-level frame's document href
            update.document_url = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeUrl"])(sender.url);
            update.top_level_url = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeUrl"])(sender.tab.url);
            if (data.operation === "call" && data.args.length > 0) {
                update.arguments = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_2__["escapeString"])(JSON.stringify(data.args));
            }
            this.dataReceiver.saveRecord("javascript", update);
        };
        // Listen for messages from content script injected to instrument JavaScript API
        this.onMessageListener = (msg, sender) => {
            // console.debug("javascript-instrumentation background listener - msg, sender, sendReply", msg, sender, sendReply);
            if (msg.namespace && msg.namespace === "javascript-instrumentation") {
                switch (msg.type) {
                    case "logCall":
                    case "logValue":
                        processCallsAndValues(msg.data, sender);
                        break;
                }
            }
        };
        browser.runtime.onMessage.addListener(this.onMessageListener);
    }
    cleanup() {
        if (this.onMessageListener) {
            browser.runtime.onMessage.removeListener(this.onMessageListener);
        }
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiamF2YXNjcmlwdC1pbnN0cnVtZW50LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2JhY2tncm91bmQvamF2YXNjcmlwdC1pbnN0cnVtZW50LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUNBLE9BQU8sRUFBRSx1QkFBdUIsRUFBRSxNQUFNLHdDQUF3QyxDQUFDO0FBQ2pGLE9BQU8sRUFBRSxvQkFBb0IsRUFBRSxNQUFNLCtCQUErQixDQUFDO0FBQ3JFLE9BQU8sRUFBRSxTQUFTLEVBQUUsWUFBWSxFQUFFLFNBQVMsRUFBRSxNQUFNLHFCQUFxQixDQUFDO0FBR3pFLE1BQU0sT0FBTyxvQkFBb0I7SUFJL0IsWUFBWSxZQUFZO1FBQ3RCLElBQUksQ0FBQyxZQUFZLEdBQUcsWUFBWSxDQUFDO0lBQ25DLENBQUM7SUFFTSxHQUFHLENBQUMsT0FBTztRQUNoQixNQUFNLHFCQUFxQixHQUFHLENBQUMsSUFBSSxFQUFFLE1BQXFCLEVBQUUsRUFBRTtZQUM1RCxNQUFNLE1BQU0sR0FBRyxFQUF5QixDQUFDO1lBQ3pDLE1BQU0sQ0FBQyxRQUFRLEdBQUcsT0FBTyxDQUFDO1lBQzFCLE1BQU0sQ0FBQyxzQkFBc0IsR0FBRyxvQkFBb0IsQ0FBQztZQUNyRCxNQUFNLENBQUMsYUFBYSxHQUFHLHVCQUF1QixFQUFFLENBQUM7WUFDakQsTUFBTSxDQUFDLHlCQUF5QixHQUFHLElBQUksQ0FBQyxPQUFPLENBQUM7WUFDaEQsTUFBTSxDQUFDLFNBQVMsR0FBRyxNQUFNLENBQUMsR0FBRyxDQUFDLFFBQVEsQ0FBQztZQUN2QyxNQUFNLENBQUMsTUFBTSxHQUFHLE1BQU0sQ0FBQyxHQUFHLENBQUMsRUFBRSxDQUFDO1lBQzlCLE1BQU0sQ0FBQyxRQUFRLEdBQUcsTUFBTSxDQUFDLE9BQU8sQ0FBQztZQUNqQyxNQUFNLENBQUMsVUFBVSxHQUFHLFNBQVMsQ0FBQyxJQUFJLENBQUMsU0FBUyxDQUFDLENBQUM7WUFDOUMsTUFBTSxDQUFDLFdBQVcs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

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/background/navigation-instrument.js":
/*!******************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/background/navigation-instrument.js ***!
  \******************************************************************************************************/
/*! exports provided: transformWebNavigationBaseEventDetailsToOpenWPMSchema, NavigationInstrument */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "transformWebNavigationBaseEventDetailsToOpenWPMSchema", function() { return transformWebNavigationBaseEventDetailsToOpenWPMSchema; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "NavigationInstrument", function() { return NavigationInstrument; });
/* harmony import */ var _lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../lib/extension-session-event-ordinal */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-event-ordinal.js");
/* harmony import */ var _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../lib/extension-session-uuid */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-uuid.js");
/* harmony import */ var _lib_pending_navigation__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../lib/pending-navigation */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-navigation.js");
/* harmony import */ var _lib_string_utils__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../lib/string-utils */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/string-utils.js");
/* harmony import */ var _lib_uuid__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../lib/uuid */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/uuid.js");





const transformWebNavigationBaseEventDetailsToOpenWPMSchema = async (crawlID, details) => {
    const tab = details.tabId > -1
        ? await browser.tabs.get(details.tabId)
        : {
            windowId: undefined,
            incognito: undefined,
            cookieStoreId: undefined,
            openerTabId: undefined,
            width: undefined,
            height: undefined,
        };
    const window = tab.windowId
        ? await browser.windows.get(tab.windowId)
        : { width: undefined, height: undefined, type: undefined };
    const navigation = {
        crawl_id: crawlID,
        incognito: Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_3__["boolToInt"])(tab.incognito),
        extension_session_uuid: _lib_extension_session_uuid__WEBPACK_IMPORTED_MODULE_1__["extensionSessionUuid"],
        process_id: details.processId,
        window_id: tab.windowId,
        tab_id: details.tabId,
        tab_opener_tab_id: tab.openerTabId,
        frame_id: details.frameId,
        window_width: window.width,
        window_height: window.height,
        window_type: window.type,
        tab_width: tab.width,
        tab_height: tab.height,
        tab_cookie_store_id: Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_3__["escapeString"])(tab.cookieStoreId),
        uuid: Object(_lib_uuid__WEBPACK_IMPORTED_MODULE_4__["makeUUID"])(),
        url: Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_3__["escapeUrl"])(details.url),
    };
    return navigation;
};
class NavigationInstrument {
    constructor(dataReceiver) {
        this.pendingNavigations = {};
        this.dataReceiver = dataReceiver;
    }
    static navigationId(processId, tabId, frameId) {
        return `${processId}-${tabId}-${frameId}`;
    }
    run(crawlID) {
        this.onBeforeNavigateListener = async (details) => {
            const navigationId = NavigationInstrument.navigationId(details.processId, details.tabId, details.frameId);
            const pendingNavigation = this.instantiatePendingNavigation(navigationId);
            const navigation = await transformWebNavigationBaseEventDetailsToOpenWPMSchema(crawlID, details);
            navigation.parent_frame_id = details.parentFrameId;
            navigation.before_navigate_event_ordinal = Object(_lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__["incrementedEventOrdinal"])();
            navigation.before_navigate_time_stamp = new Date(details.timeStamp).toISOString();
            pendingNavigation.resolveOnBeforeNavigateEventNavigation(navigation);
        };
        browser.webNavigation.onBeforeNavigate.addListener(this.onBeforeNavigateListener);
        this.onCommittedListener = async (details) => {
            const navigationId = NavigationInstrument.navigationId(details.processId, details.tabId, details.frameId);
            const navigation = await transformWebNavigationBaseEventDetailsToOpenWPMSchema(crawlID, details);
            navigation.transition_qualifiers = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_3__["escapeString"])(JSON.stringify(details.transitionQualifiers));
            navigation.transition_type = Object(_lib_string_utils__WEBPACK_IMPORTED_MODULE_3__["escapeString"])(details.transitionType);
            navigation.committed_event_ordinal = Object(_lib_extension_session_event_ordinal__WEBPACK_IMPORTED_MODULE_0__["incrementedEventOrdinal"])();
            navigation.committed_time_stamp = new Date(details.timeStamp).toISOString();
            // include attributes from the corresponding onBeforeNavigation event
            const pendingNavigation = this.getPendingNavigation(navigationId);
            if (pendingNavigation) {
                pendingNavigation.resolveOnCommittedEventNavigation(navigation);
                const resolved = await pendingNavigation.resolvedWithinTimeout(1000);
                if (resolved) {
                    const onBeforeNavigateEventNavigation = await pendingNavigation.onBeforeNavigateEventNavigation;
                    navigation.parent_frame_id =
                        onBeforeNavigateEventNavigation.parent_frame_id;
                    navigation.before_navigate_event_ordinal =
                        onBeforeNavigateEventNavigation.before_navigate_event_ordinal;
                    navigation.before_navigate_time_stamp =
                        onBeforeNavigateEventNavigation.before_navigate_time_stamp;
                }
            }
            this.dataReceiver.saveRecord("navigations", navigation);
        };
        browser.webNavigation.onCommitted.addListener(this.onCommittedListener);
    }
    cleanup() {
        if (this.onBeforeNavigateListener) {
            browser.webNavigation.onBeforeNavigate.removeListener(this.onBeforeNavigateListener);
        }
        if (this.onCommittedListener) {
            browser.webNavigation.onCommitted.removeListener(this.onCommittedListener);
        }
    }
    instantiatePendingNavigation(navigationId) {
        this.pendingNavigations[navigationId] = new _lib_pending_navigation__WEBPACK_IMPORTED_MODULE_2__["PendingNavigation"]();
        return this.pendingNavigations[navigationId];
    }
    getPendingNavigation(navigationId) {
        return this.pendingNavigations[navigationId];
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoibmF2aWdhdGlvbi1pbnN0cnVtZW50LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2JhY2tncm91bmQvbmF2aWdhdGlvbi1pbnN0cnVtZW50LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBLE9BQU8sRUFBRSx1QkFBdUIsRUFBRSxNQUFNLHdDQUF3QyxDQUFDO0FBQ2pGLE9BQU8sRUFBRSxvQkFBb0IsRUFBRSxNQUFNLCtCQUErQixDQUFDO0FBQ3JFLE9BQU8sRUFBRSxpQkFBaUIsRUFBRSxNQUFNLDJCQUEyQixDQUFDO0FBQzlELE9BQU8sRUFBRSxTQUFTLEVBQUUsWUFBWSxFQUFFLFNBQVMsRUFBRSxNQUFNLHFCQUFxQixDQUFDO0FBQ3pFLE9BQU8sRUFBRSxRQUFRLEVBQUUsTUFBTSxhQUFhLENBQUM7QUFRdkMsTUFBTSxDQUFDLE1BQU0scURBQXFELEdBQUcsS0FBSyxFQUN4RSxPQUFPLEVBQ1AsT0FBc0MsRUFDakIsRUFBRTtJQUN2QixNQUFNLEdBQUcsR0FDUCxPQUFPLENBQUMsS0FBSyxHQUFHLENBQUMsQ0FBQztRQUNoQixDQUFDLENBQUMsTUFBTSxPQUFPLENBQUMsSUFBSSxDQUFDLEdBQUcsQ0FBQyxPQUFPLENBQUMsS0FBSyxDQUFDO1FBQ3ZDLENBQUMsQ0FBQztZQUNFLFFBQVEsRUFBRSxTQUFTO1lBQ25CLFNBQVMsRUFBRSxTQUFTO1lBQ3BCLGFBQWEsRUFBRSxTQUFTO1lBQ3hCLFdBQVcsRUFBRSxTQUFTO1lBQ3RCLEtBQUssRUFBRSxTQUFTO1lBQ2hCLE1BQU0sRUFBRSxTQUFTO1NBQ2xCLENBQUM7SUFDUixNQUFNLE1BQU0sR0FBRyxHQUFHLENBQUMsUUFBUTtRQUN6QixDQUFDLENBQUMsTUFBTSxPQUFPLENBQUMsT0FBTyxDQUFDLEdBQUcsQ0FBQyxHQUFHLENBQUMsUUFBUSxDQUFDO1FBQ3pDLENBQUMsQ0FBQyxFQUFFLEtBQUssRUFBRSxTQUFTLEVBQUUsTUFBTSxFQUFFLFNBQVMsRUFBRSxJ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

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/content/javascript-instrument-content-scope.js":
/*!*****************************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/content/javascript-instrument-content-scope.js ***!
  \*****************************************************************************************************************/
/*! exports provided: injectJavascriptInstrumentPageScript */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "injectJavascriptInstrumentPageScript", function() { return injectJavascriptInstrumentPageScript; });
/* harmony import */ var _javascript_instrument_page_scope__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./javascript-instrument-page-scope */ "./node_modules/openwpm-webext-instrumentation/build/module/content/javascript-instrument-page-scope.js");

function getPageScriptAsString() {
    // return a string
    return "(" + _javascript_instrument_page_scope__WEBPACK_IMPORTED_MODULE_0__["pageScript"] + "());";
}
function insertScript(text, data) {
    const parent = document.documentElement, script = document.createElement("script");
    script.text = text;
    script.async = false;
    for (const key in data) {
        script.setAttribute("data-" + key.replace("_", "-"), data[key]);
    }
    parent.insertBefore(script, parent.firstChild);
    parent.removeChild(script);
}
function emitMsg(type, msg) {
    msg.timeStamp = new Date().toISOString();
    browser.runtime.sendMessage({
        namespace: "javascript-instrumentation",
        type,
        data: msg,
    });
}
const event_id = Math.random();
// listen for messages from the script we are about to insert
document.addEventListener(event_id.toString(), function (e) {
    // pass these on to the background page
    const msgs = e.detail;
    if (Array.isArray(msgs)) {
        msgs.forEach(function (msg) {
            emitMsg(msg.type, msg.content);
        });
    }
    else {
        emitMsg(msgs.type, msgs.content);
    }
});
function injectJavascriptInstrumentPageScript(testing = false) {
    insertScript(getPageScriptAsString(), {
        event_id,
        testing,
    });
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiamF2YXNjcmlwdC1pbnN0cnVtZW50LWNvbnRlbnQtc2NvcGUuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvY29udGVudC9qYXZhc2NyaXB0LWluc3RydW1lbnQtY29udGVudC1zY29wZS50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxPQUFPLEVBQUUsVUFBVSxFQUFFLE1BQU0sb0NBQW9DLENBQUM7QUFFaEUsU0FBUyxxQkFBcUI7SUFDNUIsa0JBQWtCO0lBQ2xCLE9BQU8sR0FBRyxHQUFHLFVBQVUsR0FBRyxNQUFNLENBQUM7QUFDbkMsQ0FBQztBQUVELFNBQVMsWUFBWSxDQUFDLElBQUksRUFBRSxJQUFJO0lBQzlCLE1BQU0sTUFBTSxHQUFHLFFBQVEsQ0FBQyxlQUFlLEVBQ3JDLE1BQU0sR0FBRyxRQUFRLENBQUMsYUFBYSxDQUFDLFFBQVEsQ0FBQyxDQUFDO0lBQzVDLE1BQU0sQ0FBQyxJQUFJLEdBQUcsSUFBSSxDQUFDO0lBQ25CLE1BQU0sQ0FBQyxLQUFLLEdBQUcsS0FBSyxDQUFDO0lBRXJCLEtBQUssTUFBTSxHQUFHLElBQUksSUFBSSxFQUFFO1FBQ3RCLE1BQU0sQ0FBQyxZQUFZLENBQUMsT0FBTyxHQUFHLEdBQUcsQ0FBQyxPQUFPLENBQUMsR0FBRyxFQUFFLEdBQUcsQ0FBQyxFQUFFLElBQUksQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDO0tBQ2pFO0lBRUQsTUFBTSxDQUFDLFlBQVksQ0FBQyxNQUFNLEVBQUUsTUFBTSxDQUFDLFVBQVUsQ0FBQyxDQUFDO0lBQy9DLE1BQU0sQ0FBQyxXQUFXLENBQUMsTUFBTSxDQUFDLENBQUM7QUFDN0IsQ0FBQztBQUVELFNBQVMsT0FBTyxDQUFDLElBQUksRUFBRSxHQUFHO0lBQ3hCLEdBQUcsQ0FBQyxTQUFTLEdBQUcsSUFBSSxJQUFJLEVBQUUsQ0FBQyxXQUFXLEVBQUUsQ0FBQztJQUN6QyxPQUFPLENBQUMsT0FBTyxDQUFDLFdBQVcsQ0FBQztRQUMxQixTQUFTLEVBQUUsNEJBQTRCO1FBQ3ZDLElBQUk7UUFDSixJQUFJLEVBQUUsR0FBRztLQUNWLENBQUMsQ0FBQztBQUNMLENBQUM7QUFFRCxNQUFNLFFBQVEsR0FBRyxJQUFJLENBQUMsTUFBTSxFQUFFLENBQUM7QUFFL0IsNkRBQTZEO0FBQzdELFFBQVEsQ0FBQyxnQkFBZ0IsQ0FBQyxRQUFRLENBQUMsUUFBUSxFQUFFLEVBQUUsVUFBUyxDQUFjO0lBQ3BFLHVDQUF1QztJQUN2QyxNQUFNLElBQUksR0FBRyxDQUFDLENBQUMsTUFBTSxDQUFDO0lBQ3RCLElBQUksS0FBSyxDQUFDLE9BQU8sQ0FBQyxJQUFJLENBQUMsRUFBRTtRQUN2QixJQUFJLENBQUMsT0FBTyxDQUFDLFVBQVMsR0FBRztZQUN2QixPQUFPLENBQUMsR0FBRyxDQUFDLElBQUksRUFBRSxHQUFHLENBQUMsT0FBTyxDQUFDLENBQUM7UUFDakMsQ0FBQyxDQUFDLENBQUM7S0FDSjtTQUFNO1FBQ0wsT0FBTyxDQUFDLElBQUksQ0FBQyxJQUFJLEVBQUUsSUFBSSxDQUFDLE9BQU8sQ0FBQyxDQUFDO0tBQ2xDO0FBQ0gsQ0FBQyxDQUFDLENBQUM7QUFFSCxNQUFNLFVBQVUsb0NBQW9DLENBQUMsT0FBTyxHQUFHLEtBQUs7SUFDbEUsWUFBWSxDQUFDLHFCQUFxQixFQUFFLEVBQUU7UUFDcEMsUUFBUTtRQUNSLE9BQU87S0FDUixDQUFDLENBQUM7QUFDTCxDQUFDIn0=

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/content/javascript-instrument-page-scope.js":
/*!**************************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/content/javascript-instrument-page-scope.js ***!
  \**************************************************************************************************************/
/*! exports provided: pageScript */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "pageScript", function() { return pageScript; });
// Intrumentation injection code is based on privacybadgerfirefox
// https://github.com/EFForg/privacybadgerfirefox/blob/master/data/fingerprinting.js
const pageScript = function () {
    // from Underscore v1.6.0
    function debounce(func, wait, immediate = false) {
        let timeout, args, context, timestamp, result;
        const later = function () {
            const last = Date.now() - timestamp;
            if (last < wait) {
                timeout = setTimeout(later, wait - last);
            }
            else {
                timeout = null;
                if (!immediate) {
                    result = func.apply(context, args);
                    context = args = null;
                }
            }
        };
        return function () {
            context = this;
            args = arguments;
            timestamp = Date.now();
            const callNow = immediate && !timeout;
            if (!timeout) {
                timeout = setTimeout(later, wait);
            }
            if (callNow) {
                result = func.apply(context, args);
                context = args = null;
            }
            return result;
        };
    }
    // End of Debounce
    // messages the injected script
    const send = (function () {
        let messages = [];
        // debounce sending queued messages
        const _send = debounce(function () {
            document.dispatchEvent(new CustomEvent(event_id, {
                detail: messages,
            }));
            // clear the queue
            messages = [];
        }, 100);
        return function (msgType, msg) {
            // queue the message
            messages.push({ type: msgType, content: msg });
            _send();
        };
    })();
    const event_id = document.currentScript.getAttribute("data-event-id");
    /*
     * Instrumentation helpers
     */
    const testing = document.currentScript.getAttribute("data-testing") === "true";
    if (testing) {
        console.log("OpenWPM: Currently testing?", testing);
    }
    // Recursively generates a path for an element
    function getPathToDomElement(element, visibilityAttr = false) {
        if (element === document.body) {
            return element.tagName;
        }
        if (element.parentNode === null) {
            return "NULL/" + element.tagName;
        }
        let siblingIndex = 1;
        const siblings = element.parentNode.childNodes;
        for (let i = 0; i < siblings.length; i++) {
            const sibling = siblings[i];
            if (sibling === element) {
                let path = getPathToDomElement(element.parentNode, visibilityAttr);
                path += "/" + element.tagName + "[" + siblingIndex;
                path += "," + element.id;
                path += "," + element.className;
                if (visibilityAttr) {
                    path += "," + element.hidden;
                    path += "," + element.style.display;
                    path += "," + element.style.visibility;
                }
                if (element.tagName === "A") {
                    path += "," + element.href;
                }
                path += "]";
                return path;
            }
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                siblingIndex++;
            }
        }
    }
    // Helper for JSONifying objects
    function serializeObject(object, stringifyFunctions = false) {
        // Handle permissions errors
        try {
            if (object === null) {
                return "null";
            }
            if (typeof object === "function") {
                if (stringifyFunctions) {
                    return object.toString();
                }
                else {
                    return "FUNCTION";
                }
            }
            if (typeof object !== "object") {
                return object;
            }
            const seenObjects = [];
            return JSON.stringify(object, function (key, value) {
                if (value === null) {
                    return "null";
                }
                if (typeof value === "function") {
                    if (stringifyFunctions) {
                        return value.toString();
                    }
                    else {
                        return "FUNCTION";
                    }
                }
                if (typeof value === "object") {
                    // Remove wrapping on content objects
                    if ("wrappedJSObject" in value) {
                        value = value.wrappedJSObject;
                    }
                    // Serialize DOM elements
                    if (value instanceof HTMLElement) {
                        return getPathToDomElement(value);
                    }
                    // Prevent serialization cycles
                    if (key === "" || seenObjects.indexOf(value) < 0) {
                        seenObjects.push(value);
                        return value;
                    }
                    else {
                        return typeof value;
                    }
                }
                return value;
            });
        }
        catch (error) {
            console.log("OpenWPM: SERIALIZATION ERROR: " + error);
            return "SERIALIZATION ERROR: " + error;
        }
    }
    function logErrorToConsole(error) {
        console.log("OpenWPM: Error name: " + error.name);
        console.log("OpenWPM: Error message: " + error.message);
        console.log("OpenWPM: Error filename: " + error.fileName);
        console.log("OpenWPM: Error line number: " + error.lineNumber);
        console.log("OpenWPM: Error stack: " + error.stack);
    }
    // Helper to get originating script urls
    function getStackTrace() {
        let stack;
        try {
            throw new Error();
        }
        catch (err) {
            stack = err.stack;
        }
        return stack;
    }
    // from http://stackoverflow.com/a/5202185
    String.prototype.rsplit = function (sep, maxsplit) {
        const split = this.split(sep);
        return maxsplit
            ? [split.slice(0, -maxsplit).join(sep)].concat(split.slice(-maxsplit))
            : split;
    };
    function getOriginatingScriptContext(getCallStack = false) {
        const trace = getStackTrace()
            .trim()
            .split("\n");
        // return a context object even if there is an error
        const empty_context = {
            scriptUrl: "",
            scriptLine: "",
            scriptCol: "",
            funcName: "",
            scriptLocEval: "",
            callStack: "",
        };
        if (trace.length < 4) {
            return empty_context;
        }
        // 0, 1 and 2 are OpenWPM's own functions (e.g. getStackTrace), skip them.
        const callSite = trace[3];
        if (!callSite) {
            return empty_context;
        }
        /*
         * Stack frame format is simply: FUNC_NAME@FILENAME:LINE_NO:COLUMN_NO
         *
         * If eval or Function is involved we have an additional part after the FILENAME, e.g.:
         * FUNC_NAME@FILENAME line 123 > eval line 1 > eval:LINE_NO:COLUMN_NO
         * or FUNC_NAME@FILENAME line 234 > Function:LINE_NO:COLUMN_NO
         *
         * We store the part between the FILENAME and the LINE_NO in scriptLocEval
         */
        try {
            let scriptUrl = "";
            let scriptLocEval = ""; // for eval or Function calls
            const callSiteParts = callSite.split("@");
            const funcName = callSiteParts[0] || "";
            const items = callSiteParts[1].rsplit(":", 2);
            const columnNo = items[items.length - 1];
            const lineNo = items[items.length - 2];
            const scriptFileName = items[items.length - 3] || "";
            const lineNoIdx = scriptFileName.indexOf(" line "); // line in the URL means eval or Function
            if (lineNoIdx === -1) {
                scriptUrl = scriptFileName; // TODO: sometimes we have filename only, e.g. XX.js
            }
            else {
                scriptUrl = scriptFileName.slice(0, lineNoIdx);
                scriptLocEval = scriptFileName.slice(lineNoIdx + 1, scriptFileName.length);
            }
            const callContext = {
                scriptUrl,
                scriptLine: lineNo,
                scriptCol: columnNo,
                funcName,
                scriptLocEval,
                callStack: getCallStack
                    ? trace
                        .slice(3)
                        .join("\n")
                        .trim()
                    : "",
            };
            return callContext;
        }
        catch (e) {
            console.log("OpenWPM: Error parsing the script context", e, callSite);
            return empty_context;
        }
    }
    // Counter to cap # of calls logged for each script/api combination
    const maxLogCount = 500;
    const logCounter = new Object();
    function updateCounterAndCheckIfOver(scriptUrl, symbol) {
        const key = scriptUrl + "|" + symbol;
        if (key in logCounter && logCounter[key] >= maxLogCount) {
            return true;
        }
        else if (!(key in logCounter)) {
            logCounter[key] = 1;
        }
        else {
            logCounter[key] += 1;
        }
        return false;
    }
    // Prevent logging of gets arising from logging
    let inLog = false;
    // To keep track of the original order of events
    let ordinal = 0;
    // For gets, sets, etc. on a single value
    function logValue(instrumentedVariableName, value, operation, callContext, logSettings) {
        if (inLog) {
            return;
        }
        inLog = true;
        const overLimit = updateCounterAndCheckIfOver(callContext.scriptUrl, instrumentedVariableName);
        if (overLimit) {
            inLog = false;
            return;
        }
        const msg = {
            operation,
            symbol: instrumentedVariableName,
            value: serializeObject(value, !!logSettings.logFunctionsAsStrings),
            scriptUrl: callContext.scriptUrl,
            scriptLine: callContext.scriptLine,
            scriptCol: callContext.scriptCol,
            funcName: callContext.funcName,
            scriptLocEval: callContext.scriptLocEval,
            callStack: callContext.callStack,
            ordinal: ordinal++,
        };
        try {
            send("logValue", msg);
        }
        catch (error) {
            console.log("OpenWPM: Unsuccessful value log!");
            logErrorToConsole(error);
        }
        inLog = false;
    }
    // For functions
    function logCall(instrumentedFunctionName, args, callContext, logSettings) {
        if (inLog) {
            return;
        }
        inLog = true;
        const overLimit = updateCounterAndCheckIfOver(callContext.scriptUrl, instrumentedFunctionName);
        if (overLimit) {
            inLog = false;
            return;
        }
        try {
            // Convert special arguments array to a standard array for JSONifying
            const serialArgs = [];
            for (let i = 0; i < args.length; i++) {
                serialArgs.push(serializeObject(args[i], !!logSettings.logFunctionsAsStrings));
            }
            const msg = {
                operation: "call",
                symbol: instrumentedFunctionName,
                args: serialArgs,
                value: "",
                scriptUrl: callContext.scriptUrl,
                scriptLine: callContext.scriptLine,
                scriptCol: callContext.scriptCol,
                funcName: callContext.funcName,
                scriptLocEval: callContext.scriptLocEval,
                callStack: callContext.callStack,
                ordinal: ordinal++,
            };
            send("logCall", msg);
        }
        catch (error) {
            console.log("OpenWPM: Unsuccessful call log: " + instrumentedFunctionName);
            logErrorToConsole(error);
        }
        inLog = false;
    }
    // Rough implementations of Object.getPropertyDescriptor and Object.getPropertyNames
    // See http://wiki.ecmascript.org/doku.php?id=harmony:extended_object_api
    Object.getPropertyDescriptor = function (subject, name) {
        let pd = Object.getOwnPropertyDescriptor(subject, name);
        let proto = Object.getPrototypeOf(subject);
        while (pd === undefined && proto !== null) {
            pd = Object.getOwnPropertyDescriptor(proto, name);
            proto = Object.getPrototypeOf(proto);
        }
        return pd;
    };
    Object.getPropertyNames = function (subject) {
        let props = Object.getOwnPropertyNames(subject);
        let proto = Object.getPrototypeOf(subject);
        while (proto !== null) {
            props = props.concat(Object.getOwnPropertyNames(proto));
            proto = Object.getPrototypeOf(proto);
        }
        // FIXME: remove duplicate property names from props
        return props;
    };
    /*
     *  Direct instrumentation of javascript objects
     */
    function isObject(object, propertyName) {
        let property;
        try {
            property = object[propertyName];
        }
        catch (error) {
            return false;
        }
        if (property === null) {
            // null is type "object"
            return false;
        }
        return typeof property === "object";
    }
    function instrumentObject(object, objectName, logSettings = {}) {
        // Use for objects or object prototypes
        //
        // Parameters
        // ----------
        //   object : Object
        //     Object to instrument
        //   objectName : String
        //     Name of the object to be instrumented (saved to database)
        //   logSettings : Object
        //     (optional) object that can be used to specify additional logging
        //     configurations. See available options below.
        //
        // logSettings options (all optional)
        // -------------------
        //   propertiesToInstrument : Array
        //     An array of properties to instrument on this object. Default is
        //     all properties.
        //   excludedProperties : Array
        //     Properties excluded from instrumentation. Default is an empty
        //     array.
        //   logCallStack : boolean
        //     Set to true save the call stack info with each property call.
        //     Default is `false`.
        //   logFunctionsAsStrings : boolean
        //     Set to true to save functional arguments as strings during
        //     argument serialization. Default is `false`.
        //   preventSets : boolean
        //     Set to true to prevent nested objects and functions from being
        //     overwritten (and thus having their instrumentation removed).
        //     Other properties (static values) can still be set with this is
        //     enabled. Default is `false`.
        //   recursive : boolean
        //     Set to `true` to recursively instrument all object properties of
        //     the given `object`. Default is `false`
        //     NOTE:
        //       (1)`logSettings['propertiesToInstrument']` does not propagate
        //           to sub-objects.
        //       (2) Sub-objects of prototypes can not be instrumented
        //           recursively as these properties can not be accessed
        //           until an instance of the prototype is created.
        //   depth : integer
        //     Recursion limit when instrumenting object recursively.
        //     Default is `5`.
        const properties = logSettings.propertiesToInstrument
            ? logSettings.propertiesToInstrument
            : Object.getPropertyNames(object);
        for (let i = 0; i < properties.length; i++) {
            if (logSettings.excludedProperties &&
                logSettings.excludedProperties.indexOf(properties[i]) > -1) {
                continue;
            }
            // If `recursive` flag set we want to recursively instrument any
            // object properties that aren't the prototype object. Only recurse if
            // depth not set (at which point its set to default) or not at limit.
            if (!!logSettings.recursive &&
                properties[i] !== "__proto__" &&
                isObject(object, properties[i]) &&
                (!("depth" in logSettings) || logSettings.depth > 0)) {
                // set recursion limit to default if not specified
                if (!("depth" in logSettings)) {
                    logSettings.depth = 5;
                }
                instrumentObject(object[properties[i]], objectName + "." + properties[i], {
                    excludedProperties: logSettings.excludedProperties,
                    logCallStack: logSettings.logCallStack,
                    logFunctionsAsStrings: logSettings.logFunctionsAsStrings,
                    preventSets: logSettings.preventSets,
                    recursive: logSettings.recursive,
                    depth: logSettings.depth - 1,
                });
            }
            try {
                instrumentObjectProperty(object, objectName, properties[i], logSettings);
            }
            catch (error) {
                logErrorToConsole(error);
            }
        }
    }
    if (testing) {
        window.instrumentObject = instrumentObject;
    }
    // Log calls to a given function
    // This helper function returns a wrapper around `func` which logs calls
    // to `func`. `objectName` and `methodName` are used strictly to identify
    // which object method `func` is coming from in the logs
    function instrumentFunction(objectName, methodName, func, logSettings) {
        return function () {
            const callContext = getOriginatingScriptContext(!!logSettings.logCallStack);
            logCall(objectName + "." + methodName, arguments, callContext, logSettings);
            return func.apply(this, arguments);
        };
    }
    // Log properties of prototypes and objects
    function instrumentObjectProperty(object, objectName, propertyName, logSettings = {}) {
        // Store original descriptor in closure
        const propDesc = Object.getPropertyDescriptor(object, propertyName);
        if (!propDesc) {
            console.error("Property descriptor not found for", objectName, propertyName, object);
            return;
        }
        // Instrument data or accessor property descriptors
        const originalGetter = propDesc.get;
        const originalSetter = propDesc.set;
        let originalValue = propDesc.value;
        // We overwrite both data and accessor properties as an instrumented
        // accessor property
        Object.defineProperty(object, propertyName, {
            configurable: true,
            get: (function () {
                return function () {
                    let origProperty;
                    const callContext = getOriginatingScriptContext(!!logSettings.logCallStack);
                    // get original value
                    if (originalGetter) {
                        // if accessor property
                        origProperty = originalGetter.call(this);
                    }
                    else if ("value" in propDesc) {
                        // if data property
                        origProperty = originalValue;
                    }
                    else {
                        console.error("Property descriptor for", objectName + "." + propertyName, "doesn't have getter or value?");
                        logValue(objectName + "." + propertyName, "", "get(failed)", callContext, logSettings);
                        return;
                    }
                    // Log `gets` except those that have instrumented return values
                    // * All returned functions are instrumented with a wrapper
                    // * Returned objects may be instrumented if recursive
                    //   instrumentation is enabled and this isn't at the depth limit.
                    if (typeof origProperty === "function") {
                        return instrumentFunction(objectName, propertyName, origProperty, logSettings);
                    }
                    else if (typeof origProperty === "object" &&
                        !!logSettings.recursive &&
                        (!("depth" in logSettings) || logSettings.depth > 0)) {
                        return origProperty;
                    }
                    else {
                        logValue(objectName + "." + propertyName, origProperty, "get", callContext, logSettings);
                        return origProperty;
                    }
                };
            })(),
            set: (function () {
                return function (value) {
                    const callContext = getOriginatingScriptContext(!!logSettings.logCallStack);
                    let returnValue;
                    // Prevent sets for functions and objects if enabled
                    if (!!logSettings.preventSets &&
                        (typeof originalValue === "function" ||
                            typeof originalValue === "object")) {
                        logValue(objectName + "." + propertyName, value, "set(prevented)", callContext, logSettings);
                        return value;
                    }
                    // set new value to original setter/location
                    if (originalSetter) {
                        // if accessor property
                        returnValue = originalSetter.call(this, value);
                    }
                    else if ("value" in propDesc) {
                        inLog = true;
                        if (object.isPrototypeOf(this)) {
                            Object.defineProperty(this, propertyName, {
                                value,
                            });
                        }
                        else {
                            originalValue = value;
                        }
                        returnValue = value;
                        inLog = false;
                    }
                    else {
                        console.error("Property descriptor for", objectName + "." + propertyName, "doesn't have setter or value?");
                        logValue(objectName + "." + propertyName, value, "set(failed)", callContext, logSettings);
                        return value;
                    }
                    // log set
                    logValue(objectName + "." + propertyName, value, "set", callContext, logSettings);
                    // return new value
                    return returnValue;
                };
            })(),
        });
    }
    /*
     * Start Instrumentation
     */
    // TODO: user should be able to choose what to instrument
    // Access to navigator properties
    const navigatorProperties = [
        "appCodeName",
        "appName",
        "appVersion",
        "buildID",
        "cookieEnabled",
        "doNotTrack",
        "geolocation",
        "language",
        "languages",
        "onLine",
        "oscpu",
        "platform",
        "product",
        "productSub",
        "userAgent",
        "vendorSub",
        "vendor",
    ];
    navigatorProperties.forEach(function (property) {
        instrumentObjectProperty(window.navigator, "window.navigator", property);
    });
    // Access to screen properties
    // instrumentObject(window.screen, "window.screen");
    // TODO: why do we instrument only two screen properties
    const screenProperties = ["pixelDepth", "colorDepth"];
    screenProperties.forEach(function (property) {
        instrumentObjectProperty(window.screen, "window.screen", property);
    });
    // Access to plugins
    const pluginProperties = [
        "name",
        "filename",
        "description",
        "version",
        "length",
    ];
    for (let i = 0; i < window.navigator.plugins.length; i++) {
        const pluginName = window.navigator.plugins[i].name;
        pluginProperties.forEach(function (property) {
            instrumentObjectProperty(window.navigator.plugins[pluginName], "window.navigator.plugins[" + pluginName + "]", property);
        });
    }
    // Access to MIMETypes
    const mimeTypeProperties = ["description", "suffixes", "type"];
    for (let i = 0; i < window.navigator.mimeTypes.length; i++) {
        const mimeTypeName = window.navigator.mimeTypes[i].type; // note: upstream typings seems to be incorrect
        mimeTypeProperties.forEach(function (property) {
            instrumentObjectProperty(window.navigator.mimeTypes[mimeTypeName], "window.navigator.mimeTypes[" + mimeTypeName + "]", property);
        });
    }
    // Name, localStorage, and sessionsStorage logging
    // Instrumenting window.localStorage directly doesn't seem to work, so the Storage
    // prototype must be instrumented instead. Unfortunately this fails to differentiate
    // between sessionStorage and localStorage. Instead, you'll have to look for a sequence
    // of a get for the localStorage object followed by a getItem/setItem for the Storage object.
    const windowProperties = ["name", "localStorage", "sessionStorage"];
    windowProperties.forEach(function (property) {
        instrumentObjectProperty(window, "window", property);
    });
    instrumentObject(window.Storage.prototype, "window.Storage");
    // Access to document.cookie
    instrumentObjectProperty(window.document, "window.document", "cookie", {
        logCallStack: true,
    });
    // Access to document.referrer
    instrumentObjectProperty(window.document, "window.document", "referrer", {
        logCallStack: true,
    });
    // Access to canvas
    instrumentObject(window.HTMLCanvasElement.prototype, "HTMLCanvasElement");
    const excludedProperties = [
        "quadraticCurveTo",
        "lineTo",
        "transform",
        "globalAlpha",
        "moveTo",
        "drawImage",
        "setTransform",
        "clearRect",
        "closePath",
        "beginPath",
        "canvas",
        "translate",
    ];
    instrumentObject(window.CanvasRenderingContext2D.prototype, "CanvasRenderingContext2D", { excludedProperties });
    // Access to webRTC
    instrumentObject(window.RTCPeerConnection.prototype, "RTCPeerConnection");
    // Access to Audio API
    instrumentObject(window.AudioContext.prototype, "AudioContext");
    instrumentObject(window.OfflineAudioContext.prototype, "OfflineAudioContext");
    instrumentObject(window.OscillatorNode.prototype, "OscillatorNode");
    instrumentObject(window.AnalyserNode.prototype, "AnalyserNode");
    instrumentObject(window.GainNode.prototype, "GainNode");
    instrumentObject(window.ScriptProcessorNode.prototype, "ScriptProcessorNode");
    if (testing) {
        console.log("OpenWPM: Content-side javascript instrumentation started", new Date().toISOString());
    }
};
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiamF2YXNjcmlwdC1pbnN0cnVtZW50LXBhZ2Utc2NvcGUuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvY29udGVudC9qYXZhc2NyaXB0LWluc3RydW1lbnQtcGFnZS1zY29wZS50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxpRUFBaUU7QUFDakUsb0ZBQW9GO0FBZ0JwRixNQUFNLENBQUMsTUFBTSxVQUFVLEdBQUc7SUFDeEIseUJBQXlCO0lBQ3pCLFNBQVMsUUFBUSxDQUFDLElBQUksRUFBRSxJQUFJLEVBQUUsU0FBUyxHQUFHLEtBQUs7UUFDN0MsSUFBSSxPQUFPLEVBQUUsSUFBSSxFQUFFLE9BQU8sRUFBRSxTQUFTLEVBQUUsTUFBTSxDQUFDO1FBRTlDLE1BQU0sS0FBSyxHQUFHO1lBQ1osTUFBTSxJQUFJLEdBQUcsSUFBSSxDQUFDLEdBQUcsRUFBRSxHQUFHLFNBQVMsQ0FBQztZQUNwQyxJQUFJLElBQUksR0FBRyxJQUFJLEVBQUU7Z0JBQ2YsT0FBTyxHQUFHLFVBQVUsQ0FBQyxLQUFLLEVBQUUsSUFBSSxHQUFHLElBQUksQ0FBQyxDQUFDO2FBQzFDO2lCQUFNO2dCQUNMLE9BQU8sR0FBRyxJQUFJLENBQUM7Z0JBQ2YsSUFBSSxDQUFDLFNBQVMsRUFBRTtvQkFDZCxNQUFNLEdBQUcsSUFBSSxDQUFDLEtBQUssQ0FBQyxPQUFPLEVBQUUsSUFBSSxDQUFDLENBQUM7b0JBQ25DLE9BQU8sR0FBRyxJQUFJLEdBQUcsSUFBSSxDQUFDO2lCQUN2QjthQUNGO1FBQ0gsQ0FBQyxDQUFDO1FBRUYsT0FBTztZQUNMLE9BQU8sR0FBRyxJQUFJLENBQUM7WUFDZixJQUFJLEdBQUcsU0FBUyxDQUFDO1lBQ2pCLFNBQVMsR0FBRyxJQUFJLENBQUMsR0FBRyxFQUFFLENBQUM7WUFDdkIsTUFBTSxPQUFPLEdBQUcsU0FBUyxJQUFJLENBQUMsT0FBTyxDQUFDO1lBQ3RDLElBQUksQ0FBQyxPQUFPLEVBQUU7Z0JBQ1osT0FBTyxHQUFH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

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/index.js":
/*!***************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/index.js ***!
  \***************************************************************************/
/*! exports provided: transformCookieObjectToMatchOpenWPMSchema, CookieInstrument, HttpInstrument, JavascriptInstrument, transformWebNavigationBaseEventDetailsToOpenWPMSchema, NavigationInstrument, injectJavascriptInstrumentPageScript, HttpPostParser, encode_utf8, escapeString, escapeUrl, boolToInt, dateTimeUnicodeFormatString */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _background_cookie_instrument__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./background/cookie-instrument */ "./node_modules/openwpm-webext-instrumentation/build/module/background/cookie-instrument.js");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "transformCookieObjectToMatchOpenWPMSchema", function() { return _background_cookie_instrument__WEBPACK_IMPORTED_MODULE_0__["transformCookieObjectToMatchOpenWPMSchema"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "CookieInstrument", function() { return _background_cookie_instrument__WEBPACK_IMPORTED_MODULE_0__["CookieInstrument"]; });

/* harmony import */ var _background_http_instrument__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./background/http-instrument */ "./node_modules/openwpm-webext-instrumentation/build/module/background/http-instrument.js");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "HttpInstrument", function() { return _background_http_instrument__WEBPACK_IMPORTED_MODULE_1__["HttpInstrument"]; });

/* harmony import */ var _background_javascript_instrument__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./background/javascript-instrument */ "./node_modules/openwpm-webext-instrumentation/build/module/background/javascript-instrument.js");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "JavascriptInstrument", function() { return _background_javascript_instrument__WEBPACK_IMPORTED_MODULE_2__["JavascriptInstrument"]; });

/* harmony import */ var _background_navigation_instrument__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./background/navigation-instrument */ "./node_modules/openwpm-webext-instrumentation/build/module/background/navigation-instrument.js");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "transformWebNavigationBaseEventDetailsToOpenWPMSchema", function() { return _background_navigation_instrument__WEBPACK_IMPORTED_MODULE_3__["transformWebNavigationBaseEventDetailsToOpenWPMSchema"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "NavigationInstrument", function() { return _background_navigation_instrument__WEBPACK_IMPORTED_MODULE_3__["NavigationInstrument"]; });

/* harmony import */ var _content_javascript_instrument_content_scope__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./content/javascript-instrument-content-scope */ "./node_modules/openwpm-webext-instrumentation/build/module/content/javascript-instrument-content-scope.js");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "injectJavascriptInstrumentPageScript", function() { return _content_javascript_instrument_content_scope__WEBPACK_IMPORTED_MODULE_4__["injectJavascriptInstrumentPageScript"]; });

/* harmony import */ var _lib_http_post_parser__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./lib/http-post-parser */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/http-post-parser.js");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "HttpPostParser", function() { return _lib_http_post_parser__WEBPACK_IMPORTED_MODULE_5__["HttpPostParser"]; });

/* harmony import */ var _lib_string_utils__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./lib/string-utils */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/string-utils.js");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "encode_utf8", function() { return _lib_string_utils__WEBPACK_IMPORTED_MODULE_6__["encode_utf8"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "escapeString", function() { return _lib_string_utils__WEBPACK_IMPORTED_MODULE_6__["escapeString"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "escapeUrl", function() { return _lib_string_utils__WEBPACK_IMPORTED_MODULE_6__["escapeUrl"]; });

/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "boolToInt", function() { return _lib_string_utils__WEBPACK_IMPORTED_MODULE_6__["boolToInt"]; });

/* harmony import */ var _schema__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./schema */ "./node_modules/openwpm-webext-instrumentation/build/module/schema.js");
/* harmony reexport (safe) */ __webpack_require__.d(__webpack_exports__, "dateTimeUnicodeFormatString", function() { return _schema__WEBPACK_IMPORTED_MODULE_7__["dateTimeUnicodeFormatString"]; });









//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi9zcmMvaW5kZXgudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsY0FBYyxnQ0FBZ0MsQ0FBQztBQUMvQyxjQUFjLDhCQUE4QixDQUFDO0FBQzdDLGNBQWMsb0NBQW9DLENBQUM7QUFDbkQsY0FBYyxvQ0FBb0MsQ0FBQztBQUNuRCxjQUFjLCtDQUErQyxDQUFDO0FBQzlELGNBQWMsd0JBQXdCLENBQUM7QUFDdkMsY0FBYyxvQkFBb0IsQ0FBQztBQUNuQyxjQUFjLFVBQVUsQ0FBQyJ9

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-event-ordinal.js":
/*!*********************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-event-ordinal.js ***!
  \*********************************************************************************************************/
/*! exports provided: incrementedEventOrdinal */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "incrementedEventOrdinal", function() { return incrementedEventOrdinal; });
/**
 * This enables us to keep information about the original order
 * in which events arrived to our event listeners.
 */
let eventOrdinal = 0;
const incrementedEventOrdinal = () => {
    return eventOrdinal++;
};
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZXh0ZW5zaW9uLXNlc3Npb24tZXZlbnQtb3JkaW5hbC5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvZXh0ZW5zaW9uLXNlc3Npb24tZXZlbnQtb3JkaW5hbC50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQTs7O0dBR0c7QUFDSCxJQUFJLFlBQVksR0FBRyxDQUFDLENBQUM7QUFFckIsTUFBTSxDQUFDLE1BQU0sdUJBQXVCLEdBQUcsR0FBRyxFQUFFO0lBQzFDLE9BQU8sWUFBWSxFQUFFLENBQUM7QUFDeEIsQ0FBQyxDQUFDIn0=

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-uuid.js":
/*!************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/extension-session-uuid.js ***!
  \************************************************************************************************/
/*! exports provided: extensionSessionUuid */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "extensionSessionUuid", function() { return extensionSessionUuid; });
/* harmony import */ var _uuid__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./uuid */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/uuid.js");

/**
 * This enables us to access a unique reference to this browser
 * session - regenerated any time the background process gets
 * restarted (which should only be on browser restarts)
 */
const extensionSessionUuid = Object(_uuid__WEBPACK_IMPORTED_MODULE_0__["makeUUID"])();
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZXh0ZW5zaW9uLXNlc3Npb24tdXVpZC5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvZXh0ZW5zaW9uLXNlc3Npb24tdXVpZC50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxPQUFPLEVBQUUsUUFBUSxFQUFFLE1BQU0sUUFBUSxDQUFDO0FBRWxDOzs7O0dBSUc7QUFDSCxNQUFNLENBQUMsTUFBTSxvQkFBb0IsR0FBRyxRQUFRLEVBQUUsQ0FBQyJ9

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/http-post-parser.js":
/*!******************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/http-post-parser.js ***!
  \******************************************************************************************/
/*! exports provided: HttpPostParser */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "HttpPostParser", function() { return HttpPostParser; });
// Incorporates code from: https://github.com/redline13/selenium-jmeter/blob/6966d4b326cd78261e31e6e317076569051cac37/content/library/recorder/HttpPostParser.js
class HttpPostParser {
    /*
    private hasheaders: boolean;
    private seekablestream;
    private stream;
    private postBody;
    private postLines;
    private postHeaders;
    private body;
    */
    constructor(
    // onBeforeSendHeadersEventDetails: WebRequestOnBeforeSendHeadersEventDetails,
    onBeforeRequestEventDetails, dataReceiver) {
        // this.onBeforeSendHeadersEventDetails = onBeforeSendHeadersEventDetails;
        this.onBeforeRequestEventDetails = onBeforeRequestEventDetails;
        this.dataReceiver = dataReceiver;
        /*
        console.log(
          "HttpPostParser",
          // onBeforeSendHeadersEventDetails,
          onBeforeRequestEventDetails,
        );
        */
    }
    /**
     * @param encodingType from the HTTP Request headers
     */
    parsePostRequest( /*encodingType*/) {
        // const requestHeaders = this.onBeforeSendHeadersEventDetails.requestHeaders;
        const requestBody = this.onBeforeRequestEventDetails.requestBody;
        if (requestBody.error) {
            this.dataReceiver.logError("Exception: Upstream failed to parse POST: " + requestBody.error);
        }
        if (requestBody.formData) {
            return {
                // TODO: requestBody.formData should probably be transformed into another format
                post_body: requestBody.formData,
            };
        }
        // Return empty response until we have all instrumentation converted
        return {};
        /*
        this.dataReceiver.logDebug(
          "Exception: Instrumentation to parse POST requests without formData is not yet restored",
        );
    
        // TODO: Refactor to corresponding webext logic or discard
        try {
          this.setupStream();
          this.parseStream();
        } catch (e) {
          this.dataReceiver.logError("Exception: Failed to parse POST: " + e);
          return {};
        }
    
        const postBody = this.postBody;
    
        if (!postBody) {
          // some scripts strangely sends empty post bodies (confirmed with the developer tools)
          return {};
        }
    
        let isMultiPart = false; // encType: multipart/form-data
        const postHeaders = this.postHeaders; // request headers from upload stream
        // See, http://stackoverflow.com/questions/16548517/what-is-request-headers-from-upload-stream
    
        // add encodingType from postHeaders if it's missing
        if (!encodingType && postHeaders && "Content-Type" in postHeaders) {
          encodingType = postHeaders["Content-Type"];
        }
    
        if (encodingType.indexOf("multipart/form-data") !== -1) {
          isMultiPart = true;
        }
    
        let jsonPostData = "";
        let escapedJsonPostData = "";
        if (isMultiPart) {
          jsonPostData = this.parseMultiPartData(postBody /*, encodingType* /);
          escapedJsonPostData = escapeString(jsonPostData);
        } else {
          jsonPostData = this.parseEncodedFormData(postBody, encodingType);
          escapedJsonPostData = escapeString(jsonPostData);
        }
        return { post_headers: postHeaders, post_body: escapedJsonPostData };
        */
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaHR0cC1wb3N0LXBhcnNlci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvaHR0cC1wb3N0LXBhcnNlci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxnS0FBZ0s7QUFlaEssTUFBTSxPQUFPLGNBQWM7SUFJekI7Ozs7Ozs7O01BUUU7SUFFRjtJQUNFLDhFQUE4RTtJQUM5RSwyQkFBa0UsRUFDbEUsWUFBWTtRQUVaLDBFQUEwRTtRQUMxRSxJQUFJLENBQUMsMkJBQTJCLEdBQUcsMkJBQTJCLENBQUM7UUFDL0QsSUFBSSxDQUFDLFlBQVksR0FBRyxZQUFZLENBQUM7UUFDakM7Ozs7OztVQU1FO0lBQ0osQ0FBQztJQUVEOztPQUVHO0lBQ0ksZ0JBQWdCLEVBQUMsZ0JBQWdCO1FBQ3RDLDhFQUE4RTtRQUM5RSxNQUFNLFdBQVcsR0FBRyxJQUFJLENBQUMsMkJBQTJCLENBQUMsV0FBVyxDQUFDO1FBQ2pFLElBQUksV0FBVyxDQUFDLEtBQUssRUFBRTtZQUNyQixJQUFJLENBQUMsWUFBWSxDQUFDLFFBQVEsQ0FDeEIsNENBQTRDLEdBQUcsV0FBVyxDQUFDLEtBQUssQ0FDakUsQ0FBQztTQUNIO1FBQ0QsSUFBSSxXQUFXLENBQUMsUUFBUSxFQUFFO1lBQ3hCLE9BQU87Z0JBQ0wsZ0ZBQWdGO2dCQUNoRixTQUFTLEVBQUUsV0FBVyxDQUFDLFFBQVE7YUFDaEMsQ0FBQztTQUNIO1FBRUQsb0VBQW9FO1FBQ3BFLE9BQU8sRUFBRSxDQUFDO1FBQ1Y7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O1VBNENFO0lBQ0osQ0FBQztDQTJURiJ9

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-navigation.js":
/*!********************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-navigation.js ***!
  \********************************************************************************************/
/*! exports provided: PendingNavigation */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "PendingNavigation", function() { return PendingNavigation; });
/**
 * Ties together the two separate navigation events that together holds information about both parent frame id and transition-related attributes
 */
class PendingNavigation {
    constructor() {
        this.onBeforeNavigateEventNavigation = new Promise(resolve => {
            this.resolveOnBeforeNavigateEventNavigation = resolve;
        });
        this.onCommittedEventNavigation = new Promise(resolve => {
            this.resolveOnCommittedEventNavigation = resolve;
        });
    }
    resolved() {
        return Promise.all([
            this.onBeforeNavigateEventNavigation,
            this.onCommittedEventNavigation,
        ]);
    }
    /**
     * Either returns or times out and returns undefined or
     * returns the results from resolved() above
     * @param ms
     */
    async resolvedWithinTimeout(ms) {
        const resolved = await Promise.race([
            this.resolved(),
            new Promise(resolve => setTimeout(resolve, ms)),
        ]);
        return resolved;
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicGVuZGluZy1uYXZpZ2F0aW9uLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9wZW5kaW5nLW5hdmlnYXRpb24udHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBRUE7O0dBRUc7QUFDSCxNQUFNLE9BQU8saUJBQWlCO0lBSzVCO1FBQ0UsSUFBSSxDQUFDLCtCQUErQixHQUFHLElBQUksT0FBTyxDQUFDLE9BQU8sQ0FBQyxFQUFFO1lBQzNELElBQUksQ0FBQyxzQ0FBc0MsR0FBRyxPQUFPLENBQUM7UUFDeEQsQ0FBQyxDQUFDLENBQUM7UUFDSCxJQUFJLENBQUMsMEJBQTBCLEdBQUcsSUFBSSxPQUFPLENBQUMsT0FBTyxDQUFDLEVBQUU7WUFDdEQsSUFBSSxDQUFDLGlDQUFpQyxHQUFHLE9BQU8sQ0FBQztRQUNuRCxDQUFDLENBQUMsQ0FBQztJQUNMLENBQUM7SUFDTSxRQUFRO1FBQ2IsT0FBTyxPQUFPLENBQUMsR0FBRyxDQUFDO1lBQ2pCLElBQUksQ0FBQywrQkFBK0I7WUFDcEMsSUFBSSxDQUFDLDBCQUEwQjtTQUNoQyxDQUFDLENBQUM7SUFDTCxDQUFDO0lBRUQ7Ozs7T0FJRztJQUNJLEtBQUssQ0FBQyxxQkFBcUIsQ0FBQyxFQUFFO1FBQ25DLE1BQU0sUUFBUSxHQUFHLE1BQU0sT0FBTyxDQUFDLElBQUksQ0FBQztZQUNsQyxJQUFJLENBQUMsUUFBUSxFQUFFO1lBQ2YsSUFBSSxPQUFPLENBQUMsT0FBTyxDQUFDLEVBQUUsQ0FBQyxVQUFVLENBQUMsT0FBTyxFQUFFLEVBQUUsQ0FBQyxDQUFDO1NBQ2hELENBQUMsQ0FBQztRQUNILE9BQU8sUUFBUSxDQUFDO0lBQ2xCLENBQUM7Q0FDRiJ9

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-request.js":
/*!*****************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-request.js ***!
  \*****************************************************************************************/
/*! exports provided: PendingRequest */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "PendingRequest", function() { return PendingRequest; });
/**
 * Ties together the two separate events that together holds information about both request headers and body
 */
class PendingRequest {
    constructor() {
        this.onBeforeRequestEventDetails = new Promise(resolve => {
            this.resolveOnBeforeRequestEventDetails = resolve;
        });
        this.onBeforeSendHeadersEventDetails = new Promise(resolve => {
            this.resolveOnBeforeSendHeadersEventDetails = resolve;
        });
    }
    resolved() {
        return Promise.all([
            this.onBeforeRequestEventDetails,
            this.onBeforeSendHeadersEventDetails,
        ]);
    }
    /**
     * Either returns or times out and returns undefined or
     * returns the results from resolved() above
     * @param ms
     */
    async resolvedWithinTimeout(ms) {
        const resolved = await Promise.race([
            this.resolved(),
            new Promise(resolve => setTimeout(resolve, ms)),
        ]);
        return resolved;
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicGVuZGluZy1yZXF1ZXN0LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9wZW5kaW5nLXJlcXVlc3QudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBS0E7O0dBRUc7QUFDSCxNQUFNLE9BQU8sY0FBYztJQWF6QjtRQUNFLElBQUksQ0FBQywyQkFBMkIsR0FBRyxJQUFJLE9BQU8sQ0FBQyxPQUFPLENBQUMsRUFBRTtZQUN2RCxJQUFJLENBQUMsa0NBQWtDLEdBQUcsT0FBTyxDQUFDO1FBQ3BELENBQUMsQ0FBQyxDQUFDO1FBQ0gsSUFBSSxDQUFDLCtCQUErQixHQUFHLElBQUksT0FBTyxDQUFDLE9BQU8sQ0FBQyxFQUFFO1lBQzNELElBQUksQ0FBQyxzQ0FBc0MsR0FBRyxPQUFPLENBQUM7UUFDeEQsQ0FBQyxDQUFDLENBQUM7SUFDTCxDQUFDO0lBQ00sUUFBUTtRQUNiLE9BQU8sT0FBTyxDQUFDLEdBQUcsQ0FBQztZQUNqQixJQUFJLENBQUMsMkJBQTJCO1lBQ2hDLElBQUksQ0FBQywrQkFBK0I7U0FDckMsQ0FBQyxDQUFDO0lBQ0wsQ0FBQztJQUVEOzs7O09BSUc7SUFDSSxLQUFLLENBQUMscUJBQXFCLENBQUMsRUFBRTtRQUNuQyxNQUFNLFFBQVEsR0FBRyxNQUFNLE9BQU8sQ0FBQyxJQUFJLENBQUM7WUFDbEMsSUFBSSxDQUFDLFFBQVEsRUFBRTtZQUNmLElBQUksT0FBTyxDQUFDLE9BQU8sQ0FBQyxFQUFFLENBQUMsVUFBVSxDQUFDLE9BQU8sRUFBRSxFQUFFLENBQUMsQ0FBQztTQUNoRCxDQUFDLENBQUM7UUFDSCxPQUFPLFFBQVEsQ0FBQztJQUNsQixDQUFDO0NBQ0YifQ==

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-response.js":
/*!******************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/pending-response.js ***!
  \******************************************************************************************/
/*! exports provided: PendingResponse */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "PendingResponse", function() { return PendingResponse; });
/* harmony import */ var _response_body_listener__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./response-body-listener */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/response-body-listener.js");

/**
 * Ties together the two separate events that together holds information about both response headers and body
 */
class PendingResponse {
    constructor() {
        this.onBeforeRequestEventDetails = new Promise(resolve => {
            this.resolveOnBeforeRequestEventDetails = resolve;
        });
        this.onCompletedEventDetails = new Promise(resolve => {
            this.resolveOnCompletedEventDetails = resolve;
        });
    }
    addResponseResponseBodyListener(details) {
        this.responseBodyListener = new _response_body_listener__WEBPACK_IMPORTED_MODULE_0__["ResponseBodyListener"](details);
    }
    resolved() {
        return Promise.all([
            this.onBeforeRequestEventDetails,
            this.onCompletedEventDetails,
        ]);
    }
    /**
     * Either returns or times out and returns undefined or
     * returns the results from resolved() above
     * @param ms
     */
    async resolvedWithinTimeout(ms) {
        const resolved = await Promise.race([
            this.resolved(),
            new Promise(resolve => setTimeout(resolve, ms)),
        ]);
        return resolved;
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicGVuZGluZy1yZXNwb25zZS5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvcGVuZGluZy1yZXNwb25zZS50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFJQSxPQUFPLEVBQUUsb0JBQW9CLEVBQUUsTUFBTSwwQkFBMEIsQ0FBQztBQUVoRTs7R0FFRztBQUNILE1BQU0sT0FBTyxlQUFlO0lBYzFCO1FBQ0UsSUFBSSxDQUFDLDJCQUEyQixHQUFHLElBQUksT0FBTyxDQUFDLE9BQU8sQ0FBQyxFQUFFO1lBQ3ZELElBQUksQ0FBQyxrQ0FBa0MsR0FBRyxPQUFPLENBQUM7UUFDcEQsQ0FBQyxDQUFDLENBQUM7UUFDSCxJQUFJLENBQUMsdUJBQXVCLEdBQUcsSUFBSSxPQUFPLENBQUMsT0FBTyxDQUFDLEVBQUU7WUFDbkQsSUFBSSxDQUFDLDhCQUE4QixHQUFHLE9BQU8sQ0FBQztRQUNoRCxDQUFDLENBQUMsQ0FBQztJQUNMLENBQUM7SUFDTSwrQkFBK0IsQ0FDcEMsT0FBOEM7UUFFOUMsSUFBSSxDQUFDLG9CQUFvQixHQUFHLElBQUksb0JBQW9CLENBQUMsT0FBTyxDQUFDLENBQUM7SUFDaEUsQ0FBQztJQUNNLFFBQVE7UUFDYixPQUFPLE9BQU8sQ0FBQyxHQUFHLENBQUM7WUFDakIsSUFBSSxDQUFDLDJCQUEyQjtZQUNoQyxJQUFJLENBQUMsdUJBQXVCO1NBQzdCLENBQUMsQ0FBQztJQUNMLENBQUM7SUFFRDs7OztPQUlHO0lBQ0ksS0FBSyxDQUFDLHFCQUFxQixDQUFDLEVBQUU7UUFDbkMsTUFBTSxRQUFRLEdBQUcsTUFBTSxPQUFPLENBQUMsSUFBSSxDQUFDO1lBQ2xDLElBQUksQ0FBQyxRQUFRLEVBQUU7WUFDZixJQUFJLE9BQU8sQ0FBQyxPQUFPLENBQUMsRUFBRSxDQUFDLFVBQVUsQ0FBQyxPQUFPLEVBQUUsRUFBRSxDQUFDLENBQUM7U0FDaEQsQ0FBQyxDQUFDO1FBQ0gsT0FBTyxRQUFRLENBQUM7SUFDbEIsQ0FBQztDQUNGIn0=

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/response-body-listener.js":
/*!************************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/response-body-listener.js ***!
  \************************************************************************************************/
/*! exports provided: ResponseBodyListener */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ResponseBodyListener", function() { return ResponseBodyListener; });
/* harmony import */ var _sha256__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./sha256 */ "./node_modules/openwpm-webext-instrumentation/build/module/lib/sha256.js");

class ResponseBodyListener {
    constructor(details) {
        this.responseBody = new Promise(resolve => {
            this.resolveResponseBody = resolve;
        });
        this.contentHash = new Promise(resolve => {
            this.resolveContentHash = resolve;
        });
        // Used to parse Response stream
        const filter = browser.webRequest.filterResponseData(details.requestId);
        const decoder = new TextDecoder("utf-8");
        // const encoder = new TextEncoder();
        let responseBody = "";
        filter.ondata = event => {
            Object(_sha256__WEBPACK_IMPORTED_MODULE_0__["sha256Buffer"])(event.data).then(digest => {
                this.resolveContentHash(digest);
            });
            const str = decoder.decode(event.data, { stream: true });
            responseBody = responseBody + str;
            // pass through all the response data
            filter.write(event.data);
        };
        filter.onstop = _event => {
            this.resolveResponseBody(responseBody);
            filter.disconnect();
        };
    }
    async getResponseBody() {
        return this.responseBody;
    }
    async getContentHash() {
        return this.contentHash;
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicmVzcG9uc2UtYm9keS1saXN0ZW5lci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvcmVzcG9uc2UtYm9keS1saXN0ZW5lci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFDQSxPQUFPLEVBQUUsWUFBWSxFQUFFLE1BQU0sVUFBVSxDQUFDO0FBRXhDLE1BQU0sT0FBTyxvQkFBb0I7SUFNL0IsWUFBWSxPQUE4QztRQUN4RCxJQUFJLENBQUMsWUFBWSxHQUFHLElBQUksT0FBTyxDQUFDLE9BQU8sQ0FBQyxFQUFFO1lBQ3hDLElBQUksQ0FBQyxtQkFBbUIsR0FBRyxPQUFPLENBQUM7UUFDckMsQ0FBQyxDQUFDLENBQUM7UUFDSCxJQUFJLENBQUMsV0FBVyxHQUFHLElBQUksT0FBTyxDQUFDLE9BQU8sQ0FBQyxFQUFFO1lBQ3ZDLElBQUksQ0FBQyxrQkFBa0IsR0FBRyxPQUFPLENBQUM7UUFDcEMsQ0FBQyxDQUFDLENBQUM7UUFFSCxnQ0FBZ0M7UUFDaEMsTUFBTSxNQUFNLEdBQVEsT0FBTyxDQUFDLFVBQVUsQ0FBQyxrQkFBa0IsQ0FDdkQsT0FBTyxDQUFDLFNBQVMsQ0FDWCxDQUFDO1FBRVQsTUFBTSxPQUFPLEdBQUcsSUFBSSxXQUFXLENBQUMsT0FBTyxDQUFDLENBQUM7UUFDekMscUNBQXFDO1FBRXJDLElBQUksWUFBWSxHQUFHLEVBQUUsQ0FBQztRQUN0QixNQUFNLENBQUMsTUFBTSxHQUFHLEtBQUssQ0FBQyxFQUFFO1lBQ3RCLFlBQVksQ0FBQyxLQUFLLENBQUMsSUFBSSxDQUFDLENBQUMsSUFBSSxDQUFDLE1BQU0sQ0FBQyxFQUFFO2dCQUNyQyxJQUFJLENBQUMsa0JBQWtCLENBQUMsTUFBTSxDQUFDLENBQUM7WUFDbEMsQ0FBQyxDQUFDLENBQUM7WUFDSCxNQUFNLEdBQUcsR0FBRyxPQUFPLENBQUMsTUFBTSxDQUFDLEtBQUssQ0FBQyxJQUFJLEVBQUUsRUFBRSxNQUFNLEVBQUUsSUFBSSxFQUFFLENBQUMsQ0FBQztZQUN6RCxZQUFZLEdBQUcsWUFBWSxHQUFHLEdBQUcsQ0FBQztZQUNsQyxxQ0FBcUM7WUFDckMsTUFBTSxDQUFDLEtBQUssQ0FBQyxLQUFLLENBQUMsSUFBSSxDQUFDLENBQUM7UUFDM0IsQ0FBQyxDQUFDO1FBRUYsTUFBTSxDQUFDLE1BQU0sR0FBRyxNQUFNLENBQUMsRUFBRTtZQUN2QixJQUFJLENBQUMsbUJBQW1CLENBQUMsWUFBWSxDQUFDLENBQUM7WUFDdkMsTUFBTSxDQUFDLFVBQVUsRUFBRSxDQUFDO1FBQ3RCLENBQUMsQ0FBQztJQUNKLENBQUM7SUFFTSxLQUFLLENBQUMsZUFBZTtRQUMxQixPQUFPLElBQUksQ0FBQyxZQUFZLENBQUM7SUFDM0IsQ0FBQztJQUVNLEtBQUssQ0FBQyxjQUFjO1FBQ3pCLE9BQU8sSUFBSSxDQUFDLFdBQVcsQ0FBQztJQUMxQixDQUFDO0NBQ0YifQ==

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/sha256.js":
/*!********************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/sha256.js ***!
  \********************************************************************************/
/*! exports provided: sha256, sha256Buffer */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "sha256", function() { return sha256; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "sha256Buffer", function() { return sha256Buffer; });
/**
 * Code originally from the example at
 * https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest
 *
 * Note: Using SHA256 instead of the previously used MD5 due to
 * the following comment found at the documentation page linked above:
 *
 * Warning: Older insecure hash functions, like MD5, are not supported
 * by this method. Even a supported method, SHA-1, is considered weak,
 * has been broken and should be avoided for cryptographic applications.
 */
function sha256(str) {
    // We transform the string into an arraybuffer.
    const buffer = new TextEncoder().encode(str);
    return sha256Buffer(buffer);
}
function sha256Buffer(buffer) {
    return crypto.subtle.digest("SHA-256", buffer).then(function (hash) {
        return hex(hash);
    });
}
function hex(buffer) {
    const hexCodes = [];
    const view = new DataView(buffer);
    for (let i = 0; i < view.byteLength; i += 4) {
        // Using getUint32 reduces the number of iterations needed (we process 4 bytes each time)
        const value = view.getUint32(i);
        // toString(16) will give the hex representation of the number without padding
        const stringValue = value.toString(16);
        // We use concatenation and slice for padding
        const padding = "00000000";
        const paddedValue = (padding + stringValue).slice(-padding.length);
        hexCodes.push(paddedValue);
    }
    // Join all the hex strings into one
    return hexCodes.join("");
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic2hhMjU2LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9zaGEyNTYudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7Ozs7Ozs7Ozs7R0FVRztBQUVILE1BQU0sVUFBVSxNQUFNLENBQUMsR0FBRztJQUN4QiwrQ0FBK0M7SUFDL0MsTUFBTSxNQUFNLEdBQUcsSUFBSSxXQUFXLEVBQUUsQ0FBQyxNQUFNLENBQUMsR0FBRyxDQUFDLENBQUM7SUFDN0MsT0FBTyxZQUFZLENBQUMsTUFBTSxDQUFDLENBQUM7QUFDOUIsQ0FBQztBQUVELE1BQU0sVUFBVSxZQUFZLENBQUMsTUFBTTtJQUNqQyxPQUFPLE1BQU0sQ0FBQyxNQUFNLENBQUMsTUFBTSxDQUFDLFNBQVMsRUFBRSxNQUFNLENBQUMsQ0FBQyxJQUFJLENBQUMsVUFBUyxJQUFJO1FBQy9ELE9BQU8sR0FBRyxDQUFDLElBQUksQ0FBQyxDQUFDO0lBQ25CLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQztBQUVELFNBQVMsR0FBRyxDQUFDLE1BQU07SUFDakIsTUFBTSxRQUFRLEdBQUcsRUFBRSxDQUFDO0lBQ3BCLE1BQU0sSUFBSSxHQUFHLElBQUksUUFBUSxDQUFDLE1BQU0sQ0FBQyxDQUFDO0lBQ2xDLEtBQUssSUFBSSxDQUFDLEdBQUcsQ0FBQyxFQUFFLENBQUMsR0FBRyxJQUFJLENBQUMsVUFBVSxFQUFFLENBQUMsSUFBSSxDQUFDLEVBQUU7UUFDM0MseUZBQXlGO1FBQ3pGLE1BQU0sS0FBSyxHQUFHLElBQUksQ0FBQyxTQUFTLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDaEMsOEVBQThFO1FBQzlFLE1BQU0sV0FBVyxHQUFHLEtBQUssQ0FBQyxRQUFRLENBQUMsRUFBRSxDQUFDLENBQUM7UUFDdkMsNkNBQTZDO1FBQzdDLE1BQU0sT0FBTyxHQUFHLFVBQVUsQ0FBQztRQUMzQixNQUFNLFdBQVcsR0FBRyxDQUFDLE9BQU8sR0FBRyxXQUFXLENBQUMsQ0FBQyxLQUFLLENBQUMsQ0FBQyxPQUFPLENBQUMsTUFBTSxDQUFDLENBQUM7UUFDbkUsUUFBUSxDQUFDLElBQUksQ0FBQyxXQUFXLENBQUMsQ0FBQztLQUM1QjtJQUVELG9DQUFvQztJQUNwQyxPQUFPLFFBQVEsQ0FBQyxJQUFJLENBQUMsRUFBRSxDQUFDLENBQUM7QUFDM0IsQ0FBQyJ9

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/string-utils.js":
/*!**************************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/string-utils.js ***!
  \**************************************************************************************/
/*! exports provided: encode_utf8, escapeString, escapeUrl, boolToInt */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "encode_utf8", function() { return encode_utf8; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "escapeString", function() { return escapeString; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "escapeUrl", function() { return escapeUrl; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "boolToInt", function() { return boolToInt; });
function encode_utf8(s) {
    return unescape(encodeURIComponent(s));
}
const escapeString = function (str) {
    // Convert to string if necessary
    if (typeof str != "string") {
        str = String(str);
    }
    return encode_utf8(str);
};
const escapeUrl = function (url, stripDataUrlData = true) {
    url = escapeString(url);
    // data:[<mediatype>][;base64],<data>
    if (url.substr(0, 5) === "data:" &&
        stripDataUrlData &&
        url.indexOf(",") > -1) {
        url = url.substr(0, url.indexOf(",") + 1) + "<data-stripped>";
    }
    return url;
};
const boolToInt = function (bool) {
    return bool ? 1 : 0;
};
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic3RyaW5nLXV0aWxzLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9zdHJpbmctdXRpbHMudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsTUFBTSxVQUFVLFdBQVcsQ0FBQyxDQUFDO0lBQzNCLE9BQU8sUUFBUSxDQUFDLGtCQUFrQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQztBQUVELE1BQU0sQ0FBQyxNQUFNLFlBQVksR0FBRyxVQUFTLEdBQVE7SUFDM0MsaUNBQWlDO0lBQ2pDLElBQUksT0FBTyxHQUFHLElBQUksUUFBUSxFQUFFO1FBQzFCLEdBQUcsR0FBRyxNQUFNLENBQUMsR0FBRyxDQUFDLENBQUM7S0FDbkI7SUFFRCxPQUFPLFdBQVcsQ0FBQyxHQUFHLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUM7QUFFRixNQUFNLENBQUMsTUFBTSxTQUFTLEdBQUcsVUFDdkIsR0FBVyxFQUNYLG1CQUE0QixJQUFJO0lBRWhDLEdBQUcsR0FBRyxZQUFZLENBQUMsR0FBRyxDQUFDLENBQUM7SUFDeEIscUNBQXFDO0lBQ3JDLElBQ0UsR0FBRyxDQUFDLE1BQU0sQ0FBQyxDQUFDLEVBQUUsQ0FBQyxDQUFDLEtBQUssT0FBTztRQUM1QixnQkFBZ0I7UUFDaEIsR0FBRyxDQUFDLE9BQU8sQ0FBQyxHQUFHLENBQUMsR0FBRyxDQUFDLENBQUMsRUFDckI7UUFDQSxHQUFHLEdBQUcsR0FBRyxDQUFDLE1BQU0sQ0FBQyxDQUFDLEVBQUUsR0FBRyxDQUFDLE9BQU8sQ0FBQyxHQUFHLENBQUMsR0FBRyxDQUFDLENBQUMsR0FBRyxpQkFBaUIsQ0FBQztLQUMvRDtJQUNELE9BQU8sR0FBRyxDQUFDO0FBQ2IsQ0FBQyxDQUFDO0FBRUYsTUFBTSxDQUFDLE1BQU0sU0FBUyxHQUFHLFVBQVMsSUFBYTtJQUM3QyxPQUFPLElBQUksQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDIn0=

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/lib/uuid.js":
/*!******************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/lib/uuid.js ***!
  \******************************************************************************/
/*! exports provided: makeUUID */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "makeUUID", function() { return makeUUID; });
/* tslint:disable:no-bitwise */
// from https://gist.github.com/jed/982883#gistcomment-2403369
const hex = [];
for (let i = 0; i < 256; i++) {
    hex[i] = (i < 16 ? "0" : "") + i.toString(16);
}
const makeUUID = () => {
    const r = crypto.getRandomValues(new Uint8Array(16));
    r[6] = (r[6] & 0x0f) | 0x40;
    r[8] = (r[8] & 0x3f) | 0x80;
    return (hex[r[0]] +
        hex[r[1]] +
        hex[r[2]] +
        hex[r[3]] +
        "-" +
        hex[r[4]] +
        hex[r[5]] +
        "-" +
        hex[r[6]] +
        hex[r[7]] +
        "-" +
        hex[r[8]] +
        hex[r[9]] +
        "-" +
        hex[r[10]] +
        hex[r[11]] +
        hex[r[12]] +
        hex[r[13]] +
        hex[r[14]] +
        hex[r[15]]);
};
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoidXVpZC5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvdXVpZC50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSwrQkFBK0I7QUFFL0IsOERBQThEO0FBQzlELE1BQU0sR0FBRyxHQUFHLEVBQUUsQ0FBQztBQUVmLEtBQUssSUFBSSxDQUFDLEdBQUcsQ0FBQyxFQUFFLENBQUMsR0FBRyxHQUFHLEVBQUUsQ0FBQyxFQUFFLEVBQUU7SUFDNUIsR0FBRyxDQUFDLENBQUMsQ0FBQyxHQUFHLENBQUMsQ0FBQyxHQUFHLEVBQUUsQ0FBQyxDQUFDLENBQUMsR0FBRyxDQUFDLENBQUMsQ0FBQyxFQUFFLENBQUMsR0FBRyxDQUFDLENBQUMsUUFBUSxDQUFDLEVBQUUsQ0FBQyxDQUFDO0NBQy9DO0FBRUQsTUFBTSxDQUFDLE1BQU0sUUFBUSxHQUFHLEdBQUcsRUFBRTtJQUMzQixNQUFNLENBQUMsR0FBRyxNQUFNLENBQUMsZUFBZSxDQUFDLElBQUksVUFBVSxDQUFDLEVBQUUsQ0FBQyxDQUFDLENBQUM7SUFFckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxHQUFHLElBQUksQ0FBQyxHQUFHLElBQUksQ0FBQztJQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLEdBQUcsSUFBSSxDQUFDLEdBQUcsSUFBSSxDQUFDO0lBRTVCLE9BQU8sQ0FDTCxHQUFHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ1QsR0FBRyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztRQUNULEdBQUcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDVCxHQUFHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ1QsR0FBRztRQUNILEdBQUcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDVCxHQUFHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ1QsR0FBRztRQUNILEdBQUcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDVCxHQUFHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ1QsR0FBRztRQUNILEdBQUcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDVCxHQUFHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBQ1QsR0FBRztRQUNILEdBQUcsQ0FBQyxDQUFDLENBQUMsRUFBRSxDQUFDLENBQUM7UUFDVixHQUFHLENBQUMsQ0FBQyxDQUFDLEVBQUUsQ0FBQyxDQUFDO1FBQ1YsR0FBRyxDQUFDLENBQUMsQ0FBQyxFQUFFLENBQUMsQ0FBQztRQUNWLEdBQUcsQ0FBQyxDQUFDLENBQUMsRUFBRSxDQUFDLENBQUM7UUFDVixHQUFHLENBQUMsQ0FBQyxDQUFDLEVBQUUsQ0FBQyxDQUFDO1FBQ1YsR0FBRyxDQUFDLENBQUMsQ0FBQyxFQUFFLENBQUMsQ0FBQyxDQUNYLENBQUM7QUFDSixDQUFDLENBQUMifQ==

/***/ }),

/***/ "./node_modules/openwpm-webext-instrumentation/build/module/schema.js":
/*!****************************************************************************!*\
  !*** ./node_modules/openwpm-webext-instrumentation/build/module/schema.js ***!
  \****************************************************************************/
/*! exports provided: dateTimeUnicodeFormatString */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "dateTimeUnicodeFormatString", function() { return dateTimeUnicodeFormatString; });
// https://www.unicode.org/reports/tr35/tr35-dates.html#Date_Field_Symbol_Table
const dateTimeUnicodeFormatString = "yyyy-MM-dd'T'HH:mm:ss.SSSXX";
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic2NoZW1hLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vc3JjL3NjaGVtYS50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFJQSwrRUFBK0U7QUFDL0UsTUFBTSxDQUFDLE1BQU0sMkJBQTJCLEdBQUcsNkJBQTZCLENBQUMifQ==

/***/ })

/******/ });
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly8vd2VicGFjay9ib290c3RyYXAiLCJ3ZWJwYWNrOi8vLy4vY29udGVudC5qcy9pbmRleC5qcyIsIndlYnBhY2s6Ly8vLi9ub2RlX21vZHVsZXMvb3BlbndwbS13ZWJleHQtaW5zdHJ1bWVudGF0aW9uL2J1aWxkL21vZHVsZS9iYWNrZ3JvdW5kL2Nvb2tpZS1pbnN0cnVtZW50LmpzIiwid2VicGFjazovLy8uL25vZGVfbW9kdWxlcy9vcGVud3BtLXdlYmV4dC1pbnN0cnVtZW50YXRpb24vYnVpbGQvbW9kdWxlL2JhY2tncm91bmQvaHR0cC1pbnN0cnVtZW50LmpzIiwid2VicGFjazovLy8uL25vZGVfbW9kdWxlcy9vcGVud3BtLXdlYmV4dC1pbnN0cnVtZW50YXRpb24vYnVpbGQvbW9kdWxlL2JhY2tncm91bmQvamF2YXNjcmlwdC1pbnN0cnVtZW50LmpzIiwid2VicGFjazovLy8uL25vZGVfbW9kdWxlcy9vcGVud3BtLXdlYmV4dC1pbnN0cnVtZW50YXRpb24vYnVpbGQvbW9kdWxlL2JhY2tncm91bmQvbmF2aWdhdGlvbi1pbnN0cnVtZW50LmpzIiwid2VicGFjazovLy8uL25vZGVfbW9kdWxlcy9vcGVud3BtLXdlYmV4dC1pbnN0cnVtZW50YXRpb24vYnVpbGQvbW9kdWxlL2NvbnRlbnQvamF2YXNjcmlwdC1pbnN0cnVtZW50LWNvbnRlbnQtc2NvcGUuanMiLCJ3ZWJwYWNrOi8vLy4vbm9kZV9tb2R1bGVzL29wZW53cG0td2ViZXh0LWluc3RydW1lbnRhdGlvbi9idWlsZC9tb2R1bGUvY29udGVudC9qYXZhc2NyaXB0LWluc3RydW1lbnQtcGFnZS1zY29wZS5qcyIsIndlYnBhY2s6Ly8vLi9ub2RlX21vZHVsZXMvb3BlbndwbS13ZWJleHQtaW5zdHJ1bWVudGF0aW9uL2J1aWxkL21vZHVsZS9pbmRleC5qcyIsIndlYnBhY2s6Ly8vLi9ub2RlX21vZHVsZXMvb3BlbndwbS13ZWJleHQtaW5zdHJ1bWVudGF0aW9uL2J1aWxkL21vZHVsZS9saWIvZXh0ZW5zaW9uLXNlc3Npb24tZXZlbnQtb3JkaW5hbC5qcyIsIndlYnBhY2s6Ly8vLi9ub2RlX21vZHVsZXMvb3BlbndwbS13ZWJleHQtaW5zdHJ1bWVudGF0aW9uL2J1aWxkL21vZHVsZS9saWIvZXh0ZW5zaW9uLXNlc3Npb24tdXVpZC5qcyIsIndlYnBhY2s6Ly8vLi9ub2RlX21vZHVsZXMvb3BlbndwbS13ZWJleHQtaW5zdHJ1bWVudGF0aW9uL2J1aWxkL21vZHVsZS9saWIvaHR0cC1wb3N0LXBhcnNlci5qcyIsIndlYnBhY2s6Ly8vLi9ub2RlX21vZHVsZXMvb3BlbndwbS13ZWJleHQtaW5zdHJ1bWVudGF0aW9uL2J1aWxkL21vZHVsZS9saWIvcGVuZGluZy1uYXZpZ2F0aW9uLmpzIiwid2VicGFjazovLy8uL25vZGVfbW9kdWxlcy9vcGVud3BtLXdlYmV4dC1pbnN0cnVtZW50YXRpb24vYnVpbGQvbW9kdWxlL2xpYi9wZW5kaW5nLXJlcXVlc3QuanMiLCJ3ZWJwYWNrOi8vLy4vbm9kZV9tb2R1bGVzL29wZW53cG0td2ViZXh0LWluc3RydW1lbnRhdGlvbi9idWlsZC9tb2R1bGUvbGliL3BlbmRpbmctcmVzcG9uc2UuanMiLCJ3ZWJwYWNrOi8vLy4vbm9kZV9tb2R1bGVzL29wZW53cG0td2ViZXh0LWluc3RydW1lbnRhdGlvbi9idWlsZC9tb2R1bGUvbGliL3Jlc3BvbnNlLWJvZHktbGlzdGVuZXIuanMiLCJ3ZWJwYWNrOi8vLy4vbm9kZV9tb2R1bGVzL29wZW53cG0td2ViZXh0LWluc3RydW1lbnRhdGlvbi9idWlsZC9tb2R1bGUvbGliL3NoYTI1Ni5qcyIsIndlYnBhY2s6Ly8vLi9ub2RlX21vZHVsZXMvb3BlbndwbS13ZWJleHQtaW5zdHJ1bWVudGF0aW9uL2J1aWxkL21vZHVsZS9saWIvc3RyaW5nLXV0aWxzLmpzIiwid2VicGFjazovLy8uL25vZGVfbW9kdWxlcy9vcGVud3BtLXdlYmV4dC1pbnN0cnVtZW50YXRpb24vYnVpbGQvbW9kdWxlL2xpYi91dWlkLmpzIiwid2VicGFjazovLy8uL25vZGVfbW9kdWxlcy9vcGVud3BtLXdlYmV4dC1pbnN0cnVtZW50YXRpb24vYnVpbGQvbW9kdWxlL3NjaGVtYS5qcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiO0FBQUE7QUFDQTs7QUFFQTtBQUNBOztBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQUVBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQTtBQUNBO0FBQ0E7OztBQUdBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQTtBQUNBO0FBQ0E7QUFDQSxrREFBMEMsZ0NBQWdDO0FBQzFFO0FBQ0E7O0FBRUE7QUFDQTtBQUNBO0FBQ0EsZ0VBQXdELGtCQUFrQjtBQUMxRTtBQUNBLHlEQUFpRCxjQUFjO0FBQy9EOztBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxpREFBeUMsaUNBQWlDO0FBQzFFLHdIQUFnSCxtQkFBbUIsRUFBRTtBQUNySTtBQUNBOztBQUVBO0FBQ0E7QUFDQTtBQUNBLG1DQUEyQiwwQkFBMEIsRUFBRTtBQUN2RCx5Q0FBaUMsZUFBZTtBQUNoRDtBQUNBO0FBQ0E7O0FBRUE7QUFDQSw4REFBc0QsK0RBQStEOztBQUVySDtBQUNBOzs7QUFHQTtBQUNBOzs7Ozs7Ozs7Ozs7O0FDbEZBO0FBQUE7QUFBc0Y7O0FBRXRGLDJHQUFvQzs7Ozs7Ozs7Ozs7Ozs7QUNGcEM7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQWlGO0FBQ1o7QUFDUDtBQUN2RDtBQUNQO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSw2Q0FBNkM7QUFDN0M7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsMkRBQTJEO0FBQzNEO0FBQ0E7QUFDQTtBQUNBLG9DQUFvQyxtRUFBUztBQUM3QyxvQ0FBb0MsbUVBQVM7QUFDN0Msa0NBQWtDLG1FQUFTO0FBQzNDLDRCQUE0QixzRUFBWTtBQUN4QyxpQ0FBaUMsbUVBQVM7QUFDMUMsNEJBQTRCLHNFQUFZO0FBQ3hDLDRC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Ozs7O0FDM0MzQztBQUFBO0FBQUE7QUFDQTtBQUNPO0FBQ1A7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsYUFBYTtBQUNiO0FBQ0E7QUFDQSxTQUFTO0FBQ1Q7QUFDQTtBQUNBLDJCQUEyQiw4QkFBOEI7QUFDekQ7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSx1QkFBdUIscUJBQXFCO0FBQzVDO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLGFBQWE7QUFDYjtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxtQ0FBbUM7QUFDbkM7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsK0RBQStEO0FBQy9EO0FBQ0EsMkNBQTJDO0FBQzNDO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsMkJBQTJCLGlCQUFpQjtBQUM1QztBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLGtFQUFrRTtBQUNsRTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLHVCQUF1Qix1QkFBdUI7QUFDOUM7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxpQkFBaUI7QUFDakI7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0Esd0ZBQXdGO0FBQ3hGO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtB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c0Q7Ozs7Ozs7Ozs7OztBQ25DM0M7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNPO0FBQ1A7QUFDQTtBQUNBO0FBQ0E7QUFDTztBQUNQO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBO0FBQ0E7QUFDQSxtQkFBbUIscUJBQXFCO0FBQ3hDO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLDJDQUEyQyxtNEM7Ozs7Ozs7Ozs7OztBQ3JDM0M7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFPO0FBQ1A7QUFDQTtBQUNPO0FBQ1A7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ087QUFDUDtBQUNBLDJCQUEyQjtBQUMzQjtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNPO0FBQ1A7QUFDQTtBQUNBLDJDQUEyQywyc0M7Ozs7Ozs7Ozs7OztBQ3ZCM0M7QUFBQTtBQUFBO0FBQ0E7QUFDQTtBQUNBLGVBQWUsU0FBUztBQUN4QjtBQUNBO0FBQ087QUFDUDtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSwyQ0FBMkMsMnpEOzs7Ozs7Ozs7Ozs7QUMvQjNDO0FBQUE7QUFBQTtBQUNPO0FBQ1AsMkNBQTJDLG1PIiwiZmlsZSI6ImNvbnRlbnQuanMiLCJzb3VyY2VzQ29udGVudCI6WyIgXHQvLyBUaGUgbW9kdWxlIGNhY2hlXG4gXHR2YXIgaW5zdGFsbGVkTW9kdWxlcyA9IHt9O1xuXG4gXHQvLyBUaGUgcmVxdWlyZSBmdW5jdGlvblxuIFx0ZnVuY3Rpb24gX193ZWJwYWNrX3JlcXVpcmVfXyhtb2R1bGVJZCkge1xuXG4gXHRcdC8vIENoZWNrIGlmIG1vZHVsZSBpcyBpbiBjYWNoZVxuIFx0XHRpZihpbnN0YWxsZWRNb2R1bGVzW21vZHVsZUlkXSkge1xuIFx0XHRcdHJldHVybiBpbnN0YWxsZWRNb2R1bGVzW21vZHVsZUlkXS5leHBvcnRzO1xuIFx0XHR9XG4gXHRcdC8vIENyZWF0ZSBhIG5ldyBtb2R1bGUgKGFuZCBwdXQgaXQgaW50byB0aGUgY2FjaGUpXG4gXHRcdHZhciBtb2R1bGUgPSBpbnN0YWxsZWRNb2R1bGVzW21vZHVsZUlkXSA9IHtcbiBcdFx0XHRpOiBtb2R1bGVJZCxcbiBcdFx0XHRsOiBmYWxzZSxcbiBcdFx0XHRleHBvcnRzOiB7fVxuIFx0XHR9O1xuXG4gXHRcdC8vIEV4ZWN1dGUgdGhlIG1vZHVsZSBmdW5jdGlvblxuIFx0XHRtb2R1bGVzW21vZHVsZUlkXS5jYWxsKG1vZHVsZS5leHBvcnRzLCBtb2R1bGUsIG1vZHVsZS5leHBvcnRzLCBfX3dlYnBhY2tfcmVxdWlyZV9fKTtcblxuIFx0XHQvLyBGbGFnIHRoZSBtb2R1bGUgYXMgbG9hZGVkXG4gXHRcdG1vZHVsZS5sID0gdHJ1ZTtcblxuIFx0XHQvLyBSZXR1cm4gdGhlIGV4cG9ydHMgb2YgdGhlIG1vZHVsZVxuIFx0XHRyZXR1cm4gbW9kdWxlLmV4cG9ydHM7XG4gXHR9XG5cblxuIFx0Ly8gZXhwb3NlIHRoZSBtb2R1bGVzIG9iamVjdCAoX193ZWJwYWNrX21vZHVsZXNfXylcbiBcdF9fd2VicGFja19yZXF1aXJlX18ubSA9IG1vZHVsZXM7XG5cbiBcdC8vIGV4cG9zZSB0aGUgbW9kdWxlIGNhY2hlXG4gXHRfX3dlYnBhY2tfcmVxdWlyZV9fLmMgPSBpbnN0YWxsZWRNb2R1bGVzO1xuXG4gXHQvLyBkZWZpbmUgZ2V0dGVyIGZ1bmN0aW9uIGZvciBoYXJtb255IGV4cG9ydHNcbiBcdF9fd2VicGFja19yZXF1aXJlX18uZCA9IGZ1bmN0aW9uKGV4cG9ydHMsIG5hbWUsIGdldHRlcikge1xuIFx0XHRpZighX193ZWJwYWNrX3JlcXVpcmVfXy5vKGV4cG9ydHMsIG5hbWUpKSB7XG4gXHRcdFx0T2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIG5hbWUsIHsgZW51bWVyYWJsZTogdHJ1ZSwgZ2V0OiBnZXR0ZXIgfSk7XG4gXHRcdH1cbiBcdH07XG5cbiBcdC8vIGRlZmluZSBfX2VzTW9kdWxlIG9uIGV4cG9ydHNcbiBcdF9fd2VicGFja19yZXF1aXJlX18uciA9IGZ1bmN0aW9uKGV4cG9ydHMpIHtcbiBcdFx0aWYodHlwZW9mIFN5bWJvbCAhPT0gJ3VuZGVmaW5lZCcgJiYgU3ltYm9sLnRvU3RyaW5nVGFnKSB7XG4gXHRcdFx0T2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFN5bWJvbC50b1N0cmluZ1RhZywgeyB2YWx1ZTogJ01vZHVsZScgfSk7XG4gXHRcdH1cbiBcdFx0T2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsICdfX2VzTW9kdWxlJywgeyB2YWx1ZTogdHJ1ZSB9KTtcbiBcdH07XG5cbiBcdC8vIGNyZWF0ZSBhIGZha2UgbmFtZXNwYWNlIG9iamVjdFxuIFx0Ly8gbW9kZSAmIDE6IHZhbHVlIGlzIGEgbW9kdWxlIGlkLCByZXF1aXJlIGl0XG4gXHQvLyBtb2RlICYgMjogbWVyZ2UgYWxsIHByb3BlcnRpZXMgb2YgdmFsdWUgaW50byB0aGUgbnNcbiBcdC8vIG1vZGUgJiA0OiByZXR1cm4gdmFsdWUgd2hlbiBhbHJlYWR5IG5zIG9iamVjdFxuIFx0Ly8gbW9kZSAmIDh8MTogYmVoYXZlIGxpa2UgcmVxdWlyZVxuIFx0X193ZWJwYWNrX3JlcXVpcmVfXy50ID0gZnVuY3Rpb24odmFsdWUsIG1vZGUpIHtcbiBcdFx0aWYobW9kZSAmIDEpIHZhbHVlID0gX193ZWJwYWNrX3JlcXVpcmVfXyh2YWx1ZSk7XG4gXHRcdGlmKG1vZGUgJiA4KSByZXR1cm4gdmFsdWU7XG4gXHRcdGlmKChtb2RlICYgNCkgJiYgdHlwZW9mIHZhbHVlID09PSAnb2JqZWN0JyAmJiB2YWx1ZSAmJiB2YWx1ZS5fX2VzTW9kdWxlKSByZXR1cm4gdmFsdWU7XG4gXHRcdHZhciBucyA9IE9iamVjdC5jcmVhdGUobnVsbCk7XG4gXHRcdF9fd2VicGFja19yZXF1aXJlX18ucihucyk7XG4gXHRcdE9iamVjdC5kZWZpbmVQcm9wZXJ0eShucywgJ2RlZmF1bHQnLCB7IGVudW1lcmFibGU6IHRydWUsIHZhbHVlOiB2YWx1ZSB9KTtcbiBcdFx0aWYobW9kZSAmIDIgJiYgdHlwZW9mIHZhbHVlICE9ICdzdHJpbmcnKSBmb3IodmFyIGtleSBpbiB2YWx1ZSkgX193ZWJwYWNrX3JlcXVpcmVfXy5kKG5zLCBrZXksIGZ1bmN0aW9uKGtleSkgeyByZXR1cm4gdmFsdWVba2V5XTsgfS5iaW5kKG51bGwsIGtleSkpO1xuIFx0XHRyZXR1cm4gbnM7XG4gXHR9O1xuXG4gXHQvLyBnZXREZWZhdWx0RXhwb3J0IGZ1bmN0aW9uIGZvciBjb21wYXRpYmlsaXR5IHdpdGggbm9uLWhhcm1vbnkgbW9kdWxlc1xuIFx0X193ZWJwYWNrX3JlcXVpcmVfXy5uID0gZnVuY3Rpb24obW9kdWxlKSB7XG4gXHRcdHZhciBnZXR0ZXIgPSBtb2R1bGUgJiYgbW9kdWxlLl9fZXNNb2R1bGUgP1xuIFx0XHRcdGZ1bmN0aW9uIGdldERlZmF1bHQoKSB7IHJldHVybiBtb2R1bGVbJ2RlZmF1bHQnXTsgfSA6XG4gXHRcdFx0ZnVuY3Rpb24gZ2V0TW9kdWxlRXhwb3J0cygpIHsgcmV0dXJuIG1vZHVsZTsgfTtcbiBcdFx0X193ZWJwYWNrX3JlcXVpcmVfXy5kKGdldHRlciwgJ2EnLCBnZXR0ZXIpO1xuIFx0XHRyZXR1cm4gZ2V0dGVyO1xuIFx0fTtcblxuIFx0Ly8gT2JqZWN0LnByb3RvdHlwZS5oYXNPd25Qcm9wZXJ0eS5jYWxsXG4gXHRfX3dlYnBhY2tfcmVxdWlyZV9fLm8gPSBmdW5jdGlvbihvYmplY3QsIHByb3BlcnR5KSB7IHJldHVybiBPYmplY3QucHJvdG90eXBlLmhhc093blByb3BlcnR5LmNhbGwob2JqZWN0LCBwcm9wZXJ0eSk7IH07XG5cbiBcdC8vIF9fd2VicGFja19wdWJsaWNfcGF0aF9fXG4gXHRfX3dlYnBhY2tfcmVxdWlyZV9fLnAgPSBcIlwiO1xuXG5cbiBcdC8vIExvYWQgZW50cnkgbW9kdWxlIGFuZCByZXR1cm4gZXhwb3J0c1xuIFx0cmV0dXJuIF9fd2VicGFja19yZXF1aXJlX18oX193ZWJwYWNrX3JlcXVpcmVfXy5zID0gXCIuL2NvbnRlbnQuanMvaW5kZXguanNcIik7XG4iLCJpbXBvcnQgeyBpbmplY3RKYXZhc2NyaXB0SW5zdHJ1bWVudFBhZ2VTY3JpcHQgfSBmcm9tIFwib3BlbndwbS13ZWJleHQtaW5zdHJ1bWVudGF0aW9uXCI7XG5cbmluamVjdEphdmFzY3JpcHRJbnN0cnVtZW50UGFnZVNjcmlwdCgpO1xuXG4iLCJpbXBvcnQgeyBpbmNyZW1lbnRlZEV2ZW50T3JkaW5hbCB9IGZyb20gXCIuLi9saWIvZXh0ZW5zaW9uLXNlc3Npb24tZXZlbnQtb3JkaW5hbFwiO1xuaW1wb3J0IHsgZXh0ZW5zaW9uU2Vzc2lvblV1aWQgfSBmcm9tIFwiLi4vbGliL2V4dGVuc2lvbi1zZXNzaW9uLXV1aWRcIjtcbmltcG9ydCB7IGJvb2xUb0ludCwgZXNjYXBlU3RyaW5nIH0gZnJvbSBcIi4uL2xpYi9zdHJpbmctdXRpbHNcIjtcbmV4cG9ydCBjb25zdCB0cmFuc2Zvcm1Db29raWVPYmplY3RUb01hdGNoT3BlbldQTVNjaGVtYSA9IChjb29raWUpID0+IHtcbiAgICBjb25zdCBqYXZhc2NyaXB0Q29va2llID0ge307XG4gICAgLy8gRXhwaXJ5IHRpbWUgKGluIHNlY29uZHMpXG4gICAgLy8gTWF5IHJldHVybiB+TWF4KGludDY0KS4gSSBiZWxpZXZlIHRoaXMgaXMgYSBzZXNzaW9uXG4gICAgLy8gY29va2llIHdoaWNoIGRvZXNuJ3QgZXhwaXJlLiBTZXNzaW9ucyBjb29raWVzIHdpdGhcbiAgICAvLyBub24tbWF4IGV4cGlyeSB0aW1lIGV4cGlyZSBhZnRlciBzZXNzaW9uIG9yIGF0IGV4cGlyeS5cbiAgICBjb25zdCBleHBpcnlUaW1lID0gY29va2llLmV4cGlyYXRpb25EYXRlOyAvLyByZXR1cm5zIHNlY29uZHNcbiAgICBsZXQgZXhwaXJ5VGltZVN0cmluZztcbiAgICBjb25zdCBtYXhJbnQ2NCA9IDkyMjMzNzIwMzY4NTQ3NzYwMDA7XG4gICAgaWYgKCFjb29raWUuZXhwaXJhdGlvbkRhdGUgfHwgZXhwaXJ5VGltZSA9PT0gbWF4SW50NjQpIHtcbiAgICAgICAgZXhwaXJ5VGltZVN0cmluZyA9IFwiOTk5OS0xMi0zMVQyMTo1OTo1OS4wMDBaXCI7XG4gICAgfVxuICAgIGVsc2Uge1xuICAgICAgICBjb25zdCBleHBpcnlUaW1lRGF0ZSA9IG5ldyBEYXRlKGV4cGlyeVRpbWUgKiAxMDAwKTsgLy8gcmVxdWlyZXMgbWlsbGlzZWNvbmRzXG4gICAgICAgIGV4cGlyeVRpbWVTdHJpbmcgPSBleHBpcnlUaW1lRGF0ZS50b0lTT1N0cmluZygpO1xuICAgIH1cbiAgICBqYXZhc2NyaXB0Q29va2llLmV4cGlyeSA9IGV4cGlyeVRpbWVTdHJpbmc7XG4gICAgamF2YXNjcmlwdENvb2tpZS5pc19odHRwX29ubHkgPSBib29sVG9JbnQoY29va2llLmh0dHBPbmx5KTtcbiAgICBqYXZhc2NyaXB0Q29va2llLmlzX2hvc3Rfb25seSA9IGJvb2xUb0ludChjb29raWUuaG9zdE9ubHkpO1xuICAgIGphdmFzY3JpcHRDb29raWUuaXNfc2Vzc2lvbiA9IGJvb2xUb0ludChjb29raWUuc2Vzc2lvbik7XG4gICAgamF2YXNjcmlwdENvb2tpZS5ob3N0ID0gZXNjYXBlU3RyaW5nKGNvb2tpZS5kb21haW4pO1xuICAgIGphdmFzY3JpcHRDb29raWUuaXNfc2VjdXJlID0gYm9vbFRvSW50KGNvb2tpZS5zZWN1cmUpO1xuICAgIGphdmFzY3JpcHRDb29raWUubmFtZSA9IGVzY2FwZVN0cmluZyhjb29raWUubmFtZSk7XG4gICAgamF2YXNjcmlwdENvb2tpZS5wYXRoID0gZXNjYXBlU3RyaW5nKGNvb2tpZS5wYXRoKTtcbiAgICBqYXZhc2NyaXB0Q29va2llLnZhbHVlID0gZXNjYXBlU3RyaW5nKGNvb2tpZS52YWx1ZSk7XG4gICAgamF2YXNjcmlwdENvb2tpZS5zYW1lX3NpdGUgPSBlc2NhcGVTdHJpbmcoY29va2llLnNhbWVTaXRlKTtcbiAgICBqYXZhc2NyaXB0Q29va2llLmZpcnN0X3BhcnR5X2RvbWFpbiA9IGVzY2FwZVN0cmluZyhjb29raWUuZmlyc3RQYXJ0eURvbWFpbik7XG4gICAgamF2YXNjcmlwdENvb2tpZS5zdG9yZV9pZCA9IGVzY2FwZVN0cmluZyhjb29raWUuc3RvcmVJZCk7XG4gICAgamF2YXNjcmlwdENvb2tpZS50aW1lX3N0YW1wID0gbmV3IERhdGUoKS50b0lTT1N0cmluZygpO1xuICAgIHJldHVybiBqYXZhc2NyaXB0Q29va2llO1xufTtcbmV4cG9ydCBjbGFzcyBDb29raWVJbnN0cnVtZW50IHtcbiAgICBjb25zdHJ1Y3RvcihkYXRhUmVjZWl2ZXIpIHtcbiAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIgPSBkYXRhUmVjZWl2ZXI7XG4gICAgfVxuICAgIHJ1bihjcmF3bElEKSB7XG4gICAgICAgIC8vIEluc3RydW1lbnQgY29va2llIGNoYW5nZXNcbiAgICAgICAgdGhpcy5vbkNoYW5nZWRMaXN0ZW5lciA9IGFzeW5jIChjaGFuZ2VJbmZvKSA9PiB7XG4gICAgICAgICAgICBjb25zdCBldmVudFR5cGUgPSBjaGFuZ2VJbmZvLnJlbW92ZWQgPyBcImRlbGV0ZWRcIiA6IFwiYWRkZWQtb3ItY2hhbmdlZFwiO1xuICAgICAgICAgICAgY29uc3QgdXBkYXRlID0ge1xuICAgICAgICAgICAgICAgIHJlY29yZF90eXBlOiBldmVudFR5cGUsXG4gICAgICAgICAgICAgICAgY2hhbmdlX2NhdXNlOiBjaGFuZ2VJbmZvLmNhdXNlLFxuICAgICAgICAgICAgICAgIGNyYXdsX2lkOiBjcmF3bElELFxuICAgICAgICAgICAgICAgIGV4dGVuc2lvbl9zZXNzaW9uX3V1aWQ6IGV4dGVuc2lvblNlc3Npb25VdWlkLFxuICAgICAgICAgICAgICAgIGV2ZW50X29yZGluYWw6IGluY3JlbWVudGVkRXZlbnRPcmRpbmFsKCksXG4gICAgICAgICAgICAgICAgLi4udHJhbnNmb3JtQ29va2llT2JqZWN0VG9NYXRjaE9wZW5XUE1TY2hlbWEoY2hhbmdlSW5mby5jb29raWUpLFxuICAgICAgICAgICAgfTtcbiAgICAgICAgICAgIHRoaXMuZGF0YVJlY2VpdmVyLnNhdmVSZWNvcmQoXCJqYXZhc2NyaXB0X2Nvb2tpZXNcIiwgdXBkYXRlKTtcbiAgICAgICAgfTtcbiAgICAgICAgYnJvd3Nlci5jb29raWVzLm9uQ2hhbmdlZC5hZGRMaXN0ZW5lcih0aGlzLm9uQ2hhbmdlZExpc3RlbmVyKTtcbiAgICB9XG4gICAgYXN5bmMgc2F2ZUFsbENvb2tpZXMoY3Jhd2xJRCkge1xuICAgICAgICBjb25zdCBhbGxDb29raWVzID0gYXdhaXQgYnJvd3Nlci5jb29raWVzLmdldEFsbCh7fSk7XG4gICAgICAgIGF3YWl0IFByb21pc2UuYWxsKGFsbENvb2tpZXMubWFwKChjb29raWUpID0+IHtcbiAgICAgICAgICAgIGNvbnN0IHVwZGF0ZSA9IHtcbiAgICAgICAgICAgICAgICByZWNvcmRfdHlwZTogXCJtYW51YWwtZXhwb3J0XCIsXG4gICAgICAgICAgICAgICAgY3Jhd2xfaWQ6IGNyYXdsSUQsXG4gICAgICAgICAgICAgICAgZXh0ZW5zaW9uX3Nlc3Npb25fdXVpZDogZXh0ZW5zaW9uU2Vzc2lvblV1aWQsXG4gICAgICAgICAgICAgICAgLi4udHJhbnNmb3JtQ29va2llT2JqZWN0VG9NYXRjaE9wZW5XUE1TY2hlbWEoY29va2llKSxcbiAgICAgICAgICAgIH07XG4gICAgICAgICAgICByZXR1cm4gdGhpcy5kYXRhUmVjZWl2ZXIuc2F2ZVJlY29yZChcImphdmFzY3JpcHRfY29va2llc1wiLCB1cGRhdGUpO1xuICAgICAgICB9KSk7XG4gICAgfVxuICAgIGNsZWFudXAoKSB7XG4gICAgICAgIGlmICh0aGlzLm9uQ2hhbmdlZExpc3RlbmVyKSB7XG4gICAgICAgICAgICBicm93c2VyLmNvb2tpZXMub25DaGFuZ2VkLnJlbW92ZUxpc3RlbmVyKHRoaXMub25DaGFuZ2VkTGlzdGVuZXIpO1xuICAgICAgICB9XG4gICAgfVxufVxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pWTI5dmEybGxMV2x1YzNSeWRXMWxiblF1YW5NaUxDSnpiM1Z5WTJWU2IyOTBJam9pSWl3aWMyOTFjbU5sY3lJNld5SXVMaTh1TGk4dUxpOXpjbU12WW1GamEyZHliM1Z1WkM5amIyOXJhV1V0YVc1emRISjFiV1Z1ZEM1MGN5SmRMQ0p1WVcxbGN5STZXMTBzSW0xaGNIQnBibWR6SWpvaVFVRkJRU3hQUVVGUExFVkJRVVVzZFVKQlFYVkNMRVZCUVVVc1RVRkJUU3gzUTBGQmQwTXNRMEZCUXp0QlFVTnFSaXhQUVVGUExFVkJRVVVzYjBKQlFXOUNMRVZCUVVVc1RVRkJUU3dyUWtGQkswSXNRMEZCUXp0QlFVTnlSU3hQUVVGUExFVkJRVVVzVTBGQlV5eEZRVUZGTEZsQlFWa3NSVUZCUlN4TlFVRk5MSEZDUVVGeFFpeERRVUZETzBGQlN6bEVMRTFCUVUwc1EwRkJReXhOUVVGTkxIbERRVUY1UXl4SFFVRkhMRU5CUVVNc1RVRkJZeXhGUVVGRkxFVkJRVVU3U1VGRE1VVXNUVUZCVFN4blFrRkJaMElzUjBGQlJ5eEZRVUZ6UWl4RFFVRkRPMGxCUldoRUxESkNRVUV5UWp0SlFVTXpRaXh6UkVGQmMwUTdTVUZEZEVRc2NVUkJRWEZFTzBsQlEzSkVMSGxFUVVGNVJEdEpRVU42UkN4TlFVRk5MRlZCUVZVc1IwRkJSeXhOUVVGTkxFTkJRVU1zWTBGQll5eERRVUZETEVOQlFVTXNhMEpCUVd0Q08wbEJRelZFTEVsQlFVa3NaMEpCUVdkQ0xFTkJRVU03U1VGRGNrSXNUVUZCVFN4UlFVRlJMRWRCUVVjc2JVSkJRVzFDTEVOQlFVTTdTVUZEY2tNc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eGpRVUZqTEVsQlFVa3NWVUZCVlN4TFFVRkxMRkZCUVZFc1JVRkJSVHRSUVVOeVJDeG5Ra0ZCWjBJc1IwRkJSeXd3UWtGQk1FSXNRMEZCUXp0TFFVTXZRenRUUVVGTk8xRkJRMHdzVFVGQlRTeGpRVUZqTEVkQlFVY3NTVUZCU1N4SlFVRkpMRU5CUVVNc1ZVRkJWU3hIUVVGSExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTXNkMEpCUVhkQ08xRkJRelZGTEdkQ1FVRm5RaXhIUVVGSExHTkJRV01zUTBGQlF5eFhRVUZYTEVWQlFVVXNRMEZCUXp0TFFVTnFSRHRKUVVORUxHZENRVUZuUWl4RFFVRkRMRTFCUVUwc1IwRkJSeXhuUWtGQlowSXNRMEZCUXp0SlFVTXpReXhuUWtGQlowSXNRMEZCUXl4WlFVRlpMRWRCUVVjc1UwRkJVeXhEUVVGRExFMUJRVTBzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXp0SlFVTXpSQ3huUWtGQlowSXNRMEZCUXl4WlFVRlpMRWRCUVVjc1UwRkJVeXhEUVVGRExFMUJRVTBzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXp0SlFVTXpSQ3huUWtGQlowSXNRMEZCUXl4VlFVRlZMRWRCUVVjc1UwRkJVeXhEUVVGRExFMUJRVTBzUTBGQlF5eFBRVUZQTEVOQlFVTXNRMEZCUXp0SlFVVjRSQ3huUWtGQlowSXNRMEZCUXl4SlFVRkpMRWRCUVVjc1dVRkJXU3hEUVVGRExFMUJRVTBzUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXp0SlFVTndSQ3huUWtGQlowSXNRMEZCUXl4VFFVRlRMRWRCUVVjc1UwRkJVeXhEUVVGRExFMUJRVTBzUTBGQlF5eE5RVUZOTEVOQlFVTXNRMEZCUXp0SlFVTjBSQ3huUWtGQlowSXNRMEZCUXl4SlFVRkpMRWRCUVVjc1dVRkJXU3hEUVVGRExFMUJRVTBzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXp0SlFVTnNSQ3huUWtGQlowSXNRMEZCUXl4SlFVRkpMRWRCUVVjc1dVRkJXU3hEUVVGRExFMUJRVTBzUTBGQlF5eEpRVUZKTEVOQlFVTXNRMEZCUXp0SlFVTnNSQ3huUWtGQlowSXNRMEZCUXl4TFFVRkxMRWRCUVVjc1dVRkJXU3hEUVVGRExFMUJRVTBzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXp0SlFVTndSQ3huUWtGQlowSXNRMEZCUXl4VFFVRlRMRWRCUVVjc1dVRkJXU3hEUVVGRExFMUJRVTBzUTBGQlF5eFJRVUZSTEVOQlFVTXNRMEZCUXp0SlFVTXpSQ3huUWtGQlowSXNRMEZCUXl4clFrRkJhMElzUjBGQlJ5eFpRVUZaTEVOQlFVTXNUVUZCVFN4RFFVRkRMR2RDUVVGblFpeERRVUZETEVOQlFVTTdTVUZETlVVc1owSkJRV2RDTEVOQlFVTXNVVUZCVVN4SFFVRkhMRmxCUVZrc1EwRkJReXhOUVVGTkxFTkJRVU1zVDBGQlR5eERRVUZETEVOQlFVTTdTVUZGZWtRc1owSkJRV2RDTEVOQlFVTXNWVUZCVlN4SFFVRkhMRWxCUVVrc1NVRkJTU3hGUVVGRkxFTkJRVU1zVjBGQlZ5eEZRVUZGTEVOQlFVTTdTVUZGZGtRc1QwRkJUeXhuUWtGQlowSXNRMEZCUXp0QlFVTXhRaXhEUVVGRExFTkJRVU03UVVGRlJpeE5RVUZOTEU5QlFVOHNaMEpCUVdkQ08wbEJTVE5DTEZsQlFWa3NXVUZCV1R0UlFVTjBRaXhKUVVGSkxFTkJRVU1zV1VGQldTeEhRVUZITEZsQlFWa3NRMEZCUXp0SlFVTnVReXhEUVVGRE8wbEJSVTBzUjBGQlJ5eERRVUZETEU5QlFVODdVVUZEYUVJc05FSkJRVFJDTzFGQlF6VkNMRWxCUVVrc1EwRkJReXhwUWtGQmFVSXNSMEZCUnl4TFFVRkxMRVZCUVVVc1ZVRlBMMElzUlVGQlJTeEZRVUZGTzFsQlEwZ3NUVUZCVFN4VFFVRlRMRWRCUVVjc1ZVRkJWU3hEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETEVOQlFVTXNVMEZCVXl4RFFVRkRMRU5CUVVNc1EwRkJReXhyUWtGQmEwSXNRMEZCUXp0WlFVTjBSU3hOUVVGTkxFMUJRVTBzUjBGQk1rSTdaMEpCUTNKRExGZEJRVmNzUlVGQlJTeFRRVUZUTzJkQ1FVTjBRaXhaUVVGWkxFVkJRVVVzVlVGQlZTeERRVUZETEV0QlFVczdaMEpCUXpsQ0xGRkJRVkVzUlVGQlJTeFBRVUZQTzJkQ1FVTnFRaXh6UWtGQmMwSXNSVUZCUlN4dlFrRkJiMEk3WjBKQlF6VkRMR0ZCUVdFc1JVRkJSU3gxUWtGQmRVSXNSVUZCUlR0blFrRkRlRU1zUjBGQlJ5eDVRMEZCZVVNc1EwRkJReXhWUVVGVkxFTkJRVU1zVFVGQlRTeERRVUZETzJGQlEyaEZMRU5CUVVNN1dVRkRSaXhKUVVGSkxFTkJRVU1zV1VGQldTeERRVUZETEZWQlFWVXNRMEZCUXl4dlFrRkJiMElzUlVGQlJTeE5RVUZOTEVOQlFVTXNRMEZCUXp0UlFVTTNSQ3hEUVVGRExFTkJRVU03VVVGRFJpeFBRVUZQTEVOQlFVTXNUMEZCVHl4RFFVRkRMRk5CUVZNc1EwRkJReXhYUVVGWExFTkJRVU1zU1VGQlNTeERRVUZETEdsQ1FVRnBRaXhEUVVGRExFTkJRVU03U1VGRGFFVXNRMEZCUXp0SlFVVk5MRXRCUVVzc1EwRkJReXhqUVVGakxFTkJRVU1zVDBGQlR6dFJRVU5xUXl4TlFVRk5MRlZCUVZVc1IwRkJSeXhOUVVGTkxFOUJRVThzUTBGQlF5eFBRVUZQTEVOQlFVTXNUVUZCVFN4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRE8xRkJRM0JFTEUxQlFVMHNUMEZCVHl4RFFVRkRMRWRCUVVjc1EwRkRaaXhWUVVGVkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNUVUZCWXl4RlFVRkZMRVZCUVVVN1dVRkRhRU1zVFVGQlRTeE5RVUZOTEVkQlFUSkNPMmRDUVVOeVF5eFhRVUZYTEVWQlFVVXNaVUZCWlR0blFrRkROVUlzVVVGQlVTeEZRVUZGTEU5QlFVODdaMEpCUTJwQ0xITkNRVUZ6UWl4RlFVRkZMRzlDUVVGdlFqdG5Ra0ZETlVNc1IwRkJSeXg1UTBGQmVVTXNRMEZCUXl4TlFVRk5MRU5CUVVNN1lVRkRja1FzUTBGQlF6dFpRVU5HTEU5QlFVOHNTVUZCU1N4RFFVRkRMRmxCUVZrc1EwRkJReXhWUVVGVkxFTkJRVU1zYjBKQlFXOUNMRVZCUVVVc1RVRkJUU3hEUVVGRExFTkJRVU03VVVGRGNFVXNRMEZCUXl4RFFVRkRMRU5CUTBnc1EwRkJRenRKUVVOS0xFTkJRVU03U1VGRlRTeFBRVUZQTzFGQlExb3NTVUZCU1N4SlFVRkpMRU5CUVVNc2FVSkJRV2xDTEVWQlFVVTdXVUZETVVJc1QwRkJUeXhEUVVGRExFOUJRVThzUTBGQlF5eFRRVUZUTEVOQlFVTXNZMEZCWXl4RFFVRkRMRWxCUVVrc1EwRkJReXhwUWtGQmFVSXNRMEZCUXl4RFFVRkRPMU5CUTJ4Rk8wbEJRMGdzUTBGQlF6dERRVU5HSW4wPSIsImltcG9ydCB7IGluY3JlbWVudGVkRXZlbnRPcmRpbmFsIH0gZnJvbSBcIi4uL2xpYi9leHRlbnNpb24tc2Vzc2lvbi1ldmVudC1vcmRpbmFsXCI7XG5pbXBvcnQgeyBleHRlbnNpb25TZXNzaW9uVXVpZCB9IGZyb20gXCIuLi9saWIvZXh0ZW5zaW9uLXNlc3Npb24tdXVpZFwiO1xuaW1wb3J0IHsgSHR0cFBvc3RQYXJzZXIgfSBmcm9tIFwiLi4vbGliL2h0dHAtcG9zdC1wYXJzZXJcIjtcbmltcG9ydCB7IFBlbmRpbmdSZXF1ZXN0IH0gZnJvbSBcIi4uL2xpYi9wZW5kaW5nLXJlcXVlc3RcIjtcbmltcG9ydCB7IFBlbmRpbmdSZXNwb25zZSB9IGZyb20gXCIuLi9saWIvcGVuZGluZy1yZXNwb25zZVwiO1xuaW1wb3J0IHsgYm9vbFRvSW50LCBlc2NhcGVTdHJpbmcsIGVzY2FwZVVybCB9IGZyb20gXCIuLi9saWIvc3RyaW5nLXV0aWxzXCI7XG4vKipcbiAqIE5vdGU6IERpZmZlcmVudCBwYXJ0cyBvZiB0aGUgZGVzaXJlZCBpbmZvcm1hdGlvbiBhcnJpdmVzIGluIGRpZmZlcmVudCBldmVudHMgYXMgcGVyIGJlbG93OlxuICogcmVxdWVzdCA9IGhlYWRlcnMgaW4gb25CZWZvcmVTZW5kSGVhZGVycyArIGJvZHkgaW4gb25CZWZvcmVSZXF1ZXN0XG4gKiByZXNwb25zZSA9IGhlYWRlcnMgaW4gb25Db21wbGV0ZWQgKyBib2R5IHZpYSBhIG9uQmVmb3JlUmVxdWVzdCBmaWx0ZXJcbiAqIHJlZGlyZWN0ID0gb3JpZ2luYWwgcmVxdWVzdCBoZWFkZXJzK2JvZHksIGZvbGxvd2VkIGJ5IGEgb25CZWZvcmVSZWRpcmVjdCBhbmQgdGhlbiBhIG5ldyBzZXQgb2YgcmVxdWVzdCBoZWFkZXJzK2JvZHkgYW5kIHJlc3BvbnNlIGhlYWRlcnMrYm9keVxuICogRG9jczogaHR0cHM6Ly9kZXZlbG9wZXIubW96aWxsYS5vcmcvZW4tVVMvZG9jcy9Vc2VyOndiYW1iZXJnL3dlYlJlcXVlc3QuUmVxdWVzdERldGFpbHNcbiAqL1xuZXhwb3J0IGNsYXNzIEh0dHBJbnN0cnVtZW50IHtcbiAgICBjb25zdHJ1Y3RvcihkYXRhUmVjZWl2ZXIpIHtcbiAgICAgICAgdGhpcy5wZW5kaW5nUmVxdWVzdHMgPSB7fTtcbiAgICAgICAgdGhpcy5wZW5kaW5nUmVzcG9uc2VzID0ge307XG4gICAgICAgIHRoaXMuZGF0YVJlY2VpdmVyID0gZGF0YVJlY2VpdmVyO1xuICAgIH1cbiAgICBydW4oY3Jhd2xJRCwgc2F2ZUphdmFzY3JpcHQsIHNhdmVBbGxDb250ZW50KSB7XG4gICAgICAgIGNvbnN0IGFsbFR5cGVzID0gW1xuICAgICAgICAgICAgXCJiZWFjb25cIixcbiAgICAgICAgICAgIFwiY3NwX3JlcG9ydFwiLFxuICAgICAgICAgICAgXCJmb250XCIsXG4gICAgICAgICAgICBcImltYWdlXCIsXG4gICAgICAgICAgICBcImltYWdlc2V0XCIsXG4gICAgICAgICAgICBcIm1haW5fZnJhbWVcIixcbiAgICAgICAgICAgIFwibWVkaWFcIixcbiAgICAgICAgICAgIFwib2JqZWN0XCIsXG4gICAgICAgICAgICBcIm9iamVjdF9zdWJyZXF1ZXN0XCIsXG4gICAgICAgICAgICBcInBpbmdcIixcbiAgICAgICAgICAgIFwic2NyaXB0XCIsXG4gICAgICAgICAgICAvLyBcInNwZWN1bGF0aXZlXCIsXG4gICAgICAgICAgICBcInN0eWxlc2hlZXRcIixcbiAgICAgICAgICAgIFwic3ViX2ZyYW1lXCIsXG4gICAgICAgICAgICBcIndlYl9tYW5pZmVzdFwiLFxuICAgICAgICAgICAgXCJ3ZWJzb2NrZXRcIixcbiAgICAgICAgICAgIFwieGJsXCIsXG4gICAgICAgICAgICBcInhtbF9kdGRcIixcbiAgICAgICAgICAgIFwieG1saHR0cHJlcXVlc3RcIixcbiAgICAgICAgICAgIFwieHNsdFwiLFxuICAgICAgICAgICAgXCJvdGhlclwiLFxuICAgICAgICBdO1xuICAgICAgICBjb25zdCBmaWx0ZXIgPSB7IHVybHM6IFtcIjxhbGxfdXJscz5cIl0sIHR5cGVzOiBhbGxUeXBlcyB9O1xuICAgICAgICBjb25zdCByZXF1ZXN0U3RlbXNGcm9tRXh0ZW5zaW9uID0gZGV0YWlscyA9PiB7XG4gICAgICAgICAgICByZXR1cm4gKGRldGFpbHMub3JpZ2luVXJsICYmIGRldGFpbHMub3JpZ2luVXJsLmluZGV4T2YoXCJtb3otZXh0ZW5zaW9uOi8vXCIpID4gLTEpO1xuICAgICAgICB9O1xuICAgICAgICAvKlxuICAgICAgICAgKiBBdHRhY2ggaGFuZGxlcnMgdG8gZXZlbnQgbGlzdGVuZXJzXG4gICAgICAgICAqL1xuICAgICAgICB0aGlzLm9uQmVmb3JlUmVxdWVzdExpc3RlbmVyID0gZGV0YWlscyA9PiB7XG4gICAgICAgICAgICBjb25zdCBibG9ja2luZ1Jlc3BvbnNlVGhhdERvZXNOb3RoaW5nID0ge307XG4gICAgICAgICAgICAvLyBJZ25vcmUgcmVxdWVzdHMgbWFkZSBieSBleHRlbnNpb25zXG4gICAgICAgICAgICBpZiAocmVxdWVzdFN0ZW1zRnJvbUV4dGVuc2lvbihkZXRhaWxzKSkge1xuICAgICAgICAgICAgICAgIHJldHVybiBibG9ja2luZ1Jlc3BvbnNlVGhhdERvZXNOb3RoaW5nO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgY29uc3QgcGVuZGluZ1JlcXVlc3QgPSB0aGlzLmdldFBlbmRpbmdSZXF1ZXN0KGRldGFpbHMucmVxdWVzdElkKTtcbiAgICAgICAgICAgIHBlbmRpbmdSZXF1ZXN0LnJlc29sdmVPbkJlZm9yZVJlcXVlc3RFdmVudERldGFpbHMoZGV0YWlscyk7XG4gICAgICAgICAgICBjb25zdCBwZW5kaW5nUmVzcG9uc2UgPSB0aGlzLmdldFBlbmRpbmdSZXNwb25zZShkZXRhaWxzLnJlcXVlc3RJZCk7XG4gICAgICAgICAgICBwZW5kaW5nUmVzcG9uc2UucmVzb2x2ZU9uQmVmb3JlUmVxdWVzdEV2ZW50RGV0YWlscyhkZXRhaWxzKTtcbiAgICAgICAgICAgIGlmIChzYXZlQWxsQ29udGVudCkge1xuICAgICAgICAgICAgICAgIHBlbmRpbmdSZXNwb25zZS5hZGRSZXNwb25zZVJlc3BvbnNlQm9keUxpc3RlbmVyKGRldGFpbHMpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgZWxzZSBpZiAoc2F2ZUphdmFzY3JpcHQgJiYgdGhpcy5pc0pTKGRldGFpbHMudHlwZSkpIHtcbiAgICAgICAgICAgICAgICBwZW5kaW5nUmVzcG9uc2UuYWRkUmVzcG9uc2VSZXNwb25zZUJvZHlMaXN0ZW5lcihkZXRhaWxzKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIHJldHVybiBibG9ja2luZ1Jlc3BvbnNlVGhhdERvZXNOb3RoaW5nO1xuICAgICAgICB9O1xuICAgICAgICBicm93c2VyLndlYlJlcXVlc3Qub25CZWZvcmVSZXF1ZXN0LmFkZExpc3RlbmVyKHRoaXMub25CZWZvcmVSZXF1ZXN0TGlzdGVuZXIsIGZpbHRlciwgc2F2ZUphdmFzY3JpcHQgfHwgc2F2ZUFsbENvbnRlbnRcbiAgICAgICAgICAgID8gW1wicmVxdWVzdEJvZHlcIiwgXCJibG9ja2luZ1wiXVxuICAgICAgICAgICAgOiBbXCJyZXF1ZXN0Qm9keVwiXSk7XG4gICAgICAgIHRoaXMub25CZWZvcmVTZW5kSGVhZGVyc0xpc3RlbmVyID0gZGV0YWlscyA9PiB7XG4gICAgICAgICAgICAvLyBJZ25vcmUgcmVxdWVzdHMgbWFkZSBieSBleHRlbnNpb25zXG4gICAgICAgICAgICBpZiAocmVxdWVzdFN0ZW1zRnJvbUV4dGVuc2lvbihkZXRhaWxzKSkge1xuICAgICAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGNvbnN0IHBlbmRpbmdSZXF1ZXN0ID0gdGhpcy5nZXRQZW5kaW5nUmVxdWVzdChkZXRhaWxzLnJlcXVlc3RJZCk7XG4gICAgICAgICAgICBwZW5kaW5nUmVxdWVzdC5yZXNvbHZlT25CZWZvcmVTZW5kSGVhZGVyc0V2ZW50RGV0YWlscyhkZXRhaWxzKTtcbiAgICAgICAgICAgIHRoaXMub25CZWZvcmVTZW5kSGVhZGVyc0hhbmRsZXIoZGV0YWlscywgY3Jhd2xJRCwgaW5jcmVtZW50ZWRFdmVudE9yZGluYWwoKSk7XG4gICAgICAgIH07XG4gICAgICAgIGJyb3dzZXIud2ViUmVxdWVzdC5vbkJlZm9yZVNlbmRIZWFkZXJzLmFkZExpc3RlbmVyKHRoaXMub25CZWZvcmVTZW5kSGVhZGVyc0xpc3RlbmVyLCBmaWx0ZXIsIFtcInJlcXVlc3RIZWFkZXJzXCJdKTtcbiAgICAgICAgdGhpcy5vbkJlZm9yZVJlZGlyZWN0TGlzdGVuZXIgPSBkZXRhaWxzID0+IHtcbiAgICAgICAgICAgIC8vIElnbm9yZSByZXF1ZXN0cyBtYWRlIGJ5IGV4dGVuc2lvbnNcbiAgICAgICAgICAgIGlmIChyZXF1ZXN0U3RlbXNGcm9tRXh0ZW5zaW9uKGRldGFpbHMpKSB7XG4gICAgICAgICAgICAgICAgcmV0dXJuO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgdGhpcy5vbkJlZm9yZVJlZGlyZWN0SGFuZGxlcihkZXRhaWxzLCBjcmF3bElELCBpbmNyZW1lbnRlZEV2ZW50T3JkaW5hbCgpKTtcbiAgICAgICAgfTtcbiAgICAgICAgYnJvd3Nlci53ZWJSZXF1ZXN0Lm9uQmVmb3JlUmVkaXJlY3QuYWRkTGlzdGVuZXIodGhpcy5vbkJlZm9yZVJlZGlyZWN0TGlzdGVuZXIsIGZpbHRlciwgW1wicmVzcG9uc2VIZWFkZXJzXCJdKTtcbiAgICAgICAgdGhpcy5vbkNvbXBsZXRlZExpc3RlbmVyID0gZGV0YWlscyA9PiB7XG4gICAgICAgICAgICAvLyBJZ25vcmUgcmVxdWVzdHMgbWFkZSBieSBleHRlbnNpb25zXG4gICAgICAgICAgICBpZiAocmVxdWVzdFN0ZW1zRnJvbUV4dGVuc2lvbihkZXRhaWxzKSkge1xuICAgICAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGNvbnN0IHBlbmRpbmdSZXNwb25zZSA9IHRoaXMuZ2V0UGVuZGluZ1Jlc3BvbnNlKGRldGFpbHMucmVxdWVzdElkKTtcbiAgICAgICAgICAgIHBlbmRpbmdSZXNwb25zZS5yZXNvbHZlT25Db21wbGV0ZWRFdmVudERldGFpbHMoZGV0YWlscyk7XG4gICAgICAgICAgICB0aGlzLm9uQ29tcGxldGVkSGFuZGxlcihkZXRhaWxzLCBjcmF3bElELCBpbmNyZW1lbnRlZEV2ZW50T3JkaW5hbCgpLCBzYXZlSmF2YXNjcmlwdCwgc2F2ZUFsbENvbnRlbnQpO1xuICAgICAgICB9O1xuICAgICAgICBicm93c2VyLndlYlJlcXVlc3Qub25Db21wbGV0ZWQuYWRkTGlzdGVuZXIodGhpcy5vbkNvbXBsZXRlZExpc3RlbmVyLCBmaWx0ZXIsIFtcInJlc3BvbnNlSGVhZGVyc1wiXSk7XG4gICAgfVxuICAgIGNsZWFudXAoKSB7XG4gICAgICAgIGlmICh0aGlzLm9uQmVmb3JlUmVxdWVzdExpc3RlbmVyKSB7XG4gICAgICAgICAgICBicm93c2VyLndlYlJlcXVlc3Qub25CZWZvcmVSZXF1ZXN0LnJlbW92ZUxpc3RlbmVyKHRoaXMub25CZWZvcmVSZXF1ZXN0TGlzdGVuZXIpO1xuICAgICAgICB9XG4gICAgICAgIGlmICh0aGlzLm9uQmVmb3JlU2VuZEhlYWRlcnNMaXN0ZW5lcikge1xuICAgICAgICAgICAgYnJvd3Nlci53ZWJSZXF1ZXN0Lm9uQmVmb3JlU2VuZEhlYWRlcnMucmVtb3ZlTGlzdGVuZXIodGhpcy5vbkJlZm9yZVNlbmRIZWFkZXJzTGlzdGVuZXIpO1xuICAgICAgICB9XG4gICAgICAgIGlmICh0aGlzLm9uQmVmb3JlUmVkaXJlY3RMaXN0ZW5lcikge1xuICAgICAgICAgICAgYnJvd3Nlci53ZWJSZXF1ZXN0Lm9uQmVmb3JlUmVkaXJlY3QucmVtb3ZlTGlzdGVuZXIodGhpcy5vbkJlZm9yZVJlZGlyZWN0TGlzdGVuZXIpO1xuICAgICAgICB9XG4gICAgICAgIGlmICh0aGlzLm9uQ29tcGxldGVkTGlzdGVuZXIpIHtcbiAgICAgICAgICAgIGJyb3dzZXIud2ViUmVxdWVzdC5vbkNvbXBsZXRlZC5yZW1vdmVMaXN0ZW5lcih0aGlzLm9uQ29tcGxldGVkTGlzdGVuZXIpO1xuICAgICAgICB9XG4gICAgfVxuICAgIGdldFBlbmRpbmdSZXF1ZXN0KHJlcXVlc3RJZCkge1xuICAgICAgICBpZiAoIXRoaXMucGVuZGluZ1JlcXVlc3RzW3JlcXVlc3RJZF0pIHtcbiAgICAgICAgICAgIHRoaXMucGVuZGluZ1JlcXVlc3RzW3JlcXVlc3RJZF0gPSBuZXcgUGVuZGluZ1JlcXVlc3QoKTtcbiAgICAgICAgfVxuICAgICAgICByZXR1cm4gdGhpcy5wZW5kaW5nUmVxdWVzdHNbcmVxdWVzdElkXTtcbiAgICB9XG4gICAgZ2V0UGVuZGluZ1Jlc3BvbnNlKHJlcXVlc3RJZCkge1xuICAgICAgICBpZiAoIXRoaXMucGVuZGluZ1Jlc3BvbnNlc1tyZXF1ZXN0SWRdKSB7XG4gICAgICAgICAgICB0aGlzLnBlbmRpbmdSZXNwb25zZXNbcmVxdWVzdElkXSA9IG5ldyBQZW5kaW5nUmVzcG9uc2UoKTtcbiAgICAgICAgfVxuICAgICAgICByZXR1cm4gdGhpcy5wZW5kaW5nUmVzcG9uc2VzW3JlcXVlc3RJZF07XG4gICAgfVxuICAgIC8qXG4gICAgICogSFRUUCBSZXF1ZXN0IEhhbmRsZXIgYW5kIEhlbHBlciBGdW5jdGlvbnNcbiAgICAgKi9cbiAgICAvKlxuICAgIC8vIFRPRE86IFJlZmFjdG9yIHRvIGNvcnJlc3BvbmRpbmcgd2ViZXh0IGxvZ2ljIG9yIGRpc2NhcmRcbiAgICBwcml2YXRlIGdldF9zdGFja190cmFjZV9zdHIoKSB7XG4gICAgICAvLyByZXR1cm4gdGhlIHN0YWNrIHRyYWNlIGFzIGEgc3RyaW5nXG4gICAgICAvLyBUT0RPOiBjaGVjayBpZiBodHRwLW9uLW1vZGlmeS1yZXF1ZXN0IGlzIGEgZ29vZCBwbGFjZSB0byBjYXB0dXJlIHRoZSBzdGFja1xuICAgICAgLy8gSW4gdGhlIG1hbnVhbCB0ZXN0cyB3ZSBjb3VsZCBjYXB0dXJlIGV4YWN0bHkgdGhlIHNhbWUgdHJhY2UgYXMgdGhlXG4gICAgICAvLyBcIkNhdXNlXCIgY29sdW1uIG9mIHRoZSBkZXZ0b29scyBuZXR3b3JrIHBhbmVsLlxuICAgICAgY29uc3Qgc3RhY2t0cmFjZSA9IFtdO1xuICAgICAgbGV0IGZyYW1lID0gY29tcG9uZW50cy5zdGFjaztcbiAgICAgIGlmIChmcmFtZSAmJiBmcmFtZS5jYWxsZXIpIHtcbiAgICAgICAgLy8gaW50ZXJuYWwvY2hyb21lIGNhbGxlcnMgb2NjdXB5IHRoZSBmaXJzdCB0aHJlZSBmcmFtZXMsIHBvcCB0aGVtIVxuICAgICAgICBmcmFtZSA9IGZyYW1lLmNhbGxlci5jYWxsZXIuY2FsbGVyO1xuICAgICAgICB3aGlsZSAoZnJhbWUpIHtcbiAgICAgICAgICAvLyBjaHJvbWUgc2NyaXB0cyBhcHBlYXIgYXMgY2FsbGVycyBpbiBzb21lIGNhc2VzLCBmaWx0ZXIgdGhlbSBvdXRcbiAgICAgICAgICBjb25zdCBzY2hlbWUgPSBmcmFtZS5maWxlbmFtZS5zcGxpdChcIjovL1wiKVswXTtcbiAgICAgICAgICBpZiAoW1wicmVzb3VyY2VcIiwgXCJjaHJvbWVcIiwgXCJmaWxlXCJdLmluZGV4T2Yoc2NoZW1lKSA9PT0gLTEpIHtcbiAgICAgICAgICAgIC8vIGlnbm9yZSBjaHJvbWUgc2NyaXB0c1xuICAgICAgICAgICAgc3RhY2t0cmFjZS5wdXNoKFxuICAgICAgICAgICAgICBmcmFtZS5uYW1lICtcbiAgICAgICAgICAgICAgICBcIkBcIiArXG4gICAgICAgICAgICAgICAgZnJhbWUuZmlsZW5hbWUgK1xuICAgICAgICAgICAgICAgIFwiOlwiICtcbiAgICAgICAgICAgICAgICBmcmFtZS5saW5lTnVtYmVyICtcbiAgICAgICAgICAgICAgICBcIjpcIiArXG4gICAgICAgICAgICAgICAgZnJhbWUuY29sdW1uTnVtYmVyICtcbiAgICAgICAgICAgICAgICBcIjtcIiArXG4gICAgICAgICAgICAgICAgZnJhbWUuYXN5bmNDYXVzZSxcbiAgICAgICAgICAgICk7XG4gICAgICAgICAgfVxuICAgICAgICAgIGZyYW1lID0gZnJhbWUuY2FsbGVyIHx8IGZyYW1lLmFzeW5jQ2FsbGVyO1xuICAgICAgICB9XG4gICAgICB9XG4gICAgICByZXR1cm4gc3RhY2t0cmFjZS5qb2luKFwiXFxuXCIpO1xuICAgIH1cbiAgICAqL1xuICAgIGFzeW5jIG9uQmVmb3JlU2VuZEhlYWRlcnNIYW5kbGVyKGRldGFpbHMsIGNyYXdsSUQsIGV2ZW50T3JkaW5hbCkge1xuICAgICAgICAvKlxuICAgICAgICBjb25zb2xlLmxvZyhcbiAgICAgICAgICBcIm9uQmVmb3JlU2VuZEhlYWRlcnNIYW5kbGVyIChwcmV2aW91c2x5IGh0dHBSZXF1ZXN0SGFuZGxlcilcIixcbiAgICAgICAgICBkZXRhaWxzLFxuICAgICAgICAgIGNyYXdsSUQsXG4gICAgICAgICk7XG4gICAgICAgICovXG4gICAgICAgIGNvbnN0IHRhYiA9IGRldGFpbHMudGFiSWQgPiAtMVxuICAgICAgICAgICAgPyBhd2FpdCBicm93c2VyLnRhYnMuZ2V0KGRldGFpbHMudGFiSWQpXG4gICAgICAgICAgICA6IHsgd2luZG93SWQ6IHVuZGVmaW5lZCwgaW5jb2duaXRvOiB1bmRlZmluZWQsIHVybDogdW5kZWZpbmVkIH07XG4gICAgICAgIGNvbnN0IHVwZGF0ZSA9IHt9O1xuICAgICAgICB1cGRhdGUuaW5jb2duaXRvID0gYm9vbFRvSW50KHRhYi5pbmNvZ25pdG8pO1xuICAgICAgICB1cGRhdGUuY3Jhd2xfaWQgPSBjcmF3bElEO1xuICAgICAgICB1cGRhdGUuZXh0ZW5zaW9uX3Nlc3Npb25fdXVpZCA9IGV4dGVuc2lvblNlc3Npb25VdWlkO1xuICAgICAgICB1cGRhdGUuZXZlbnRfb3JkaW5hbCA9IGV2ZW50T3JkaW5hbDtcbiAgICAgICAgdXBkYXRlLndpbmRvd19pZCA9IHRhYi53aW5kb3dJZDtcbiAgICAgICAgdXBkYXRlLnRhYl9pZCA9IGRldGFpbHMudGFiSWQ7XG4gICAgICAgIHVwZGF0ZS5mcmFtZV9pZCA9IGRldGFpbHMuZnJhbWVJZDtcbiAgICAgICAgLy8gcmVxdWVzdElkIGlzIGEgdW5pcXVlIGlkZW50aWZpZXIgdGhhdCBjYW4gYmUgdXNlZCB0byBsaW5rIHJlcXVlc3RzIGFuZCByZXNwb25zZXNcbiAgICAgICAgdXBkYXRlLnJlcXVlc3RfaWQgPSBkZXRhaWxzLnJlcXVlc3RJZDtcbiAgICAgICAgLy8gY29uc3Qgc3RhY2t0cmFjZV9zdHIgPSBnZXRfc3RhY2tfdHJhY2Vfc3RyKCk7XG4gICAgICAgIC8vIHVwZGF0ZS5yZXFfY2FsbF9zdGFjayA9IGVzY2FwZVN0cmluZyhzdGFja3RyYWNlX3N0cik7XG4gICAgICAgIGNvbnN0IHVybCA9IGRldGFpbHMudXJsO1xuICAgICAgICB1cGRhdGUudXJsID0gZXNjYXBlVXJsKHVybCk7XG4gICAgICAgIGNvbnN0IHJlcXVlc3RNZXRob2QgPSBkZXRhaWxzLm1ldGhvZDtcbiAgICAgICAgdXBkYXRlLm1ldGhvZCA9IGVzY2FwZVN0cmluZyhyZXF1ZXN0TWV0aG9kKTtcbiAgICAgICAgY29uc3QgY3VycmVudF90aW1lID0gbmV3IERhdGUoZGV0YWlscy50aW1lU3RhbXApO1xuICAgICAgICB1cGRhdGUudGltZV9zdGFtcCA9IGN1cnJlbnRfdGltZS50b0lTT1N0cmluZygpO1xuICAgICAgICBsZXQgZW5jb2RpbmdUeXBlID0gXCJcIjtcbiAgICAgICAgbGV0IHJlZmVycmVyID0gXCJcIjtcbiAgICAgICAgY29uc3QgaGVhZGVycyA9IFtdO1xuICAgICAgICBsZXQgaXNPY3NwID0gZmFsc2U7XG4gICAgICAgIGlmIChkZXRhaWxzLnJlcXVlc3RIZWFkZXJzKSB7XG4gICAgICAgICAgICBkZXRhaWxzLnJlcXVlc3RIZWFkZXJzLm1hcChyZXF1ZXN0SGVhZGVyID0+IHtcbiAgICAgICAgICAgICAgICBjb25zdCB7IG5hbWUsIHZhbHVlIH0gPSByZXF1ZXN0SGVhZGVyO1xuICAgICAgICAgICAgICAgIGNvbnN0IGhlYWRlcl9wYWlyID0gW107XG4gICAgICAgICAgICAgICAgaGVhZGVyX3BhaXIucHVzaChlc2NhcGVTdHJpbmcobmFtZSkpO1xuICAgICAgICAgICAgICAgIGhlYWRlcl9wYWlyLnB1c2goZXNjYXBlU3RyaW5nKHZhbHVlKSk7XG4gICAgICAgICAgICAgICAgaGVhZGVycy5wdXNoKGhlYWRlcl9wYWlyKTtcbiAgICAgICAgICAgICAgICBpZiAobmFtZSA9PT0gXCJDb250ZW50LVR5cGVcIikge1xuICAgICAgICAgICAgICAgICAgICBlbmNvZGluZ1R5cGUgPSB2YWx1ZTtcbiAgICAgICAgICAgICAgICAgICAgaWYgKGVuY29kaW5nVHlwZS5pbmRleE9mKFwiYXBwbGljYXRpb24vb2NzcC1yZXF1ZXN0XCIpICE9PSAtMSkge1xuICAgICAgICAgICAgICAgICAgICAgICAgaXNPY3NwID0gdHJ1ZTtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBpZiAobmFtZSA9PT0gXCJSZWZlcmVyXCIpIHtcbiAgICAgICAgICAgICAgICAgICAgcmVmZXJyZXIgPSB2YWx1ZTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgfVxuICAgICAgICB1cGRhdGUucmVmZXJyZXIgPSBlc2NhcGVTdHJpbmcocmVmZXJyZXIpO1xuICAgICAgICBpZiAocmVxdWVzdE1ldGhvZCA9PT0gXCJQT1NUXCIgJiYgIWlzT2NzcCAvKiBkb24ndCBwcm9jZXNzIE9DU1AgcmVxdWVzdHMgKi8pIHtcbiAgICAgICAgICAgIGNvbnN0IHBlbmRpbmdSZXF1ZXN0ID0gdGhpcy5nZXRQZW5kaW5nUmVxdWVzdChkZXRhaWxzLnJlcXVlc3RJZCk7XG4gICAgICAgICAgICBjb25zdCByZXNvbHZlZCA9IGF3YWl0IHBlbmRpbmdSZXF1ZXN0LnJlc29sdmVkV2l0aGluVGltZW91dCgxMDAwKTtcbiAgICAgICAgICAgIGlmICghcmVzb2x2ZWQpIHtcbiAgICAgICAgICAgICAgICB0aGlzLmRhdGFSZWNlaXZlci5sb2dFcnJvcihcIlBlbmRpbmcgcmVxdWVzdCB0aW1lZCBvdXQgd2FpdGluZyBmb3IgZGF0YSBmcm9tIGJvdGggb25CZWZvcmVSZXF1ZXN0IGFuZCBvbkJlZm9yZVNlbmRIZWFkZXJzIGV2ZW50c1wiKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGVsc2Uge1xuICAgICAgICAgICAgICAgIGNvbnN0IG9uQmVmb3JlUmVxdWVzdEV2ZW50RGV0YWlscyA9IGF3YWl0IHBlbmRpbmdSZXF1ZXN0Lm9uQmVmb3JlUmVxdWVzdEV2ZW50RGV0YWlscztcbiAgICAgICAgICAgICAgICBjb25zdCByZXF1ZXN0Qm9keSA9IG9uQmVmb3JlUmVxdWVzdEV2ZW50RGV0YWlscy5yZXF1ZXN0Qm9keTtcbiAgICAgICAgICAgICAgICBpZiAocmVxdWVzdEJvZHkpIHtcbiAgICAgICAgICAgICAgICAgICAgY29uc3QgcG9zdFBhcnNlciA9IG5ldyBIdHRwUG9zdFBhcnNlcihcbiAgICAgICAgICAgICAgICAgICAgLy8gZGV0YWlscyxcbiAgICAgICAgICAgICAgICAgICAgb25CZWZvcmVSZXF1ZXN0RXZlbnREZXRhaWxzLCB0aGlzLmRhdGFSZWNlaXZlcik7XG4gICAgICAgICAgICAgICAgICAgIGNvbnN0IHBvc3RPYmogPSBwb3N0UGFyc2VyXG4gICAgICAgICAgICAgICAgICAgICAgICAucGFyc2VQb3N0UmVxdWVzdCgpO1xuICAgICAgICAgICAgICAgICAgICAvLyBBZGQgKFBPU1QpIHJlcXVlc3QgaGVhZGVycyBmcm9tIHVwbG9hZCBzdHJlYW1cbiAgICAgICAgICAgICAgICAgICAgaWYgKFwicG9zdF9oZWFkZXJzXCIgaW4gcG9zdE9iaikge1xuICAgICAgICAgICAgICAgICAgICAgICAgLy8gT25seSBzdG9yZSBQT1NUIGhlYWRlcnMgdGhhdCB3ZSBrbm93IGFuZCBuZWVkLiBXZSBtYXkgbWlzaW50ZXJwcmV0IFBPU1QgZGF0YSBhcyBoZWFkZXJzXG4gICAgICAgICAgICAgICAgICAgICAgICAvLyBhcyBkZXRlY3Rpb24gaXMgYmFzZWQgb24gXCJrZXk6dmFsdWVcIiBmb3JtYXQgKG5vbi1oZWFkZXIgUE9TVCBkYXRhIGNhbiBiZSBpbiB0aGlzIGZvcm1hdCBhcyB3ZWxsKVxuICAgICAgICAgICAgICAgICAgICAgICAgY29uc3QgY29udGVudEhlYWRlcnMgPSBbXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgXCJDb250ZW50LVR5cGVcIixcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBcIkNvbnRlbnQtRGlzcG9zaXRpb25cIixcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBcIkNvbnRlbnQtTGVuZ3RoXCIsXG4gICAgICAgICAgICAgICAgICAgICAgICBdO1xuICAgICAgICAgICAgICAgICAgICAgICAgZm9yIChjb25zdCBuYW1lIGluIHBvc3RPYmoucG9zdF9oZWFkZXJzKSB7XG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgaWYgKGNvbnRlbnRIZWFkZXJzLmluY2x1ZGVzKG5hbWUpKSB7XG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNvbnN0IGhlYWRlcl9wYWlyID0gW107XG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGhlYWRlcl9wYWlyLnB1c2goZXNjYXBlU3RyaW5nKG5hbWUpKTtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgaGVhZGVyX3BhaXIucHVzaChlc2NhcGVTdHJpbmcocG9zdE9iai5wb3N0X2hlYWRlcnNbbmFtZV0pKTtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgaGVhZGVycy5wdXNoKGhlYWRlcl9wYWlyKTtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgLy8gd2Ugc3RvcmUgUE9TVCBib2R5IGluIEpTT04gZm9ybWF0LCBleGNlcHQgd2hlbiBpdCdzIGEgc3RyaW5nIHdpdGhvdXQgYSAoa2V5LXZhbHVlKSBzdHJ1Y3R1cmVcbiAgICAgICAgICAgICAgICAgICAgaWYgKFwicG9zdF9ib2R5XCIgaW4gcG9zdE9iaikge1xuICAgICAgICAgICAgICAgICAgICAgICAgdXBkYXRlLnBvc3RfYm9keSA9IHBvc3RPYmoucG9zdF9ib2R5O1xuICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICAgIHVwZGF0ZS5oZWFkZXJzID0gSlNPTi5zdHJpbmdpZnkoaGVhZGVycyk7XG4gICAgICAgIC8vIENoZWNrIGlmIHhoclxuICAgICAgICBjb25zdCBpc1hIUiA9IGRldGFpbHMudHlwZSA9PT0gXCJ4bWxodHRwcmVxdWVzdFwiO1xuICAgICAgICB1cGRhdGUuaXNfWEhSID0gYm9vbFRvSW50KGlzWEhSKTtcbiAgICAgICAgLy8gQ2hlY2sgaWYgZnJhbWUgT1IgZnVsbCBwYWdlIGxvYWRcbiAgICAgICAgY29uc3QgaXNGdWxsUGFnZUxvYWQgPSBkZXRhaWxzLmZyYW1lSWQgPT09IDA7XG4gICAgICAgIGNvbnN0IGlzRnJhbWVMb2FkID0gZGV0YWlscy50eXBlID09PSBcInN1Yl9mcmFtZVwiO1xuICAgICAgICB1cGRhdGUuaXNfZnVsbF9wYWdlID0gYm9vbFRvSW50KGlzRnVsbFBhZ2VMb2FkKTtcbiAgICAgICAgdXBkYXRlLmlzX2ZyYW1lX2xvYWQgPSBib29sVG9JbnQoaXNGcmFtZUxvYWQpO1xuICAgICAgICAvLyBHcmFiIHRoZSB0cmlnZ2VyaW5nIGFuZCBsb2FkaW5nIFByaW5jaXBhbHNcbiAgICAgICAgbGV0IHRyaWdnZXJpbmdPcmlnaW47XG4gICAgICAgIGxldCBsb2FkaW5nT3JpZ2luO1xuICAgICAgICBpZiAoZGV0YWlscy5vcmlnaW5VcmwpIHtcbiAgICAgICAgICAgIGNvbnN0IHBhcnNlZE9yaWdpblVybCA9IG5ldyBVUkwoZGV0YWlscy5vcmlnaW5VcmwpO1xuICAgICAgICAgICAgdHJpZ2dlcmluZ09yaWdpbiA9IHBhcnNlZE9yaWdpblVybC5vcmlnaW47XG4gICAgICAgIH1cbiAgICAgICAgaWYgKGRldGFpbHMuZG9jdW1lbnRVcmwpIHtcbiAgICAgICAgICAgIGNvbnN0IHBhcnNlZERvY3VtZW50VXJsID0gbmV3IFVSTChkZXRhaWxzLmRvY3VtZW50VXJsKTtcbiAgICAgICAgICAgIGxvYWRpbmdPcmlnaW4gPSBwYXJzZWREb2N1bWVudFVybC5vcmlnaW47XG4gICAgICAgIH1cbiAgICAgICAgdXBkYXRlLnRyaWdnZXJpbmdfb3JpZ2luID0gZXNjYXBlU3RyaW5nKHRyaWdnZXJpbmdPcmlnaW4pO1xuICAgICAgICB1cGRhdGUubG9hZGluZ19vcmlnaW4gPSBlc2NhcGVTdHJpbmcobG9hZGluZ09yaWdpbik7XG4gICAgICAgIC8vIGxvYWRpbmdEb2N1bWVudCdzIGhyZWZcbiAgICAgICAgLy8gVGhlIGxvYWRpbmdEb2N1bWVudCBpcyB0aGUgZG9jdW1lbnQgdGhlIGVsZW1lbnQgcmVzaWRlcywgcmVnYXJkbGVzcyBvZlxuICAgICAgICAvLyBob3cgdGhlIGxvYWQgd2FzIHRyaWdnZXJlZC5cbiAgICAgICAgY29uc3QgbG9hZGluZ0hyZWYgPSBkZXRhaWxzLmRvY3VtZW50VXJsO1xuICAgICAgICB1cGRhdGUubG9hZGluZ19ocmVmID0gZXNjYXBlU3RyaW5nKGxvYWRpbmdIcmVmKTtcbiAgICAgICAgLy8gcmVzb3VyY2VUeXBlIG9mIHRoZSByZXF1ZXN0aW5nIG5vZGUuIFRoaXMgaXMgc2V0IGJ5IHRoZSB0eXBlIG9mXG4gICAgICAgIC8vIG5vZGUgbWFraW5nIHRoZSByZXF1ZXN0IChpLmUuIGFuIDxpbWcgc3JjPS4uLj4gbm9kZSB3aWxsIHNldCB0byB0eXBlIFwiaW1hZ2VcIikuXG4gICAgICAgIC8vIERvY3VtZW50YXRpb246XG4gICAgICAgIC8vIGh0dHBzOi8vZGV2ZWxvcGVyLm1vemlsbGEub3JnL2VuLVVTL2RvY3MvTW96aWxsYS9BZGQtb25zL1dlYkV4dGVuc2lvbnMvQVBJL3dlYlJlcXVlc3QvUmVzb3VyY2VUeXBlXG4gICAgICAgIHVwZGF0ZS5yZXNvdXJjZV90eXBlID0gZGV0YWlscy50eXBlO1xuICAgICAgICAvKlxuICAgICAgICAvLyBUT0RPOiBSZWZhY3RvciB0byBjb3JyZXNwb25kaW5nIHdlYmV4dCBsb2dpYyBvciBkaXNjYXJkXG4gICAgICAgIGNvbnN0IFRoaXJkUGFydHlVdGlsID0gQ2NbXCJAbW96aWxsYS5vcmcvdGhpcmRwYXJ0eXV0aWw7MVwiXS5nZXRTZXJ2aWNlKFxuICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIENpLm1veklUaGlyZFBhcnR5VXRpbCk7XG4gICAgICAgIC8vIERvIHRoaXJkLXBhcnR5IGNoZWNrc1xuICAgICAgICAvLyBUaGVzZSBzcGVjaWZpYyBjaGVja3MgYXJlIGRvbmUgYmVjYXVzZSBpdCdzIHdoYXQncyB1c2VkIGluIFRyYWNraW5nIFByb3RlY3Rpb25cbiAgICAgICAgLy8gU2VlOiBodHRwOi8vc2VhcmNoZm94Lm9yZy9tb3ppbGxhLWNlbnRyYWwvc291cmNlL25ldHdlcmsvYmFzZS9uc0NoYW5uZWxDbGFzc2lmaWVyLmNwcCMxMDdcbiAgICAgICAgdHJ5IHtcbiAgICAgICAgICBjb25zdCBpc1RoaXJkUGFydHlDaGFubmVsID0gVGhpcmRQYXJ0eVV0aWwuaXNUaGlyZFBhcnR5Q2hhbm5lbChkZXRhaWxzKTtcbiAgICAgICAgICBjb25zdCB0b3BXaW5kb3cgPSBUaGlyZFBhcnR5VXRpbC5nZXRUb3BXaW5kb3dGb3JDaGFubmVsKGRldGFpbHMpO1xuICAgICAgICAgIGNvbnN0IHRvcFVSSSA9IFRoaXJkUGFydHlVdGlsLmdldFVSSUZyb21XaW5kb3codG9wV2luZG93KTtcbiAgICAgICAgICBpZiAodG9wVVJJKSB7XG4gICAgICAgICAgICBjb25zdCB0b3BVcmwgPSB0b3BVUkkuc3BlYztcbiAgICAgICAgICAgIGNvbnN0IGNoYW5uZWxVUkkgPSBkZXRhaWxzLlVSSTtcbiAgICAgICAgICAgIGNvbnN0IGlzVGhpcmRQYXJ0eVRvVG9wV2luZG93ID0gVGhpcmRQYXJ0eVV0aWwuaXNUaGlyZFBhcnR5VVJJKFxuICAgICAgICAgICAgICBjaGFubmVsVVJJLFxuICAgICAgICAgICAgICB0b3BVUkksXG4gICAgICAgICAgICApO1xuICAgICAgICAgICAgdXBkYXRlLmlzX3RoaXJkX3BhcnR5X3RvX3RvcF93aW5kb3cgPSBpc1RoaXJkUGFydHlUb1RvcFdpbmRvdztcbiAgICAgICAgICAgIHVwZGF0ZS5pc190aGlyZF9wYXJ0eV9jaGFubmVsID0gaXNUaGlyZFBhcnR5Q2hhbm5lbDtcbiAgICAgICAgICB9XG4gICAgICAgIH0gY2F0Y2ggKGFuRXJyb3IpIHtcbiAgICAgICAgICAvLyBFeGNlcHRpb25zIGV4cGVjdGVkIGZvciBjaGFubmVscyB0cmlnZ2VyZWQgb3IgbG9hZGluZyBpbiBhXG4gICAgICAgICAgLy8gTnVsbFByaW5jaXBhbCBvciBTeXN0ZW1QcmluY2lwYWwuIFRoZXkgYXJlIGFsc28gZXhwZWN0ZWQgZm9yIGZhdmljb25cbiAgICAgICAgICAvLyBsb2Fkcywgd2hpY2ggd2UgYXR0ZW1wdCB0byBmaWx0ZXIuIERlcGVuZGluZyBvbiB0aGUgbmFtaW5nLCBzb21lIGZhdmljb25zXG4gICAgICAgICAgLy8gbWF5IGNvbnRpbnVlIHRvIGxlYWQgdG8gZXJyb3IgbG9ncy5cbiAgICAgICAgICBpZiAoXG4gICAgICAgICAgICB1cGRhdGUudHJpZ2dlcmluZ19vcmlnaW4gIT09IFwiW1N5c3RlbSBQcmluY2lwYWxdXCIgJiZcbiAgICAgICAgICAgIHVwZGF0ZS50cmlnZ2VyaW5nX29yaWdpbiAhPT0gdW5kZWZpbmVkICYmXG4gICAgICAgICAgICB1cGRhdGUubG9hZGluZ19vcmlnaW4gIT09IFwiW1N5c3RlbSBQcmluY2lwYWxdXCIgJiZcbiAgICAgICAgICAgIHVwZGF0ZS5sb2FkaW5nX29yaWdpbiAhPT0gdW5kZWZpbmVkICYmXG4gICAgICAgICAgICAhdXBkYXRlLnVybC5lbmRzV2l0aChcImljb1wiKVxuICAgICAgICAgICkge1xuICAgICAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIubG9nRXJyb3IoXG4gICAgICAgICAgICAgIFwiRXJyb3Igd2hpbGUgcmV0cmlldmluZyBhZGRpdGlvbmFsIGNoYW5uZWwgaW5mb3JtYXRpb24gZm9yIFVSTDogXCIgK1xuICAgICAgICAgICAgICBcIlxcblwiICtcbiAgICAgICAgICAgICAgdXBkYXRlLnVybCArXG4gICAgICAgICAgICAgIFwiXFxuIEVycm9yIHRleHQ6XCIgK1xuICAgICAgICAgICAgICBKU09OLnN0cmluZ2lmeShhbkVycm9yKSxcbiAgICAgICAgICAgICk7XG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICAgICovXG4gICAgICAgIHVwZGF0ZS50b3BfbGV2ZWxfdXJsID0gZXNjYXBlVXJsKHRhYi51cmwpO1xuICAgICAgICB1cGRhdGUucGFyZW50X2ZyYW1lX2lkID0gZGV0YWlscy5wYXJlbnRGcmFtZUlkO1xuICAgICAgICB1cGRhdGUuZnJhbWVfYW5jZXN0b3JzID0gZXNjYXBlU3RyaW5nKEpTT04uc3RyaW5naWZ5KGRldGFpbHMuZnJhbWVBbmNlc3RvcnMpKTtcbiAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIuc2F2ZVJlY29yZChcImh0dHBfcmVxdWVzdHNcIiwgdXBkYXRlKTtcbiAgICB9XG4gICAgYXN5bmMgb25CZWZvcmVSZWRpcmVjdEhhbmRsZXIoZGV0YWlscywgY3Jhd2xJRCwgZXZlbnRPcmRpbmFsKSB7XG4gICAgICAgIC8qXG4gICAgICAgIGNvbnNvbGUubG9nKFxuICAgICAgICAgIFwib25CZWZvcmVSZWRpcmVjdEhhbmRsZXIgKHByZXZpb3VzbHkgaHR0cFJlcXVlc3RIYW5kbGVyKVwiLFxuICAgICAgICAgIGRldGFpbHMsXG4gICAgICAgICAgY3Jhd2xJRCxcbiAgICAgICAgKTtcbiAgICAgICAgKi9cbiAgICAgICAgLy8gU2F2ZSBIVFRQIHJlZGlyZWN0IGV2ZW50c1xuICAgICAgICAvLyBFdmVudHMgYXJlIHNhdmVkIHRvIHRoZSBgaHR0cF9yZWRpcmVjdHNgIHRhYmxlXG4gICAgICAgIC8qXG4gICAgICAgIC8vIFRPRE86IFJlZmFjdG9yIHRvIGNvcnJlc3BvbmRpbmcgd2ViZXh0IGxvZ2ljIG9yIGRpc2NhcmRcbiAgICAgICAgLy8gRXZlbnRzIGFyZSBzYXZlZCB0byB0aGUgYGh0dHBfcmVkaXJlY3RzYCB0YWJsZSwgYW5kIG1hcCB0aGUgb2xkXG4gICAgICAgIC8vIHJlcXVlc3QvcmVzcG9uc2UgY2hhbm5lbCBpZCB0byB0aGUgbmV3IHJlcXVlc3QvcmVzcG9uc2UgY2hhbm5lbCBpZC5cbiAgICAgICAgLy8gSW1wbGVtZW50YXRpb24gYmFzZWQgb246IGh0dHBzOi8vc3RhY2tvdmVyZmxvdy5jb20vYS8xMTI0MDYyN1xuICAgICAgICBjb25zdCBvbGROb3RpZmljYXRpb25zID0gZGV0YWlscy5ub3RpZmljYXRpb25DYWxsYmFja3M7XG4gICAgICAgIGxldCBvbGRFdmVudFNpbmsgPSBudWxsO1xuICAgICAgICBkZXRhaWxzLm5vdGlmaWNhdGlvbkNhbGxiYWNrcyA9IHtcbiAgICAgICAgICBRdWVyeUludGVyZmFjZTogWFBDT01VdGlscy5nZW5lcmF0ZVFJKFtcbiAgICAgICAgICAgIENpLm5zSUludGVyZmFjZVJlcXVlc3RvcixcbiAgICAgICAgICAgIENpLm5zSUNoYW5uZWxFdmVudFNpbmssXG4gICAgICAgICAgXSksXG4gICAgXG4gICAgICAgICAgZ2V0SW50ZXJmYWNlKGlpZCkge1xuICAgICAgICAgICAgLy8gV2UgYXJlIG9ubHkgaW50ZXJlc3RlZCBpbiBuc0lDaGFubmVsRXZlbnRTaW5rLFxuICAgICAgICAgICAgLy8gcmV0dXJuIHRoZSBvbGQgY2FsbGJhY2tzIGZvciBhbnkgb3RoZXIgaW50ZXJmYWNlIHJlcXVlc3RzLlxuICAgICAgICAgICAgaWYgKGlpZC5lcXVhbHMoQ2kubnNJQ2hhbm5lbEV2ZW50U2luaykpIHtcbiAgICAgICAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgICAgICBvbGRFdmVudFNpbmsgPSBvbGROb3RpZmljYXRpb25zLlF1ZXJ5SW50ZXJmYWNlKGlpZCk7XG4gICAgICAgICAgICAgIH0gY2F0Y2ggKGFuRXJyb3IpIHtcbiAgICAgICAgICAgICAgICB0aGlzLmRhdGFSZWNlaXZlci5sb2dFcnJvcihcbiAgICAgICAgICAgICAgICAgIFwiRXJyb3IgZHVyaW5nIGNhbGwgdG8gY3VzdG9tIG5vdGlmaWNhdGlvbkNhbGxiYWNrczo6Z2V0SW50ZXJmYWNlLlwiICtcbiAgICAgICAgICAgICAgICAgICAgSlNPTi5zdHJpbmdpZnkoYW5FcnJvciksXG4gICAgICAgICAgICAgICAgKTtcbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICByZXR1cm4gdGhpcztcbiAgICAgICAgICAgIH1cbiAgICBcbiAgICAgICAgICAgIGlmIChvbGROb3RpZmljYXRpb25zKSB7XG4gICAgICAgICAgICAgIHJldHVybiBvbGROb3RpZmljYXRpb25zLmdldEludGVyZmFjZShpaWQpO1xuICAgICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgICAgdGhyb3cgQ3IuTlNfRVJST1JfTk9fSU5URVJGQUNFO1xuICAgICAgICAgICAgfVxuICAgICAgICAgIH0sXG4gICAgXG4gICAgICAgICAgYXN5bmNPbkNoYW5uZWxSZWRpcmVjdChvbGRDaGFubmVsLCBuZXdDaGFubmVsLCBmbGFncywgY2FsbGJhY2spIHtcbiAgICBcbiAgICAgICAgICAgIG5ld0NoYW5uZWwuUXVlcnlJbnRlcmZhY2UoQ2kubnNJSHR0cENoYW5uZWwpO1xuICAgIFxuICAgICAgICAgICAgY29uc3QgaHR0cFJlZGlyZWN0OiBIdHRwUmVkaXJlY3QgPSB7XG4gICAgICAgICAgICAgIGNyYXdsX2lkOiBjcmF3bElELFxuICAgICAgICAgICAgICBvbGRfcmVxdWVzdF9pZDogb2xkQ2hhbm5lbC5jaGFubmVsSWQsXG4gICAgICAgICAgICAgIG5ld19yZXF1ZXN0X2lkOiBuZXdDaGFubmVsLmNoYW5uZWxJZCxcbiAgICAgICAgICAgICAgdGltZV9zdGFtcDogbmV3IERhdGUoKS50b0lTT1N0cmluZygpLFxuICAgICAgICAgICAgfTtcbiAgICAgICAgICAgIHRoaXMuZGF0YVJlY2VpdmVyLnNhdmVSZWNvcmQoXCJodHRwX3JlZGlyZWN0c1wiLCBodHRwUmVkaXJlY3QpO1xuICAgIFxuICAgICAgICAgICAgaWYgKG9sZEV2ZW50U2luaykge1xuICAgICAgICAgICAgICBvbGRFdmVudFNpbmsuYXN5bmNPbkNoYW5uZWxSZWRpcmVjdChcbiAgICAgICAgICAgICAgICBvbGRDaGFubmVsLFxuICAgICAgICAgICAgICAgIG5ld0NoYW5uZWwsXG4gICAgICAgICAgICAgICAgZmxhZ3MsXG4gICAgICAgICAgICAgICAgY2FsbGJhY2ssXG4gICAgICAgICAgICAgICk7XG4gICAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgICBjYWxsYmFjay5vblJlZGlyZWN0VmVyaWZ5Q2FsbGJhY2soQ3IuTlNfT0spO1xuICAgICAgICAgICAgfVxuICAgICAgICAgIH0sXG4gICAgICAgIH07XG4gICAgICAgICovXG4gICAgICAgIGNvbnN0IHJlc3BvbnNlU3RhdHVzID0gZGV0YWlscy5zdGF0dXNDb2RlO1xuICAgICAgICBjb25zdCByZXNwb25zZVN0YXR1c1RleHQgPSBkZXRhaWxzLnN0YXR1c0xpbmU7XG4gICAgICAgIGNvbnN0IHRhYiA9IGRldGFpbHMudGFiSWQgPiAtMVxuICAgICAgICAgICAgPyBhd2FpdCBicm93c2VyLnRhYnMuZ2V0KGRldGFpbHMudGFiSWQpXG4gICAgICAgICAgICA6IHsgd2luZG93SWQ6IHVuZGVmaW5lZCwgaW5jb2duaXRvOiB1bmRlZmluZWQgfTtcbiAgICAgICAgY29uc3QgaHR0cFJlZGlyZWN0ID0ge1xuICAgICAgICAgICAgaW5jb2duaXRvOiBib29sVG9JbnQodGFiLmluY29nbml0byksXG4gICAgICAgICAgICBjcmF3bF9pZDogY3Jhd2xJRCxcbiAgICAgICAgICAgIG9sZF9yZXF1ZXN0X3VybDogZXNjYXBlVXJsKGRldGFpbHMudXJsKSxcbiAgICAgICAgICAgIG9sZF9yZXF1ZXN0X2lkOiBkZXRhaWxzLnJlcXVlc3RJZCxcbiAgICAgICAgICAgIG5ld19yZXF1ZXN0X3VybDogZXNjYXBlVXJsKGRldGFpbHMucmVkaXJlY3RVcmwpLFxuICAgICAgICAgICAgbmV3X3JlcXVlc3RfaWQ6IG51bGwsXG4gICAgICAgICAgICBleHRlbnNpb25fc2Vzc2lvbl91dWlkOiBleHRlbnNpb25TZXNzaW9uVXVpZCxcbiAgICAgICAgICAgIGV2ZW50X29yZGluYWw6IGV2ZW50T3JkaW5hbCxcbiAgICAgICAgICAgIHdpbmRvd19pZDogdGFiLndpbmRvd0lkLFxuICAgICAgICAgICAgdGFiX2lkOiBkZXRhaWxzLnRhYklkLFxuICAgICAgICAgICAgZnJhbWVfaWQ6IGRldGFpbHMuZnJhbWVJZCxcbiAgICAgICAgICAgIHJlc3BvbnNlX3N0YXR1czogcmVzcG9uc2VTdGF0dXMsXG4gICAgICAgICAgICByZXNwb25zZV9zdGF0dXNfdGV4dDogZXNjYXBlU3RyaW5nKHJlc3BvbnNlU3RhdHVzVGV4dCksXG4gICAgICAgICAgICB0aW1lX3N0YW1wOiBuZXcgRGF0ZShkZXRhaWxzLnRpbWVTdGFtcCkudG9JU09TdHJpbmcoKSxcbiAgICAgICAgfTtcbiAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIuc2F2ZVJlY29yZChcImh0dHBfcmVkaXJlY3RzXCIsIGh0dHBSZWRpcmVjdCk7XG4gICAgfVxuICAgIC8qXG4gICAgKiBIVFRQIFJlc3BvbnNlIEhhbmRsZXJzIGFuZCBIZWxwZXIgRnVuY3Rpb25zXG4gICAgKi9cbiAgICBhc3luYyBsb2dXaXRoUmVzcG9uc2VCb2R5KGRldGFpbHMsIHVwZGF0ZSkge1xuICAgICAgICBjb25zdCBwZW5kaW5nUmVzcG9uc2UgPSB0aGlzLmdldFBlbmRpbmdSZXNwb25zZShkZXRhaWxzLnJlcXVlc3RJZCk7XG4gICAgICAgIHRyeSB7XG4gICAgICAgICAgICBjb25zdCByZXNwb25zZUJvZHlMaXN0ZW5lciA9IHBlbmRpbmdSZXNwb25zZS5yZXNwb25zZUJvZHlMaXN0ZW5lcjtcbiAgICAgICAgICAgIGNvbnN0IHJlc3BCb2R5ID0gYXdhaXQgcmVzcG9uc2VCb2R5TGlzdGVuZXIuZ2V0UmVzcG9uc2VCb2R5KCk7XG4gICAgICAgICAgICBjb25zdCBjb250ZW50SGFzaCA9IGF3YWl0IHJlc3BvbnNlQm9keUxpc3RlbmVyLmdldENvbnRlbnRIYXNoKCk7XG4gICAgICAgICAgICB0aGlzLmRhdGFSZWNlaXZlci5zYXZlQ29udGVudChlc2NhcGVTdHJpbmcocmVzcEJvZHkpLCBlc2NhcGVTdHJpbmcoY29udGVudEhhc2gpKTtcbiAgICAgICAgICAgIHRoaXMuZGF0YVJlY2VpdmVyLnNhdmVSZWNvcmQoXCJodHRwX3Jlc3BvbnNlc1wiLCB1cGRhdGUpO1xuICAgICAgICB9XG4gICAgICAgIGNhdGNoIChlcnIpIHtcbiAgICAgICAgICAgIC8qXG4gICAgICAgICAgICAvLyBUT0RPOiBSZWZhY3RvciB0byBjb3JyZXNwb25kaW5nIHdlYmV4dCBsb2dpYyBvciBkaXNjYXJkXG4gICAgICAgICAgICBkYXRhUmVjZWl2ZXIubG9nRXJyb3IoXG4gICAgICAgICAgICAgIFwiVW5hYmxlIHRvIHJldHJpZXZlIHJlc3BvbnNlIGJvZHkuXCIgKyBKU09OLnN0cmluZ2lmeShhUmVhc29uKSxcbiAgICAgICAgICAgICk7XG4gICAgICAgICAgICB1cGRhdGUuY29udGVudF9oYXNoID0gXCI8ZXJyb3I+XCI7XG4gICAgICAgICAgICBkYXRhUmVjZWl2ZXIuc2F2ZVJlY29yZChcImh0dHBfcmVzcG9uc2VzXCIsIHVwZGF0ZSk7XG4gICAgICAgICAgICAqL1xuICAgICAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIubG9nRXJyb3IoXCJVbmFibGUgdG8gcmV0cmlldmUgcmVzcG9uc2UgYm9keS5cIiArXG4gICAgICAgICAgICAgICAgXCJMaWtlbHkgY2F1c2VkIGJ5IGEgcHJvZ3JhbW1pbmcgZXJyb3IuIEVycm9yIE1lc3NhZ2U6XCIgK1xuICAgICAgICAgICAgICAgIGVyci5uYW1lICtcbiAgICAgICAgICAgICAgICBlcnIubWVzc2FnZSArXG4gICAgICAgICAgICAgICAgXCJcXG5cIiArXG4gICAgICAgICAgICAgICAgZXJyLnN0YWNrKTtcbiAgICAgICAgICAgIHVwZGF0ZS5jb250ZW50X2hhc2ggPSBcIjxlcnJvcj5cIjtcbiAgICAgICAgICAgIHRoaXMuZGF0YVJlY2VpdmVyLnNhdmVSZWNvcmQoXCJodHRwX3Jlc3BvbnNlc1wiLCB1cGRhdGUpO1xuICAgICAgICB9XG4gICAgfVxuICAgIC8qKlxuICAgICAqIFJldHVybiB0cnVlIGlmIHRoaXMgcmVxdWVzdCBpcyBsb2FkaW5nIGphdmFzY3JpcHRcbiAgICAgKiBXZSByZWx5IG1vc3RseSBvbiB0aGUgY29udGVudCBwb2xpY3kgdHlwZSB0byBmaWx0ZXIgcmVzcG9uc2VzXG4gICAgICogYW5kIGZhbGwgYmFjayB0byB0aGUgVVJJIGFuZCBjb250ZW50IHR5cGUgc3RyaW5nIGZvciB0eXBlcyB0aGF0IGNhblxuICAgICAqIGxvYWQgdmFyaW91cyByZXNvdXJjZSB0eXBlcy5cbiAgICAgKiBTZWU6IGh0dHBzOi8vZGV2ZWxvcGVyLm1vemlsbGEub3JnL2VuLVVTL2RvY3MvTW96aWxsYS9BZGQtb25zL1dlYkV4dGVuc2lvbnMvQVBJL3dlYlJlcXVlc3QvUmVzb3VyY2VUeXBlXG4gICAgICpcbiAgICAgKiBAcGFyYW0gcmVzb3VyY2VUeXBlXG4gICAgICovXG4gICAgaXNKUyhyZXNvdXJjZVR5cGUpIHtcbiAgICAgICAgcmV0dXJuIHJlc291cmNlVHlwZSA9PT0gXCJzY3JpcHRcIjtcbiAgICB9XG4gICAgLy8gSW5zdHJ1bWVudCBIVFRQIHJlc3BvbnNlc1xuICAgIGFzeW5jIG9uQ29tcGxldGVkSGFuZGxlcihkZXRhaWxzLCBjcmF3bElELCBldmVudE9yZGluYWwsIHNhdmVKYXZhc2NyaXB0LCBzYXZlQWxsQ29udGVudCkge1xuICAgICAgICAvKlxuICAgICAgICBjb25zb2xlLmxvZyhcbiAgICAgICAgICBcIm9uQ29tcGxldGVkSGFuZGxlciAocHJldmlvdXNseSBodHRwUmVxdWVzdEhhbmRsZXIpXCIsXG4gICAgICAgICAgZGV0YWlscyxcbiAgICAgICAgICBjcmF3bElELFxuICAgICAgICAgIHNhdmVKYXZhc2NyaXB0LFxuICAgICAgICAgIHNhdmVBbGxDb250ZW50LFxuICAgICAgICApO1xuICAgICAgICAqL1xuICAgICAgICBjb25zdCB0YWIgPSBkZXRhaWxzLnRhYklkID4gLTFcbiAgICAgICAgICAgID8gYXdhaXQgYnJvd3Nlci50YWJzLmdldChkZXRhaWxzLnRhYklkKVxuICAgICAgICAgICAgOiB7IHdpbmRvd0lkOiB1bmRlZmluZWQsIGluY29nbml0bzogdW5kZWZpbmVkIH07XG4gICAgICAgIGNvbnN0IHVwZGF0ZSA9IHt9O1xuICAgICAgICB1cGRhdGUuaW5jb2duaXRvID0gYm9vbFRvSW50KHRhYi5pbmNvZ25pdG8pO1xuICAgICAgICB1cGRhdGUuY3Jhd2xfaWQgPSBjcmF3bElEO1xuICAgICAgICB1cGRhdGUuZXh0ZW5zaW9uX3Nlc3Npb25fdXVpZCA9IGV4dGVuc2lvblNlc3Npb25VdWlkO1xuICAgICAgICB1cGRhdGUuZXZlbnRfb3JkaW5hbCA9IGV2ZW50T3JkaW5hbDtcbiAgICAgICAgdXBkYXRlLndpbmRvd19pZCA9IHRhYi53aW5kb3dJZDtcbiAgICAgICAgdXBkYXRlLnRhYl9pZCA9IGRldGFpbHMudGFiSWQ7XG4gICAgICAgIHVwZGF0ZS5mcmFtZV9pZCA9IGRldGFpbHMuZnJhbWVJZDtcbiAgICAgICAgLy8gcmVxdWVzdElkIGlzIGEgdW5pcXVlIGlkZW50aWZpZXIgdGhhdCBjYW4gYmUgdXNlZCB0byBsaW5rIHJlcXVlc3RzIGFuZCByZXNwb25zZXNcbiAgICAgICAgdXBkYXRlLnJlcXVlc3RfaWQgPSBkZXRhaWxzLnJlcXVlc3RJZDtcbiAgICAgICAgY29uc3QgaXNDYWNoZWQgPSBkZXRhaWxzLmZyb21DYWNoZTtcbiAgICAgICAgdXBkYXRlLmlzX2NhY2hlZCA9IGJvb2xUb0ludChpc0NhY2hlZCk7XG4gICAgICAgIGNvbnN0IHVybCA9IGRldGFpbHMudXJsO1xuICAgICAgICB1cGRhdGUudXJsID0gZXNjYXBlVXJsKHVybCk7XG4gICAgICAgIGNvbnN0IHJlcXVlc3RNZXRob2QgPSBkZXRhaWxzLm1ldGhvZDtcbiAgICAgICAgdXBkYXRlLm1ldGhvZCA9IGVzY2FwZVN0cmluZyhyZXF1ZXN0TWV0aG9kKTtcbiAgICAgICAgLy8gVE9ETzogUmVmYWN0b3IgdG8gY29ycmVzcG9uZGluZyB3ZWJleHQgbG9naWMgb3IgZGlzY2FyZFxuICAgICAgICAvLyAocmVxdWVzdCBoZWFkZXJzIGFyZSBub3QgYXZhaWxhYmxlIGluIGh0dHAgcmVzcG9uc2UgZXZlbnQgbGlzdGVuZXIgb2JqZWN0LFxuICAgICAgICAvLyBidXQgdGhlIHJlZmVycmVyIHByb3BlcnR5IG9mIHRoZSBjb3JyZXNwb25kaW5nIHJlcXVlc3QgY291bGQgYmUgcXVlcmllZClcbiAgICAgICAgLy9cbiAgICAgICAgLy8gbGV0IHJlZmVycmVyID0gXCJcIjtcbiAgICAgICAgLy8gaWYgKGRldGFpbHMucmVmZXJyZXIpIHtcbiAgICAgICAgLy8gICByZWZlcnJlciA9IGRldGFpbHMucmVmZXJyZXIuc3BlYztcbiAgICAgICAgLy8gfVxuICAgICAgICAvLyB1cGRhdGUucmVmZXJyZXIgPSBlc2NhcGVTdHJpbmcocmVmZXJyZXIpO1xuICAgICAgICBjb25zdCByZXNwb25zZVN0YXR1cyA9IGRldGFpbHMuc3RhdHVzQ29kZTtcbiAgICAgICAgdXBkYXRlLnJlc3BvbnNlX3N0YXR1cyA9IHJlc3BvbnNlU3RhdHVzO1xuICAgICAgICBjb25zdCByZXNwb25zZVN0YXR1c1RleHQgPSBkZXRhaWxzLnN0YXR1c0xpbmU7XG4gICAgICAgIHVwZGF0ZS5yZXNwb25zZV9zdGF0dXNfdGV4dCA9IGVzY2FwZVN0cmluZyhyZXNwb25zZVN0YXR1c1RleHQpO1xuICAgICAgICBjb25zdCBjdXJyZW50X3RpbWUgPSBuZXcgRGF0ZShkZXRhaWxzLnRpbWVTdGFtcCk7XG4gICAgICAgIHVwZGF0ZS50aW1lX3N0YW1wID0gY3VycmVudF90aW1lLnRvSVNPU3RyaW5nKCk7XG4gICAgICAgIGNvbnN0IGhlYWRlcnMgPSBbXTtcbiAgICAgICAgbGV0IGxvY2F0aW9uID0gXCJcIjtcbiAgICAgICAgaWYgKGRldGFpbHMucmVzcG9uc2VIZWFkZXJzKSB7XG4gICAgICAgICAgICBkZXRhaWxzLnJlc3BvbnNlSGVhZGVycy5tYXAocmVzcG9uc2VIZWFkZXIgPT4ge1xuICAgICAgICAgICAgICAgIGNvbnN0IHsgbmFtZSwgdmFsdWUgfSA9IHJlc3BvbnNlSGVhZGVyO1xuICAgICAgICAgICAgICAgIGNvbnN0IGhlYWRlcl9wYWlyID0gW107XG4gICAgICAgICAgICAgICAgaGVhZGVyX3BhaXIucHVzaChlc2NhcGVTdHJpbmcobmFtZSkpO1xuICAgICAgICAgICAgICAgIGhlYWRlcl9wYWlyLnB1c2goZXNjYXBlU3RyaW5nKHZhbHVlKSk7XG4gICAgICAgICAgICAgICAgaGVhZGVycy5wdXNoKGhlYWRlcl9wYWlyKTtcbiAgICAgICAgICAgICAgICBpZiAobmFtZS50b0xvd2VyQ2FzZSgpID09PSBcImxvY2F0aW9uXCIpIHtcbiAgICAgICAgICAgICAgICAgICAgbG9jYXRpb24gPSB2YWx1ZTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgfVxuICAgICAgICB1cGRhdGUuaGVhZGVycyA9IEpTT04uc3RyaW5naWZ5KGhlYWRlcnMpO1xuICAgICAgICB1cGRhdGUubG9jYXRpb24gPSBlc2NhcGVTdHJpbmcobG9jYXRpb24pO1xuICAgICAgICBpZiAoc2F2ZUFsbENvbnRlbnQpIHtcbiAgICAgICAgICAgIHRoaXMubG9nV2l0aFJlc3BvbnNlQm9keShkZXRhaWxzLCB1cGRhdGUpO1xuICAgICAgICB9XG4gICAgICAgIGVsc2UgaWYgKHNhdmVKYXZhc2NyaXB0ICYmIHRoaXMuaXNKUyhkZXRhaWxzLnR5cGUpKSB7XG4gICAgICAgICAgICB0aGlzLmxvZ1dpdGhSZXNwb25zZUJvZHkoZGV0YWlscywgdXBkYXRlKTtcbiAgICAgICAgfVxuICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgIHRoaXMuZGF0YVJlY2VpdmVyLnNhdmVSZWNvcmQoXCJodHRwX3Jlc3BvbnNlc1wiLCB1cGRhdGUpO1xuICAgICAgICB9XG4gICAgfVxufVxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pYUhSMGNDMXBibk4wY25WdFpXNTBMbXB6SWl3aWMyOTFjbU5sVW05dmRDSTZJaUlzSW5OdmRYSmpaWE1pT2xzaUxpNHZMaTR2TGk0dmMzSmpMMkpoWTJ0bmNtOTFibVF2YUhSMGNDMXBibk4wY25WdFpXNTBMblJ6SWwwc0ltNWhiV1Z6SWpwYlhTd2liV0Z3Y0dsdVozTWlPaUpCUVVGQkxFOUJRVThzUlVGQlJTeDFRa0ZCZFVJc1JVRkJSU3hOUVVGTkxIZERRVUYzUXl4RFFVRkRPMEZCUTJwR0xFOUJRVThzUlVGQlJTeHZRa0ZCYjBJc1JVRkJSU3hOUVVGTkxDdENRVUVyUWl4RFFVRkRPMEZCUTNKRkxFOUJRVThzUlVGQlJTeGpRVUZqTEVWQlFYRkNMRTFCUVUwc2VVSkJRWGxDTEVOQlFVTTdRVUZETlVVc1QwRkJUeXhGUVVGRkxHTkJRV01zUlVGQlJTeE5RVUZOTEhkQ1FVRjNRaXhEUVVGRE8wRkJRM2hFTEU5QlFVOHNSVUZCUlN4bFFVRmxMRVZCUVVVc1RVRkJUU3g1UWtGQmVVSXNRMEZCUXp0QlFVa3hSQ3hQUVVGUExFVkJRVVVzVTBGQlV5eEZRVUZGTEZsQlFWa3NSVUZCUlN4VFFVRlRMRVZCUVVVc1RVRkJUU3h4UWtGQmNVSXNRMEZCUXp0QlFWTjZSVHM3T3pzN08wZEJUVWM3UVVGRlNDeE5RVUZOTEU5QlFVOHNZMEZCWXp0SlFXRjZRaXhaUVVGWkxGbEJRVms3VVVGWWFFSXNiMEpCUVdVc1IwRkZia0lzUlVGQlJTeERRVUZETzFGQlEwTXNjVUpCUVdkQ0xFZEJSWEJDTEVWQlFVVXNRMEZCUXp0UlFVOU1MRWxCUVVrc1EwRkJReXhaUVVGWkxFZEJRVWNzV1VGQldTeERRVUZETzBsQlEyNURMRU5CUVVNN1NVRkZUU3hIUVVGSExFTkJRVU1zVDBGQlR5eEZRVUZGTEdOQlFXTXNSVUZCUlN4alFVRmpPMUZCUTJoRUxFMUJRVTBzVVVGQlVTeEhRVUZ0UWp0WlFVTXZRaXhSUVVGUk8xbEJRMUlzV1VGQldUdFpRVU5hTEUxQlFVMDdXVUZEVGl4UFFVRlBPMWxCUTFBc1ZVRkJWVHRaUVVOV0xGbEJRVms3V1VGRFdpeFBRVUZQTzFsQlExQXNVVUZCVVR0WlFVTlNMRzFDUVVGdFFqdFpRVU51UWl4TlFVRk5PMWxCUTA0c1VVRkJVVHRaUVVOU0xHbENRVUZwUWp0WlFVTnFRaXhaUVVGWk8xbEJRMW9zVjBGQlZ6dFpRVU5ZTEdOQlFXTTdXVUZEWkN4WFFVRlhPMWxCUTFnc1MwRkJTenRaUVVOTUxGTkJRVk03V1VGRFZDeG5Ra0ZCWjBJN1dVRkRhRUlzVFVGQlRUdFpRVU5PTEU5QlFVODdVMEZEVWl4RFFVRkRPMUZCUlVZc1RVRkJUU3hOUVVGTkxFZEJRV3RDTEVWQlFVVXNTVUZCU1N4RlFVRkZMRU5CUVVNc1dVRkJXU3hEUVVGRExFVkJRVVVzUzBGQlN5eEZRVUZGTEZGQlFWRXNSVUZCUlN4RFFVRkRPMUZCUlhoRkxFMUJRVTBzZVVKQlFYbENMRWRCUVVjc1QwRkJUeXhEUVVGRExFVkJRVVU3V1VGRE1VTXNUMEZCVHl4RFFVTk1MRTlCUVU4c1EwRkJReXhUUVVGVExFbEJRVWtzVDBGQlR5eERRVUZETEZOQlFWTXNRMEZCUXl4UFFVRlBMRU5CUVVNc2EwSkJRV3RDTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkRlRVVzUTBGQlF6dFJRVU5LTEVOQlFVTXNRMEZCUXp0UlFVVkdPenRYUVVWSE8xRkJSVWdzU1VGQlNTeERRVUZETEhWQ1FVRjFRaXhIUVVGSExFOUJRVThzUTBGQlF5eEZRVUZGTzFsQlEzWkRMRTFCUVUwc0swSkJRU3RDTEVkQlFYRkNMRVZCUVVVc1EwRkJRenRaUVVNM1JDeHhRMEZCY1VNN1dVRkRja01zU1VGQlNTeDVRa0ZCZVVJc1EwRkJReXhQUVVGUExFTkJRVU1zUlVGQlJUdG5Ra0ZEZEVNc1QwRkJUeXdyUWtGQkswSXNRMEZCUXp0aFFVTjRRenRaUVVORUxFMUJRVTBzWTBGQll5eEhRVUZITEVsQlFVa3NRMEZCUXl4cFFrRkJhVUlzUTBGQlF5eFBRVUZQTEVOQlFVTXNVMEZCVXl4RFFVRkRMRU5CUVVNN1dVRkRha1VzWTBGQll5eERRVUZETEd0RFFVRnJReXhEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETzFsQlF6TkVMRTFCUVUwc1pVRkJaU3hIUVVGSExFbEJRVWtzUTBGQlF5eHJRa0ZCYTBJc1EwRkJReXhQUVVGUExFTkJRVU1zVTBGQlV5eERRVUZETEVOQlFVTTdXVUZEYmtVc1pVRkJaU3hEUVVGRExHdERRVUZyUXl4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRE8xbEJRelZFTEVsQlFVa3NZMEZCWXl4RlFVRkZPMmRDUVVOc1FpeGxRVUZsTEVOQlFVTXNLMEpCUVN0Q0xFTkJRVU1zVDBGQlR5eERRVUZETEVOQlFVTTdZVUZETVVRN2FVSkJRVTBzU1VGQlNTeGpRVUZqTEVsQlFVa3NTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhQUVVGUExFTkJRVU1zU1VGQlNTeERRVUZETEVWQlFVVTdaMEpCUTNCRUxHVkJRV1VzUTBGQlF5d3JRa0ZCSzBJc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF6dGhRVU14UkR0WlFVTkVMRTlCUVU4c0swSkJRU3RDTEVOQlFVTTdVVUZEZWtNc1EwRkJReXhEUVVGRE8xRkJRMFlzVDBGQlR5eERRVUZETEZWQlFWVXNRMEZCUXl4bFFVRmxMRU5CUVVNc1YwRkJWeXhEUVVNMVF5eEpRVUZKTEVOQlFVTXNkVUpCUVhWQ0xFVkJRelZDTEUxQlFVMHNSVUZEVGl4alFVRmpMRWxCUVVrc1kwRkJZenRaUVVNNVFpeERRVUZETEVOQlFVTXNRMEZCUXl4aFFVRmhMRVZCUVVVc1ZVRkJWU3hEUVVGRE8xbEJRemRDTEVOQlFVTXNRMEZCUXl4RFFVRkRMR0ZCUVdFc1EwRkJReXhEUVVOd1FpeERRVUZETzFGQlJVWXNTVUZCU1N4RFFVRkRMREpDUVVFeVFpeEhRVUZITEU5QlFVOHNRMEZCUXl4RlFVRkZPMWxCUXpORExIRkRRVUZ4UXp0WlFVTnlReXhKUVVGSkxIbENRVUY1UWl4RFFVRkRMRTlCUVU4c1EwRkJReXhGUVVGRk8yZENRVU4wUXl4UFFVRlBPMkZCUTFJN1dVRkRSQ3hOUVVGTkxHTkJRV01zUjBGQlJ5eEpRVUZKTEVOQlFVTXNhVUpCUVdsQ0xFTkJRVU1zVDBGQlR5eERRVUZETEZOQlFWTXNRMEZCUXl4RFFVRkRPMWxCUTJwRkxHTkJRV01zUTBGQlF5eHpRMEZCYzBNc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF6dFpRVU12UkN4SlFVRkpMRU5CUVVNc01FSkJRVEJDTEVOQlF6ZENMRTlCUVU4c1JVRkRVQ3hQUVVGUExFVkJRMUFzZFVKQlFYVkNMRVZCUVVVc1EwRkRNVUlzUTBGQlF6dFJRVU5LTEVOQlFVTXNRMEZCUXp0UlFVTkdMRTlCUVU4c1EwRkJReXhWUVVGVkxFTkJRVU1zYlVKQlFXMUNMRU5CUVVNc1YwRkJWeXhEUVVOb1JDeEpRVUZKTEVOQlFVTXNNa0pCUVRKQ0xFVkJRMmhETEUxQlFVMHNSVUZEVGl4RFFVRkRMR2RDUVVGblFpeERRVUZETEVOQlEyNUNMRU5CUVVNN1VVRkZSaXhKUVVGSkxFTkJRVU1zZDBKQlFYZENMRWRCUVVjc1QwRkJUeXhEUVVGRExFVkJRVVU3V1VGRGVFTXNjVU5CUVhGRE8xbEJRM0pETEVsQlFVa3NlVUpCUVhsQ0xFTkJRVU1zVDBGQlR5eERRVUZETEVWQlFVVTdaMEpCUTNSRExFOUJRVTg3WVVGRFVqdFpRVU5FTEVsQlFVa3NRMEZCUXl4MVFrRkJkVUlzUTBGQlF5eFBRVUZQTEVWQlFVVXNUMEZCVHl4RlFVRkZMSFZDUVVGMVFpeEZRVUZGTEVOQlFVTXNRMEZCUXp0UlFVTTFSU3hEUVVGRExFTkJRVU03VVVGRFJpeFBRVUZQTEVOQlFVTXNWVUZCVlN4RFFVRkRMR2RDUVVGblFpeERRVUZETEZkQlFWY3NRMEZETjBNc1NVRkJTU3hEUVVGRExIZENRVUYzUWl4RlFVTTNRaXhOUVVGTkxFVkJRMDRzUTBGQlF5eHBRa0ZCYVVJc1EwRkJReXhEUVVOd1FpeERRVUZETzFGQlJVWXNTVUZCU1N4RFFVRkRMRzFDUVVGdFFpeEhRVUZITEU5QlFVOHNRMEZCUXl4RlFVRkZPMWxCUTI1RExIRkRRVUZ4UXp0WlFVTnlReXhKUVVGSkxIbENRVUY1UWl4RFFVRkRMRTlCUVU4c1EwRkJReXhGUVVGRk8yZENRVU4wUXl4UFFVRlBPMkZCUTFJN1dVRkRSQ3hOUVVGTkxHVkJRV1VzUjBGQlJ5eEpRVUZKTEVOQlFVTXNhMEpCUVd0Q0xFTkJRVU1zVDBGQlR5eERRVUZETEZOQlFWTXNRMEZCUXl4RFFVRkRPMWxCUTI1RkxHVkJRV1VzUTBGQlF5dzRRa0ZCT0VJc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF6dFpRVU40UkN4SlFVRkpMRU5CUVVNc2EwSkJRV3RDTEVOQlEzSkNMRTlCUVU4c1JVRkRVQ3hQUVVGUExFVkJRMUFzZFVKQlFYVkNMRVZCUVVVc1JVRkRla0lzWTBGQll5eEZRVU5rTEdOQlFXTXNRMEZEWml4RFFVRkRPMUZCUTBvc1EwRkJReXhEUVVGRE8xRkJRMFlzVDBGQlR5eERRVUZETEZWQlFWVXNRMEZCUXl4WFFVRlhMRU5CUVVNc1YwRkJWeXhEUVVONFF5eEpRVUZKTEVOQlFVTXNiVUpCUVcxQ0xFVkJRM2hDTEUxQlFVMHNSVUZEVGl4RFFVRkRMR2xDUVVGcFFpeERRVUZETEVOQlEzQkNMRU5CUVVNN1NVRkRTaXhEUVVGRE8wbEJSVTBzVDBGQlR6dFJRVU5hTEVsQlFVa3NTVUZCU1N4RFFVRkRMSFZDUVVGMVFpeEZRVUZGTzFsQlEyaERMRTlCUVU4c1EwRkJReXhWUVVGVkxFTkJRVU1zWlVGQlpTeERRVUZETEdOQlFXTXNRMEZETDBNc1NVRkJTU3hEUVVGRExIVkNRVUYxUWl4RFFVTTNRaXhEUVVGRE8xTkJRMGc3VVVGRFJDeEpRVUZKTEVsQlFVa3NRMEZCUXl3eVFrRkJNa0lzUlVGQlJUdFpRVU53UXl4UFFVRlBMRU5CUVVNc1ZVRkJWU3hEUVVGRExHMUNRVUZ0UWl4RFFVRkRMR05CUVdNc1EwRkRia1FzU1VGQlNTeERRVUZETERKQ1FVRXlRaXhEUVVOcVF5eERRVUZETzFOQlEwZzdVVUZEUkN4SlFVRkpMRWxCUVVrc1EwRkJReXgzUWtGQmQwSXNSVUZCUlR0WlFVTnFReXhQUVVGUExFTkJRVU1zVlVGQlZTeERRVUZETEdkQ1FVRm5RaXhEUVVGRExHTkJRV01zUTBGRGFFUXNTVUZCU1N4RFFVRkRMSGRDUVVGM1FpeERRVU01UWl4RFFVRkRPMU5CUTBnN1VVRkRSQ3hKUVVGSkxFbEJRVWtzUTBGQlF5eHRRa0ZCYlVJc1JVRkJSVHRaUVVNMVFpeFBRVUZQTEVOQlFVTXNWVUZCVlN4RFFVRkRMRmRCUVZjc1EwRkJReXhqUVVGakxFTkJRVU1zU1VGQlNTeERRVUZETEcxQ1FVRnRRaXhEUVVGRExFTkJRVU03VTBGRGVrVTdTVUZEU0N4RFFVRkRPMGxCUlU4c2FVSkJRV2xDTEVOQlFVTXNVMEZCVXp0UlFVTnFReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEdWQlFXVXNRMEZCUXl4VFFVRlRMRU5CUVVNc1JVRkJSVHRaUVVOd1F5eEpRVUZKTEVOQlFVTXNaVUZCWlN4RFFVRkRMRk5CUVZNc1EwRkJReXhIUVVGSExFbEJRVWtzWTBGQll5eEZRVUZGTEVOQlFVTTdVMEZEZUVRN1VVRkRSQ3hQUVVGUExFbEJRVWtzUTBGQlF5eGxRVUZsTEVOQlFVTXNVMEZCVXl4RFFVRkRMRU5CUVVNN1NVRkRla01zUTBGQlF6dEpRVVZQTEd0Q1FVRnJRaXhEUVVGRExGTkJRVk03VVVGRGJFTXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJReXhuUWtGQlowSXNRMEZCUXl4VFFVRlRMRU5CUVVNc1JVRkJSVHRaUVVOeVF5eEpRVUZKTEVOQlFVTXNaMEpCUVdkQ0xFTkJRVU1zVTBGQlV5eERRVUZETEVkQlFVY3NTVUZCU1N4bFFVRmxMRVZCUVVVc1EwRkJRenRUUVVNeFJEdFJRVU5FTEU5QlFVOHNTVUZCU1N4RFFVRkRMR2RDUVVGblFpeERRVUZETEZOQlFWTXNRMEZCUXl4RFFVRkRPMGxCUXpGRExFTkJRVU03U1VGRlJEczdUMEZGUnp0SlFVVklPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN08wMUJhME5GTzBsQlJVMHNTMEZCU3l4RFFVRkRMREJDUVVFd1FpeERRVU4wUXl4UFFVRnJSQ3hGUVVOc1JDeFBRVUZQTEVWQlExQXNXVUZCYjBJN1VVRkZjRUk3T3pzN096dFZRVTFGTzFGQlJVWXNUVUZCVFN4SFFVRkhMRWRCUTFBc1QwRkJUeXhEUVVGRExFdEJRVXNzUjBGQlJ5eERRVUZETEVOQlFVTTdXVUZEYUVJc1EwRkJReXhEUVVGRExFMUJRVTBzVDBGQlR5eERRVUZETEVsQlFVa3NRMEZCUXl4SFFVRkhMRU5CUVVNc1QwRkJUeXhEUVVGRExFdEJRVXNzUTBGQlF6dFpRVU4yUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hSUVVGUkxFVkJRVVVzVTBGQlV5eEZRVUZGTEZOQlFWTXNSVUZCUlN4VFFVRlRMRVZCUVVVc1IwRkJSeXhGUVVGRkxGTkJRVk1zUlVGQlJTeERRVUZETzFGQlJYQkZMRTFCUVUwc1RVRkJUU3hIUVVGSExFVkJRV2xDTEVOQlFVTTdVVUZGYWtNc1RVRkJUU3hEUVVGRExGTkJRVk1zUjBGQlJ5eFRRVUZUTEVOQlFVTXNSMEZCUnl4RFFVRkRMRk5CUVZNc1EwRkJReXhEUVVGRE8xRkJRelZETEUxQlFVMHNRMEZCUXl4UlFVRlJMRWRCUVVjc1QwRkJUeXhEUVVGRE8xRkJRekZDTEUxQlFVMHNRMEZCUXl4elFrRkJjMElzUjBGQlJ5eHZRa0ZCYjBJc1EwRkJRenRSUVVOeVJDeE5RVUZOTEVOQlFVTXNZVUZCWVN4SFFVRkhMRmxCUVZrc1EwRkJRenRSUVVOd1F5eE5RVUZOTEVOQlFVTXNVMEZCVXl4SFFVRkhMRWRCUVVjc1EwRkJReXhSUVVGUkxFTkJRVU03VVVGRGFFTXNUVUZCVFN4RFFVRkRMRTFCUVUwc1IwRkJSeXhQUVVGUExFTkJRVU1zUzBGQlN5eERRVUZETzFGQlF6bENMRTFCUVUwc1EwRkJReXhSUVVGUkxFZEJRVWNzVDBGQlR5eERRVUZETEU5QlFVOHNRMEZCUXp0UlFVVnNReXh0UmtGQmJVWTdVVUZEYmtZc1RVRkJUU3hEUVVGRExGVkJRVlVzUjBGQlJ5eFBRVUZQTEVOQlFVTXNVMEZCVXl4RFFVRkRPMUZCUlhSRExHZEVRVUZuUkR0UlFVTm9SQ3gzUkVGQmQwUTdVVUZGZUVRc1RVRkJUU3hIUVVGSExFZEJRVWNzVDBGQlR5eERRVUZETEVkQlFVY3NRMEZCUXp0UlFVTjRRaXhOUVVGTkxFTkJRVU1zUjBGQlJ5eEhRVUZITEZOQlFWTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVVMVFpeE5RVUZOTEdGQlFXRXNSMEZCUnl4UFFVRlBMRU5CUVVNc1RVRkJUU3hEUVVGRE8xRkJRM0pETEUxQlFVMHNRMEZCUXl4TlFVRk5MRWRCUVVjc1dVRkJXU3hEUVVGRExHRkJRV0VzUTBGQlF5eERRVUZETzFGQlJUVkRMRTFCUVUwc1dVRkJXU3hIUVVGSExFbEJRVWtzU1VGQlNTeERRVUZETEU5QlFVOHNRMEZCUXl4VFFVRlRMRU5CUVVNc1EwRkJRenRSUVVOcVJDeE5RVUZOTEVOQlFVTXNWVUZCVlN4SFFVRkhMRmxCUVZrc1EwRkJReXhYUVVGWExFVkJRVVVzUTBGQlF6dFJRVVV2UXl4SlFVRkpMRmxCUVZrc1IwRkJSeXhGUVVGRkxFTkJRVU03VVVGRGRFSXNTVUZCU1N4UlFVRlJMRWRCUVVjc1JVRkJSU3hEUVVGRE8xRkJRMnhDTEUxQlFVMHNUMEZCVHl4SFFVRkhMRVZCUVVVc1EwRkJRenRSUVVOdVFpeEpRVUZKTEUxQlFVMHNSMEZCUnl4TFFVRkxMRU5CUVVNN1VVRkRia0lzU1VGQlNTeFBRVUZQTEVOQlFVTXNZMEZCWXl4RlFVRkZPMWxCUXpGQ0xFOUJRVThzUTBGQlF5eGpRVUZqTEVOQlFVTXNSMEZCUnl4RFFVRkRMR0ZCUVdFc1EwRkJReXhGUVVGRk8yZENRVU42UXl4TlFVRk5MRVZCUVVVc1NVRkJTU3hGUVVGRkxFdEJRVXNzUlVGQlJTeEhRVUZITEdGQlFXRXNRMEZCUXp0blFrRkRkRU1zVFVGQlRTeFhRVUZYTEVkQlFVY3NSVUZCUlN4RFFVRkRPMmRDUVVOMlFpeFhRVUZYTEVOQlFVTXNTVUZCU1N4RFFVRkRMRmxCUVZrc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETzJkQ1FVTnlReXhYUVVGWExFTkJRVU1zU1VGQlNTeERRVUZETEZsQlFWa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhEUVVGRE8yZENRVU4wUXl4UFFVRlBMRU5CUVVNc1NVRkJTU3hEUVVGRExGZEJRVmNzUTBGQlF5eERRVUZETzJkQ1FVTXhRaXhKUVVGSkxFbEJRVWtzUzBGQlN5eGpRVUZqTEVWQlFVVTdiMEpCUXpOQ0xGbEJRVmtzUjBGQlJ5eExRVUZMTEVOQlFVTTdiMEpCUTNKQ0xFbEJRVWtzV1VGQldTeERRVUZETEU5QlFVOHNRMEZCUXl3d1FrRkJNRUlzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RlFVRkZPM2RDUVVNelJDeE5RVUZOTEVkQlFVY3NTVUZCU1N4RFFVRkRPM0ZDUVVObU8ybENRVU5HTzJkQ1FVTkVMRWxCUVVrc1NVRkJTU3hMUVVGTExGTkJRVk1zUlVGQlJUdHZRa0ZEZEVJc1VVRkJVU3hIUVVGSExFdEJRVXNzUTBGQlF6dHBRa0ZEYkVJN1dVRkRTQ3hEUVVGRExFTkJRVU1zUTBGQlF6dFRRVU5LTzFGQlJVUXNUVUZCVFN4RFFVRkRMRkZCUVZFc1IwRkJSeXhaUVVGWkxFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTTdVVUZGZWtNc1NVRkJTU3hoUVVGaExFdEJRVXNzVFVGQlRTeEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMR2xEUVVGcFF5eEZRVUZGTzFsQlEzcEZMRTFCUVUwc1kwRkJZeXhIUVVGSExFbEJRVWtzUTBGQlF5eHBRa0ZCYVVJc1EwRkJReXhQUVVGUExFTkJRVU1zVTBGQlV5eERRVUZETEVOQlFVTTdXVUZEYWtVc1RVRkJUU3hSUVVGUkxFZEJRVWNzVFVGQlRTeGpRVUZqTEVOQlFVTXNjVUpCUVhGQ0xFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdXVUZEYkVVc1NVRkJTU3hEUVVGRExGRkJRVkVzUlVGQlJUdG5Ra0ZEWWl4SlFVRkpMRU5CUVVNc1dVRkJXU3hEUVVGRExGRkJRVkVzUTBGRGVFSXNjVWRCUVhGSExFTkJRM1JITEVOQlFVTTdZVUZEU0R0cFFrRkJUVHRuUWtGRFRDeE5RVUZOTERKQ1FVRXlRaXhIUVVGSExFMUJRVTBzWTBGQll5eERRVUZETERKQ1FVRXlRaXhEUVVGRE8yZENRVU55Uml4TlFVRk5MRmRCUVZjc1IwRkJSeXd5UWtGQk1rSXNRMEZCUXl4WFFVRlhMRU5CUVVNN1owSkJSVFZFTEVsQlFVa3NWMEZCVnl4RlFVRkZPMjlDUVVObUxFMUJRVTBzVlVGQlZTeEhRVUZITEVsQlFVa3NZMEZCWXp0dlFrRkRia01zVjBGQlZ6dHZRa0ZEV0N3eVFrRkJNa0lzUlVGRE0wSXNTVUZCU1N4RFFVRkRMRmxCUVZrc1EwRkRiRUlzUTBGQlF6dHZRa0ZEUml4TlFVRk5MRTlCUVU4c1IwRkJjMElzVlVGQlZUdDVRa0ZETVVNc1owSkJRV2RDTEVWQlJXWXNRMEZCUXp0dlFrRkZUQ3huUkVGQlowUTdiMEpCUTJoRUxFbEJRVWtzWTBGQll5eEpRVUZKTEU5QlFVOHNSVUZCUlR0M1FrRkROMElzTUVaQlFUQkdPM2RDUVVNeFJpeHRSMEZCYlVjN2QwSkJRMjVITEUxQlFVMHNZMEZCWXl4SFFVRkhPelJDUVVOeVFpeGpRVUZqT3pSQ1FVTmtMSEZDUVVGeFFqczBRa0ZEY2tJc1owSkJRV2RDTzNsQ1FVTnFRaXhEUVVGRE8zZENRVU5HTEV0QlFVc3NUVUZCVFN4SlFVRkpMRWxCUVVrc1QwRkJUeXhEUVVGRExGbEJRVmtzUlVGQlJUczBRa0ZEZGtNc1NVRkJTU3hqUVVGakxFTkJRVU1zVVVGQlVTeERRVUZETEVsQlFVa3NRMEZCUXl4RlFVRkZPMmREUVVOcVF5eE5RVUZOTEZkQlFWY3NSMEZCUnl4RlFVRkZMRU5CUVVNN1owTkJRM1pDTEZkQlFWY3NRMEZCUXl4SlFVRkpMRU5CUVVNc1dVRkJXU3hEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETEVOQlFVTTdaME5CUTNKRExGZEJRVmNzUTBGQlF5eEpRVUZKTEVOQlFVTXNXVUZCV1N4RFFVRkRMRTlCUVU4c1EwRkJReXhaUVVGWkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMmREUVVNelJDeFBRVUZQTEVOQlFVTXNTVUZCU1N4RFFVRkRMRmRCUVZjc1EwRkJReXhEUVVGRE96WkNRVU16UWp0NVFrRkRSanR4UWtGRFJqdHZRa0ZEUkN3clJrRkJLMFk3YjBKQlF5OUdMRWxCUVVrc1YwRkJWeXhKUVVGSkxFOUJRVThzUlVGQlJUdDNRa0ZETVVJc1RVRkJUU3hEUVVGRExGTkJRVk1zUjBGQlJ5eFBRVUZQTEVOQlFVTXNVMEZCVXl4RFFVRkRPM0ZDUVVOMFF6dHBRa0ZEUmp0aFFVTkdPMU5CUTBZN1VVRkZSQ3hOUVVGTkxFTkJRVU1zVDBGQlR5eEhRVUZITEVsQlFVa3NRMEZCUXl4VFFVRlRMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU03VVVGRmVrTXNaVUZCWlR0UlFVTm1MRTFCUVUwc1MwRkJTeXhIUVVGSExFOUJRVThzUTBGQlF5eEpRVUZKTEV0QlFVc3NaMEpCUVdkQ0xFTkJRVU03VVVGRGFFUXNUVUZCVFN4RFFVRkRMRTFCUVUwc1IwRkJSeXhUUVVGVExFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTTdVVUZGYWtNc2JVTkJRVzFETzFGQlEyNURMRTFCUVUwc1kwRkJZeXhIUVVGSExFOUJRVThzUTBGQlF5eFBRVUZQTEV0QlFVc3NRMEZCUXl4RFFVRkRPMUZCUXpkRExFMUJRVTBzVjBGQlZ5eEhRVUZITEU5QlFVOHNRMEZCUXl4SlFVRkpMRXRCUVVzc1YwRkJWeXhEUVVGRE8xRkJRMnBFTEUxQlFVMHNRMEZCUXl4WlFVRlpMRWRCUVVjc1UwRkJVeXhEUVVGRExHTkJRV01zUTBGQlF5eERRVUZETzFGQlEyaEVMRTFCUVUwc1EwRkJReXhoUVVGaExFZEJRVWNzVTBGQlV5eERRVUZETEZkQlFWY3NRMEZCUXl4RFFVRkRPMUZCUlRsRExEWkRRVUUyUXp0UlFVTTNReXhKUVVGSkxHZENRVUZuUWl4RFFVRkRPMUZCUTNKQ0xFbEJRVWtzWVVGQllTeERRVUZETzFGQlEyeENMRWxCUVVrc1QwRkJUeXhEUVVGRExGTkJRVk1zUlVGQlJUdFpRVU55UWl4TlFVRk5MR1ZCUVdVc1IwRkJSeXhKUVVGSkxFZEJRVWNzUTBGQlF5eFBRVUZQTEVOQlFVTXNVMEZCVXl4RFFVRkRMRU5CUVVNN1dVRkRia1FzWjBKQlFXZENMRWRCUVVjc1pVRkJaU3hEUVVGRExFMUJRVTBzUTBGQlF6dFRRVU16UXp0UlFVTkVMRWxCUVVrc1QwRkJUeXhEUVVGRExGZEJRVmNzUlVGQlJUdFpRVU4yUWl4TlFVRk5MR2xDUVVGcFFpeEhRVUZITEVsQlFVa3NSMEZCUnl4RFFVRkRMRTlCUVU4c1EwRkJReXhYUVVGWExFTkJRVU1zUTBGQlF6dFpRVU4yUkN4aFFVRmhMRWRCUVVjc2FVSkJRV2xDTEVOQlFVTXNUVUZCVFN4RFFVRkRPMU5CUXpGRE8xRkJRMFFzVFVGQlRTeERRVUZETEdsQ1FVRnBRaXhIUVVGSExGbEJRVmtzUTBGQlF5eG5Ra0ZCWjBJc1EwRkJReXhEUVVGRE8xRkJRekZFTEUxQlFVMHNRMEZCUXl4alFVRmpMRWRCUVVjc1dVRkJXU3hEUVVGRExHRkJRV0VzUTBGQlF5eERRVUZETzFGQlJYQkVMSGxDUVVGNVFqdFJRVU42UWl4NVJVRkJlVVU3VVVGRGVrVXNPRUpCUVRoQ08xRkJRemxDTEUxQlFVMHNWMEZCVnl4SFFVRkhMRTlCUVU4c1EwRkJReXhYUVVGWExFTkJRVU03VVVGRGVFTXNUVUZCVFN4RFFVRkRMRmxCUVZrc1IwRkJSeXhaUVVGWkxFTkJRVU1zVjBGQlZ5eERRVUZETEVOQlFVTTdVVUZGYUVRc2EwVkJRV3RGTzFGQlEyeEZMR2xHUVVGcFJqdFJRVU5xUml4cFFrRkJhVUk3VVVGRGFrSXNjVWRCUVhGSE8xRkJRM0pITEUxQlFVMHNRMEZCUXl4aFFVRmhMRWRCUVVjc1QwRkJUeXhEUVVGRExFbEJRVWtzUTBGQlF6dFJRVVZ3UXpzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPMVZCTUVORk8xRkJRMFlzVFVGQlRTeERRVUZETEdGQlFXRXNSMEZCUnl4VFFVRlRMRU5CUVVNc1IwRkJSeXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETzFGQlF6RkRMRTFCUVUwc1EwRkJReXhsUVVGbExFZEJRVWNzVDBGQlR5eERRVUZETEdGQlFXRXNRMEZCUXp0UlFVTXZReXhOUVVGTkxFTkJRVU1zWlVGQlpTeEhRVUZITEZsQlFWa3NRMEZEYmtNc1NVRkJTU3hEUVVGRExGTkJRVk1zUTBGQlF5eFBRVUZQTEVOQlFVTXNZMEZCWXl4RFFVRkRMRU5CUTNaRExFTkJRVU03VVVGRlJpeEpRVUZKTEVOQlFVTXNXVUZCV1N4RFFVRkRMRlZCUVZVc1EwRkJReXhsUVVGbExFVkJRVVVzVFVGQlRTeERRVUZETEVOQlFVTTdTVUZEZUVRc1EwRkJRenRKUVVWUExFdEJRVXNzUTBGQlF5eDFRa0ZCZFVJc1EwRkRia01zVDBGQkswTXNSVUZETDBNc1QwRkJUeXhGUVVOUUxGbEJRVzlDTzFGQlJYQkNPenM3T3pzN1ZVRk5SVHRSUVVWR0xEUkNRVUUwUWp0UlFVTTFRaXhwUkVGQmFVUTdVVUZGYWtRN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPMVZCTWtSRk8xRkJSVVlzVFVGQlRTeGpRVUZqTEVkQlFVY3NUMEZCVHl4RFFVRkRMRlZCUVZVc1EwRkJRenRSUVVNeFF5eE5RVUZOTEd0Q1FVRnJRaXhIUVVGSExFOUJRVThzUTBGQlF5eFZRVUZWTEVOQlFVTTdVVUZGT1VNc1RVRkJUU3hIUVVGSExFZEJRMUFzVDBGQlR5eERRVUZETEV0QlFVc3NSMEZCUnl4RFFVRkRMRU5CUVVNN1dVRkRhRUlzUTBGQlF5eERRVUZETEUxQlFVMHNUMEZCVHl4RFFVRkRMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zVDBGQlR5eERRVUZETEV0QlFVc3NRMEZCUXp0WlFVTjJReXhEUVVGRExFTkJRVU1zUlVGQlJTeFJRVUZSTEVWQlFVVXNVMEZCVXl4RlFVRkZMRk5CUVZNc1JVRkJSU3hUUVVGVExFVkJRVVVzUTBGQlF6dFJRVU53UkN4TlFVRk5MRmxCUVZrc1IwRkJhVUk3V1VGRGFrTXNVMEZCVXl4RlFVRkZMRk5CUVZNc1EwRkJReXhIUVVGSExFTkJRVU1zVTBGQlV5eERRVUZETzFsQlEyNURMRkZCUVZFc1JVRkJSU3hQUVVGUE8xbEJRMnBDTEdWQlFXVXNSVUZCUlN4VFFVRlRMRU5CUVVNc1QwRkJUeXhEUVVGRExFZEJRVWNzUTBGQlF6dFpRVU4yUXl4alFVRmpMRVZCUVVVc1QwRkJUeXhEUVVGRExGTkJRVk03V1VGRGFrTXNaVUZCWlN4RlFVRkZMRk5CUVZNc1EwRkJReXhQUVVGUExFTkJRVU1zVjBGQlZ5eERRVUZETzFsQlF5OURMR05CUVdNc1JVRkJSU3hKUVVGSk8xbEJRM0JDTEhOQ1FVRnpRaXhGUVVGRkxHOUNRVUZ2UWp0WlFVTTFReXhoUVVGaExFVkJRVVVzV1VGQldUdFpRVU16UWl4VFFVRlRMRVZCUVVVc1IwRkJSeXhEUVVGRExGRkJRVkU3V1VGRGRrSXNUVUZCVFN4RlFVRkZMRTlCUVU4c1EwRkJReXhMUVVGTE8xbEJRM0pDTEZGQlFWRXNSVUZCUlN4UFFVRlBMRU5CUVVNc1QwRkJUenRaUVVONlFpeGxRVUZsTEVWQlFVVXNZMEZCWXp0WlFVTXZRaXh2UWtGQmIwSXNSVUZCUlN4WlFVRlpMRU5CUVVNc2EwSkJRV3RDTEVOQlFVTTdXVUZEZEVRc1ZVRkJWU3hGUVVGRkxFbEJRVWtzU1VGQlNTeERRVUZETEU5QlFVOHNRMEZCUXl4VFFVRlRMRU5CUVVNc1EwRkJReXhYUVVGWExFVkJRVVU3VTBGRGRFUXNRMEZCUXp0UlFVVkdMRWxCUVVrc1EwRkJReXhaUVVGWkxFTkJRVU1zVlVGQlZTeERRVUZETEdkQ1FVRm5RaXhGUVVGRkxGbEJRVmtzUTBGQlF5eERRVUZETzBsQlF5OUVMRU5CUVVNN1NVRkZSRHM3VFVGRlJUdEpRVVZOTEV0QlFVc3NRMEZCUXl4dFFrRkJiVUlzUTBGREwwSXNUMEZCT0VNc1JVRkRPVU1zVFVGQlRUdFJRVVZPTEUxQlFVMHNaVUZCWlN4SFFVRkhMRWxCUVVrc1EwRkJReXhyUWtGQmEwSXNRMEZCUXl4UFFVRlBMRU5CUVVNc1UwRkJVeXhEUVVGRExFTkJRVU03VVVGRGJrVXNTVUZCU1R0WlFVTkdMRTFCUVUwc2IwSkJRVzlDTEVkQlFVY3NaVUZCWlN4RFFVRkRMRzlDUVVGdlFpeERRVUZETzFsQlEyeEZMRTFCUVUwc1VVRkJVU3hIUVVGSExFMUJRVTBzYjBKQlFXOUNMRU5CUVVNc1pVRkJaU3hGUVVGRkxFTkJRVU03V1VGRE9VUXNUVUZCVFN4WFFVRlhMRWRCUVVjc1RVRkJUU3h2UWtGQmIwSXNRMEZCUXl4alFVRmpMRVZCUVVVc1EwRkJRenRaUVVOb1JTeEpRVUZKTEVOQlFVTXNXVUZCV1N4RFFVRkRMRmRCUVZjc1EwRkRNMElzV1VGQldTeERRVUZETEZGQlFWRXNRMEZCUXl4RlFVTjBRaXhaUVVGWkxFTkJRVU1zVjBGQlZ5eERRVUZETEVOQlF6RkNMRU5CUVVNN1dVRkRSaXhKUVVGSkxFTkJRVU1zV1VGQldTeERRVUZETEZWQlFWVXNRMEZCUXl4blFrRkJaMElzUlVGQlJTeE5RVUZOTEVOQlFVTXNRMEZCUXp0VFFVTjRSRHRSUVVGRExFOUJRVThzUjBGQlJ5eEZRVUZGTzFsQlExbzdPenM3T3pzN1kwRlBSVHRaUVVOR0xFbEJRVWtzUTBGQlF5eFpRVUZaTEVOQlFVTXNVVUZCVVN4RFFVTjRRaXh0UTBGQmJVTTdaMEpCUTJwRExITkVRVUZ6UkR0blFrRkRkRVFzUjBGQlJ5eERRVUZETEVsQlFVazdaMEpCUTFJc1IwRkJSeXhEUVVGRExFOUJRVTg3WjBKQlExZ3NTVUZCU1R0blFrRkRTaXhIUVVGSExFTkJRVU1zUzBGQlN5eERRVU5hTEVOQlFVTTdXVUZEUml4TlFVRk5MRU5CUVVNc1dVRkJXU3hIUVVGSExGTkJRVk1zUTBGQlF6dFpRVU5vUXl4SlFVRkpMRU5CUVVNc1dVRkJXU3hEUVVGRExGVkJRVlVzUTBGQlF5eG5Ra0ZCWjBJc1JVRkJSU3hOUVVGTkxFTkJRVU1zUTBGQlF6dFRRVU40UkR0SlFVTklMRU5CUVVNN1NVRkZSRHM3T3pzN096czdUMEZSUnp0SlFVTkxMRWxCUVVrc1EwRkJReXhaUVVFd1FqdFJRVU55UXl4UFFVRlBMRmxCUVZrc1MwRkJTeXhSUVVGUkxFTkJRVU03U1VGRGJrTXNRMEZCUXp0SlFVVkVMRFJDUVVFMFFqdEpRVU53UWl4TFFVRkxMRU5CUVVNc2EwSkJRV3RDTEVOQlF6bENMRTlCUVRCRExFVkJRekZETEU5QlFVOHNSVUZEVUN4WlFVRlpMRVZCUTFvc1kwRkJZeXhGUVVOa0xHTkJRV003VVVGRlpEczdPenM3T3pzN1ZVRlJSVHRSUVVWR0xFMUJRVTBzUjBGQlJ5eEhRVU5RTEU5QlFVOHNRMEZCUXl4TFFVRkxMRWRCUVVjc1EwRkJReXhEUVVGRE8xbEJRMmhDTEVOQlFVTXNRMEZCUXl4TlFVRk5MRTlCUVU4c1EwRkJReXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEU5QlFVOHNRMEZCUXl4TFFVRkxMRU5CUVVNN1dVRkRka01zUTBGQlF5eERRVUZETEVWQlFVVXNVVUZCVVN4RlFVRkZMRk5CUVZNc1JVRkJSU3hUUVVGVExFVkJRVVVzVTBGQlV5eEZRVUZGTEVOQlFVTTdVVUZGY0VRc1RVRkJUU3hOUVVGTkxFZEJRVWNzUlVGQmEwSXNRMEZCUXp0UlFVVnNReXhOUVVGTkxFTkJRVU1zVTBGQlV5eEhRVUZITEZOQlFWTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1UwRkJVeXhEUVVGRExFTkJRVU03VVVGRE5VTXNUVUZCVFN4RFFVRkRMRkZCUVZFc1IwRkJSeXhQUVVGUExFTkJRVU03VVVGRE1VSXNUVUZCVFN4RFFVRkRMSE5DUVVGelFpeEhRVUZITEc5Q1FVRnZRaXhEUVVGRE8xRkJRM0pFTEUxQlFVMHNRMEZCUXl4aFFVRmhMRWRCUVVjc1dVRkJXU3hEUVVGRE8xRkJRM0JETEUxQlFVMHNRMEZCUXl4VFFVRlRMRWRCUVVjc1IwRkJSeXhEUVVGRExGRkJRVkVzUTBGQlF6dFJRVU5vUXl4TlFVRk5MRU5CUVVNc1RVRkJUU3hIUVVGSExFOUJRVThzUTBGQlF5eExRVUZMTEVOQlFVTTdVVUZET1VJc1RVRkJUU3hEUVVGRExGRkJRVkVzUjBGQlJ5eFBRVUZQTEVOQlFVTXNUMEZCVHl4RFFVRkRPMUZCUld4RExHMUdRVUZ0Ump0UlFVTnVSaXhOUVVGTkxFTkJRVU1zVlVGQlZTeEhRVUZITEU5QlFVOHNRMEZCUXl4VFFVRlRMRU5CUVVNN1VVRkZkRU1zVFVGQlRTeFJRVUZSTEVkQlFVY3NUMEZCVHl4RFFVRkRMRk5CUVZNc1EwRkJRenRSUVVOdVF5eE5RVUZOTEVOQlFVTXNVMEZCVXl4SFFVRkhMRk5CUVZNc1EwRkJReXhSUVVGUkxFTkJRVU1zUTBGQlF6dFJRVVYyUXl4TlFVRk5MRWRCUVVjc1IwRkJSeXhQUVVGUExFTkJRVU1zUjBGQlJ5eERRVUZETzFGQlEzaENMRTFCUVUwc1EwRkJReXhIUVVGSExFZEJRVWNzVTBGQlV5eERRVUZETEVkQlFVY3NRMEZCUXl4RFFVRkRPMUZCUlRWQ0xFMUJRVTBzWVVGQllTeEhRVUZITEU5QlFVOHNRMEZCUXl4TlFVRk5MRU5CUVVNN1VVRkRja01zVFVGQlRTeERRVUZETEUxQlFVMHNSMEZCUnl4WlFVRlpMRU5CUVVNc1lVRkJZU3hEUVVGRExFTkJRVU03VVVGRk5VTXNNRVJCUVRCRU8xRkJRekZFTERaRlFVRTJSVHRSUVVNM1JTd3lSVUZCTWtVN1VVRkRNMFVzUlVGQlJUdFJRVU5HTEhGQ1FVRnhRanRSUVVOeVFpd3dRa0ZCTUVJN1VVRkRNVUlzYzBOQlFYTkRPMUZCUTNSRExFbEJRVWs3VVVGRFNpdzBRMEZCTkVNN1VVRkZOVU1zVFVGQlRTeGpRVUZqTEVkQlFVY3NUMEZCVHl4RFFVRkRMRlZCUVZVc1EwRkJRenRSUVVNeFF5eE5RVUZOTEVOQlFVTXNaVUZCWlN4SFFVRkhMR05CUVdNc1EwRkJRenRSUVVWNFF5eE5RVUZOTEd0Q1FVRnJRaXhIUVVGSExFOUJRVThzUTBGQlF5eFZRVUZWTEVOQlFVTTdVVUZET1VNc1RVRkJUU3hEUVVGRExHOUNRVUZ2UWl4SFFVRkhMRmxCUVZrc1EwRkJReXhyUWtGQmEwSXNRMEZCUXl4RFFVRkRPMUZCUlM5RUxFMUJRVTBzV1VGQldTeEhRVUZITEVsQlFVa3NTVUZCU1N4RFFVRkRMRTlCUVU4c1EwRkJReXhUUVVGVExFTkJRVU1zUTBGQlF6dFJRVU5xUkN4TlFVRk5MRU5CUVVNc1ZVRkJWU3hIUVVGSExGbEJRVmtzUTBGQlF5eFhRVUZYTEVWQlFVVXNRMEZCUXp0UlFVVXZReXhOUVVGTkxFOUJRVThzUjBGQlJ5eEZRVUZGTEVOQlFVTTdVVUZEYmtJc1NVRkJTU3hSUVVGUkxFZEJRVWNzUlVGQlJTeERRVUZETzFGQlEyeENMRWxCUVVrc1QwRkJUeXhEUVVGRExHVkJRV1VzUlVGQlJUdFpRVU16UWl4UFFVRlBMRU5CUVVNc1pVRkJaU3hEUVVGRExFZEJRVWNzUTBGQlF5eGpRVUZqTEVOQlFVTXNSVUZCUlR0blFrRkRNME1zVFVGQlRTeEZRVUZGTEVsQlFVa3NSVUZCUlN4TFFVRkxMRVZCUVVVc1IwRkJSeXhqUVVGakxFTkJRVU03WjBKQlEzWkRMRTFCUVUwc1YwRkJWeXhIUVVGSExFVkJRVVVzUTBGQlF6dG5Ra0ZEZGtJc1YwRkJWeXhEUVVGRExFbEJRVWtzUTBGQlF5eFpRVUZaTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1EwRkJRenRuUWtGRGNrTXNWMEZCVnl4RFFVRkRMRWxCUVVrc1EwRkJReXhaUVVGWkxFTkJRVU1zUzBGQlN5eERRVUZETEVOQlFVTXNRMEZCUXp0blFrRkRkRU1zVDBGQlR5eERRVUZETEVsQlFVa3NRMEZCUXl4WFFVRlhMRU5CUVVNc1EwRkJRenRuUWtGRE1VSXNTVUZCU1N4SlFVRkpMRU5CUVVNc1YwRkJWeXhGUVVGRkxFdEJRVXNzVlVGQlZTeEZRVUZGTzI5Q1FVTnlReXhSUVVGUkxFZEJRVWNzUzBGQlN5eERRVUZETzJsQ1FVTnNRanRaUVVOSUxFTkJRVU1zUTBGQlF5eERRVUZETzFOQlEwbzdVVUZEUkN4TlFVRk5MRU5CUVVNc1QwRkJUeXhIUVVGSExFbEJRVWtzUTBGQlF5eFRRVUZUTEVOQlFVTXNUMEZCVHl4RFFVRkRMRU5CUVVNN1VVRkRla01zVFVGQlRTeERRVUZETEZGQlFWRXNSMEZCUnl4WlFVRlpMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU03VVVGRmVrTXNTVUZCU1N4alFVRmpMRVZCUVVVN1dVRkRiRUlzU1VGQlNTeERRVUZETEcxQ1FVRnRRaXhEUVVGRExFOUJRVThzUlVGQlJTeE5RVUZOTEVOQlFVTXNRMEZCUXp0VFFVTXpRenRoUVVGTkxFbEJRVWtzWTBGQll5eEpRVUZKTEVsQlFVa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1QwRkJUeXhEUVVGRExFbEJRVWtzUTBGQlF5eEZRVUZGTzFsQlEzQkVMRWxCUVVrc1EwRkJReXh0UWtGQmJVSXNRMEZCUXl4UFFVRlBMRVZCUVVVc1RVRkJUU3hEUVVGRExFTkJRVU03VTBGRE0wTTdZVUZCVFR0WlFVTk1MRWxCUVVrc1EwRkJReXhaUVVGWkxFTkJRVU1zVlVGQlZTeERRVUZETEdkQ1FVRm5RaXhGUVVGRkxFMUJRVTBzUTBGQlF5eERRVUZETzFOQlEzaEVPMGxCUTBnc1EwRkJRenREUVVOR0luMD0iLCJpbXBvcnQgeyBpbmNyZW1lbnRlZEV2ZW50T3JkaW5hbCB9IGZyb20gXCIuLi9saWIvZXh0ZW5zaW9uLXNlc3Npb24tZXZlbnQtb3JkaW5hbFwiO1xuaW1wb3J0IHsgZXh0ZW5zaW9uU2Vzc2lvblV1aWQgfSBmcm9tIFwiLi4vbGliL2V4dGVuc2lvbi1zZXNzaW9uLXV1aWRcIjtcbmltcG9ydCB7IGJvb2xUb0ludCwgZXNjYXBlU3RyaW5nLCBlc2NhcGVVcmwgfSBmcm9tIFwiLi4vbGliL3N0cmluZy11dGlsc1wiO1xuZXhwb3J0IGNsYXNzIEphdmFzY3JpcHRJbnN0cnVtZW50IHtcbiAgICBjb25zdHJ1Y3RvcihkYXRhUmVjZWl2ZXIpIHtcbiAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIgPSBkYXRhUmVjZWl2ZXI7XG4gICAgfVxuICAgIHJ1bihjcmF3bElEKSB7XG4gICAgICAgIGNvbnN0IHByb2Nlc3NDYWxsc0FuZFZhbHVlcyA9IChkYXRhLCBzZW5kZXIpID0+IHtcbiAgICAgICAgICAgIGNvbnN0IHVwZGF0ZSA9IHt9O1xuICAgICAgICAgICAgdXBkYXRlLmNyYXdsX2lkID0gY3Jhd2xJRDtcbiAgICAgICAgICAgIHVwZGF0ZS5leHRlbnNpb25fc2Vzc2lvbl91dWlkID0gZXh0ZW5zaW9uU2Vzc2lvblV1aWQ7XG4gICAgICAgICAgICB1cGRhdGUuZXZlbnRfb3JkaW5hbCA9IGluY3JlbWVudGVkRXZlbnRPcmRpbmFsKCk7XG4gICAgICAgICAgICB1cGRhdGUucGFnZV9zY29wZWRfZXZlbnRfb3JkaW5hbCA9IGRhdGEub3JkaW5hbDtcbiAgICAgICAgICAgIHVwZGF0ZS53aW5kb3dfaWQgPSBzZW5kZXIudGFiLndpbmRvd0lkO1xuICAgICAgICAgICAgdXBkYXRlLnRhYl9pZCA9IHNlbmRlci50YWIuaWQ7XG4gICAgICAgICAgICB1cGRhdGUuZnJhbWVfaWQgPSBzZW5kZXIuZnJhbWVJZDtcbiAgICAgICAgICAgIHVwZGF0ZS5zY3JpcHRfdXJsID0gZXNjYXBlVXJsKGRhdGEuc2NyaXB0VXJsKTtcbiAgICAgICAgICAgIHVwZGF0ZS5zY3JpcHRfbGluZSA9IGVzY2FwZVN0cmluZyhkYXRhLnNjcmlwdExpbmUpO1xuICAgICAgICAgICAgdXBkYXRlLnNjcmlwdF9jb2wgPSBlc2NhcGVTdHJpbmcoZGF0YS5zY3JpcHRDb2wpO1xuICAgICAgICAgICAgdXBkYXRlLmZ1bmNfbmFtZSA9IGVzY2FwZVN0cmluZyhkYXRhLmZ1bmNOYW1lKTtcbiAgICAgICAgICAgIHVwZGF0ZS5zY3JpcHRfbG9jX2V2YWwgPSBlc2NhcGVTdHJpbmcoZGF0YS5zY3JpcHRMb2NFdmFsKTtcbiAgICAgICAgICAgIHVwZGF0ZS5jYWxsX3N0YWNrID0gZXNjYXBlU3RyaW5nKGRhdGEuY2FsbFN0YWNrKTtcbiAgICAgICAgICAgIHVwZGF0ZS5zeW1ib2wgPSBlc2NhcGVTdHJpbmcoZGF0YS5zeW1ib2wpO1xuICAgICAgICAgICAgdXBkYXRlLm9wZXJhdGlvbiA9IGVzY2FwZVN0cmluZyhkYXRhLm9wZXJhdGlvbik7XG4gICAgICAgICAgICB1cGRhdGUudmFsdWUgPSBlc2NhcGVTdHJpbmcoZGF0YS52YWx1ZSk7XG4gICAgICAgICAgICB1cGRhdGUudGltZV9zdGFtcCA9IGRhdGEudGltZVN0YW1wO1xuICAgICAgICAgICAgdXBkYXRlLmluY29nbml0byA9IGJvb2xUb0ludChzZW5kZXIudGFiLmluY29nbml0byk7XG4gICAgICAgICAgICAvLyBkb2N1bWVudF91cmwgaXMgdGhlIGN1cnJlbnQgZnJhbWUncyBkb2N1bWVudCBocmVmXG4gICAgICAgICAgICAvLyB0b3BfbGV2ZWxfdXJsIGlzIHRoZSB0b3AtbGV2ZWwgZnJhbWUncyBkb2N1bWVudCBocmVmXG4gICAgICAgICAgICB1cGRhdGUuZG9jdW1lbnRfdXJsID0gZXNjYXBlVXJsKHNlbmRlci51cmwpO1xuICAgICAgICAgICAgdXBkYXRlLnRvcF9sZXZlbF91cmwgPSBlc2NhcGVVcmwoc2VuZGVyLnRhYi51cmwpO1xuICAgICAgICAgICAgaWYgKGRhdGEub3BlcmF0aW9uID09PSBcImNhbGxcIiAmJiBkYXRhLmFyZ3MubGVuZ3RoID4gMCkge1xuICAgICAgICAgICAgICAgIHVwZGF0ZS5hcmd1bWVudHMgPSBlc2NhcGVTdHJpbmcoSlNPTi5zdHJpbmdpZnkoZGF0YS5hcmdzKSk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICB0aGlzLmRhdGFSZWNlaXZlci5zYXZlUmVjb3JkKFwiamF2YXNjcmlwdFwiLCB1cGRhdGUpO1xuICAgICAgICB9O1xuICAgICAgICAvLyBMaXN0ZW4gZm9yIG1lc3NhZ2VzIGZyb20gY29udGVudCBzY3JpcHQgaW5qZWN0ZWQgdG8gaW5zdHJ1bWVudCBKYXZhU2NyaXB0IEFQSVxuICAgICAgICB0aGlzLm9uTWVzc2FnZUxpc3RlbmVyID0gKG1zZywgc2VuZGVyKSA9PiB7XG4gICAgICAgICAgICAvLyBjb25zb2xlLmRlYnVnKFwiamF2YXNjcmlwdC1pbnN0cnVtZW50YXRpb24gYmFja2dyb3VuZCBsaXN0ZW5lciAtIG1zZywgc2VuZGVyLCBzZW5kUmVwbHlcIiwgbXNnLCBzZW5kZXIsIHNlbmRSZXBseSk7XG4gICAgICAgICAgICBpZiAobXNnLm5hbWVzcGFjZSAmJiBtc2cubmFtZXNwYWNlID09PSBcImphdmFzY3JpcHQtaW5zdHJ1bWVudGF0aW9uXCIpIHtcbiAgICAgICAgICAgICAgICBzd2l0Y2ggKG1zZy50eXBlKSB7XG4gICAgICAgICAgICAgICAgICAgIGNhc2UgXCJsb2dDYWxsXCI6XG4gICAgICAgICAgICAgICAgICAgIGNhc2UgXCJsb2dWYWx1ZVwiOlxuICAgICAgICAgICAgICAgICAgICAgICAgcHJvY2Vzc0NhbGxzQW5kVmFsdWVzKG1zZy5kYXRhLCBzZW5kZXIpO1xuICAgICAgICAgICAgICAgICAgICAgICAgYnJlYWs7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuICAgICAgICB9O1xuICAgICAgICBicm93c2VyLnJ1bnRpbWUub25NZXNzYWdlLmFkZExpc3RlbmVyKHRoaXMub25NZXNzYWdlTGlzdGVuZXIpO1xuICAgIH1cbiAgICBjbGVhbnVwKCkge1xuICAgICAgICBpZiAodGhpcy5vbk1lc3NhZ2VMaXN0ZW5lcikge1xuICAgICAgICAgICAgYnJvd3Nlci5ydW50aW1lLm9uTWVzc2FnZS5yZW1vdmVMaXN0ZW5lcih0aGlzLm9uTWVzc2FnZUxpc3RlbmVyKTtcbiAgICAgICAgfVxuICAgIH1cbn1cbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWFtRjJZWE5qY21sd2RDMXBibk4wY25WdFpXNTBMbXB6SWl3aWMyOTFjbU5sVW05dmRDSTZJaUlzSW5OdmRYSmpaWE1pT2xzaUxpNHZMaTR2TGk0dmMzSmpMMkpoWTJ0bmNtOTFibVF2YW1GMllYTmpjbWx3ZEMxcGJuTjBjblZ0Wlc1MExuUnpJbDBzSW01aGJXVnpJanBiWFN3aWJXRndjR2x1WjNNaU9pSkJRVU5CTEU5QlFVOHNSVUZCUlN4MVFrRkJkVUlzUlVGQlJTeE5RVUZOTEhkRFFVRjNReXhEUVVGRE8wRkJRMnBHTEU5QlFVOHNSVUZCUlN4dlFrRkJiMElzUlVGQlJTeE5RVUZOTEN0Q1FVRXJRaXhEUVVGRE8wRkJRM0pGTEU5QlFVOHNSVUZCUlN4VFFVRlRMRVZCUVVVc1dVRkJXU3hGUVVGRkxGTkJRVk1zUlVGQlJTeE5RVUZOTEhGQ1FVRnhRaXhEUVVGRE8wRkJSM3BGTEUxQlFVMHNUMEZCVHl4dlFrRkJiMEk3U1VGSkwwSXNXVUZCV1N4WlFVRlpPMUZCUTNSQ0xFbEJRVWtzUTBGQlF5eFpRVUZaTEVkQlFVY3NXVUZCV1N4RFFVRkRPMGxCUTI1RExFTkJRVU03U1VGRlRTeEhRVUZITEVOQlFVTXNUMEZCVHp0UlFVTm9RaXhOUVVGTkxIRkNRVUZ4UWl4SFFVRkhMRU5CUVVNc1NVRkJTU3hGUVVGRkxFMUJRWEZDTEVWQlFVVXNSVUZCUlR0WlFVTTFSQ3hOUVVGTkxFMUJRVTBzUjBGQlJ5eEZRVUY1UWl4RFFVRkRPMWxCUTNwRExFMUJRVTBzUTBGQlF5eFJRVUZSTEVkQlFVY3NUMEZCVHl4RFFVRkRPMWxCUXpGQ0xFMUJRVTBzUTBGQlF5eHpRa0ZCYzBJc1IwRkJSeXh2UWtGQmIwSXNRMEZCUXp0WlFVTnlSQ3hOUVVGTkxFTkJRVU1zWVVGQllTeEhRVUZITEhWQ1FVRjFRaXhGUVVGRkxFTkJRVU03V1VGRGFrUXNUVUZCVFN4RFFVRkRMSGxDUVVGNVFpeEhRVUZITEVsQlFVa3NRMEZCUXl4UFFVRlBMRU5CUVVNN1dVRkRhRVFzVFVGQlRTeERRVUZETEZOQlFWTXNSMEZCUnl4TlFVRk5MRU5CUVVNc1IwRkJSeXhEUVVGRExGRkJRVkVzUTBGQlF6dFpRVU4yUXl4TlFVRk5MRU5CUVVNc1RVRkJUU3hIUVVGSExFMUJRVTBzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlN4RFFVRkRPMWxCUXpsQ0xFMUJRVTBzUTBGQlF5eFJRVUZSTEVkQlFVY3NUVUZCVFN4RFFVRkRMRTlCUVU4c1EwRkJRenRaUVVOcVF5eE5RVUZOTEVOQlFVTXNWVUZCVlN4SFFVRkhMRk5CUVZNc1EwRkJReXhKUVVGSkxFTkJRVU1zVTBGQlV5eERRVUZETEVOQlFVTTdXVUZET1VNc1RVRkJUU3hEUVVGRExGZEJRVmNzUjBGQlJ5eFpRVUZaTEVOQlFVTXNTVUZCU1N4RFFVRkRMRlZCUVZVc1EwRkJReXhEUVVGRE8xbEJRMjVFTEUxQlFVMHNRMEZCUXl4VlFVRlZMRWRCUVVjc1dVRkJXU3hEUVVGRExFbEJRVWtzUTBGQlF5eFRRVUZUTEVOQlFVTXNRMEZCUXp0WlFVTnFSQ3hOUVVGTkxFTkJRVU1zVTBGQlV5eEhRVUZITEZsQlFWa3NRMEZCUXl4SlFVRkpMRU5CUVVNc1VVRkJVU3hEUVVGRExFTkJRVU03V1VGREwwTXNUVUZCVFN4RFFVRkRMR1ZCUVdVc1IwRkJSeXhaUVVGWkxFTkJRVU1zU1VGQlNTeERRVUZETEdGQlFXRXNRMEZCUXl4RFFVRkRPMWxCUXpGRUxFMUJRVTBzUTBGQlF5eFZRVUZWTEVkQlFVY3NXVUZCV1N4RFFVRkRMRWxCUVVrc1EwRkJReXhUUVVGVExFTkJRVU1zUTBGQlF6dFpRVU5xUkN4TlFVRk5MRU5CUVVNc1RVRkJUU3hIUVVGSExGbEJRVmtzUTBGQlF5eEpRVUZKTEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNN1dVRkRNVU1zVFVGQlRTeERRVUZETEZOQlFWTXNSMEZCUnl4WlFVRlpMRU5CUVVNc1NVRkJTU3hEUVVGRExGTkJRVk1zUTBGQlF5eERRVUZETzFsQlEyaEVMRTFCUVUwc1EwRkJReXhMUVVGTExFZEJRVWNzV1VGQldTeERRVUZETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJRenRaUVVONFF5eE5RVUZOTEVOQlFVTXNWVUZCVlN4SFFVRkhMRWxCUVVrc1EwRkJReXhUUVVGVExFTkJRVU03V1VGRGJrTXNUVUZCVFN4RFFVRkRMRk5CUVZNc1IwRkJSeXhUUVVGVExFTkJRVU1zVFVGQlRTeERRVUZETEVkQlFVY3NRMEZCUXl4VFFVRlRMRU5CUVVNc1EwRkJRenRaUVVWdVJDeHZSRUZCYjBRN1dVRkRjRVFzZFVSQlFYVkVPMWxCUTNaRUxFMUJRVTBzUTBGQlF5eFpRVUZaTEVkQlFVY3NVMEZCVXl4RFFVRkRMRTFCUVUwc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF6dFpRVU0xUXl4TlFVRk5MRU5CUVVNc1lVRkJZU3hIUVVGSExGTkJRVk1zUTBGQlF5eE5RVUZOTEVOQlFVTXNSMEZCUnl4RFFVRkRMRWRCUVVjc1EwRkJReXhEUVVGRE8xbEJSV3BFTEVsQlFVa3NTVUZCU1N4RFFVRkRMRk5CUVZNc1MwRkJTeXhOUVVGTkxFbEJRVWtzU1VGQlNTeERRVUZETEVsQlFVa3NRMEZCUXl4TlFVRk5MRWRCUVVjc1EwRkJReXhGUVVGRk8yZENRVU55UkN4TlFVRk5MRU5CUVVNc1UwRkJVeXhIUVVGSExGbEJRVmtzUTBGQlF5eEpRVUZKTEVOQlFVTXNVMEZCVXl4RFFVRkRMRWxCUVVrc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5eERRVUZETzJGQlF6VkVPMWxCUlVRc1NVRkJTU3hEUVVGRExGbEJRVmtzUTBGQlF5eFZRVUZWTEVOQlFVTXNXVUZCV1N4RlFVRkZMRTFCUVUwc1EwRkJReXhEUVVGRE8xRkJRM0pFTEVOQlFVTXNRMEZCUXp0UlFVVkdMR2RHUVVGblJqdFJRVU5vUml4SlFVRkpMRU5CUVVNc2FVSkJRV2xDTEVkQlFVY3NRMEZCUXl4SFFVRkhMRVZCUVVVc1RVRkJUU3hGUVVGRkxFVkJRVVU3V1VGRGRrTXNiMGhCUVc5SU8xbEJRM0JJTEVsQlFVa3NSMEZCUnl4RFFVRkRMRk5CUVZNc1NVRkJTU3hIUVVGSExFTkJRVU1zVTBGQlV5eExRVUZMTERSQ1FVRTBRaXhGUVVGRk8yZENRVU51UlN4UlFVRlJMRWRCUVVjc1EwRkJReXhKUVVGSkxFVkJRVVU3YjBKQlEyaENMRXRCUVVzc1UwRkJVeXhEUVVGRE8yOUNRVU5tTEV0QlFVc3NWVUZCVlR0M1FrRkRZaXh4UWtGQmNVSXNRMEZCUXl4SFFVRkhMRU5CUVVNc1NVRkJTU3hGUVVGRkxFMUJRVTBzUTBGQlF5eERRVUZETzNkQ1FVTjRReXhOUVVGTk8ybENRVU5VTzJGQlEwWTdVVUZEU0N4RFFVRkRMRU5CUVVNN1VVRkRSaXhQUVVGUExFTkJRVU1zVDBGQlR5eERRVUZETEZOQlFWTXNRMEZCUXl4WFFVRlhMRU5CUVVNc1NVRkJTU3hEUVVGRExHbENRVUZwUWl4RFFVRkRMRU5CUVVNN1NVRkRhRVVzUTBGQlF6dEpRVVZOTEU5QlFVODdVVUZEV2l4SlFVRkpMRWxCUVVrc1EwRkJReXhwUWtGQmFVSXNSVUZCUlR0WlFVTXhRaXhQUVVGUExFTkJRVU1zVDBGQlR5eERRVUZETEZOQlFWTXNRMEZCUXl4alFVRmpMRU5CUVVNc1NVRkJTU3hEUVVGRExHbENRVUZwUWl4RFFVRkRMRU5CUVVNN1UwRkRiRVU3U1VGRFNDeERRVUZETzBOQlEwWWlmUT09IiwiaW1wb3J0IHsgaW5jcmVtZW50ZWRFdmVudE9yZGluYWwgfSBmcm9tIFwiLi4vbGliL2V4dGVuc2lvbi1zZXNzaW9uLWV2ZW50LW9yZGluYWxcIjtcbmltcG9ydCB7IGV4dGVuc2lvblNlc3Npb25VdWlkIH0gZnJvbSBcIi4uL2xpYi9leHRlbnNpb24tc2Vzc2lvbi11dWlkXCI7XG5pbXBvcnQgeyBQZW5kaW5nTmF2aWdhdGlvbiB9IGZyb20gXCIuLi9saWIvcGVuZGluZy1uYXZpZ2F0aW9uXCI7XG5pbXBvcnQgeyBib29sVG9JbnQsIGVzY2FwZVN0cmluZywgZXNjYXBlVXJsIH0gZnJvbSBcIi4uL2xpYi9zdHJpbmctdXRpbHNcIjtcbmltcG9ydCB7IG1ha2VVVUlEIH0gZnJvbSBcIi4uL2xpYi91dWlkXCI7XG5leHBvcnQgY29uc3QgdHJhbnNmb3JtV2ViTmF2aWdhdGlvbkJhc2VFdmVudERldGFpbHNUb09wZW5XUE1TY2hlbWEgPSBhc3luYyAoY3Jhd2xJRCwgZGV0YWlscykgPT4ge1xuICAgIGNvbnN0IHRhYiA9IGRldGFpbHMudGFiSWQgPiAtMVxuICAgICAgICA/IGF3YWl0IGJyb3dzZXIudGFicy5nZXQoZGV0YWlscy50YWJJZClcbiAgICAgICAgOiB7XG4gICAgICAgICAgICB3aW5kb3dJZDogdW5kZWZpbmVkLFxuICAgICAgICAgICAgaW5jb2duaXRvOiB1bmRlZmluZWQsXG4gICAgICAgICAgICBjb29raWVTdG9yZUlkOiB1bmRlZmluZWQsXG4gICAgICAgICAgICBvcGVuZXJUYWJJZDogdW5kZWZpbmVkLFxuICAgICAgICAgICAgd2lkdGg6IHVuZGVmaW5lZCxcbiAgICAgICAgICAgIGhlaWdodDogdW5kZWZpbmVkLFxuICAgICAgICB9O1xuICAgIGNvbnN0IHdpbmRvdyA9IHRhYi53aW5kb3dJZFxuICAgICAgICA/IGF3YWl0IGJyb3dzZXIud2luZG93cy5nZXQodGFiLndpbmRvd0lkKVxuICAgICAgICA6IHsgd2lkdGg6IHVuZGVmaW5lZCwgaGVpZ2h0OiB1bmRlZmluZWQsIHR5cGU6IHVuZGVmaW5lZCB9O1xuICAgIGNvbnN0IG5hdmlnYXRpb24gPSB7XG4gICAgICAgIGNyYXdsX2lkOiBjcmF3bElELFxuICAgICAgICBpbmNvZ25pdG86IGJvb2xUb0ludCh0YWIuaW5jb2duaXRvKSxcbiAgICAgICAgZXh0ZW5zaW9uX3Nlc3Npb25fdXVpZDogZXh0ZW5zaW9uU2Vzc2lvblV1aWQsXG4gICAgICAgIHByb2Nlc3NfaWQ6IGRldGFpbHMucHJvY2Vzc0lkLFxuICAgICAgICB3aW5kb3dfaWQ6IHRhYi53aW5kb3dJZCxcbiAgICAgICAgdGFiX2lkOiBkZXRhaWxzLnRhYklkLFxuICAgICAgICB0YWJfb3BlbmVyX3RhYl9pZDogdGFiLm9wZW5lclRhYklkLFxuICAgICAgICBmcmFtZV9pZDogZGV0YWlscy5mcmFtZUlkLFxuICAgICAgICB3aW5kb3dfd2lkdGg6IHdpbmRvdy53aWR0aCxcbiAgICAgICAgd2luZG93X2hlaWdodDogd2luZG93LmhlaWdodCxcbiAgICAgICAgd2luZG93X3R5cGU6IHdpbmRvdy50eXBlLFxuICAgICAgICB0YWJfd2lkdGg6IHRhYi53aWR0aCxcbiAgICAgICAgdGFiX2hlaWdodDogdGFiLmhlaWdodCxcbiAgICAgICAgdGFiX2Nvb2tpZV9zdG9yZV9pZDogZXNjYXBlU3RyaW5nKHRhYi5jb29raWVTdG9yZUlkKSxcbiAgICAgICAgdXVpZDogbWFrZVVVSUQoKSxcbiAgICAgICAgdXJsOiBlc2NhcGVVcmwoZGV0YWlscy51cmwpLFxuICAgIH07XG4gICAgcmV0dXJuIG5hdmlnYXRpb247XG59O1xuZXhwb3J0IGNsYXNzIE5hdmlnYXRpb25JbnN0cnVtZW50IHtcbiAgICBjb25zdHJ1Y3RvcihkYXRhUmVjZWl2ZXIpIHtcbiAgICAgICAgdGhpcy5wZW5kaW5nTmF2aWdhdGlvbnMgPSB7fTtcbiAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIgPSBkYXRhUmVjZWl2ZXI7XG4gICAgfVxuICAgIHN0YXRpYyBuYXZpZ2F0aW9uSWQocHJvY2Vzc0lkLCB0YWJJZCwgZnJhbWVJZCkge1xuICAgICAgICByZXR1cm4gYCR7cHJvY2Vzc0lkfS0ke3RhYklkfS0ke2ZyYW1lSWR9YDtcbiAgICB9XG4gICAgcnVuKGNyYXdsSUQpIHtcbiAgICAgICAgdGhpcy5vbkJlZm9yZU5hdmlnYXRlTGlzdGVuZXIgPSBhc3luYyAoZGV0YWlscykgPT4ge1xuICAgICAgICAgICAgY29uc3QgbmF2aWdhdGlvbklkID0gTmF2aWdhdGlvbkluc3RydW1lbnQubmF2aWdhdGlvbklkKGRldGFpbHMucHJvY2Vzc0lkLCBkZXRhaWxzLnRhYklkLCBkZXRhaWxzLmZyYW1lSWQpO1xuICAgICAgICAgICAgY29uc3QgcGVuZGluZ05hdmlnYXRpb24gPSB0aGlzLmluc3RhbnRpYXRlUGVuZGluZ05hdmlnYXRpb24obmF2aWdhdGlvbklkKTtcbiAgICAgICAgICAgIGNvbnN0IG5hdmlnYXRpb24gPSBhd2FpdCB0cmFuc2Zvcm1XZWJOYXZpZ2F0aW9uQmFzZUV2ZW50RGV0YWlsc1RvT3BlbldQTVNjaGVtYShjcmF3bElELCBkZXRhaWxzKTtcbiAgICAgICAgICAgIG5hdmlnYXRpb24ucGFyZW50X2ZyYW1lX2lkID0gZGV0YWlscy5wYXJlbnRGcmFtZUlkO1xuICAgICAgICAgICAgbmF2aWdhdGlvbi5iZWZvcmVfbmF2aWdhdGVfZXZlbnRfb3JkaW5hbCA9IGluY3JlbWVudGVkRXZlbnRPcmRpbmFsKCk7XG4gICAgICAgICAgICBuYXZpZ2F0aW9uLmJlZm9yZV9uYXZpZ2F0ZV90aW1lX3N0YW1wID0gbmV3IERhdGUoZGV0YWlscy50aW1lU3RhbXApLnRvSVNPU3RyaW5nKCk7XG4gICAgICAgICAgICBwZW5kaW5nTmF2aWdhdGlvbi5yZXNvbHZlT25CZWZvcmVOYXZpZ2F0ZUV2ZW50TmF2aWdhdGlvbihuYXZpZ2F0aW9uKTtcbiAgICAgICAgfTtcbiAgICAgICAgYnJvd3Nlci53ZWJOYXZpZ2F0aW9uLm9uQmVmb3JlTmF2aWdhdGUuYWRkTGlzdGVuZXIodGhpcy5vbkJlZm9yZU5hdmlnYXRlTGlzdGVuZXIpO1xuICAgICAgICB0aGlzLm9uQ29tbWl0dGVkTGlzdGVuZXIgPSBhc3luYyAoZGV0YWlscykgPT4ge1xuICAgICAgICAgICAgY29uc3QgbmF2aWdhdGlvbklkID0gTmF2aWdhdGlvbkluc3RydW1lbnQubmF2aWdhdGlvbklkKGRldGFpbHMucHJvY2Vzc0lkLCBkZXRhaWxzLnRhYklkLCBkZXRhaWxzLmZyYW1lSWQpO1xuICAgICAgICAgICAgY29uc3QgbmF2aWdhdGlvbiA9IGF3YWl0IHRyYW5zZm9ybVdlYk5hdmlnYXRpb25CYXNlRXZlbnREZXRhaWxzVG9PcGVuV1BNU2NoZW1hKGNyYXdsSUQsIGRldGFpbHMpO1xuICAgICAgICAgICAgbmF2aWdhdGlvbi50cmFuc2l0aW9uX3F1YWxpZmllcnMgPSBlc2NhcGVTdHJpbmcoSlNPTi5zdHJpbmdpZnkoZGV0YWlscy50cmFuc2l0aW9uUXVhbGlmaWVycykpO1xuICAgICAgICAgICAgbmF2aWdhdGlvbi50cmFuc2l0aW9uX3R5cGUgPSBlc2NhcGVTdHJpbmcoZGV0YWlscy50cmFuc2l0aW9uVHlwZSk7XG4gICAgICAgICAgICBuYXZpZ2F0aW9uLmNvbW1pdHRlZF9ldmVudF9vcmRpbmFsID0gaW5jcmVtZW50ZWRFdmVudE9yZGluYWwoKTtcbiAgICAgICAgICAgIG5hdmlnYXRpb24uY29tbWl0dGVkX3RpbWVfc3RhbXAgPSBuZXcgRGF0ZShkZXRhaWxzLnRpbWVTdGFtcCkudG9JU09TdHJpbmcoKTtcbiAgICAgICAgICAgIC8vIGluY2x1ZGUgYXR0cmlidXRlcyBmcm9tIHRoZSBjb3JyZXNwb25kaW5nIG9uQmVmb3JlTmF2aWdhdGlvbiBldmVudFxuICAgICAgICAgICAgY29uc3QgcGVuZGluZ05hdmlnYXRpb24gPSB0aGlzLmdldFBlbmRpbmdOYXZpZ2F0aW9uKG5hdmlnYXRpb25JZCk7XG4gICAgICAgICAgICBpZiAocGVuZGluZ05hdmlnYXRpb24pIHtcbiAgICAgICAgICAgICAgICBwZW5kaW5nTmF2aWdhdGlvbi5yZXNvbHZlT25Db21taXR0ZWRFdmVudE5hdmlnYXRpb24obmF2aWdhdGlvbik7XG4gICAgICAgICAgICAgICAgY29uc3QgcmVzb2x2ZWQgPSBhd2FpdCBwZW5kaW5nTmF2aWdhdGlvbi5yZXNvbHZlZFdpdGhpblRpbWVvdXQoMTAwMCk7XG4gICAgICAgICAgICAgICAgaWYgKHJlc29sdmVkKSB7XG4gICAgICAgICAgICAgICAgICAgIGNvbnN0IG9uQmVmb3JlTmF2aWdhdGVFdmVudE5hdmlnYXRpb24gPSBhd2FpdCBwZW5kaW5nTmF2aWdhdGlvbi5vbkJlZm9yZU5hdmlnYXRlRXZlbnROYXZpZ2F0aW9uO1xuICAgICAgICAgICAgICAgICAgICBuYXZpZ2F0aW9uLnBhcmVudF9mcmFtZV9pZCA9XG4gICAgICAgICAgICAgICAgICAgICAgICBvbkJlZm9yZU5hdmlnYXRlRXZlbnROYXZpZ2F0aW9uLnBhcmVudF9mcmFtZV9pZDtcbiAgICAgICAgICAgICAgICAgICAgbmF2aWdhdGlvbi5iZWZvcmVfbmF2aWdhdGVfZXZlbnRfb3JkaW5hbCA9XG4gICAgICAgICAgICAgICAgICAgICAgICBvbkJlZm9yZU5hdmlnYXRlRXZlbnROYXZpZ2F0aW9uLmJlZm9yZV9uYXZpZ2F0ZV9ldmVudF9vcmRpbmFsO1xuICAgICAgICAgICAgICAgICAgICBuYXZpZ2F0aW9uLmJlZm9yZV9uYXZpZ2F0ZV90aW1lX3N0YW1wID1cbiAgICAgICAgICAgICAgICAgICAgICAgIG9uQmVmb3JlTmF2aWdhdGVFdmVudE5hdmlnYXRpb24uYmVmb3JlX25hdmlnYXRlX3RpbWVfc3RhbXA7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuICAgICAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIuc2F2ZVJlY29yZChcIm5hdmlnYXRpb25zXCIsIG5hdmlnYXRpb24pO1xuICAgICAgICB9O1xuICAgICAgICBicm93c2VyLndlYk5hdmlnYXRpb24ub25Db21taXR0ZWQuYWRkTGlzdGVuZXIodGhpcy5vbkNvbW1pdHRlZExpc3RlbmVyKTtcbiAgICB9XG4gICAgY2xlYW51cCgpIHtcbiAgICAgICAgaWYgKHRoaXMub25CZWZvcmVOYXZpZ2F0ZUxpc3RlbmVyKSB7XG4gICAgICAgICAgICBicm93c2VyLndlYk5hdmlnYXRpb24ub25CZWZvcmVOYXZpZ2F0ZS5yZW1vdmVMaXN0ZW5lcih0aGlzLm9uQmVmb3JlTmF2aWdhdGVMaXN0ZW5lcik7XG4gICAgICAgIH1cbiAgICAgICAgaWYgKHRoaXMub25Db21taXR0ZWRMaXN0ZW5lcikge1xuICAgICAgICAgICAgYnJvd3Nlci53ZWJOYXZpZ2F0aW9uLm9uQ29tbWl0dGVkLnJlbW92ZUxpc3RlbmVyKHRoaXMub25Db21taXR0ZWRMaXN0ZW5lcik7XG4gICAgICAgIH1cbiAgICB9XG4gICAgaW5zdGFudGlhdGVQZW5kaW5nTmF2aWdhdGlvbihuYXZpZ2F0aW9uSWQpIHtcbiAgICAgICAgdGhpcy5wZW5kaW5nTmF2aWdhdGlvbnNbbmF2aWdhdGlvbklkXSA9IG5ldyBQZW5kaW5nTmF2aWdhdGlvbigpO1xuICAgICAgICByZXR1cm4gdGhpcy5wZW5kaW5nTmF2aWdhdGlvbnNbbmF2aWdhdGlvbklkXTtcbiAgICB9XG4gICAgZ2V0UGVuZGluZ05hdmlnYXRpb24obmF2aWdhdGlvbklkKSB7XG4gICAgICAgIHJldHVybiB0aGlzLnBlbmRpbmdOYXZpZ2F0aW9uc1tuYXZpZ2F0aW9uSWRdO1xuICAgIH1cbn1cbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWJtRjJhV2RoZEdsdmJpMXBibk4wY25WdFpXNTBMbXB6SWl3aWMyOTFjbU5sVW05dmRDSTZJaUlzSW5OdmRYSmpaWE1pT2xzaUxpNHZMaTR2TGk0dmMzSmpMMkpoWTJ0bmNtOTFibVF2Ym1GMmFXZGhkR2x2YmkxcGJuTjBjblZ0Wlc1MExuUnpJbDBzSW01aGJXVnpJanBiWFN3aWJXRndjR2x1WjNNaU9pSkJRVUZCTEU5QlFVOHNSVUZCUlN4MVFrRkJkVUlzUlVGQlJTeE5RVUZOTEhkRFFVRjNReXhEUVVGRE8wRkJRMnBHTEU5QlFVOHNSVUZCUlN4dlFrRkJiMElzUlVGQlJTeE5RVUZOTEN0Q1FVRXJRaXhEUVVGRE8wRkJRM0pGTEU5QlFVOHNSVUZCUlN4cFFrRkJhVUlzUlVGQlJTeE5RVUZOTERKQ1FVRXlRaXhEUVVGRE8wRkJRemxFTEU5QlFVOHNSVUZCUlN4VFFVRlRMRVZCUVVVc1dVRkJXU3hGUVVGRkxGTkJRVk1zUlVGQlJTeE5RVUZOTEhGQ1FVRnhRaXhEUVVGRE8wRkJRM3BGTEU5QlFVOHNSVUZCUlN4UlFVRlJMRVZCUVVVc1RVRkJUU3hoUVVGaExFTkJRVU03UVVGUmRrTXNUVUZCVFN4RFFVRkRMRTFCUVUwc2NVUkJRWEZFTEVkQlFVY3NTMEZCU3l4RlFVTjRSU3hQUVVGUExFVkJRMUFzVDBGQmMwTXNSVUZEYWtJc1JVRkJSVHRKUVVOMlFpeE5RVUZOTEVkQlFVY3NSMEZEVUN4UFFVRlBMRU5CUVVNc1MwRkJTeXhIUVVGSExFTkJRVU1zUTBGQlF6dFJRVU5vUWl4RFFVRkRMRU5CUVVNc1RVRkJUU3hQUVVGUExFTkJRVU1zU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4UFFVRlBMRU5CUVVNc1MwRkJTeXhEUVVGRE8xRkJRM1pETEVOQlFVTXNRMEZCUXp0WlFVTkZMRkZCUVZFc1JVRkJSU3hUUVVGVE8xbEJRMjVDTEZOQlFWTXNSVUZCUlN4VFFVRlRPMWxCUTNCQ0xHRkJRV0VzUlVGQlJTeFRRVUZUTzFsQlEzaENMRmRCUVZjc1JVRkJSU3hUUVVGVE8xbEJRM1JDTEV0QlFVc3NSVUZCUlN4VFFVRlRPMWxCUTJoQ0xFMUJRVTBzUlVGQlJTeFRRVUZUTzFOQlEyeENMRU5CUVVNN1NVRkRVaXhOUVVGTkxFMUJRVTBzUjBGQlJ5eEhRVUZITEVOQlFVTXNVVUZCVVR0UlFVTjZRaXhEUVVGRExFTkJRVU1zVFVGQlRTeFBRVUZQTEVOQlFVTXNUMEZCVHl4RFFVRkRMRWRCUVVjc1EwRkJReXhIUVVGSExFTkJRVU1zVVVGQlVTeERRVUZETzFGQlEzcERMRU5CUVVNc1EwRkJReXhGUVVGRkxFdEJRVXNzUlVGQlJTeFRRVUZUTEVWQlFVVXNUVUZCVFN4RlFVRkZMRk5CUVZNc1JVRkJSU3hKUVVGSkxFVkJRVVVzVTBGQlV5eEZRVUZGTEVOQlFVTTdTVUZETjBRc1RVRkJUU3hWUVVGVkxFZEJRV1U3VVVGRE4wSXNVVUZCVVN4RlFVRkZMRTlCUVU4N1VVRkRha0lzVTBGQlV5eEZRVUZGTEZOQlFWTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1UwRkJVeXhEUVVGRE8xRkJRMjVETEhOQ1FVRnpRaXhGUVVGRkxHOUNRVUZ2UWp0UlFVTTFReXhWUVVGVkxFVkJRVVVzVDBGQlR5eERRVUZETEZOQlFWTTdVVUZETjBJc1UwRkJVeXhGUVVGRkxFZEJRVWNzUTBGQlF5eFJRVUZSTzFGQlEzWkNMRTFCUVUwc1JVRkJSU3hQUVVGUExFTkJRVU1zUzBGQlN6dFJRVU55UWl4cFFrRkJhVUlzUlVGQlJTeEhRVUZITEVOQlFVTXNWMEZCVnp0UlFVTnNReXhSUVVGUkxFVkJRVVVzVDBGQlR5eERRVUZETEU5QlFVODdVVUZEZWtJc1dVRkJXU3hGUVVGRkxFMUJRVTBzUTBGQlF5eExRVUZMTzFGQlF6RkNMR0ZCUVdFc1JVRkJSU3hOUVVGTkxFTkJRVU1zVFVGQlRUdFJRVU0xUWl4WFFVRlhMRVZCUVVVc1RVRkJUU3hEUVVGRExFbEJRVWs3VVVGRGVFSXNVMEZCVXl4RlFVRkZMRWRCUVVjc1EwRkJReXhMUVVGTE8xRkJRM0JDTEZWQlFWVXNSVUZCUlN4SFFVRkhMRU5CUVVNc1RVRkJUVHRSUVVOMFFpeHRRa0ZCYlVJc1JVRkJSU3haUVVGWkxFTkJRVU1zUjBGQlJ5eERRVUZETEdGQlFXRXNRMEZCUXp0UlFVTndSQ3hKUVVGSkxFVkJRVVVzVVVGQlVTeEZRVUZGTzFGQlEyaENMRWRCUVVjc1JVRkJSU3hUUVVGVExFTkJRVU1zVDBGQlR5eERRVUZETEVkQlFVY3NRMEZCUXp0TFFVTTFRaXhEUVVGRE8wbEJRMFlzVDBGQlR5eFZRVUZWTEVOQlFVTTdRVUZEY0VJc1EwRkJReXhEUVVGRE8wRkJSVVlzVFVGQlRTeFBRVUZQTEc5Q1FVRnZRanRKUVZjdlFpeFpRVUZaTEZsQlFWazdVVUZLYUVJc2RVSkJRV3RDTEVkQlJYUkNMRVZCUVVVc1EwRkJRenRSUVVkTUxFbEJRVWtzUTBGQlF5eFpRVUZaTEVkQlFVY3NXVUZCV1N4RFFVRkRPMGxCUTI1RExFTkJRVU03U1VGYVRTeE5RVUZOTEVOQlFVTXNXVUZCV1N4RFFVRkRMRk5CUVZNc1JVRkJSU3hMUVVGTExFVkJRVVVzVDBGQlR6dFJRVU5zUkN4UFFVRlBMRWRCUVVjc1UwRkJVeXhKUVVGSkxFdEJRVXNzU1VGQlNTeFBRVUZQTEVWQlFVVXNRMEZCUXp0SlFVTTFReXhEUVVGRE8wbEJXVTBzUjBGQlJ5eERRVUZETEU5QlFVODdVVUZEYUVJc1NVRkJTU3hEUVVGRExIZENRVUYzUWl4SFFVRkhMRXRCUVVzc1JVRkRia01zVDBGQmEwUXNSVUZEYkVRc1JVRkJSVHRaUVVOR0xFMUJRVTBzV1VGQldTeEhRVUZITEc5Q1FVRnZRaXhEUVVGRExGbEJRVmtzUTBGRGNFUXNUMEZCVHl4RFFVRkRMRk5CUVZNc1JVRkRha0lzVDBGQlR5eERRVUZETEV0QlFVc3NSVUZEWWl4UFFVRlBMRU5CUVVNc1QwRkJUeXhEUVVOb1FpeERRVUZETzFsQlEwWXNUVUZCVFN4cFFrRkJhVUlzUjBGQlJ5eEpRVUZKTEVOQlFVTXNORUpCUVRSQ0xFTkJRVU1zV1VGQldTeERRVUZETEVOQlFVTTdXVUZETVVVc1RVRkJUU3hWUVVGVkxFZEJRV1VzVFVGQlRTeHhSRUZCY1VRc1EwRkRlRVlzVDBGQlR5eEZRVU5RTEU5QlFVOHNRMEZEVWl4RFFVRkRPMWxCUTBZc1ZVRkJWU3hEUVVGRExHVkJRV1VzUjBGQlJ5eFBRVUZQTEVOQlFVTXNZVUZCWVN4RFFVRkRPMWxCUTI1RUxGVkJRVlVzUTBGQlF5dzJRa0ZCTmtJc1IwRkJSeXgxUWtGQmRVSXNSVUZCUlN4RFFVRkRPMWxCUTNKRkxGVkJRVlVzUTBGQlF5d3dRa0ZCTUVJc1IwRkJSeXhKUVVGSkxFbEJRVWtzUTBGRE9VTXNUMEZCVHl4RFFVRkRMRk5CUVZNc1EwRkRiRUlzUTBGQlF5eFhRVUZYTEVWQlFVVXNRMEZCUXp0WlFVTm9RaXhwUWtGQmFVSXNRMEZCUXl4elEwRkJjME1zUTBGQlF5eFZRVUZWTEVOQlFVTXNRMEZCUXp0UlFVTjJSU3hEUVVGRExFTkJRVU03VVVGRFJpeFBRVUZQTEVOQlFVTXNZVUZCWVN4RFFVRkRMR2RDUVVGblFpeERRVUZETEZkQlFWY3NRMEZEYUVRc1NVRkJTU3hEUVVGRExIZENRVUYzUWl4RFFVTTVRaXhEUVVGRE8xRkJRMFlzU1VGQlNTeERRVUZETEcxQ1FVRnRRaXhIUVVGSExFdEJRVXNzUlVGRE9VSXNUMEZCTmtNc1JVRkROME1zUlVGQlJUdFpRVU5HTEUxQlFVMHNXVUZCV1N4SFFVRkhMRzlDUVVGdlFpeERRVUZETEZsQlFWa3NRMEZEY0VRc1QwRkJUeXhEUVVGRExGTkJRVk1zUlVGRGFrSXNUMEZCVHl4RFFVRkRMRXRCUVVzc1JVRkRZaXhQUVVGUExFTkJRVU1zVDBGQlR5eERRVU5vUWl4RFFVRkRPMWxCUTBZc1RVRkJUU3hWUVVGVkxFZEJRV1VzVFVGQlRTeHhSRUZCY1VRc1EwRkRlRVlzVDBGQlR5eEZRVU5RTEU5QlFVOHNRMEZEVWl4RFFVRkRPMWxCUTBZc1ZVRkJWU3hEUVVGRExIRkNRVUZ4UWl4SFFVRkhMRmxCUVZrc1EwRkROME1zU1VGQlNTeERRVUZETEZOQlFWTXNRMEZCUXl4UFFVRlBMRU5CUVVNc2IwSkJRVzlDTEVOQlFVTXNRMEZETjBNc1EwRkJRenRaUVVOR0xGVkJRVlVzUTBGQlF5eGxRVUZsTEVkQlFVY3NXVUZCV1N4RFFVRkRMRTlCUVU4c1EwRkJReXhqUVVGakxFTkJRVU1zUTBGQlF6dFpRVU5zUlN4VlFVRlZMRU5CUVVNc2RVSkJRWFZDTEVkQlFVY3NkVUpCUVhWQ0xFVkJRVVVzUTBGQlF6dFpRVU12UkN4VlFVRlZMRU5CUVVNc2IwSkJRVzlDTEVkQlFVY3NTVUZCU1N4SlFVRkpMRU5CUTNoRExFOUJRVThzUTBGQlF5eFRRVUZUTEVOQlEyeENMRU5CUVVNc1YwRkJWeXhGUVVGRkxFTkJRVU03V1VGRmFFSXNjVVZCUVhGRk8xbEJRM0pGTEUxQlFVMHNhVUpCUVdsQ0xFZEJRVWNzU1VGQlNTeERRVUZETEc5Q1FVRnZRaXhEUVVGRExGbEJRVmtzUTBGQlF5eERRVUZETzFsQlEyeEZMRWxCUVVrc2FVSkJRV2xDTEVWQlFVVTdaMEpCUTNKQ0xHbENRVUZwUWl4RFFVRkRMR2xEUVVGcFF5eERRVUZETEZWQlFWVXNRMEZCUXl4RFFVRkRPMmRDUVVOb1JTeE5RVUZOTEZGQlFWRXNSMEZCUnl4TlFVRk5MR2xDUVVGcFFpeERRVUZETEhGQ1FVRnhRaXhEUVVGRExFbEJRVWtzUTBGQlF5eERRVUZETzJkQ1FVTnlSU3hKUVVGSkxGRkJRVkVzUlVGQlJUdHZRa0ZEV2l4TlFVRk5MQ3RDUVVFclFpeEhRVUZITEUxQlFVMHNhVUpCUVdsQ0xFTkJRVU1zSzBKQlFTdENMRU5CUVVNN2IwSkJRMmhITEZWQlFWVXNRMEZCUXl4bFFVRmxPM2RDUVVONFFpd3JRa0ZCSzBJc1EwRkJReXhsUVVGbExFTkJRVU03YjBKQlEyeEVMRlZCUVZVc1EwRkJReXcyUWtGQk5rSTdkMEpCUTNSRExDdENRVUVyUWl4RFFVRkRMRFpDUVVFMlFpeERRVUZETzI5Q1FVTm9SU3hWUVVGVkxFTkJRVU1zTUVKQlFUQkNPM2RDUVVOdVF5d3JRa0ZCSzBJc1EwRkJReXd3UWtGQk1FSXNRMEZCUXp0cFFrRkRPVVE3WVVGRFJqdFpRVVZFTEVsQlFVa3NRMEZCUXl4WlFVRlpMRU5CUVVNc1ZVRkJWU3hEUVVGRExHRkJRV0VzUlVGQlJTeFZRVUZWTEVOQlFVTXNRMEZCUXp0UlFVTXhSQ3hEUVVGRExFTkJRVU03VVVGRFJpeFBRVUZQTEVOQlFVTXNZVUZCWVN4RFFVRkRMRmRCUVZjc1EwRkJReXhYUVVGWExFTkJRVU1zU1VGQlNTeERRVUZETEcxQ1FVRnRRaXhEUVVGRExFTkJRVU03U1VGRE1VVXNRMEZCUXp0SlFVVk5MRTlCUVU4N1VVRkRXaXhKUVVGSkxFbEJRVWtzUTBGQlF5eDNRa0ZCZDBJc1JVRkJSVHRaUVVOcVF5eFBRVUZQTEVOQlFVTXNZVUZCWVN4RFFVRkRMR2RDUVVGblFpeERRVUZETEdOQlFXTXNRMEZEYmtRc1NVRkJTU3hEUVVGRExIZENRVUYzUWl4RFFVTTVRaXhEUVVGRE8xTkJRMGc3VVVGRFJDeEpRVUZKTEVsQlFVa3NRMEZCUXl4dFFrRkJiVUlzUlVGQlJUdFpRVU0xUWl4UFFVRlBMRU5CUVVNc1lVRkJZU3hEUVVGRExGZEJRVmNzUTBGQlF5eGpRVUZqTEVOQlF6bERMRWxCUVVrc1EwRkJReXh0UWtGQmJVSXNRMEZEZWtJc1EwRkJRenRUUVVOSU8wbEJRMGdzUTBGQlF6dEpRVVZQTERSQ1FVRTBRaXhEUVVOc1F5eFpRVUZ2UWp0UlFVVndRaXhKUVVGSkxFTkJRVU1zYTBKQlFXdENMRU5CUVVNc1dVRkJXU3hEUVVGRExFZEJRVWNzU1VGQlNTeHBRa0ZCYVVJc1JVRkJSU3hEUVVGRE8xRkJRMmhGTEU5QlFVOHNTVUZCU1N4RFFVRkRMR3RDUVVGclFpeERRVUZETEZsQlFWa3NRMEZCUXl4RFFVRkRPMGxCUXk5RExFTkJRVU03U1VGRlR5eHZRa0ZCYjBJc1EwRkJReXhaUVVGdlFqdFJRVU12UXl4UFFVRlBMRWxCUVVrc1EwRkJReXhyUWtGQmEwSXNRMEZCUXl4WlFVRlpMRU5CUVVNc1EwRkJRenRKUVVNdlF5eERRVUZETzBOQlEwWWlmUT09IiwiaW1wb3J0IHsgcGFnZVNjcmlwdCB9IGZyb20gXCIuL2phdmFzY3JpcHQtaW5zdHJ1bWVudC1wYWdlLXNjb3BlXCI7XG5mdW5jdGlvbiBnZXRQYWdlU2NyaXB0QXNTdHJpbmcoKSB7XG4gICAgLy8gcmV0dXJuIGEgc3RyaW5nXG4gICAgcmV0dXJuIFwiKFwiICsgcGFnZVNjcmlwdCArIFwiKCkpO1wiO1xufVxuZnVuY3Rpb24gaW5zZXJ0U2NyaXB0KHRleHQsIGRhdGEpIHtcbiAgICBjb25zdCBwYXJlbnQgPSBkb2N1bWVudC5kb2N1bWVudEVsZW1lbnQsIHNjcmlwdCA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoXCJzY3JpcHRcIik7XG4gICAgc2NyaXB0LnRleHQgPSB0ZXh0O1xuICAgIHNjcmlwdC5hc3luYyA9IGZhbHNlO1xuICAgIGZvciAoY29uc3Qga2V5IGluIGRhdGEpIHtcbiAgICAgICAgc2NyaXB0LnNldEF0dHJpYnV0ZShcImRhdGEtXCIgKyBrZXkucmVwbGFjZShcIl9cIiwgXCItXCIpLCBkYXRhW2tleV0pO1xuICAgIH1cbiAgICBwYXJlbnQuaW5zZXJ0QmVmb3JlKHNjcmlwdCwgcGFyZW50LmZpcnN0Q2hpbGQpO1xuICAgIHBhcmVudC5yZW1vdmVDaGlsZChzY3JpcHQpO1xufVxuZnVuY3Rpb24gZW1pdE1zZyh0eXBlLCBtc2cpIHtcbiAgICBtc2cudGltZVN0YW1wID0gbmV3IERhdGUoKS50b0lTT1N0cmluZygpO1xuICAgIGJyb3dzZXIucnVudGltZS5zZW5kTWVzc2FnZSh7XG4gICAgICAgIG5hbWVzcGFjZTogXCJqYXZhc2NyaXB0LWluc3RydW1lbnRhdGlvblwiLFxuICAgICAgICB0eXBlLFxuICAgICAgICBkYXRhOiBtc2csXG4gICAgfSk7XG59XG5jb25zdCBldmVudF9pZCA9IE1hdGgucmFuZG9tKCk7XG4vLyBsaXN0ZW4gZm9yIG1lc3NhZ2VzIGZyb20gdGhlIHNjcmlwdCB3ZSBhcmUgYWJvdXQgdG8gaW5zZXJ0XG5kb2N1bWVudC5hZGRFdmVudExpc3RlbmVyKGV2ZW50X2lkLnRvU3RyaW5nKCksIGZ1bmN0aW9uIChlKSB7XG4gICAgLy8gcGFzcyB0aGVzZSBvbiB0byB0aGUgYmFja2dyb3VuZCBwYWdlXG4gICAgY29uc3QgbXNncyA9IGUuZGV0YWlsO1xuICAgIGlmIChBcnJheS5pc0FycmF5KG1zZ3MpKSB7XG4gICAgICAgIG1zZ3MuZm9yRWFjaChmdW5jdGlvbiAobXNnKSB7XG4gICAgICAgICAgICBlbWl0TXNnKG1zZy50eXBlLCBtc2cuY29udGVudCk7XG4gICAgICAgIH0pO1xuICAgIH1cbiAgICBlbHNlIHtcbiAgICAgICAgZW1pdE1zZyhtc2dzLnR5cGUsIG1zZ3MuY29udGVudCk7XG4gICAgfVxufSk7XG5leHBvcnQgZnVuY3Rpb24gaW5qZWN0SmF2YXNjcmlwdEluc3RydW1lbnRQYWdlU2NyaXB0KHRlc3RpbmcgPSBmYWxzZSkge1xuICAgIGluc2VydFNjcmlwdChnZXRQYWdlU2NyaXB0QXNTdHJpbmcoKSwge1xuICAgICAgICBldmVudF9pZCxcbiAgICAgICAgdGVzdGluZyxcbiAgICB9KTtcbn1cbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWFtRjJZWE5qY21sd2RDMXBibk4wY25WdFpXNTBMV052Ym5SbGJuUXRjMk52Y0dVdWFuTWlMQ0p6YjNWeVkyVlNiMjkwSWpvaUlpd2ljMjkxY21ObGN5STZXeUl1TGk4dUxpOHVMaTl6Y21NdlkyOXVkR1Z1ZEM5cVlYWmhjMk55YVhCMExXbHVjM1J5ZFcxbGJuUXRZMjl1ZEdWdWRDMXpZMjl3WlM1MGN5SmRMQ0p1WVcxbGN5STZXMTBzSW0xaGNIQnBibWR6SWpvaVFVRkJRU3hQUVVGUExFVkJRVVVzVlVGQlZTeEZRVUZGTEUxQlFVMHNiME5CUVc5RExFTkJRVU03UVVGRmFFVXNVMEZCVXl4eFFrRkJjVUk3U1VGRE5VSXNhMEpCUVd0Q08wbEJRMnhDTEU5QlFVOHNSMEZCUnl4SFFVRkhMRlZCUVZVc1IwRkJSeXhOUVVGTkxFTkJRVU03UVVGRGJrTXNRMEZCUXp0QlFVVkVMRk5CUVZNc1dVRkJXU3hEUVVGRExFbEJRVWtzUlVGQlJTeEpRVUZKTzBsQlF6bENMRTFCUVUwc1RVRkJUU3hIUVVGSExGRkJRVkVzUTBGQlF5eGxRVUZsTEVWQlEzSkRMRTFCUVUwc1IwRkJSeXhSUVVGUkxFTkJRVU1zWVVGQllTeERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRPMGxCUXpWRExFMUJRVTBzUTBGQlF5eEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRPMGxCUTI1Q0xFMUJRVTBzUTBGQlF5eExRVUZMTEVkQlFVY3NTMEZCU3l4RFFVRkRPMGxCUlhKQ0xFdEJRVXNzVFVGQlRTeEhRVUZITEVsQlFVa3NTVUZCU1N4RlFVRkZPMUZCUTNSQ0xFMUJRVTBzUTBGQlF5eFpRVUZaTEVOQlFVTXNUMEZCVHl4SFFVRkhMRWRCUVVjc1EwRkJReXhQUVVGUExFTkJRVU1zUjBGQlJ5eEZRVUZGTEVkQlFVY3NRMEZCUXl4RlFVRkZMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzB0QlEycEZPMGxCUlVRc1RVRkJUU3hEUVVGRExGbEJRVmtzUTBGQlF5eE5RVUZOTEVWQlFVVXNUVUZCVFN4RFFVRkRMRlZCUVZVc1EwRkJReXhEUVVGRE8wbEJReTlETEUxQlFVMHNRMEZCUXl4WFFVRlhMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU03UVVGRE4wSXNRMEZCUXp0QlFVVkVMRk5CUVZNc1QwRkJUeXhEUVVGRExFbEJRVWtzUlVGQlJTeEhRVUZITzBsQlEzaENMRWRCUVVjc1EwRkJReXhUUVVGVExFZEJRVWNzU1VGQlNTeEpRVUZKTEVWQlFVVXNRMEZCUXl4WFFVRlhMRVZCUVVVc1EwRkJRenRKUVVONlF5eFBRVUZQTEVOQlFVTXNUMEZCVHl4RFFVRkRMRmRCUVZjc1EwRkJRenRSUVVNeFFpeFRRVUZUTEVWQlFVVXNORUpCUVRSQ08xRkJRM1pETEVsQlFVazdVVUZEU2l4SlFVRkpMRVZCUVVVc1IwRkJSenRMUVVOV0xFTkJRVU1zUTBGQlF6dEJRVU5NTEVOQlFVTTdRVUZGUkN4TlFVRk5MRkZCUVZFc1IwRkJSeXhKUVVGSkxFTkJRVU1zVFVGQlRTeEZRVUZGTEVOQlFVTTdRVUZGTDBJc05rUkJRVFpFTzBGQlF6ZEVMRkZCUVZFc1EwRkJReXhuUWtGQlowSXNRMEZCUXl4UlFVRlJMRU5CUVVNc1VVRkJVU3hGUVVGRkxFVkJRVVVzVlVGQlV5eERRVUZqTzBsQlEzQkZMSFZEUVVGMVF6dEpRVU4yUXl4TlFVRk5MRWxCUVVrc1IwRkJSeXhEUVVGRExFTkJRVU1zVFVGQlRTeERRVUZETzBsQlEzUkNMRWxCUVVrc1MwRkJTeXhEUVVGRExFOUJRVThzUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlR0UlFVTjJRaXhKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFWTXNSMEZCUnp0WlFVTjJRaXhQUVVGUExFTkJRVU1zUjBGQlJ5eERRVUZETEVsQlFVa3NSVUZCUlN4SFFVRkhMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU03VVVGRGFrTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1MwRkRTanRUUVVGTk8xRkJRMHdzVDBGQlR5eERRVUZETEVsQlFVa3NRMEZCUXl4SlFVRkpMRVZCUVVVc1NVRkJTU3hEUVVGRExFOUJRVThzUTBGQlF5eERRVUZETzB0QlEyeERPMEZCUTBnc1EwRkJReXhEUVVGRExFTkJRVU03UVVGRlNDeE5RVUZOTEZWQlFWVXNiME5CUVc5RExFTkJRVU1zVDBGQlR5eEhRVUZITEV0QlFVczdTVUZEYkVVc1dVRkJXU3hEUVVGRExIRkNRVUZ4UWl4RlFVRkZMRVZCUVVVN1VVRkRjRU1zVVVGQlVUdFJRVU5TTEU5QlFVODdTMEZEVWl4RFFVRkRMRU5CUVVNN1FVRkRUQ3hEUVVGREluMD0iLCIvLyBJbnRydW1lbnRhdGlvbiBpbmplY3Rpb24gY29kZSBpcyBiYXNlZCBvbiBwcml2YWN5YmFkZ2VyZmlyZWZveFxuLy8gaHR0cHM6Ly9naXRodWIuY29tL0VGRm9yZy9wcml2YWN5YmFkZ2VyZmlyZWZveC9ibG9iL21hc3Rlci9kYXRhL2ZpbmdlcnByaW50aW5nLmpzXG5leHBvcnQgY29uc3QgcGFnZVNjcmlwdCA9IGZ1bmN0aW9uICgpIHtcbiAgICAvLyBmcm9tIFVuZGVyc2NvcmUgdjEuNi4wXG4gICAgZnVuY3Rpb24gZGVib3VuY2UoZnVuYywgd2FpdCwgaW1tZWRpYXRlID0gZmFsc2UpIHtcbiAgICAgICAgbGV0IHRpbWVvdXQsIGFyZ3MsIGNvbnRleHQsIHRpbWVzdGFtcCwgcmVzdWx0O1xuICAgICAgICBjb25zdCBsYXRlciA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIGNvbnN0IGxhc3QgPSBEYXRlLm5vdygpIC0gdGltZXN0YW1wO1xuICAgICAgICAgICAgaWYgKGxhc3QgPCB3YWl0KSB7XG4gICAgICAgICAgICAgICAgdGltZW91dCA9IHNldFRpbWVvdXQobGF0ZXIsIHdhaXQgLSBsYXN0KTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGVsc2Uge1xuICAgICAgICAgICAgICAgIHRpbWVvdXQgPSBudWxsO1xuICAgICAgICAgICAgICAgIGlmICghaW1tZWRpYXRlKSB7XG4gICAgICAgICAgICAgICAgICAgIHJlc3VsdCA9IGZ1bmMuYXBwbHkoY29udGV4dCwgYXJncyk7XG4gICAgICAgICAgICAgICAgICAgIGNvbnRleHQgPSBhcmdzID0gbnVsbDtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9XG4gICAgICAgIH07XG4gICAgICAgIHJldHVybiBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICBjb250ZXh0ID0gdGhpcztcbiAgICAgICAgICAgIGFyZ3MgPSBhcmd1bWVudHM7XG4gICAgICAgICAgICB0aW1lc3RhbXAgPSBEYXRlLm5vdygpO1xuICAgICAgICAgICAgY29uc3QgY2FsbE5vdyA9IGltbWVkaWF0ZSAmJiAhdGltZW91dDtcbiAgICAgICAgICAgIGlmICghdGltZW91dCkge1xuICAgICAgICAgICAgICAgIHRpbWVvdXQgPSBzZXRUaW1lb3V0KGxhdGVyLCB3YWl0KTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGlmIChjYWxsTm93KSB7XG4gICAgICAgICAgICAgICAgcmVzdWx0ID0gZnVuYy5hcHBseShjb250ZXh0LCBhcmdzKTtcbiAgICAgICAgICAgICAgICBjb250ZXh0ID0gYXJncyA9IG51bGw7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICByZXR1cm4gcmVzdWx0O1xuICAgICAgICB9O1xuICAgIH1cbiAgICAvLyBFbmQgb2YgRGVib3VuY2VcbiAgICAvLyBtZXNzYWdlcyB0aGUgaW5qZWN0ZWQgc2NyaXB0XG4gICAgY29uc3Qgc2VuZCA9IChmdW5jdGlvbiAoKSB7XG4gICAgICAgIGxldCBtZXNzYWdlcyA9IFtdO1xuICAgICAgICAvLyBkZWJvdW5jZSBzZW5kaW5nIHF1ZXVlZCBtZXNzYWdlc1xuICAgICAgICBjb25zdCBfc2VuZCA9IGRlYm91bmNlKGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIGRvY3VtZW50LmRpc3BhdGNoRXZlbnQobmV3IEN1c3RvbUV2ZW50KGV2ZW50X2lkLCB7XG4gICAgICAgICAgICAgICAgZGV0YWlsOiBtZXNzYWdlcyxcbiAgICAgICAgICAgIH0pKTtcbiAgICAgICAgICAgIC8vIGNsZWFyIHRoZSBxdWV1ZVxuICAgICAgICAgICAgbWVzc2FnZXMgPSBbXTtcbiAgICAgICAgfSwgMTAwKTtcbiAgICAgICAgcmV0dXJuIGZ1bmN0aW9uIChtc2dUeXBlLCBtc2cpIHtcbiAgICAgICAgICAgIC8vIHF1ZXVlIHRoZSBtZXNzYWdlXG4gICAgICAgICAgICBtZXNzYWdlcy5wdXNoKHsgdHlwZTogbXNnVHlwZSwgY29udGVudDogbXNnIH0pO1xuICAgICAgICAgICAgX3NlbmQoKTtcbiAgICAgICAgfTtcbiAgICB9KSgpO1xuICAgIGNvbnN0IGV2ZW50X2lkID0gZG9jdW1lbnQuY3VycmVudFNjcmlwdC5nZXRBdHRyaWJ1dGUoXCJkYXRhLWV2ZW50LWlkXCIpO1xuICAgIC8qXG4gICAgICogSW5zdHJ1bWVudGF0aW9uIGhlbHBlcnNcbiAgICAgKi9cbiAgICBjb25zdCB0ZXN0aW5nID0gZG9jdW1lbnQuY3VycmVudFNjcmlwdC5nZXRBdHRyaWJ1dGUoXCJkYXRhLXRlc3RpbmdcIikgPT09IFwidHJ1ZVwiO1xuICAgIGlmICh0ZXN0aW5nKSB7XG4gICAgICAgIGNvbnNvbGUubG9nKFwiT3BlbldQTTogQ3VycmVudGx5IHRlc3Rpbmc/XCIsIHRlc3RpbmcpO1xuICAgIH1cbiAgICAvLyBSZWN1cnNpdmVseSBnZW5lcmF0ZXMgYSBwYXRoIGZvciBhbiBlbGVtZW50XG4gICAgZnVuY3Rpb24gZ2V0UGF0aFRvRG9tRWxlbWVudChlbGVtZW50LCB2aXNpYmlsaXR5QXR0ciA9IGZhbHNlKSB7XG4gICAgICAgIGlmIChlbGVtZW50ID09PSBkb2N1bWVudC5ib2R5KSB7XG4gICAgICAgICAgICByZXR1cm4gZWxlbWVudC50YWdOYW1lO1xuICAgICAgICB9XG4gICAgICAgIGlmIChlbGVtZW50LnBhcmVudE5vZGUgPT09IG51bGwpIHtcbiAgICAgICAgICAgIHJldHVybiBcIk5VTEwvXCIgKyBlbGVtZW50LnRhZ05hbWU7XG4gICAgICAgIH1cbiAgICAgICAgbGV0IHNpYmxpbmdJbmRleCA9IDE7XG4gICAgICAgIGNvbnN0IHNpYmxpbmdzID0gZWxlbWVudC5wYXJlbnROb2RlLmNoaWxkTm9kZXM7XG4gICAgICAgIGZvciAobGV0IGkgPSAwOyBpIDwgc2libGluZ3MubGVuZ3RoOyBpKyspIHtcbiAgICAgICAgICAgIGNvbnN0IHNpYmxpbmcgPSBzaWJsaW5nc1tpXTtcbiAgICAgICAgICAgIGlmIChzaWJsaW5nID09PSBlbGVtZW50KSB7XG4gICAgICAgICAgICAgICAgbGV0IHBhdGggPSBnZXRQYXRoVG9Eb21FbGVtZW50KGVsZW1lbnQucGFyZW50Tm9kZSwgdmlzaWJpbGl0eUF0dHIpO1xuICAgICAgICAgICAgICAgIHBhdGggKz0gXCIvXCIgKyBlbGVtZW50LnRhZ05hbWUgKyBcIltcIiArIHNpYmxpbmdJbmRleDtcbiAgICAgICAgICAgICAgICBwYXRoICs9IFwiLFwiICsgZWxlbWVudC5pZDtcbiAgICAgICAgICAgICAgICBwYXRoICs9IFwiLFwiICsgZWxlbWVudC5jbGFzc05hbWU7XG4gICAgICAgICAgICAgICAgaWYgKHZpc2liaWxpdHlBdHRyKSB7XG4gICAgICAgICAgICAgICAgICAgIHBhdGggKz0gXCIsXCIgKyBlbGVtZW50LmhpZGRlbjtcbiAgICAgICAgICAgICAgICAgICAgcGF0aCArPSBcIixcIiArIGVsZW1lbnQuc3R5bGUuZGlzcGxheTtcbiAgICAgICAgICAgICAgICAgICAgcGF0aCArPSBcIixcIiArIGVsZW1lbnQuc3R5bGUudmlzaWJpbGl0eTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgaWYgKGVsZW1lbnQudGFnTmFtZSA9PT0gXCJBXCIpIHtcbiAgICAgICAgICAgICAgICAgICAgcGF0aCArPSBcIixcIiArIGVsZW1lbnQuaHJlZjtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgcGF0aCArPSBcIl1cIjtcbiAgICAgICAgICAgICAgICByZXR1cm4gcGF0aDtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGlmIChzaWJsaW5nLm5vZGVUeXBlID09PSAxICYmIHNpYmxpbmcudGFnTmFtZSA9PT0gZWxlbWVudC50YWdOYW1lKSB7XG4gICAgICAgICAgICAgICAgc2libGluZ0luZGV4Kys7XG4gICAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICB9XG4gICAgLy8gSGVscGVyIGZvciBKU09OaWZ5aW5nIG9iamVjdHNcbiAgICBmdW5jdGlvbiBzZXJpYWxpemVPYmplY3Qob2JqZWN0LCBzdHJpbmdpZnlGdW5jdGlvbnMgPSBmYWxzZSkge1xuICAgICAgICAvLyBIYW5kbGUgcGVybWlzc2lvbnMgZXJyb3JzXG4gICAgICAgIHRyeSB7XG4gICAgICAgICAgICBpZiAob2JqZWN0ID09PSBudWxsKSB7XG4gICAgICAgICAgICAgICAgcmV0dXJuIFwibnVsbFwiO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgaWYgKHR5cGVvZiBvYmplY3QgPT09IFwiZnVuY3Rpb25cIikge1xuICAgICAgICAgICAgICAgIGlmIChzdHJpbmdpZnlGdW5jdGlvbnMpIHtcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIG9iamVjdC50b1N0cmluZygpO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIFwiRlVOQ1RJT05cIjtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBpZiAodHlwZW9mIG9iamVjdCAhPT0gXCJvYmplY3RcIikge1xuICAgICAgICAgICAgICAgIHJldHVybiBvYmplY3Q7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBjb25zdCBzZWVuT2JqZWN0cyA9IFtdO1xuICAgICAgICAgICAgcmV0dXJuIEpTT04uc3RyaW5naWZ5KG9iamVjdCwgZnVuY3Rpb24gKGtleSwgdmFsdWUpIHtcbiAgICAgICAgICAgICAgICBpZiAodmFsdWUgPT09IG51bGwpIHtcbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIFwibnVsbFwiO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBpZiAodHlwZW9mIHZhbHVlID09PSBcImZ1bmN0aW9uXCIpIHtcbiAgICAgICAgICAgICAgICAgICAgaWYgKHN0cmluZ2lmeUZ1bmN0aW9ucykge1xuICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIHZhbHVlLnRvU3RyaW5nKCk7XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gXCJGVU5DVElPTlwiO1xuICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIGlmICh0eXBlb2YgdmFsdWUgPT09IFwib2JqZWN0XCIpIHtcbiAgICAgICAgICAgICAgICAgICAgLy8gUmVtb3ZlIHdyYXBwaW5nIG9uIGNvbnRlbnQgb2JqZWN0c1xuICAgICAgICAgICAgICAgICAgICBpZiAoXCJ3cmFwcGVkSlNPYmplY3RcIiBpbiB2YWx1ZSkge1xuICAgICAgICAgICAgICAgICAgICAgICAgdmFsdWUgPSB2YWx1ZS53cmFwcGVkSlNPYmplY3Q7XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgLy8gU2VyaWFsaXplIERPTSBlbGVtZW50c1xuICAgICAgICAgICAgICAgICAgICBpZiAodmFsdWUgaW5zdGFuY2VvZiBIVE1MRWxlbWVudCkge1xuICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIGdldFBhdGhUb0RvbUVsZW1lbnQodmFsdWUpO1xuICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgIC8vIFByZXZlbnQgc2VyaWFsaXphdGlvbiBjeWNsZXNcbiAgICAgICAgICAgICAgICAgICAgaWYgKGtleSA9PT0gXCJcIiB8fCBzZWVuT2JqZWN0cy5pbmRleE9mKHZhbHVlKSA8IDApIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIHNlZW5PYmplY3RzLnB1c2godmFsdWUpO1xuICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIHZhbHVlO1xuICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgIGVsc2Uge1xuICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIHR5cGVvZiB2YWx1ZTtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICByZXR1cm4gdmFsdWU7XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgfVxuICAgICAgICBjYXRjaCAoZXJyb3IpIHtcbiAgICAgICAgICAgIGNvbnNvbGUubG9nKFwiT3BlbldQTTogU0VSSUFMSVpBVElPTiBFUlJPUjogXCIgKyBlcnJvcik7XG4gICAgICAgICAgICByZXR1cm4gXCJTRVJJQUxJWkFUSU9OIEVSUk9SOiBcIiArIGVycm9yO1xuICAgICAgICB9XG4gICAgfVxuICAgIGZ1bmN0aW9uIGxvZ0Vycm9yVG9Db25zb2xlKGVycm9yKSB7XG4gICAgICAgIGNvbnNvbGUubG9nKFwiT3BlbldQTTogRXJyb3IgbmFtZTogXCIgKyBlcnJvci5uYW1lKTtcbiAgICAgICAgY29uc29sZS5sb2coXCJPcGVuV1BNOiBFcnJvciBtZXNzYWdlOiBcIiArIGVycm9yLm1lc3NhZ2UpO1xuICAgICAgICBjb25zb2xlLmxvZyhcIk9wZW5XUE06IEVycm9yIGZpbGVuYW1lOiBcIiArIGVycm9yLmZpbGVOYW1lKTtcbiAgICAgICAgY29uc29sZS5sb2coXCJPcGVuV1BNOiBFcnJvciBsaW5lIG51bWJlcjogXCIgKyBlcnJvci5saW5lTnVtYmVyKTtcbiAgICAgICAgY29uc29sZS5sb2coXCJPcGVuV1BNOiBFcnJvciBzdGFjazogXCIgKyBlcnJvci5zdGFjayk7XG4gICAgfVxuICAgIC8vIEhlbHBlciB0byBnZXQgb3JpZ2luYXRpbmcgc2NyaXB0IHVybHNcbiAgICBmdW5jdGlvbiBnZXRTdGFja1RyYWNlKCkge1xuICAgICAgICBsZXQgc3RhY2s7XG4gICAgICAgIHRyeSB7XG4gICAgICAgICAgICB0aHJvdyBuZXcgRXJyb3IoKTtcbiAgICAgICAgfVxuICAgICAgICBjYXRjaCAoZXJyKSB7XG4gICAgICAgICAgICBzdGFjayA9IGVyci5zdGFjaztcbiAgICAgICAgfVxuICAgICAgICByZXR1cm4gc3RhY2s7XG4gICAgfVxuICAgIC8vIGZyb20gaHR0cDovL3N0YWNrb3ZlcmZsb3cuY29tL2EvNTIwMjE4NVxuICAgIFN0cmluZy5wcm90b3R5cGUucnNwbGl0ID0gZnVuY3Rpb24gKHNlcCwgbWF4c3BsaXQpIHtcbiAgICAgICAgY29uc3Qgc3BsaXQgPSB0aGlzLnNwbGl0KHNlcCk7XG4gICAgICAgIHJldHVybiBtYXhzcGxpdFxuICAgICAgICAgICAgPyBbc3BsaXQuc2xpY2UoMCwgLW1heHNwbGl0KS5qb2luKHNlcCldLmNvbmNhdChzcGxpdC5zbGljZSgtbWF4c3BsaXQpKVxuICAgICAgICAgICAgOiBzcGxpdDtcbiAgICB9O1xuICAgIGZ1bmN0aW9uIGdldE9yaWdpbmF0aW5nU2NyaXB0Q29udGV4dChnZXRDYWxsU3RhY2sgPSBmYWxzZSkge1xuICAgICAgICBjb25zdCB0cmFjZSA9IGdldFN0YWNrVHJhY2UoKVxuICAgICAgICAgICAgLnRyaW0oKVxuICAgICAgICAgICAgLnNwbGl0KFwiXFxuXCIpO1xuICAgICAgICAvLyByZXR1cm4gYSBjb250ZXh0IG9iamVjdCBldmVuIGlmIHRoZXJlIGlzIGFuIGVycm9yXG4gICAgICAgIGNvbnN0IGVtcHR5X2NvbnRleHQgPSB7XG4gICAgICAgICAgICBzY3JpcHRVcmw6IFwiXCIsXG4gICAgICAgICAgICBzY3JpcHRMaW5lOiBcIlwiLFxuICAgICAgICAgICAgc2NyaXB0Q29sOiBcIlwiLFxuICAgICAgICAgICAgZnVuY05hbWU6IFwiXCIsXG4gICAgICAgICAgICBzY3JpcHRMb2NFdmFsOiBcIlwiLFxuICAgICAgICAgICAgY2FsbFN0YWNrOiBcIlwiLFxuICAgICAgICB9O1xuICAgICAgICBpZiAodHJhY2UubGVuZ3RoIDwgNCkge1xuICAgICAgICAgICAgcmV0dXJuIGVtcHR5X2NvbnRleHQ7XG4gICAgICAgIH1cbiAgICAgICAgLy8gMCwgMSBhbmQgMiBhcmUgT3BlbldQTSdzIG93biBmdW5jdGlvbnMgKGUuZy4gZ2V0U3RhY2tUcmFjZSksIHNraXAgdGhlbS5cbiAgICAgICAgY29uc3QgY2FsbFNpdGUgPSB0cmFjZVszXTtcbiAgICAgICAgaWYgKCFjYWxsU2l0ZSkge1xuICAgICAgICAgICAgcmV0dXJuIGVtcHR5X2NvbnRleHQ7XG4gICAgICAgIH1cbiAgICAgICAgLypcbiAgICAgICAgICogU3RhY2sgZnJhbWUgZm9ybWF0IGlzIHNpbXBseTogRlVOQ19OQU1FQEZJTEVOQU1FOkxJTkVfTk86Q09MVU1OX05PXG4gICAgICAgICAqXG4gICAgICAgICAqIElmIGV2YWwgb3IgRnVuY3Rpb24gaXMgaW52b2x2ZWQgd2UgaGF2ZSBhbiBhZGRpdGlvbmFsIHBhcnQgYWZ0ZXIgdGhlIEZJTEVOQU1FLCBlLmcuOlxuICAgICAgICAgKiBGVU5DX05BTUVARklMRU5BTUUgbGluZSAxMjMgPiBldmFsIGxpbmUgMSA+IGV2YWw6TElORV9OTzpDT0xVTU5fTk9cbiAgICAgICAgICogb3IgRlVOQ19OQU1FQEZJTEVOQU1FIGxpbmUgMjM0ID4gRnVuY3Rpb246TElORV9OTzpDT0xVTU5fTk9cbiAgICAgICAgICpcbiAgICAgICAgICogV2Ugc3RvcmUgdGhlIHBhcnQgYmV0d2VlbiB0aGUgRklMRU5BTUUgYW5kIHRoZSBMSU5FX05PIGluIHNjcmlwdExvY0V2YWxcbiAgICAgICAgICovXG4gICAgICAgIHRyeSB7XG4gICAgICAgICAgICBsZXQgc2NyaXB0VXJsID0gXCJcIjtcbiAgICAgICAgICAgIGxldCBzY3JpcHRMb2NFdmFsID0gXCJcIjsgLy8gZm9yIGV2YWwgb3IgRnVuY3Rpb24gY2FsbHNcbiAgICAgICAgICAgIGNvbnN0IGNhbGxTaXRlUGFydHMgPSBjYWxsU2l0ZS5zcGxpdChcIkBcIik7XG4gICAgICAgICAgICBjb25zdCBmdW5jTmFtZSA9IGNhbGxTaXRlUGFydHNbMF0gfHwgXCJcIjtcbiAgICAgICAgICAgIGNvbnN0IGl0ZW1zID0gY2FsbFNpdGVQYXJ0c1sxXS5yc3BsaXQoXCI6XCIsIDIpO1xuICAgICAgICAgICAgY29uc3QgY29sdW1uTm8gPSBpdGVtc1tpdGVtcy5sZW5ndGggLSAxXTtcbiAgICAgICAgICAgIGNvbnN0IGxpbmVObyA9IGl0ZW1zW2l0ZW1zLmxlbmd0aCAtIDJdO1xuICAgICAgICAgICAgY29uc3Qgc2NyaXB0RmlsZU5hbWUgPSBpdGVtc1tpdGVtcy5sZW5ndGggLSAzXSB8fCBcIlwiO1xuICAgICAgICAgICAgY29uc3QgbGluZU5vSWR4ID0gc2NyaXB0RmlsZU5hbWUuaW5kZXhPZihcIiBsaW5lIFwiKTsgLy8gbGluZSBpbiB0aGUgVVJMIG1lYW5zIGV2YWwgb3IgRnVuY3Rpb25cbiAgICAgICAgICAgIGlmIChsaW5lTm9JZHggPT09IC0xKSB7XG4gICAgICAgICAgICAgICAgc2NyaXB0VXJsID0gc2NyaXB0RmlsZU5hbWU7IC8vIFRPRE86IHNvbWV0aW1lcyB3ZSBoYXZlIGZpbGVuYW1lIG9ubHksIGUuZy4gWFguanNcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIGVsc2Uge1xuICAgICAgICAgICAgICAgIHNjcmlwdFVybCA9IHNjcmlwdEZpbGVOYW1lLnNsaWNlKDAsIGxpbmVOb0lkeCk7XG4gICAgICAgICAgICAgICAgc2NyaXB0TG9jRXZhbCA9IHNjcmlwdEZpbGVOYW1lLnNsaWNlKGxpbmVOb0lkeCArIDEsIHNjcmlwdEZpbGVOYW1lLmxlbmd0aCk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBjb25zdCBjYWxsQ29udGV4dCA9IHtcbiAgICAgICAgICAgICAgICBzY3JpcHRVcmwsXG4gICAgICAgICAgICAgICAgc2NyaXB0TGluZTogbGluZU5vLFxuICAgICAgICAgICAgICAgIHNjcmlwdENvbDogY29sdW1uTm8sXG4gICAgICAgICAgICAgICAgZnVuY05hbWUsXG4gICAgICAgICAgICAgICAgc2NyaXB0TG9jRXZhbCxcbiAgICAgICAgICAgICAgICBjYWxsU3RhY2s6IGdldENhbGxTdGFja1xuICAgICAgICAgICAgICAgICAgICA/IHRyYWNlXG4gICAgICAgICAgICAgICAgICAgICAgICAuc2xpY2UoMylcbiAgICAgICAgICAgICAgICAgICAgICAgIC5qb2luKFwiXFxuXCIpXG4gICAgICAgICAgICAgICAgICAgICAgICAudHJpbSgpXG4gICAgICAgICAgICAgICAgICAgIDogXCJcIixcbiAgICAgICAgICAgIH07XG4gICAgICAgICAgICByZXR1cm4gY2FsbENvbnRleHQ7XG4gICAgICAgIH1cbiAgICAgICAgY2F0Y2ggKGUpIHtcbiAgICAgICAgICAgIGNvbnNvbGUubG9nKFwiT3BlbldQTTogRXJyb3IgcGFyc2luZyB0aGUgc2NyaXB0IGNvbnRleHRcIiwgZSwgY2FsbFNpdGUpO1xuICAgICAgICAgICAgcmV0dXJuIGVtcHR5X2NvbnRleHQ7XG4gICAgICAgIH1cbiAgICB9XG4gICAgLy8gQ291bnRlciB0byBjYXAgIyBvZiBjYWxscyBsb2dnZWQgZm9yIGVhY2ggc2NyaXB0L2FwaSBjb21iaW5hdGlvblxuICAgIGNvbnN0IG1heExvZ0NvdW50ID0gNTAwO1xuICAgIGNvbnN0IGxvZ0NvdW50ZXIgPSBuZXcgT2JqZWN0KCk7XG4gICAgZnVuY3Rpb24gdXBkYXRlQ291bnRlckFuZENoZWNrSWZPdmVyKHNjcmlwdFVybCwgc3ltYm9sKSB7XG4gICAgICAgIGNvbnN0IGtleSA9IHNjcmlwdFVybCArIFwifFwiICsgc3ltYm9sO1xuICAgICAgICBpZiAoa2V5IGluIGxvZ0NvdW50ZXIgJiYgbG9nQ291bnRlcltrZXldID49IG1heExvZ0NvdW50KSB7XG4gICAgICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICAgICAgfVxuICAgICAgICBlbHNlIGlmICghKGtleSBpbiBsb2dDb3VudGVyKSkge1xuICAgICAgICAgICAgbG9nQ291bnRlcltrZXldID0gMTtcbiAgICAgICAgfVxuICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgIGxvZ0NvdW50ZXJba2V5XSArPSAxO1xuICAgICAgICB9XG4gICAgICAgIHJldHVybiBmYWxzZTtcbiAgICB9XG4gICAgLy8gUHJldmVudCBsb2dnaW5nIG9mIGdldHMgYXJpc2luZyBmcm9tIGxvZ2dpbmdcbiAgICBsZXQgaW5Mb2cgPSBmYWxzZTtcbiAgICAvLyBUbyBrZWVwIHRyYWNrIG9mIHRoZSBvcmlnaW5hbCBvcmRlciBvZiBldmVudHNcbiAgICBsZXQgb3JkaW5hbCA9IDA7XG4gICAgLy8gRm9yIGdldHMsIHNldHMsIGV0Yy4gb24gYSBzaW5nbGUgdmFsdWVcbiAgICBmdW5jdGlvbiBsb2dWYWx1ZShpbnN0cnVtZW50ZWRWYXJpYWJsZU5hbWUsIHZhbHVlLCBvcGVyYXRpb24sIGNhbGxDb250ZXh0LCBsb2dTZXR0aW5ncykge1xuICAgICAgICBpZiAoaW5Mb2cpIHtcbiAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgfVxuICAgICAgICBpbkxvZyA9IHRydWU7XG4gICAgICAgIGNvbnN0IG92ZXJMaW1pdCA9IHVwZGF0ZUNvdW50ZXJBbmRDaGVja0lmT3ZlcihjYWxsQ29udGV4dC5zY3JpcHRVcmwsIGluc3RydW1lbnRlZFZhcmlhYmxlTmFtZSk7XG4gICAgICAgIGlmIChvdmVyTGltaXQpIHtcbiAgICAgICAgICAgIGluTG9nID0gZmFsc2U7XG4gICAgICAgICAgICByZXR1cm47XG4gICAgICAgIH1cbiAgICAgICAgY29uc3QgbXNnID0ge1xuICAgICAgICAgICAgb3BlcmF0aW9uLFxuICAgICAgICAgICAgc3ltYm9sOiBpbnN0cnVtZW50ZWRWYXJpYWJsZU5hbWUsXG4gICAgICAgICAgICB2YWx1ZTogc2VyaWFsaXplT2JqZWN0KHZhbHVlLCAhIWxvZ1NldHRpbmdzLmxvZ0Z1bmN0aW9uc0FzU3RyaW5ncyksXG4gICAgICAgICAgICBzY3JpcHRVcmw6IGNhbGxDb250ZXh0LnNjcmlwdFVybCxcbiAgICAgICAgICAgIHNjcmlwdExpbmU6IGNhbGxDb250ZXh0LnNjcmlwdExpbmUsXG4gICAgICAgICAgICBzY3JpcHRDb2w6IGNhbGxDb250ZXh0LnNjcmlwdENvbCxcbiAgICAgICAgICAgIGZ1bmNOYW1lOiBjYWxsQ29udGV4dC5mdW5jTmFtZSxcbiAgICAgICAgICAgIHNjcmlwdExvY0V2YWw6IGNhbGxDb250ZXh0LnNjcmlwdExvY0V2YWwsXG4gICAgICAgICAgICBjYWxsU3RhY2s6IGNhbGxDb250ZXh0LmNhbGxTdGFjayxcbiAgICAgICAgICAgIG9yZGluYWw6IG9yZGluYWwrKyxcbiAgICAgICAgfTtcbiAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgIHNlbmQoXCJsb2dWYWx1ZVwiLCBtc2cpO1xuICAgICAgICB9XG4gICAgICAgIGNhdGNoIChlcnJvcikge1xuICAgICAgICAgICAgY29uc29sZS5sb2coXCJPcGVuV1BNOiBVbnN1Y2Nlc3NmdWwgdmFsdWUgbG9nIVwiKTtcbiAgICAgICAgICAgIGxvZ0Vycm9yVG9Db25zb2xlKGVycm9yKTtcbiAgICAgICAgfVxuICAgICAgICBpbkxvZyA9IGZhbHNlO1xuICAgIH1cbiAgICAvLyBGb3IgZnVuY3Rpb25zXG4gICAgZnVuY3Rpb24gbG9nQ2FsbChpbnN0cnVtZW50ZWRGdW5jdGlvbk5hbWUsIGFyZ3MsIGNhbGxDb250ZXh0LCBsb2dTZXR0aW5ncykge1xuICAgICAgICBpZiAoaW5Mb2cpIHtcbiAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgfVxuICAgICAgICBpbkxvZyA9IHRydWU7XG4gICAgICAgIGNvbnN0IG92ZXJMaW1pdCA9IHVwZGF0ZUNvdW50ZXJBbmRDaGVja0lmT3ZlcihjYWxsQ29udGV4dC5zY3JpcHRVcmwsIGluc3RydW1lbnRlZEZ1bmN0aW9uTmFtZSk7XG4gICAgICAgIGlmIChvdmVyTGltaXQpIHtcbiAgICAgICAgICAgIGluTG9nID0gZmFsc2U7XG4gICAgICAgICAgICByZXR1cm47XG4gICAgICAgIH1cbiAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgIC8vIENvbnZlcnQgc3BlY2lhbCBhcmd1bWVudHMgYXJyYXkgdG8gYSBzdGFuZGFyZCBhcnJheSBmb3IgSlNPTmlmeWluZ1xuICAgICAgICAgICAgY29uc3Qgc2VyaWFsQXJncyA9IFtdO1xuICAgICAgICAgICAgZm9yIChsZXQgaSA9IDA7IGkgPCBhcmdzLmxlbmd0aDsgaSsrKSB7XG4gICAgICAgICAgICAgICAgc2VyaWFsQXJncy5wdXNoKHNlcmlhbGl6ZU9iamVjdChhcmdzW2ldLCAhIWxvZ1NldHRpbmdzLmxvZ0Z1bmN0aW9uc0FzU3RyaW5ncykpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgY29uc3QgbXNnID0ge1xuICAgICAgICAgICAgICAgIG9wZXJhdGlvbjogXCJjYWxsXCIsXG4gICAgICAgICAgICAgICAgc3ltYm9sOiBpbnN0cnVtZW50ZWRGdW5jdGlvbk5hbWUsXG4gICAgICAgICAgICAgICAgYXJnczogc2VyaWFsQXJncyxcbiAgICAgICAgICAgICAgICB2YWx1ZTogXCJcIixcbiAgICAgICAgICAgICAgICBzY3JpcHRVcmw6IGNhbGxDb250ZXh0LnNjcmlwdFVybCxcbiAgICAgICAgICAgICAgICBzY3JpcHRMaW5lOiBjYWxsQ29udGV4dC5zY3JpcHRMaW5lLFxuICAgICAgICAgICAgICAgIHNjcmlwdENvbDogY2FsbENvbnRleHQuc2NyaXB0Q29sLFxuICAgICAgICAgICAgICAgIGZ1bmNOYW1lOiBjYWxsQ29udGV4dC5mdW5jTmFtZSxcbiAgICAgICAgICAgICAgICBzY3JpcHRMb2NFdmFsOiBjYWxsQ29udGV4dC5zY3JpcHRMb2NFdmFsLFxuICAgICAgICAgICAgICAgIGNhbGxTdGFjazogY2FsbENvbnRleHQuY2FsbFN0YWNrLFxuICAgICAgICAgICAgICAgIG9yZGluYWw6IG9yZGluYWwrKyxcbiAgICAgICAgICAgIH07XG4gICAgICAgICAgICBzZW5kKFwibG9nQ2FsbFwiLCBtc2cpO1xuICAgICAgICB9XG4gICAgICAgIGNhdGNoIChlcnJvcikge1xuICAgICAgICAgICAgY29uc29sZS5sb2coXCJPcGVuV1BNOiBVbnN1Y2Nlc3NmdWwgY2FsbCBsb2c6IFwiICsgaW5zdHJ1bWVudGVkRnVuY3Rpb25OYW1lKTtcbiAgICAgICAgICAgIGxvZ0Vycm9yVG9Db25zb2xlKGVycm9yKTtcbiAgICAgICAgfVxuICAgICAgICBpbkxvZyA9IGZhbHNlO1xuICAgIH1cbiAgICAvLyBSb3VnaCBpbXBsZW1lbnRhdGlvbnMgb2YgT2JqZWN0LmdldFByb3BlcnR5RGVzY3JpcHRvciBhbmQgT2JqZWN0LmdldFByb3BlcnR5TmFtZXNcbiAgICAvLyBTZWUgaHR0cDovL3dpa2kuZWNtYXNjcmlwdC5vcmcvZG9rdS5waHA/aWQ9aGFybW9ueTpleHRlbmRlZF9vYmplY3RfYXBpXG4gICAgT2JqZWN0LmdldFByb3BlcnR5RGVzY3JpcHRvciA9IGZ1bmN0aW9uIChzdWJqZWN0LCBuYW1lKSB7XG4gICAgICAgIGxldCBwZCA9IE9iamVjdC5nZXRPd25Qcm9wZXJ0eURlc2NyaXB0b3Ioc3ViamVjdCwgbmFtZSk7XG4gICAgICAgIGxldCBwcm90byA9IE9iamVjdC5nZXRQcm90b3R5cGVPZihzdWJqZWN0KTtcbiAgICAgICAgd2hpbGUgKHBkID09PSB1bmRlZmluZWQgJiYgcHJvdG8gIT09IG51bGwpIHtcbiAgICAgICAgICAgIHBkID0gT2JqZWN0LmdldE93blByb3BlcnR5RGVzY3JpcHRvcihwcm90bywgbmFtZSk7XG4gICAgICAgICAgICBwcm90byA9IE9iamVjdC5nZXRQcm90b3R5cGVPZihwcm90byk7XG4gICAgICAgIH1cbiAgICAgICAgcmV0dXJuIHBkO1xuICAgIH07XG4gICAgT2JqZWN0LmdldFByb3BlcnR5TmFtZXMgPSBmdW5jdGlvbiAoc3ViamVjdCkge1xuICAgICAgICBsZXQgcHJvcHMgPSBPYmplY3QuZ2V0T3duUHJvcGVydHlOYW1lcyhzdWJqZWN0KTtcbiAgICAgICAgbGV0IHByb3RvID0gT2JqZWN0LmdldFByb3RvdHlwZU9mKHN1YmplY3QpO1xuICAgICAgICB3aGlsZSAocHJvdG8gIT09IG51bGwpIHtcbiAgICAgICAgICAgIHByb3BzID0gcHJvcHMuY29uY2F0KE9iamVjdC5nZXRPd25Qcm9wZXJ0eU5hbWVzKHByb3RvKSk7XG4gICAgICAgICAgICBwcm90byA9IE9iamVjdC5nZXRQcm90b3R5cGVPZihwcm90byk7XG4gICAgICAgIH1cbiAgICAgICAgLy8gRklYTUU6IHJlbW92ZSBkdXBsaWNhdGUgcHJvcGVydHkgbmFtZXMgZnJvbSBwcm9wc1xuICAgICAgICByZXR1cm4gcHJvcHM7XG4gICAgfTtcbiAgICAvKlxuICAgICAqICBEaXJlY3QgaW5zdHJ1bWVudGF0aW9uIG9mIGphdmFzY3JpcHQgb2JqZWN0c1xuICAgICAqL1xuICAgIGZ1bmN0aW9uIGlzT2JqZWN0KG9iamVjdCwgcHJvcGVydHlOYW1lKSB7XG4gICAgICAgIGxldCBwcm9wZXJ0eTtcbiAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgIHByb3BlcnR5ID0gb2JqZWN0W3Byb3BlcnR5TmFtZV07XG4gICAgICAgIH1cbiAgICAgICAgY2F0Y2ggKGVycm9yKSB7XG4gICAgICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICAgIH1cbiAgICAgICAgaWYgKHByb3BlcnR5ID09PSBudWxsKSB7XG4gICAgICAgICAgICAvLyBudWxsIGlzIHR5cGUgXCJvYmplY3RcIlxuICAgICAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgICAgICB9XG4gICAgICAgIHJldHVybiB0eXBlb2YgcHJvcGVydHkgPT09IFwib2JqZWN0XCI7XG4gICAgfVxuICAgIGZ1bmN0aW9uIGluc3RydW1lbnRPYmplY3Qob2JqZWN0LCBvYmplY3ROYW1lLCBsb2dTZXR0aW5ncyA9IHt9KSB7XG4gICAgICAgIC8vIFVzZSBmb3Igb2JqZWN0cyBvciBvYmplY3QgcHJvdG90eXBlc1xuICAgICAgICAvL1xuICAgICAgICAvLyBQYXJhbWV0ZXJzXG4gICAgICAgIC8vIC0tLS0tLS0tLS1cbiAgICAgICAgLy8gICBvYmplY3QgOiBPYmplY3RcbiAgICAgICAgLy8gICAgIE9iamVjdCB0byBpbnN0cnVtZW50XG4gICAgICAgIC8vICAgb2JqZWN0TmFtZSA6IFN0cmluZ1xuICAgICAgICAvLyAgICAgTmFtZSBvZiB0aGUgb2JqZWN0IHRvIGJlIGluc3RydW1lbnRlZCAoc2F2ZWQgdG8gZGF0YWJhc2UpXG4gICAgICAgIC8vICAgbG9nU2V0dGluZ3MgOiBPYmplY3RcbiAgICAgICAgLy8gICAgIChvcHRpb25hbCkgb2JqZWN0IHRoYXQgY2FuIGJlIHVzZWQgdG8gc3BlY2lmeSBhZGRpdGlvbmFsIGxvZ2dpbmdcbiAgICAgICAgLy8gICAgIGNvbmZpZ3VyYXRpb25zLiBTZWUgYXZhaWxhYmxlIG9wdGlvbnMgYmVsb3cuXG4gICAgICAgIC8vXG4gICAgICAgIC8vIGxvZ1NldHRpbmdzIG9wdGlvbnMgKGFsbCBvcHRpb25hbClcbiAgICAgICAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLVxuICAgICAgICAvLyAgIHByb3BlcnRpZXNUb0luc3RydW1lbnQgOiBBcnJheVxuICAgICAgICAvLyAgICAgQW4gYXJyYXkgb2YgcHJvcGVydGllcyB0byBpbnN0cnVtZW50IG9uIHRoaXMgb2JqZWN0LiBEZWZhdWx0IGlzXG4gICAgICAgIC8vICAgICBhbGwgcHJvcGVydGllcy5cbiAgICAgICAgLy8gICBleGNsdWRlZFByb3BlcnRpZXMgOiBBcnJheVxuICAgICAgICAvLyAgICAgUHJvcGVydGllcyBleGNsdWRlZCBmcm9tIGluc3RydW1lbnRhdGlvbi4gRGVmYXVsdCBpcyBhbiBlbXB0eVxuICAgICAgICAvLyAgICAgYXJyYXkuXG4gICAgICAgIC8vICAgbG9nQ2FsbFN0YWNrIDogYm9vbGVhblxuICAgICAgICAvLyAgICAgU2V0IHRvIHRydWUgc2F2ZSB0aGUgY2FsbCBzdGFjayBpbmZvIHdpdGggZWFjaCBwcm9wZXJ0eSBjYWxsLlxuICAgICAgICAvLyAgICAgRGVmYXVsdCBpcyBgZmFsc2VgLlxuICAgICAgICAvLyAgIGxvZ0Z1bmN0aW9uc0FzU3RyaW5ncyA6IGJvb2xlYW5cbiAgICAgICAgLy8gICAgIFNldCB0byB0cnVlIHRvIHNhdmUgZnVuY3Rpb25hbCBhcmd1bWVudHMgYXMgc3RyaW5ncyBkdXJpbmdcbiAgICAgICAgLy8gICAgIGFyZ3VtZW50IHNlcmlhbGl6YXRpb24uIERlZmF1bHQgaXMgYGZhbHNlYC5cbiAgICAgICAgLy8gICBwcmV2ZW50U2V0cyA6IGJvb2xlYW5cbiAgICAgICAgLy8gICAgIFNldCB0byB0cnVlIHRvIHByZXZlbnQgbmVzdGVkIG9iamVjdHMgYW5kIGZ1bmN0aW9ucyBmcm9tIGJlaW5nXG4gICAgICAgIC8vICAgICBvdmVyd3JpdHRlbiAoYW5kIHRodXMgaGF2aW5nIHRoZWlyIGluc3RydW1lbnRhdGlvbiByZW1vdmVkKS5cbiAgICAgICAgLy8gICAgIE90aGVyIHByb3BlcnRpZXMgKHN0YXRpYyB2YWx1ZXMpIGNhbiBzdGlsbCBiZSBzZXQgd2l0aCB0aGlzIGlzXG4gICAgICAgIC8vICAgICBlbmFibGVkLiBEZWZhdWx0IGlzIGBmYWxzZWAuXG4gICAgICAgIC8vICAgcmVjdXJzaXZlIDogYm9vbGVhblxuICAgICAgICAvLyAgICAgU2V0IHRvIGB0cnVlYCB0byByZWN1cnNpdmVseSBpbnN0cnVtZW50IGFsbCBvYmplY3QgcHJvcGVydGllcyBvZlxuICAgICAgICAvLyAgICAgdGhlIGdpdmVuIGBvYmplY3RgLiBEZWZhdWx0IGlzIGBmYWxzZWBcbiAgICAgICAgLy8gICAgIE5PVEU6XG4gICAgICAgIC8vICAgICAgICgxKWBsb2dTZXR0aW5nc1sncHJvcGVydGllc1RvSW5zdHJ1bWVudCddYCBkb2VzIG5vdCBwcm9wYWdhdGVcbiAgICAgICAgLy8gICAgICAgICAgIHRvIHN1Yi1vYmplY3RzLlxuICAgICAgICAvLyAgICAgICAoMikgU3ViLW9iamVjdHMgb2YgcHJvdG90eXBlcyBjYW4gbm90IGJlIGluc3RydW1lbnRlZFxuICAgICAgICAvLyAgICAgICAgICAgcmVjdXJzaXZlbHkgYXMgdGhlc2UgcHJvcGVydGllcyBjYW4gbm90IGJlIGFjY2Vzc2VkXG4gICAgICAgIC8vICAgICAgICAgICB1bnRpbCBhbiBpbnN0YW5jZSBvZiB0aGUgcHJvdG90eXBlIGlzIGNyZWF0ZWQuXG4gICAgICAgIC8vICAgZGVwdGggOiBpbnRlZ2VyXG4gICAgICAgIC8vICAgICBSZWN1cnNpb24gbGltaXQgd2hlbiBpbnN0cnVtZW50aW5nIG9iamVjdCByZWN1cnNpdmVseS5cbiAgICAgICAgLy8gICAgIERlZmF1bHQgaXMgYDVgLlxuICAgICAgICBjb25zdCBwcm9wZXJ0aWVzID0gbG9nU2V0dGluZ3MucHJvcGVydGllc1RvSW5zdHJ1bWVudFxuICAgICAgICAgICAgPyBsb2dTZXR0aW5ncy5wcm9wZXJ0aWVzVG9JbnN0cnVtZW50XG4gICAgICAgICAgICA6IE9iamVjdC5nZXRQcm9wZXJ0eU5hbWVzKG9iamVjdCk7XG4gICAgICAgIGZvciAobGV0IGkgPSAwOyBpIDwgcHJvcGVydGllcy5sZW5ndGg7IGkrKykge1xuICAgICAgICAgICAgaWYgKGxvZ1NldHRpbmdzLmV4Y2x1ZGVkUHJvcGVydGllcyAmJlxuICAgICAgICAgICAgICAgIGxvZ1NldHRpbmdzLmV4Y2x1ZGVkUHJvcGVydGllcy5pbmRleE9mKHByb3BlcnRpZXNbaV0pID4gLTEpIHtcbiAgICAgICAgICAgICAgICBjb250aW51ZTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIC8vIElmIGByZWN1cnNpdmVgIGZsYWcgc2V0IHdlIHdhbnQgdG8gcmVjdXJzaXZlbHkgaW5zdHJ1bWVudCBhbnlcbiAgICAgICAgICAgIC8vIG9iamVjdCBwcm9wZXJ0aWVzIHRoYXQgYXJlbid0IHRoZSBwcm90b3R5cGUgb2JqZWN0LiBPbmx5IHJlY3Vyc2UgaWZcbiAgICAgICAgICAgIC8vIGRlcHRoIG5vdCBzZXQgKGF0IHdoaWNoIHBvaW50IGl0cyBzZXQgdG8gZGVmYXVsdCkgb3Igbm90IGF0IGxpbWl0LlxuICAgICAgICAgICAgaWYgKCEhbG9nU2V0dGluZ3MucmVjdXJzaXZlICYmXG4gICAgICAgICAgICAgICAgcHJvcGVydGllc1tpXSAhPT0gXCJfX3Byb3RvX19cIiAmJlxuICAgICAgICAgICAgICAgIGlzT2JqZWN0KG9iamVjdCwgcHJvcGVydGllc1tpXSkgJiZcbiAgICAgICAgICAgICAgICAoIShcImRlcHRoXCIgaW4gbG9nU2V0dGluZ3MpIHx8IGxvZ1NldHRpbmdzLmRlcHRoID4gMCkpIHtcbiAgICAgICAgICAgICAgICAvLyBzZXQgcmVjdXJzaW9uIGxpbWl0IHRvIGRlZmF1bHQgaWYgbm90IHNwZWNpZmllZFxuICAgICAgICAgICAgICAgIGlmICghKFwiZGVwdGhcIiBpbiBsb2dTZXR0aW5ncykpIHtcbiAgICAgICAgICAgICAgICAgICAgbG9nU2V0dGluZ3MuZGVwdGggPSA1O1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICBpbnN0cnVtZW50T2JqZWN0KG9iamVjdFtwcm9wZXJ0aWVzW2ldXSwgb2JqZWN0TmFtZSArIFwiLlwiICsgcHJvcGVydGllc1tpXSwge1xuICAgICAgICAgICAgICAgICAgICBleGNsdWRlZFByb3BlcnRpZXM6IGxvZ1NldHRpbmdzLmV4Y2x1ZGVkUHJvcGVydGllcyxcbiAgICAgICAgICAgICAgICAgICAgbG9nQ2FsbFN0YWNrOiBsb2dTZXR0aW5ncy5sb2dDYWxsU3RhY2ssXG4gICAgICAgICAgICAgICAgICAgIGxvZ0Z1bmN0aW9uc0FzU3RyaW5nczogbG9nU2V0dGluZ3MubG9nRnVuY3Rpb25zQXNTdHJpbmdzLFxuICAgICAgICAgICAgICAgICAgICBwcmV2ZW50U2V0czogbG9nU2V0dGluZ3MucHJldmVudFNldHMsXG4gICAgICAgICAgICAgICAgICAgIHJlY3Vyc2l2ZTogbG9nU2V0dGluZ3MucmVjdXJzaXZlLFxuICAgICAgICAgICAgICAgICAgICBkZXB0aDogbG9nU2V0dGluZ3MuZGVwdGggLSAxLFxuICAgICAgICAgICAgICAgIH0pO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgICAgICBpbnN0cnVtZW50T2JqZWN0UHJvcGVydHkob2JqZWN0LCBvYmplY3ROYW1lLCBwcm9wZXJ0aWVzW2ldLCBsb2dTZXR0aW5ncyk7XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBjYXRjaCAoZXJyb3IpIHtcbiAgICAgICAgICAgICAgICBsb2dFcnJvclRvQ29uc29sZShlcnJvcik7XG4gICAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICB9XG4gICAgaWYgKHRlc3RpbmcpIHtcbiAgICAgICAgd2luZG93Lmluc3RydW1lbnRPYmplY3QgPSBpbnN0cnVtZW50T2JqZWN0O1xuICAgIH1cbiAgICAvLyBMb2cgY2FsbHMgdG8gYSBnaXZlbiBmdW5jdGlvblxuICAgIC8vIFRoaXMgaGVscGVyIGZ1bmN0aW9uIHJldHVybnMgYSB3cmFwcGVyIGFyb3VuZCBgZnVuY2Agd2hpY2ggbG9ncyBjYWxsc1xuICAgIC8vIHRvIGBmdW5jYC4gYG9iamVjdE5hbWVgIGFuZCBgbWV0aG9kTmFtZWAgYXJlIHVzZWQgc3RyaWN0bHkgdG8gaWRlbnRpZnlcbiAgICAvLyB3aGljaCBvYmplY3QgbWV0aG9kIGBmdW5jYCBpcyBjb21pbmcgZnJvbSBpbiB0aGUgbG9nc1xuICAgIGZ1bmN0aW9uIGluc3RydW1lbnRGdW5jdGlvbihvYmplY3ROYW1lLCBtZXRob2ROYW1lLCBmdW5jLCBsb2dTZXR0aW5ncykge1xuICAgICAgICByZXR1cm4gZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgY29uc3QgY2FsbENvbnRleHQgPSBnZXRPcmlnaW5hdGluZ1NjcmlwdENvbnRleHQoISFsb2dTZXR0aW5ncy5sb2dDYWxsU3RhY2spO1xuICAgICAgICAgICAgbG9nQ2FsbChvYmplY3ROYW1lICsgXCIuXCIgKyBtZXRob2ROYW1lLCBhcmd1bWVudHMsIGNhbGxDb250ZXh0LCBsb2dTZXR0aW5ncyk7XG4gICAgICAgICAgICByZXR1cm4gZnVuYy5hcHBseSh0aGlzLCBhcmd1bWVudHMpO1xuICAgICAgICB9O1xuICAgIH1cbiAgICAvLyBMb2cgcHJvcGVydGllcyBvZiBwcm90b3R5cGVzIGFuZCBvYmplY3RzXG4gICAgZnVuY3Rpb24gaW5zdHJ1bWVudE9iamVjdFByb3BlcnR5KG9iamVjdCwgb2JqZWN0TmFtZSwgcHJvcGVydHlOYW1lLCBsb2dTZXR0aW5ncyA9IHt9KSB7XG4gICAgICAgIC8vIFN0b3JlIG9yaWdpbmFsIGRlc2NyaXB0b3IgaW4gY2xvc3VyZVxuICAgICAgICBjb25zdCBwcm9wRGVzYyA9IE9iamVjdC5nZXRQcm9wZXJ0eURlc2NyaXB0b3Iob2JqZWN0LCBwcm9wZXJ0eU5hbWUpO1xuICAgICAgICBpZiAoIXByb3BEZXNjKSB7XG4gICAgICAgICAgICBjb25zb2xlLmVycm9yKFwiUHJvcGVydHkgZGVzY3JpcHRvciBub3QgZm91bmQgZm9yXCIsIG9iamVjdE5hbWUsIHByb3BlcnR5TmFtZSwgb2JqZWN0KTtcbiAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgfVxuICAgICAgICAvLyBJbnN0cnVtZW50IGRhdGEgb3IgYWNjZXNzb3IgcHJvcGVydHkgZGVzY3JpcHRvcnNcbiAgICAgICAgY29uc3Qgb3JpZ2luYWxHZXR0ZXIgPSBwcm9wRGVzYy5nZXQ7XG4gICAgICAgIGNvbnN0IG9yaWdpbmFsU2V0dGVyID0gcHJvcERlc2Muc2V0O1xuICAgICAgICBsZXQgb3JpZ2luYWxWYWx1ZSA9IHByb3BEZXNjLnZhbHVlO1xuICAgICAgICAvLyBXZSBvdmVyd3JpdGUgYm90aCBkYXRhIGFuZCBhY2Nlc3NvciBwcm9wZXJ0aWVzIGFzIGFuIGluc3RydW1lbnRlZFxuICAgICAgICAvLyBhY2Nlc3NvciBwcm9wZXJ0eVxuICAgICAgICBPYmplY3QuZGVmaW5lUHJvcGVydHkob2JqZWN0LCBwcm9wZXJ0eU5hbWUsIHtcbiAgICAgICAgICAgIGNvbmZpZ3VyYWJsZTogdHJ1ZSxcbiAgICAgICAgICAgIGdldDogKGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgICAgICByZXR1cm4gZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgICAgICAgICBsZXQgb3JpZ1Byb3BlcnR5O1xuICAgICAgICAgICAgICAgICAgICBjb25zdCBjYWxsQ29udGV4dCA9IGdldE9yaWdpbmF0aW5nU2NyaXB0Q29udGV4dCghIWxvZ1NldHRpbmdzLmxvZ0NhbGxTdGFjayk7XG4gICAgICAgICAgICAgICAgICAgIC8vIGdldCBvcmlnaW5hbCB2YWx1ZVxuICAgICAgICAgICAgICAgICAgICBpZiAob3JpZ2luYWxHZXR0ZXIpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIC8vIGlmIGFjY2Vzc29yIHByb3BlcnR5XG4gICAgICAgICAgICAgICAgICAgICAgICBvcmlnUHJvcGVydHkgPSBvcmlnaW5hbEdldHRlci5jYWxsKHRoaXMpO1xuICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgIGVsc2UgaWYgKFwidmFsdWVcIiBpbiBwcm9wRGVzYykge1xuICAgICAgICAgICAgICAgICAgICAgICAgLy8gaWYgZGF0YSBwcm9wZXJ0eVxuICAgICAgICAgICAgICAgICAgICAgICAgb3JpZ1Byb3BlcnR5ID0gb3JpZ2luYWxWYWx1ZTtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIGNvbnNvbGUuZXJyb3IoXCJQcm9wZXJ0eSBkZXNjcmlwdG9yIGZvclwiLCBvYmplY3ROYW1lICsgXCIuXCIgKyBwcm9wZXJ0eU5hbWUsIFwiZG9lc24ndCBoYXZlIGdldHRlciBvciB2YWx1ZT9cIik7XG4gICAgICAgICAgICAgICAgICAgICAgICBsb2dWYWx1ZShvYmplY3ROYW1lICsgXCIuXCIgKyBwcm9wZXJ0eU5hbWUsIFwiXCIsIFwiZ2V0KGZhaWxlZClcIiwgY2FsbENvbnRleHQsIGxvZ1NldHRpbmdzKTtcbiAgICAgICAgICAgICAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICAvLyBMb2cgYGdldHNgIGV4Y2VwdCB0aG9zZSB0aGF0IGhhdmUgaW5zdHJ1bWVudGVkIHJldHVybiB2YWx1ZXNcbiAgICAgICAgICAgICAgICAgICAgLy8gKiBBbGwgcmV0dXJuZWQgZnVuY3Rpb25zIGFyZSBpbnN0cnVtZW50ZWQgd2l0aCBhIHdyYXBwZXJcbiAgICAgICAgICAgICAgICAgICAgLy8gKiBSZXR1cm5lZCBvYmplY3RzIG1heSBiZSBpbnN0cnVtZW50ZWQgaWYgcmVjdXJzaXZlXG4gICAgICAgICAgICAgICAgICAgIC8vICAgaW5zdHJ1bWVudGF0aW9uIGlzIGVuYWJsZWQgYW5kIHRoaXMgaXNuJ3QgYXQgdGhlIGRlcHRoIGxpbWl0LlxuICAgICAgICAgICAgICAgICAgICBpZiAodHlwZW9mIG9yaWdQcm9wZXJ0eSA9PT0gXCJmdW5jdGlvblwiKSB7XG4gICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gaW5zdHJ1bWVudEZ1bmN0aW9uKG9iamVjdE5hbWUsIHByb3BlcnR5TmFtZSwgb3JpZ1Byb3BlcnR5LCBsb2dTZXR0aW5ncyk7XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgZWxzZSBpZiAodHlwZW9mIG9yaWdQcm9wZXJ0eSA9PT0gXCJvYmplY3RcIiAmJlxuICAgICAgICAgICAgICAgICAgICAgICAgISFsb2dTZXR0aW5ncy5yZWN1cnNpdmUgJiZcbiAgICAgICAgICAgICAgICAgICAgICAgICghKFwiZGVwdGhcIiBpbiBsb2dTZXR0aW5ncykgfHwgbG9nU2V0dGluZ3MuZGVwdGggPiAwKSkge1xuICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIG9yaWdQcm9wZXJ0eTtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIGxvZ1ZhbHVlKG9iamVjdE5hbWUgKyBcIi5cIiArIHByb3BlcnR5TmFtZSwgb3JpZ1Byb3BlcnR5LCBcImdldFwiLCBjYWxsQ29udGV4dCwgbG9nU2V0dGluZ3MpO1xuICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIG9yaWdQcm9wZXJ0eTtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgIH07XG4gICAgICAgICAgICB9KSgpLFxuICAgICAgICAgICAgc2V0OiAoZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgICAgIHJldHVybiBmdW5jdGlvbiAodmFsdWUpIHtcbiAgICAgICAgICAgICAgICAgICAgY29uc3QgY2FsbENvbnRleHQgPSBnZXRPcmlnaW5hdGluZ1NjcmlwdENvbnRleHQoISFsb2dTZXR0aW5ncy5sb2dDYWxsU3RhY2spO1xuICAgICAgICAgICAgICAgICAgICBsZXQgcmV0dXJuVmFsdWU7XG4gICAgICAgICAgICAgICAgICAgIC8vIFByZXZlbnQgc2V0cyBmb3IgZnVuY3Rpb25zIGFuZCBvYmplY3RzIGlmIGVuYWJsZWRcbiAgICAgICAgICAgICAgICAgICAgaWYgKCEhbG9nU2V0dGluZ3MucHJldmVudFNldHMgJiZcbiAgICAgICAgICAgICAgICAgICAgICAgICh0eXBlb2Ygb3JpZ2luYWxWYWx1ZSA9PT0gXCJmdW5jdGlvblwiIHx8XG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgdHlwZW9mIG9yaWdpbmFsVmFsdWUgPT09IFwib2JqZWN0XCIpKSB7XG4gICAgICAgICAgICAgICAgICAgICAgICBsb2dWYWx1ZShvYmplY3ROYW1lICsgXCIuXCIgKyBwcm9wZXJ0eU5hbWUsIHZhbHVlLCBcInNldChwcmV2ZW50ZWQpXCIsIGNhbGxDb250ZXh0LCBsb2dTZXR0aW5ncyk7XG4gICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gdmFsdWU7XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgLy8gc2V0IG5ldyB2YWx1ZSB0byBvcmlnaW5hbCBzZXR0ZXIvbG9jYXRpb25cbiAgICAgICAgICAgICAgICAgICAgaWYgKG9yaWdpbmFsU2V0dGVyKSB7XG4gICAgICAgICAgICAgICAgICAgICAgICAvLyBpZiBhY2Nlc3NvciBwcm9wZXJ0eVxuICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuVmFsdWUgPSBvcmlnaW5hbFNldHRlci5jYWxsKHRoaXMsIHZhbHVlKTtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICBlbHNlIGlmIChcInZhbHVlXCIgaW4gcHJvcERlc2MpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIGluTG9nID0gdHJ1ZTtcbiAgICAgICAgICAgICAgICAgICAgICAgIGlmIChvYmplY3QuaXNQcm90b3R5cGVPZih0aGlzKSkge1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgIE9iamVjdC5kZWZpbmVQcm9wZXJ0eSh0aGlzLCBwcm9wZXJ0eU5hbWUsIHtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgdmFsdWUsXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgfSk7XG4gICAgICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBvcmlnaW5hbFZhbHVlID0gdmFsdWU7XG4gICAgICAgICAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgICAgICAgICByZXR1cm5WYWx1ZSA9IHZhbHVlO1xuICAgICAgICAgICAgICAgICAgICAgICAgaW5Mb2cgPSBmYWxzZTtcbiAgICAgICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICAgICAgICBlbHNlIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIGNvbnNvbGUuZXJyb3IoXCJQcm9wZXJ0eSBkZXNjcmlwdG9yIGZvclwiLCBvYmplY3ROYW1lICsgXCIuXCIgKyBwcm9wZXJ0eU5hbWUsIFwiZG9lc24ndCBoYXZlIHNldHRlciBvciB2YWx1ZT9cIik7XG4gICAgICAgICAgICAgICAgICAgICAgICBsb2dWYWx1ZShvYmplY3ROYW1lICsgXCIuXCIgKyBwcm9wZXJ0eU5hbWUsIHZhbHVlLCBcInNldChmYWlsZWQpXCIsIGNhbGxDb250ZXh0LCBsb2dTZXR0aW5ncyk7XG4gICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gdmFsdWU7XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgLy8gbG9nIHNldFxuICAgICAgICAgICAgICAgICAgICBsb2dWYWx1ZShvYmplY3ROYW1lICsgXCIuXCIgKyBwcm9wZXJ0eU5hbWUsIHZhbHVlLCBcInNldFwiLCBjYWxsQ29udGV4dCwgbG9nU2V0dGluZ3MpO1xuICAgICAgICAgICAgICAgICAgICAvLyByZXR1cm4gbmV3IHZhbHVlXG4gICAgICAgICAgICAgICAgICAgIHJldHVybiByZXR1cm5WYWx1ZTtcbiAgICAgICAgICAgICAgICB9O1xuICAgICAgICAgICAgfSkoKSxcbiAgICAgICAgfSk7XG4gICAgfVxuICAgIC8qXG4gICAgICogU3RhcnQgSW5zdHJ1bWVudGF0aW9uXG4gICAgICovXG4gICAgLy8gVE9ETzogdXNlciBzaG91bGQgYmUgYWJsZSB0byBjaG9vc2Ugd2hhdCB0byBpbnN0cnVtZW50XG4gICAgLy8gQWNjZXNzIHRvIG5hdmlnYXRvciBwcm9wZXJ0aWVzXG4gICAgY29uc3QgbmF2aWdhdG9yUHJvcGVydGllcyA9IFtcbiAgICAgICAgXCJhcHBDb2RlTmFtZVwiLFxuICAgICAgICBcImFwcE5hbWVcIixcbiAgICAgICAgXCJhcHBWZXJzaW9uXCIsXG4gICAgICAgIFwiYnVpbGRJRFwiLFxuICAgICAgICBcImNvb2tpZUVuYWJsZWRcIixcbiAgICAgICAgXCJkb05vdFRyYWNrXCIsXG4gICAgICAgIFwiZ2VvbG9jYXRpb25cIixcbiAgICAgICAgXCJsYW5ndWFnZVwiLFxuICAgICAgICBcImxhbmd1YWdlc1wiLFxuICAgICAgICBcIm9uTGluZVwiLFxuICAgICAgICBcIm9zY3B1XCIsXG4gICAgICAgIFwicGxhdGZvcm1cIixcbiAgICAgICAgXCJwcm9kdWN0XCIsXG4gICAgICAgIFwicHJvZHVjdFN1YlwiLFxuICAgICAgICBcInVzZXJBZ2VudFwiLFxuICAgICAgICBcInZlbmRvclN1YlwiLFxuICAgICAgICBcInZlbmRvclwiLFxuICAgIF07XG4gICAgbmF2aWdhdG9yUHJvcGVydGllcy5mb3JFYWNoKGZ1bmN0aW9uIChwcm9wZXJ0eSkge1xuICAgICAgICBpbnN0cnVtZW50T2JqZWN0UHJvcGVydHkod2luZG93Lm5hdmlnYXRvciwgXCJ3aW5kb3cubmF2aWdhdG9yXCIsIHByb3BlcnR5KTtcbiAgICB9KTtcbiAgICAvLyBBY2Nlc3MgdG8gc2NyZWVuIHByb3BlcnRpZXNcbiAgICAvLyBpbnN0cnVtZW50T2JqZWN0KHdpbmRvdy5zY3JlZW4sIFwid2luZG93LnNjcmVlblwiKTtcbiAgICAvLyBUT0RPOiB3aHkgZG8gd2UgaW5zdHJ1bWVudCBvbmx5IHR3byBzY3JlZW4gcHJvcGVydGllc1xuICAgIGNvbnN0IHNjcmVlblByb3BlcnRpZXMgPSBbXCJwaXhlbERlcHRoXCIsIFwiY29sb3JEZXB0aFwiXTtcbiAgICBzY3JlZW5Qcm9wZXJ0aWVzLmZvckVhY2goZnVuY3Rpb24gKHByb3BlcnR5KSB7XG4gICAgICAgIGluc3RydW1lbnRPYmplY3RQcm9wZXJ0eSh3aW5kb3cuc2NyZWVuLCBcIndpbmRvdy5zY3JlZW5cIiwgcHJvcGVydHkpO1xuICAgIH0pO1xuICAgIC8vIEFjY2VzcyB0byBwbHVnaW5zXG4gICAgY29uc3QgcGx1Z2luUHJvcGVydGllcyA9IFtcbiAgICAgICAgXCJuYW1lXCIsXG4gICAgICAgIFwiZmlsZW5hbWVcIixcbiAgICAgICAgXCJkZXNjcmlwdGlvblwiLFxuICAgICAgICBcInZlcnNpb25cIixcbiAgICAgICAgXCJsZW5ndGhcIixcbiAgICBdO1xuICAgIGZvciAobGV0IGkgPSAwOyBpIDwgd2luZG93Lm5hdmlnYXRvci5wbHVnaW5zLmxlbmd0aDsgaSsrKSB7XG4gICAgICAgIGNvbnN0IHBsdWdpbk5hbWUgPSB3aW5kb3cubmF2aWdhdG9yLnBsdWdpbnNbaV0ubmFtZTtcbiAgICAgICAgcGx1Z2luUHJvcGVydGllcy5mb3JFYWNoKGZ1bmN0aW9uIChwcm9wZXJ0eSkge1xuICAgICAgICAgICAgaW5zdHJ1bWVudE9iamVjdFByb3BlcnR5KHdpbmRvdy5uYXZpZ2F0b3IucGx1Z2luc1twbHVnaW5OYW1lXSwgXCJ3aW5kb3cubmF2aWdhdG9yLnBsdWdpbnNbXCIgKyBwbHVnaW5OYW1lICsgXCJdXCIsIHByb3BlcnR5KTtcbiAgICAgICAgfSk7XG4gICAgfVxuICAgIC8vIEFjY2VzcyB0byBNSU1FVHlwZXNcbiAgICBjb25zdCBtaW1lVHlwZVByb3BlcnRpZXMgPSBbXCJkZXNjcmlwdGlvblwiLCBcInN1ZmZpeGVzXCIsIFwidHlwZVwiXTtcbiAgICBmb3IgKGxldCBpID0gMDsgaSA8IHdpbmRvdy5uYXZpZ2F0b3IubWltZVR5cGVzLmxlbmd0aDsgaSsrKSB7XG4gICAgICAgIGNvbnN0IG1pbWVUeXBlTmFtZSA9IHdpbmRvdy5uYXZpZ2F0b3IubWltZVR5cGVzW2ldLnR5cGU7IC8vIG5vdGU6IHVwc3RyZWFtIHR5cGluZ3Mgc2VlbXMgdG8gYmUgaW5jb3JyZWN0XG4gICAgICAgIG1pbWVUeXBlUHJvcGVydGllcy5mb3JFYWNoKGZ1bmN0aW9uIChwcm9wZXJ0eSkge1xuICAgICAgICAgICAgaW5zdHJ1bWVudE9iamVjdFByb3BlcnR5KHdpbmRvdy5uYXZpZ2F0b3IubWltZVR5cGVzW21pbWVUeXBlTmFtZV0sIFwid2luZG93Lm5hdmlnYXRvci5taW1lVHlwZXNbXCIgKyBtaW1lVHlwZU5hbWUgKyBcIl1cIiwgcHJvcGVydHkpO1xuICAgICAgICB9KTtcbiAgICB9XG4gICAgLy8gTmFtZSwgbG9jYWxTdG9yYWdlLCBhbmQgc2Vzc2lvbnNTdG9yYWdlIGxvZ2dpbmdcbiAgICAvLyBJbnN0cnVtZW50aW5nIHdpbmRvdy5sb2NhbFN0b3JhZ2UgZGlyZWN0bHkgZG9lc24ndCBzZWVtIHRvIHdvcmssIHNvIHRoZSBTdG9yYWdlXG4gICAgLy8gcHJvdG90eXBlIG11c3QgYmUgaW5zdHJ1bWVudGVkIGluc3RlYWQuIFVuZm9ydHVuYXRlbHkgdGhpcyBmYWlscyB0byBkaWZmZXJlbnRpYXRlXG4gICAgLy8gYmV0d2VlbiBzZXNzaW9uU3RvcmFnZSBhbmQgbG9jYWxTdG9yYWdlLiBJbnN0ZWFkLCB5b3UnbGwgaGF2ZSB0byBsb29rIGZvciBhIHNlcXVlbmNlXG4gICAgLy8gb2YgYSBnZXQgZm9yIHRoZSBsb2NhbFN0b3JhZ2Ugb2JqZWN0IGZvbGxvd2VkIGJ5IGEgZ2V0SXRlbS9zZXRJdGVtIGZvciB0aGUgU3RvcmFnZSBvYmplY3QuXG4gICAgY29uc3Qgd2luZG93UHJvcGVydGllcyA9IFtcIm5hbWVcIiwgXCJsb2NhbFN0b3JhZ2VcIiwgXCJzZXNzaW9uU3RvcmFnZVwiXTtcbiAgICB3aW5kb3dQcm9wZXJ0aWVzLmZvckVhY2goZnVuY3Rpb24gKHByb3BlcnR5KSB7XG4gICAgICAgIGluc3RydW1lbnRPYmplY3RQcm9wZXJ0eSh3aW5kb3csIFwid2luZG93XCIsIHByb3BlcnR5KTtcbiAgICB9KTtcbiAgICBpbnN0cnVtZW50T2JqZWN0KHdpbmRvdy5TdG9yYWdlLnByb3RvdHlwZSwgXCJ3aW5kb3cuU3RvcmFnZVwiKTtcbiAgICAvLyBBY2Nlc3MgdG8gZG9jdW1lbnQuY29va2llXG4gICAgaW5zdHJ1bWVudE9iamVjdFByb3BlcnR5KHdpbmRvdy5kb2N1bWVudCwgXCJ3aW5kb3cuZG9jdW1lbnRcIiwgXCJjb29raWVcIiwge1xuICAgICAgICBsb2dDYWxsU3RhY2s6IHRydWUsXG4gICAgfSk7XG4gICAgLy8gQWNjZXNzIHRvIGRvY3VtZW50LnJlZmVycmVyXG4gICAgaW5zdHJ1bWVudE9iamVjdFByb3BlcnR5KHdpbmRvdy5kb2N1bWVudCwgXCJ3aW5kb3cuZG9jdW1lbnRcIiwgXCJyZWZlcnJlclwiLCB7XG4gICAgICAgIGxvZ0NhbGxTdGFjazogdHJ1ZSxcbiAgICB9KTtcbiAgICAvLyBBY2Nlc3MgdG8gY2FudmFzXG4gICAgaW5zdHJ1bWVudE9iamVjdCh3aW5kb3cuSFRNTENhbnZhc0VsZW1lbnQucHJvdG90eXBlLCBcIkhUTUxDYW52YXNFbGVtZW50XCIpO1xuICAgIGNvbnN0IGV4Y2x1ZGVkUHJvcGVydGllcyA9IFtcbiAgICAgICAgXCJxdWFkcmF0aWNDdXJ2ZVRvXCIsXG4gICAgICAgIFwibGluZVRvXCIsXG4gICAgICAgIFwidHJhbnNmb3JtXCIsXG4gICAgICAgIFwiZ2xvYmFsQWxwaGFcIixcbiAgICAgICAgXCJtb3ZlVG9cIixcbiAgICAgICAgXCJkcmF3SW1hZ2VcIixcbiAgICAgICAgXCJzZXRUcmFuc2Zvcm1cIixcbiAgICAgICAgXCJjbGVhclJlY3RcIixcbiAgICAgICAgXCJjbG9zZVBhdGhcIixcbiAgICAgICAgXCJiZWdpblBhdGhcIixcbiAgICAgICAgXCJjYW52YXNcIixcbiAgICAgICAgXCJ0cmFuc2xhdGVcIixcbiAgICBdO1xuICAgIGluc3RydW1lbnRPYmplY3Qod2luZG93LkNhbnZhc1JlbmRlcmluZ0NvbnRleHQyRC5wcm90b3R5cGUsIFwiQ2FudmFzUmVuZGVyaW5nQ29udGV4dDJEXCIsIHsgZXhjbHVkZWRQcm9wZXJ0aWVzIH0pO1xuICAgIC8vIEFjY2VzcyB0byB3ZWJSVENcbiAgICBpbnN0cnVtZW50T2JqZWN0KHdpbmRvdy5SVENQZWVyQ29ubmVjdGlvbi5wcm90b3R5cGUsIFwiUlRDUGVlckNvbm5lY3Rpb25cIik7XG4gICAgLy8gQWNjZXNzIHRvIEF1ZGlvIEFQSVxuICAgIGluc3RydW1lbnRPYmplY3Qod2luZG93LkF1ZGlvQ29udGV4dC5wcm90b3R5cGUsIFwiQXVkaW9Db250ZXh0XCIpO1xuICAgIGluc3RydW1lbnRPYmplY3Qod2luZG93Lk9mZmxpbmVBdWRpb0NvbnRleHQucHJvdG90eXBlLCBcIk9mZmxpbmVBdWRpb0NvbnRleHRcIik7XG4gICAgaW5zdHJ1bWVudE9iamVjdCh3aW5kb3cuT3NjaWxsYXRvck5vZGUucHJvdG90eXBlLCBcIk9zY2lsbGF0b3JOb2RlXCIpO1xuICAgIGluc3RydW1lbnRPYmplY3Qod2luZG93LkFuYWx5c2VyTm9kZS5wcm90b3R5cGUsIFwiQW5hbHlzZXJOb2RlXCIpO1xuICAgIGluc3RydW1lbnRPYmplY3Qod2luZG93LkdhaW5Ob2RlLnByb3RvdHlwZSwgXCJHYWluTm9kZVwiKTtcbiAgICBpbnN0cnVtZW50T2JqZWN0KHdpbmRvdy5TY3JpcHRQcm9jZXNzb3JOb2RlLnByb3RvdHlwZSwgXCJTY3JpcHRQcm9jZXNzb3JOb2RlXCIpO1xuICAgIGlmICh0ZXN0aW5nKSB7XG4gICAgICAgIGNvbnNvbGUubG9nKFwiT3BlbldQTTogQ29udGVudC1zaWRlIGphdmFzY3JpcHQgaW5zdHJ1bWVudGF0aW9uIHN0YXJ0ZWRcIiwgbmV3IERhdGUoKS50b0lTT1N0cmluZygpKTtcbiAgICB9XG59O1xuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pYW1GMllYTmpjbWx3ZEMxcGJuTjBjblZ0Wlc1MExYQmhaMlV0YzJOdmNHVXVhbk1pTENKemIzVnlZMlZTYjI5MElqb2lJaXdpYzI5MWNtTmxjeUk2V3lJdUxpOHVMaTh1TGk5emNtTXZZMjl1ZEdWdWRDOXFZWFpoYzJOeWFYQjBMV2x1YzNSeWRXMWxiblF0Y0dGblpTMXpZMjl3WlM1MGN5SmRMQ0p1WVcxbGN5STZXMTBzSW0xaGNIQnBibWR6SWpvaVFVRkJRU3hwUlVGQmFVVTdRVUZEYWtVc2IwWkJRVzlHTzBGQlowSndSaXhOUVVGTkxFTkJRVU1zVFVGQlRTeFZRVUZWTEVkQlFVYzdTVUZEZUVJc2VVSkJRWGxDTzBsQlEzcENMRk5CUVZNc1VVRkJVU3hEUVVGRExFbEJRVWtzUlVGQlJTeEpRVUZKTEVWQlFVVXNVMEZCVXl4SFFVRkhMRXRCUVVzN1VVRkROME1zU1VGQlNTeFBRVUZQTEVWQlFVVXNTVUZCU1N4RlFVRkZMRTlCUVU4c1JVRkJSU3hUUVVGVExFVkJRVVVzVFVGQlRTeERRVUZETzFGQlJUbERMRTFCUVUwc1MwRkJTeXhIUVVGSE8xbEJRMW9zVFVGQlRTeEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRMRWRCUVVjc1JVRkJSU3hIUVVGSExGTkJRVk1zUTBGQlF6dFpRVU53UXl4SlFVRkpMRWxCUVVrc1IwRkJSeXhKUVVGSkxFVkJRVVU3WjBKQlEyWXNUMEZCVHl4SFFVRkhMRlZCUVZVc1EwRkJReXhMUVVGTExFVkJRVVVzU1VGQlNTeEhRVUZITEVsQlFVa3NRMEZCUXl4RFFVRkRPMkZCUXpGRE8ybENRVUZOTzJkQ1FVTk1MRTlCUVU4c1IwRkJSeXhKUVVGSkxFTkJRVU03WjBKQlEyWXNTVUZCU1N4RFFVRkRMRk5CUVZNc1JVRkJSVHR2UWtGRFpDeE5RVUZOTEVkQlFVY3NTVUZCU1N4RFFVRkRMRXRCUVVzc1EwRkJReXhQUVVGUExFVkJRVVVzU1VGQlNTeERRVUZETEVOQlFVTTdiMEpCUTI1RExFOUJRVThzUjBGQlJ5eEpRVUZKTEVkQlFVY3NTVUZCU1N4RFFVRkRPMmxDUVVOMlFqdGhRVU5HTzFGQlEwZ3NRMEZCUXl4RFFVRkRPMUZCUlVZc1QwRkJUenRaUVVOTUxFOUJRVThzUjBGQlJ5eEpRVUZKTEVOQlFVTTdXVUZEWml4SlFVRkpMRWRCUVVjc1UwRkJVeXhEUVVGRE8xbEJRMnBDTEZOQlFWTXNSMEZCUnl4SlFVRkpMRU5CUVVNc1IwRkJSeXhGUVVGRkxFTkJRVU03V1VGRGRrSXNUVUZCVFN4UFFVRlBMRWRCUVVjc1UwRkJVeXhKUVVGSkxFTkJRVU1zVDBGQlR5eERRVUZETzFsQlEzUkRMRWxCUVVrc1EwRkJReXhQUVVGUExFVkJRVVU3WjBKQlExb3NUMEZCVHl4SFFVRkhMRlZCUVZVc1EwRkJReXhMUVVGTExFVkJRVVVzU1VGQlNTeERRVUZETEVOQlFVTTdZVUZEYmtNN1dVRkRSQ3hKUVVGSkxFOUJRVThzUlVGQlJUdG5Ra0ZEV0N4TlFVRk5MRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eFBRVUZQTEVWQlFVVXNTVUZCU1N4RFFVRkRMRU5CUVVNN1owSkJRMjVETEU5QlFVOHNSMEZCUnl4SlFVRkpMRWRCUVVjc1NVRkJTU3hEUVVGRE8yRkJRM1pDTzFsQlJVUXNUMEZCVHl4TlFVRk5MRU5CUVVNN1VVRkRhRUlzUTBGQlF5eERRVUZETzBsQlEwb3NRMEZCUXp0SlFVTkVMR3RDUVVGclFqdEpRVVZzUWl3clFrRkJLMEk3U1VGREwwSXNUVUZCVFN4SlFVRkpMRWRCUVVjc1EwRkJRenRSUVVOYUxFbEJRVWtzVVVGQlVTeEhRVUZITEVWQlFVVXNRMEZCUXp0UlFVTnNRaXh0UTBGQmJVTTdVVUZEYmtNc1RVRkJUU3hMUVVGTExFZEJRVWNzVVVGQlVTeERRVUZETzFsQlEzSkNMRkZCUVZFc1EwRkJReXhoUVVGaExFTkJRM0JDTEVsQlFVa3NWMEZCVnl4RFFVRkRMRkZCUVZFc1JVRkJSVHRuUWtGRGVFSXNUVUZCVFN4RlFVRkZMRkZCUVZFN1lVRkRha0lzUTBGQlF5eERRVU5JTEVOQlFVTTdXVUZGUml4clFrRkJhMEk3V1VGRGJFSXNVVUZCVVN4SFFVRkhMRVZCUVVVc1EwRkJRenRSUVVOb1FpeERRVUZETEVWQlFVVXNSMEZCUnl4RFFVRkRMRU5CUVVNN1VVRkZVaXhQUVVGUExGVkJRVk1zVDBGQlR5eEZRVUZGTEVkQlFVYzdXVUZETVVJc2IwSkJRVzlDTzFsQlEzQkNMRkZCUVZFc1EwRkJReXhKUVVGSkxFTkJRVU1zUlVGQlJTeEpRVUZKTEVWQlFVVXNUMEZCVHl4RlFVRkZMRTlCUVU4c1JVRkJSU3hIUVVGSExFVkJRVVVzUTBGQlF5eERRVUZETzFsQlF5OURMRXRCUVVzc1JVRkJSU3hEUVVGRE8xRkJRMVlzUTBGQlF5eERRVUZETzBsQlEwb3NRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJRenRKUVVWTUxFMUJRVTBzVVVGQlVTeEhRVUZITEZGQlFWRXNRMEZCUXl4aFFVRmhMRU5CUVVNc1dVRkJXU3hEUVVGRExHVkJRV1VzUTBGQlF5eERRVUZETzBsQlJYUkZPenRQUVVWSE8wbEJSVWdzVFVGQlRTeFBRVUZQTEVkQlExZ3NVVUZCVVN4RFFVRkRMR0ZCUVdFc1EwRkJReXhaUVVGWkxFTkJRVU1zWTBGQll5eERRVUZETEV0QlFVc3NUVUZCVFN4RFFVRkRPMGxCUTJwRkxFbEJRVWtzVDBGQlR5eEZRVUZGTzFGQlExZ3NUMEZCVHl4RFFVRkRMRWRCUVVjc1EwRkJReXcyUWtGQk5rSXNSVUZCUlN4UFFVRlBMRU5CUVVNc1EwRkJRenRMUVVOeVJEdEpRVVZFTERoRFFVRTRRenRKUVVNNVF5eFRRVUZUTEcxQ1FVRnRRaXhEUVVGRExFOUJRVThzUlVGQlJTeGpRVUZqTEVkQlFVY3NTMEZCU3p0UlFVTXhSQ3hKUVVGSkxFOUJRVThzUzBGQlN5eFJRVUZSTEVOQlFVTXNTVUZCU1N4RlFVRkZPMWxCUXpkQ0xFOUJRVThzVDBGQlR5eERRVUZETEU5QlFVOHNRMEZCUXp0VFFVTjRRanRSUVVORUxFbEJRVWtzVDBGQlR5eERRVUZETEZWQlFWVXNTMEZCU3l4SlFVRkpMRVZCUVVVN1dVRkRMMElzVDBGQlR5eFBRVUZQTEVkQlFVY3NUMEZCVHl4RFFVRkRMRTlCUVU4c1EwRkJRenRUUVVOc1F6dFJRVVZFTEVsQlFVa3NXVUZCV1N4SFFVRkhMRU5CUVVNc1EwRkJRenRSUVVOeVFpeE5RVUZOTEZGQlFWRXNSMEZCUnl4UFFVRlBMRU5CUVVNc1ZVRkJWU3hEUVVGRExGVkJRVlVzUTBGQlF6dFJRVU12UXl4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NVVUZCVVN4RFFVRkRMRTFCUVUwc1JVRkJSU3hEUVVGRExFVkJRVVVzUlVGQlJUdFpRVU40UXl4TlFVRk5MRTlCUVU4c1IwRkJSeXhSUVVGUkxFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdXVUZETlVJc1NVRkJTU3hQUVVGUExFdEJRVXNzVDBGQlR5eEZRVUZGTzJkQ1FVTjJRaXhKUVVGSkxFbEJRVWtzUjBGQlJ5eHRRa0ZCYlVJc1EwRkJReXhQUVVGUExFTkJRVU1zVlVGQlZTeEZRVUZGTEdOQlFXTXNRMEZCUXl4RFFVRkRPMmRDUVVOdVJTeEpRVUZKTEVsQlFVa3NSMEZCUnl4SFFVRkhMRTlCUVU4c1EwRkJReXhQUVVGUExFZEJRVWNzUjBGQlJ5eEhRVUZITEZsQlFWa3NRMEZCUXp0blFrRkRia1FzU1VGQlNTeEpRVUZKTEVkQlFVY3NSMEZCUnl4UFFVRlBMRU5CUVVNc1JVRkJSU3hEUVVGRE8yZENRVU42UWl4SlFVRkpMRWxCUVVrc1IwRkJSeXhIUVVGSExFOUJRVThzUTBGQlF5eFRRVUZUTEVOQlFVTTdaMEpCUTJoRExFbEJRVWtzWTBGQll5eEZRVUZGTzI5Q1FVTnNRaXhKUVVGSkxFbEJRVWtzUjBGQlJ5eEhRVUZITEU5QlFVOHNRMEZCUXl4TlFVRk5MRU5CUVVNN2IwSkJRemRDTEVsQlFVa3NTVUZCU1N4SFFVRkhMRWRCUVVjc1QwRkJUeXhEUVVGRExFdEJRVXNzUTBGQlF5eFBRVUZQTEVOQlFVTTdiMEpCUTNCRExFbEJRVWtzU1VGQlNTeEhRVUZITEVkQlFVY3NUMEZCVHl4RFFVRkRMRXRCUVVzc1EwRkJReXhWUVVGVkxFTkJRVU03YVVKQlEzaERPMmRDUVVORUxFbEJRVWtzVDBGQlR5eERRVUZETEU5QlFVOHNTMEZCU3l4SFFVRkhMRVZCUVVVN2IwSkJRek5DTEVsQlFVa3NTVUZCU1N4SFFVRkhMRWRCUVVjc1QwRkJUeXhEUVVGRExFbEJRVWtzUTBGQlF6dHBRa0ZETlVJN1owSkJRMFFzU1VGQlNTeEpRVUZKTEVkQlFVY3NRMEZCUXp0blFrRkRXaXhQUVVGUExFbEJRVWtzUTBGQlF6dGhRVU5pTzFsQlEwUXNTVUZCU1N4UFFVRlBMRU5CUVVNc1VVRkJVU3hMUVVGTExFTkJRVU1zU1VGQlNTeFBRVUZQTEVOQlFVTXNUMEZCVHl4TFFVRkxMRTlCUVU4c1EwRkJReXhQUVVGUExFVkJRVVU3WjBKQlEycEZMRmxCUVZrc1JVRkJSU3hEUVVGRE8yRkJRMmhDTzFOQlEwWTdTVUZEU0N4RFFVRkRPMGxCUlVRc1owTkJRV2RETzBsQlEyaERMRk5CUVZNc1pVRkJaU3hEUVVGRExFMUJRVTBzUlVGQlJTeHJRa0ZCYTBJc1IwRkJSeXhMUVVGTE8xRkJRM3BFTERSQ1FVRTBRanRSUVVNMVFpeEpRVUZKTzFsQlEwWXNTVUZCU1N4TlFVRk5MRXRCUVVzc1NVRkJTU3hGUVVGRk8yZENRVU51UWl4UFFVRlBMRTFCUVUwc1EwRkJRenRoUVVObU8xbEJRMFFzU1VGQlNTeFBRVUZQTEUxQlFVMHNTMEZCU3l4VlFVRlZMRVZCUVVVN1owSkJRMmhETEVsQlFVa3NhMEpCUVd0Q0xFVkJRVVU3YjBKQlEzUkNMRTlCUVU4c1RVRkJUU3hEUVVGRExGRkJRVkVzUlVGQlJTeERRVUZETzJsQ1FVTXhRanR4UWtGQlRUdHZRa0ZEVEN4UFFVRlBMRlZCUVZVc1EwRkJRenRwUWtGRGJrSTdZVUZEUmp0WlFVTkVMRWxCUVVrc1QwRkJUeXhOUVVGTkxFdEJRVXNzVVVGQlVTeEZRVUZGTzJkQ1FVTTVRaXhQUVVGUExFMUJRVTBzUTBGQlF6dGhRVU5tTzFsQlEwUXNUVUZCVFN4WFFVRlhMRWRCUVVjc1JVRkJSU3hEUVVGRE8xbEJRM1pDTEU5QlFVOHNTVUZCU1N4RFFVRkRMRk5CUVZNc1EwRkJReXhOUVVGTkxFVkJRVVVzVlVGQlV5eEhRVUZITEVWQlFVVXNTMEZCU3p0blFrRkRMME1zU1VGQlNTeExRVUZMTEV0QlFVc3NTVUZCU1N4RlFVRkZPMjlDUVVOc1FpeFBRVUZQTEUxQlFVMHNRMEZCUXp0cFFrRkRaanRuUWtGRFJDeEpRVUZKTEU5QlFVOHNTMEZCU3l4TFFVRkxMRlZCUVZVc1JVRkJSVHR2UWtGREwwSXNTVUZCU1N4clFrRkJhMElzUlVGQlJUdDNRa0ZEZEVJc1QwRkJUeXhMUVVGTExFTkJRVU1zVVVGQlVTeEZRVUZGTEVOQlFVTTdjVUpCUTNwQ08zbENRVUZOTzNkQ1FVTk1MRTlCUVU4c1ZVRkJWU3hEUVVGRE8zRkNRVU51UWp0cFFrRkRSanRuUWtGRFJDeEpRVUZKTEU5QlFVOHNTMEZCU3l4TFFVRkxMRkZCUVZFc1JVRkJSVHR2UWtGRE4wSXNjVU5CUVhGRE8yOUNRVU55UXl4SlFVRkpMR2xDUVVGcFFpeEpRVUZKTEV0QlFVc3NSVUZCUlR0M1FrRkRPVUlzUzBGQlN5eEhRVUZITEV0QlFVc3NRMEZCUXl4bFFVRmxMRU5CUVVNN2NVSkJReTlDTzI5Q1FVVkVMSGxDUVVGNVFqdHZRa0ZEZWtJc1NVRkJTU3hMUVVGTExGbEJRVmtzVjBGQlZ5eEZRVUZGTzNkQ1FVTm9ReXhQUVVGUExHMUNRVUZ0UWl4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRE8zRkNRVU51UXp0dlFrRkZSQ3dyUWtGQkswSTdiMEpCUXk5Q0xFbEJRVWtzUjBGQlJ5eExRVUZMTEVWQlFVVXNTVUZCU1N4WFFVRlhMRU5CUVVNc1QwRkJUeXhEUVVGRExFdEJRVXNzUTBGQlF5eEhRVUZITEVOQlFVTXNSVUZCUlR0M1FrRkRhRVFzVjBGQlZ5eERRVUZETEVsQlFVa3NRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJRenQzUWtGRGVFSXNUMEZCVHl4TFFVRkxMRU5CUVVNN2NVSkJRMlE3ZVVKQlFVMDdkMEpCUTB3c1QwRkJUeXhQUVVGUExFdEJRVXNzUTBGQlF6dHhRa0ZEY2tJN2FVSkJRMFk3WjBKQlEwUXNUMEZCVHl4TFFVRkxMRU5CUVVNN1dVRkRaaXhEUVVGRExFTkJRVU1zUTBGQlF6dFRRVU5LTzFGQlFVTXNUMEZCVHl4TFFVRkxMRVZCUVVVN1dVRkRaQ3hQUVVGUExFTkJRVU1zUjBGQlJ5eERRVUZETEdkRFFVRm5ReXhIUVVGSExFdEJRVXNzUTBGQlF5eERRVUZETzFsQlEzUkVMRTlCUVU4c2RVSkJRWFZDTEVkQlFVY3NTMEZCU3l4RFFVRkRPMU5CUTNoRE8wbEJRMGdzUTBGQlF6dEpRVVZFTEZOQlFWTXNhVUpCUVdsQ0xFTkJRVU1zUzBGQlN6dFJRVU01UWl4UFFVRlBMRU5CUVVNc1IwRkJSeXhEUVVGRExIVkNRVUYxUWl4SFFVRkhMRXRCUVVzc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF6dFJRVU5zUkN4UFFVRlBMRU5CUVVNc1IwRkJSeXhEUVVGRExEQkNRVUV3UWl4SFFVRkhMRXRCUVVzc1EwRkJReXhQUVVGUExFTkJRVU1zUTBGQlF6dFJRVU40UkN4UFFVRlBMRU5CUVVNc1IwRkJSeXhEUVVGRExESkNRVUV5UWl4SFFVRkhMRXRCUVVzc1EwRkJReXhSUVVGUkxFTkJRVU1zUTBGQlF6dFJRVU14UkN4UFFVRlBMRU5CUVVNc1IwRkJSeXhEUVVGRExEaENRVUU0UWl4SFFVRkhMRXRCUVVzc1EwRkJReXhWUVVGVkxFTkJRVU1zUTBGQlF6dFJRVU12UkN4UFFVRlBMRU5CUVVNc1IwRkJSeXhEUVVGRExIZENRVUYzUWl4SFFVRkhMRXRCUVVzc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF6dEpRVU4wUkN4RFFVRkRPMGxCUlVRc2QwTkJRWGRETzBsQlEzaERMRk5CUVZNc1lVRkJZVHRSUVVOd1FpeEpRVUZKTEV0QlFVc3NRMEZCUXp0UlFVVldMRWxCUVVrN1dVRkRSaXhOUVVGTkxFbEJRVWtzUzBGQlN5eEZRVUZGTEVOQlFVTTdVMEZEYmtJN1VVRkJReXhQUVVGUExFZEJRVWNzUlVGQlJUdFpRVU5hTEV0QlFVc3NSMEZCUnl4SFFVRkhMRU5CUVVNc1MwRkJTeXhEUVVGRE8xTkJRMjVDTzFGQlJVUXNUMEZCVHl4TFFVRkxMRU5CUVVNN1NVRkRaaXhEUVVGRE8wbEJSVVFzTUVOQlFUQkRPMGxCUXpGRExFMUJRVTBzUTBGQlF5eFRRVUZUTEVOQlFVTXNUVUZCVFN4SFFVRkhMRlZCUVZNc1IwRkJSeXhGUVVGRkxGRkJRVkU3VVVGRE9VTXNUVUZCVFN4TFFVRkxMRWRCUVVjc1NVRkJTU3hEUVVGRExFdEJRVXNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0UlFVTTVRaXhQUVVGUExGRkJRVkU3V1VGRFlpeERRVUZETEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEUxQlFVMHNRMEZCUXl4TFFVRkxMRU5CUVVNc1MwRkJTeXhEUVVGRExFTkJRVU1zVVVGQlVTeERRVUZETEVOQlFVTTdXVUZEZEVVc1EwRkJReXhEUVVGRExFdEJRVXNzUTBGQlF6dEpRVU5hTEVOQlFVTXNRMEZCUXp0SlFVVkdMRk5CUVZNc01rSkJRVEpDTEVOQlFVTXNXVUZCV1N4SFFVRkhMRXRCUVVzN1VVRkRka1FzVFVGQlRTeExRVUZMTEVkQlFVY3NZVUZCWVN4RlFVRkZPMkZCUXpGQ0xFbEJRVWtzUlVGQlJUdGhRVU5PTEV0QlFVc3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJRenRSUVVObUxHOUVRVUZ2UkR0UlFVTndSQ3hOUVVGTkxHRkJRV0VzUjBGQlJ6dFpRVU53UWl4VFFVRlRMRVZCUVVVc1JVRkJSVHRaUVVOaUxGVkJRVlVzUlVGQlJTeEZRVUZGTzFsQlEyUXNVMEZCVXl4RlFVRkZMRVZCUVVVN1dVRkRZaXhSUVVGUkxFVkJRVVVzUlVGQlJUdFpRVU5hTEdGQlFXRXNSVUZCUlN4RlFVRkZPMWxCUTJwQ0xGTkJRVk1zUlVGQlJTeEZRVUZGTzFOQlEyUXNRMEZCUXp0UlFVTkdMRWxCUVVrc1MwRkJTeXhEUVVGRExFMUJRVTBzUjBGQlJ5eERRVUZETEVWQlFVVTdXVUZEY0VJc1QwRkJUeXhoUVVGaExFTkJRVU03VTBGRGRFSTdVVUZEUkN3d1JVRkJNRVU3VVVGRE1VVXNUVUZCVFN4UlFVRlJMRWRCUVVjc1MwRkJTeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlF6RkNMRWxCUVVrc1EwRkJReXhSUVVGUkxFVkJRVVU3V1VGRFlpeFBRVUZQTEdGQlFXRXNRMEZCUXp0VFFVTjBRanRSUVVORU96czdPenM3T3p0WFFWRkhPMUZCUTBnc1NVRkJTVHRaUVVOR0xFbEJRVWtzVTBGQlV5eEhRVUZITEVWQlFVVXNRMEZCUXp0WlFVTnVRaXhKUVVGSkxHRkJRV0VzUjBGQlJ5eEZRVUZGTEVOQlFVTXNRMEZCUXl3MlFrRkJOa0k3V1VGRGNrUXNUVUZCVFN4aFFVRmhMRWRCUVVjc1VVRkJVU3hEUVVGRExFdEJRVXNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0WlFVTXhReXhOUVVGTkxGRkJRVkVzUjBGQlJ5eGhRVUZoTEVOQlFVTXNRMEZCUXl4RFFVRkRMRWxCUVVrc1JVRkJSU3hEUVVGRE8xbEJRM2hETEUxQlFVMHNTMEZCU3l4SFFVRkhMR0ZCUVdFc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNSMEZCUnl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVGRE8xbEJRemxETEUxQlFVMHNVVUZCVVN4SFFVRkhMRXRCUVVzc1EwRkJReXhMUVVGTExFTkJRVU1zVFVGQlRTeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTNwRExFMUJRVTBzVFVGQlRTeEhRVUZITEV0QlFVc3NRMEZCUXl4TFFVRkxMRU5CUVVNc1RVRkJUU3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETzFsQlEzWkRMRTFCUVUwc1kwRkJZeXhIUVVGSExFdEJRVXNzUTBGQlF5eExRVUZMTEVOQlFVTXNUVUZCVFN4SFFVRkhMRU5CUVVNc1EwRkJReXhKUVVGSkxFVkJRVVVzUTBGQlF6dFpRVU55UkN4TlFVRk5MRk5CUVZNc1IwRkJSeXhqUVVGakxFTkJRVU1zVDBGQlR5eERRVUZETEZGQlFWRXNRMEZCUXl4RFFVRkRMRU5CUVVNc2VVTkJRWGxETzFsQlF6ZEdMRWxCUVVrc1UwRkJVeXhMUVVGTExFTkJRVU1zUTBGQlF5eEZRVUZGTzJkQ1FVTndRaXhUUVVGVExFZEJRVWNzWTBGQll5eERRVUZETEVOQlFVTXNiMFJCUVc5RU8yRkJRMnBHTzJsQ1FVRk5PMmRDUVVOTUxGTkJRVk1zUjBGQlJ5eGpRVUZqTEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNc1JVRkJSU3hUUVVGVExFTkJRVU1zUTBGQlF6dG5Ra0ZETDBNc1lVRkJZU3hIUVVGSExHTkJRV01zUTBGQlF5eExRVUZMTEVOQlEyeERMRk5CUVZNc1IwRkJSeXhEUVVGRExFVkJRMklzWTBGQll5eERRVUZETEUxQlFVMHNRMEZEZEVJc1EwRkJRenRoUVVOSU8xbEJRMFFzVFVGQlRTeFhRVUZYTEVkQlFVYzdaMEpCUTJ4Q0xGTkJRVk03WjBKQlExUXNWVUZCVlN4RlFVRkZMRTFCUVUwN1owSkJRMnhDTEZOQlFWTXNSVUZCUlN4UlFVRlJPMmRDUVVOdVFpeFJRVUZSTzJkQ1FVTlNMR0ZCUVdFN1owSkJRMklzVTBGQlV5eEZRVUZGTEZsQlFWazdiMEpCUTNKQ0xFTkJRVU1zUTBGQlF5eExRVUZMTzNsQ1FVTkdMRXRCUVVzc1EwRkJReXhEUVVGRExFTkJRVU03ZVVKQlExSXNTVUZCU1N4RFFVRkRMRWxCUVVrc1EwRkJRenQ1UWtGRFZpeEpRVUZKTEVWQlFVVTdiMEpCUTFnc1EwRkJReXhEUVVGRExFVkJRVVU3WVVGRFVDeERRVUZETzFsQlEwWXNUMEZCVHl4WFFVRlhMRU5CUVVNN1UwRkRjRUk3VVVGQlF5eFBRVUZQTEVOQlFVTXNSVUZCUlR0WlFVTldMRTlCUVU4c1EwRkJReXhIUVVGSExFTkJRVU1zTWtOQlFUSkRMRVZCUVVVc1EwRkJReXhGUVVGRkxGRkJRVkVzUTBGQlF5eERRVUZETzFsQlEzUkZMRTlCUVU4c1lVRkJZU3hEUVVGRE8xTkJRM1JDTzBsQlEwZ3NRMEZCUXp0SlFVVkVMRzFGUVVGdFJUdEpRVU51UlN4TlFVRk5MRmRCUVZjc1IwRkJSeXhIUVVGSExFTkJRVU03U1VGRGVFSXNUVUZCVFN4VlFVRlZMRWRCUVVjc1NVRkJTU3hOUVVGTkxFVkJRVVVzUTBGQlF6dEpRVU5vUXl4VFFVRlRMREpDUVVFeVFpeERRVUZETEZOQlFWTXNSVUZCUlN4TlFVRk5PMUZCUTNCRUxFMUJRVTBzUjBGQlJ5eEhRVUZITEZOQlFWTXNSMEZCUnl4SFFVRkhMRWRCUVVjc1RVRkJUU3hEUVVGRE8xRkJRM0pETEVsQlFVa3NSMEZCUnl4SlFVRkpMRlZCUVZVc1NVRkJTU3hWUVVGVkxFTkJRVU1zUjBGQlJ5eERRVUZETEVsQlFVa3NWMEZCVnl4RlFVRkZPMWxCUTNaRUxFOUJRVThzU1VGQlNTeERRVUZETzFOQlEySTdZVUZCVFN4SlFVRkpMRU5CUVVNc1EwRkJReXhIUVVGSExFbEJRVWtzVlVGQlZTeERRVUZETEVWQlFVVTdXVUZETDBJc1ZVRkJWU3hEUVVGRExFZEJRVWNzUTBGQlF5eEhRVUZITEVOQlFVTXNRMEZCUXp0VFFVTnlRanRoUVVGTk8xbEJRMHdzVlVGQlZTeERRVUZETEVkQlFVY3NRMEZCUXl4SlFVRkpMRU5CUVVNc1EwRkJRenRUUVVOMFFqdFJRVU5FTEU5QlFVOHNTMEZCU3l4RFFVRkRPMGxCUTJZc1EwRkJRenRKUVVWRUxDdERRVUVyUXp0SlFVTXZReXhKUVVGSkxFdEJRVXNzUjBGQlJ5eExRVUZMTEVOQlFVTTdTVUZGYkVJc1owUkJRV2RFTzBsQlEyaEVMRWxCUVVrc1QwRkJUeXhIUVVGSExFTkJRVU1zUTBGQlF6dEpRVVZvUWl4NVEwRkJlVU03U1VGRGVrTXNVMEZCVXl4UlFVRlJMRU5CUTJZc2QwSkJRWGRDTEVWQlEzaENMRXRCUVVzc1JVRkRUQ3hUUVVGVExFVkJRMVFzVjBGQlZ5eEZRVU5ZTEZkQlFWYzdVVUZGV0N4SlFVRkpMRXRCUVVzc1JVRkJSVHRaUVVOVUxFOUJRVTg3VTBGRFVqdFJRVU5FTEV0QlFVc3NSMEZCUnl4SlFVRkpMRU5CUVVNN1VVRkZZaXhOUVVGTkxGTkJRVk1zUjBGQlJ5d3lRa0ZCTWtJc1EwRkRNME1zVjBGQlZ5eERRVUZETEZOQlFWTXNSVUZEY2tJc2QwSkJRWGRDTEVOQlEzcENMRU5CUVVNN1VVRkRSaXhKUVVGSkxGTkJRVk1zUlVGQlJUdFpRVU5pTEV0QlFVc3NSMEZCUnl4TFFVRkxMRU5CUVVNN1dVRkRaQ3hQUVVGUE8xTkJRMUk3VVVGRlJDeE5RVUZOTEVkQlFVY3NSMEZCUnp0WlFVTldMRk5CUVZNN1dVRkRWQ3hOUVVGTkxFVkJRVVVzZDBKQlFYZENPMWxCUTJoRExFdEJRVXNzUlVGQlJTeGxRVUZsTEVOQlFVTXNTMEZCU3l4RlFVRkZMRU5CUVVNc1EwRkJReXhYUVVGWExFTkJRVU1zY1VKQlFYRkNMRU5CUVVNN1dVRkRiRVVzVTBGQlV5eEZRVUZGTEZkQlFWY3NRMEZCUXl4VFFVRlRPMWxCUTJoRExGVkJRVlVzUlVGQlJTeFhRVUZYTEVOQlFVTXNWVUZCVlR0WlFVTnNReXhUUVVGVExFVkJRVVVzVjBGQlZ5eERRVUZETEZOQlFWTTdXVUZEYUVNc1VVRkJVU3hGUVVGRkxGZEJRVmNzUTBGQlF5eFJRVUZSTzFsQlF6bENMR0ZCUVdFc1JVRkJSU3hYUVVGWExFTkJRVU1zWVVGQllUdFpRVU40UXl4VFFVRlRMRVZCUVVVc1YwRkJWeXhEUVVGRExGTkJRVk03V1VGRGFFTXNUMEZCVHl4RlFVRkZMRTlCUVU4c1JVRkJSVHRUUVVOdVFpeERRVUZETzFGQlJVWXNTVUZCU1R0WlFVTkdMRWxCUVVrc1EwRkJReXhWUVVGVkxFVkJRVVVzUjBGQlJ5eERRVUZETEVOQlFVTTdVMEZEZGtJN1VVRkJReXhQUVVGUExFdEJRVXNzUlVGQlJUdFpRVU5rTEU5QlFVOHNRMEZCUXl4SFFVRkhMRU5CUVVNc2EwTkJRV3RETEVOQlFVTXNRMEZCUXp0WlFVTm9SQ3hwUWtGQmFVSXNRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJRenRUUVVNeFFqdFJRVVZFTEV0QlFVc3NSMEZCUnl4TFFVRkxMRU5CUVVNN1NVRkRhRUlzUTBGQlF6dEpRVVZFTEdkQ1FVRm5RanRKUVVOb1FpeFRRVUZUTEU5QlFVOHNRMEZCUXl4M1FrRkJkMElzUlVGQlJTeEpRVUZKTEVWQlFVVXNWMEZCVnl4RlFVRkZMRmRCUVZjN1VVRkRka1VzU1VGQlNTeExRVUZMTEVWQlFVVTdXVUZEVkN4UFFVRlBPMU5CUTFJN1VVRkRSQ3hMUVVGTExFZEJRVWNzU1VGQlNTeERRVUZETzFGQlJXSXNUVUZCVFN4VFFVRlRMRWRCUVVjc01rSkJRVEpDTEVOQlF6TkRMRmRCUVZjc1EwRkJReXhUUVVGVExFVkJRM0pDTEhkQ1FVRjNRaXhEUVVONlFpeERRVUZETzFGQlEwWXNTVUZCU1N4VFFVRlRMRVZCUVVVN1dVRkRZaXhMUVVGTExFZEJRVWNzUzBGQlN5eERRVUZETzFsQlEyUXNUMEZCVHp0VFFVTlNPMUZCUlVRc1NVRkJTVHRaUVVOR0xIRkZRVUZ4UlR0WlFVTnlSU3hOUVVGTkxGVkJRVlVzUjBGQlJ5eEZRVUZGTEVOQlFVTTdXVUZEZEVJc1MwRkJTeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhOUVVGTkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVTdaMEpCUTNCRExGVkJRVlVzUTBGQlF5eEpRVUZKTEVOQlEySXNaVUZCWlN4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTXNWMEZCVnl4RFFVRkRMSEZDUVVGeFFpeERRVUZETEVOQlF6bEVMRU5CUVVNN1lVRkRTRHRaUVVORUxFMUJRVTBzUjBGQlJ5eEhRVUZITzJkQ1FVTldMRk5CUVZNc1JVRkJSU3hOUVVGTk8yZENRVU5xUWl4TlFVRk5MRVZCUVVVc2QwSkJRWGRDTzJkQ1FVTm9ReXhKUVVGSkxFVkJRVVVzVlVGQlZUdG5Ra0ZEYUVJc1MwRkJTeXhGUVVGRkxFVkJRVVU3WjBKQlExUXNVMEZCVXl4RlFVRkZMRmRCUVZjc1EwRkJReXhUUVVGVE8yZENRVU5vUXl4VlFVRlZMRVZCUVVVc1YwRkJWeXhEUVVGRExGVkJRVlU3WjBKQlEyeERMRk5CUVZNc1JVRkJSU3hYUVVGWExFTkJRVU1zVTBGQlV6dG5Ra0ZEYUVNc1VVRkJVU3hGUVVGRkxGZEJRVmNzUTBGQlF5eFJRVUZSTzJkQ1FVTTVRaXhoUVVGaExFVkJRVVVzVjBGQlZ5eERRVUZETEdGQlFXRTdaMEpCUTNoRExGTkJRVk1zUlVGQlJTeFhRVUZYTEVOQlFVTXNVMEZCVXp0blFrRkRhRU1zVDBGQlR5eEZRVUZGTEU5QlFVOHNSVUZCUlR0aFFVTnVRaXhEUVVGRE8xbEJRMFlzU1VGQlNTeERRVUZETEZOQlFWTXNSVUZCUlN4SFFVRkhMRU5CUVVNc1EwRkJRenRUUVVOMFFqdFJRVUZETEU5QlFVOHNTMEZCU3l4RlFVRkZPMWxCUTJRc1QwRkJUeXhEUVVGRExFZEJRVWNzUTBGRFZDeHJRMEZCYTBNc1IwRkJSeXgzUWtGQmQwSXNRMEZET1VRc1EwRkJRenRaUVVOR0xHbENRVUZwUWl4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRE8xTkJRekZDTzFGQlEwUXNTMEZCU3l4SFFVRkhMRXRCUVVzc1EwRkJRenRKUVVOb1FpeERRVUZETzBsQlJVUXNiMFpCUVc5R08wbEJRM0JHTEhsRlFVRjVSVHRKUVVONlJTeE5RVUZOTEVOQlFVTXNjVUpCUVhGQ0xFZEJRVWNzVlVGQlV5eFBRVUZQTEVWQlFVVXNTVUZCU1R0UlFVTnVSQ3hKUVVGSkxFVkJRVVVzUjBGQlJ5eE5RVUZOTEVOQlFVTXNkMEpCUVhkQ0xFTkJRVU1zVDBGQlR5eEZRVUZGTEVsQlFVa3NRMEZCUXl4RFFVRkRPMUZCUTNoRUxFbEJRVWtzUzBGQlN5eEhRVUZITEUxQlFVMHNRMEZCUXl4alFVRmpMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU03VVVGRE0wTXNUMEZCVHl4RlFVRkZMRXRCUVVzc1UwRkJVeXhKUVVGSkxFdEJRVXNzUzBGQlN5eEpRVUZKTEVWQlFVVTdXVUZEZWtNc1JVRkJSU3hIUVVGSExFMUJRVTBzUTBGQlF5eDNRa0ZCZDBJc1EwRkJReXhMUVVGTExFVkJRVVVzU1VGQlNTeERRVUZETEVOQlFVTTdXVUZEYkVRc1MwRkJTeXhIUVVGSExFMUJRVTBzUTBGQlF5eGpRVUZqTEVOQlFVTXNTMEZCU3l4RFFVRkRMRU5CUVVNN1UwRkRkRU03VVVGRFJDeFBRVUZQTEVWQlFVVXNRMEZCUXp0SlFVTmFMRU5CUVVNc1EwRkJRenRKUVVWR0xFMUJRVTBzUTBGQlF5eG5Ra0ZCWjBJc1IwRkJSeXhWUVVGVExFOUJRVTg3VVVGRGVFTXNTVUZCU1N4TFFVRkxMRWRCUVVjc1RVRkJUU3hEUVVGRExHMUNRVUZ0UWl4RFFVRkRMRTlCUVU4c1EwRkJReXhEUVVGRE8xRkJRMmhFTEVsQlFVa3NTMEZCU3l4SFFVRkhMRTFCUVUwc1EwRkJReXhqUVVGakxFTkJRVU1zVDBGQlR5eERRVUZETEVOQlFVTTdVVUZETTBNc1QwRkJUeXhMUVVGTExFdEJRVXNzU1VGQlNTeEZRVUZGTzFsQlEzSkNMRXRCUVVzc1IwRkJSeXhMUVVGTExFTkJRVU1zVFVGQlRTeERRVUZETEUxQlFVMHNRMEZCUXl4dFFrRkJiVUlzUTBGQlF5eExRVUZMTEVOQlFVTXNRMEZCUXl4RFFVRkRPMWxCUTNoRUxFdEJRVXNzUjBGQlJ5eE5RVUZOTEVOQlFVTXNZMEZCWXl4RFFVRkRMRXRCUVVzc1EwRkJReXhEUVVGRE8xTkJRM1JETzFGQlEwUXNiMFJCUVc5RU8xRkJRM0JFTEU5QlFVOHNTMEZCU3l4RFFVRkRPMGxCUTJZc1EwRkJReXhEUVVGRE8wbEJSVVk3TzA5QlJVYzdTVUZEU0N4VFFVRlRMRkZCUVZFc1EwRkJReXhOUVVGTkxFVkJRVVVzV1VGQldUdFJRVU53UXl4SlFVRkpMRkZCUVZFc1EwRkJRenRSUVVOaUxFbEJRVWs3V1VGRFJpeFJRVUZSTEVkQlFVY3NUVUZCVFN4RFFVRkRMRmxCUVZrc1EwRkJReXhEUVVGRE8xTkJRMnBETzFGQlFVTXNUMEZCVHl4TFFVRkxMRVZCUVVVN1dVRkRaQ3hQUVVGUExFdEJRVXNzUTBGQlF6dFRRVU5rTzFGQlEwUXNTVUZCU1N4UlFVRlJMRXRCUVVzc1NVRkJTU3hGUVVGRk8xbEJRM0pDTEhkQ1FVRjNRanRaUVVONFFpeFBRVUZQTEV0QlFVc3NRMEZCUXp0VFFVTmtPMUZCUTBRc1QwRkJUeXhQUVVGUExGRkJRVkVzUzBGQlN5eFJRVUZSTEVOQlFVTTdTVUZEZEVNc1EwRkJRenRKUVZsRUxGTkJRVk1zWjBKQlFXZENMRU5CUVVNc1RVRkJUU3hGUVVGRkxGVkJRVlVzUlVGQlJTeGpRVUV5UWl4RlFVRkZPMUZCUTNwRkxIVkRRVUYxUXp0UlFVTjJReXhGUVVGRk8xRkJRMFlzWVVGQllUdFJRVU5pTEdGQlFXRTdVVUZEWWl4dlFrRkJiMEk3VVVGRGNFSXNNa0pCUVRKQ08xRkJRek5DTEhkQ1FVRjNRanRSUVVONFFpeG5SVUZCWjBVN1VVRkRhRVVzZVVKQlFYbENPMUZCUTNwQ0xIVkZRVUYxUlR0UlFVTjJSU3h0UkVGQmJVUTdVVUZEYmtRc1JVRkJSVHRSUVVOR0xIRkRRVUZ4UXp0UlFVTnlReXh6UWtGQmMwSTdVVUZEZEVJc2JVTkJRVzFETzFGQlEyNURMSE5GUVVGelJUdFJRVU4wUlN4elFrRkJjMEk3VVVGRGRFSXNLMEpCUVN0Q08xRkJReTlDTEc5RlFVRnZSVHRSUVVOd1JTeGhRVUZoTzFGQlEySXNNa0pCUVRKQ08xRkJRek5DTEc5RlFVRnZSVHRSUVVOd1JTd3dRa0ZCTUVJN1VVRkRNVUlzYjBOQlFXOURPMUZCUTNCRExHbEZRVUZwUlR0UlFVTnFSU3hyUkVGQmEwUTdVVUZEYkVRc01FSkJRVEJDTzFGQlF6RkNMSEZGUVVGeFJUdFJRVU55UlN4dFJVRkJiVVU3VVVGRGJrVXNjVVZCUVhGRk8xRkJRM0pGTEcxRFFVRnRRenRSUVVOdVF5eDNRa0ZCZDBJN1VVRkRlRUlzZFVWQlFYVkZPMUZCUTNaRkxEWkRRVUUyUXp0UlFVTTNReXhaUVVGWk8xRkJRMW9zYzBWQlFYTkZPMUZCUTNSRkxEUkNRVUUwUWp0UlFVTTFRaXc0UkVGQk9FUTdVVUZET1VRc1owVkJRV2RGTzFGQlEyaEZMREpFUVVFeVJEdFJRVU16UkN4dlFrRkJiMEk3VVVGRGNFSXNOa1JCUVRaRU8xRkJRemRFTEhOQ1FVRnpRanRSUVVOMFFpeE5RVUZOTEZWQlFWVXNSMEZCUnl4WFFVRlhMRU5CUVVNc2MwSkJRWE5DTzFsQlEyNUVMRU5CUVVNc1EwRkJReXhYUVVGWExFTkJRVU1zYzBKQlFYTkNPMWxCUTNCRExFTkJRVU1zUTBGQlF5eE5RVUZOTEVOQlFVTXNaMEpCUVdkQ0xFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTTdVVUZEY0VNc1MwRkJTeXhKUVVGSkxFTkJRVU1zUjBGQlJ5eERRVUZETEVWQlFVVXNRMEZCUXl4SFFVRkhMRlZCUVZVc1EwRkJReXhOUVVGTkxFVkJRVVVzUTBGQlF5eEZRVUZGTEVWQlFVVTdXVUZETVVNc1NVRkRSU3hYUVVGWExFTkJRVU1zYTBKQlFXdENPMmRDUVVNNVFpeFhRVUZYTEVOQlFVTXNhMEpCUVd0Q0xFTkJRVU1zVDBGQlR5eERRVUZETEZWQlFWVXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eEZRVU14UkR0blFrRkRRU3hUUVVGVE8yRkJRMVk3V1VGRFJDeG5SVUZCWjBVN1dVRkRhRVVzYzBWQlFYTkZPMWxCUTNSRkxIRkZRVUZ4UlR0WlFVTnlSU3hKUVVORkxFTkJRVU1zUTBGQlF5eFhRVUZYTEVOQlFVTXNVMEZCVXp0blFrRkRka0lzVlVGQlZTeERRVUZETEVOQlFVTXNRMEZCUXl4TFFVRkxMRmRCUVZjN1owSkJRemRDTEZGQlFWRXNRMEZCUXl4TlFVRk5MRVZCUVVVc1ZVRkJWU3hEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzJkQ1FVTXZRaXhEUVVGRExFTkJRVU1zUTBGQlF5eFBRVUZQTEVsQlFVa3NWMEZCVnl4RFFVRkRMRWxCUVVrc1YwRkJWeXhEUVVGRExFdEJRVXNzUjBGQlJ5eERRVUZETEVOQlFVTXNSVUZEY0VRN1owSkJRMEVzYTBSQlFXdEVPMmRDUVVOc1JDeEpRVUZKTEVOQlFVTXNRMEZCUXl4UFFVRlBMRWxCUVVrc1YwRkJWeXhEUVVGRExFVkJRVVU3YjBKQlF6ZENMRmRCUVZjc1EwRkJReXhMUVVGTExFZEJRVWNzUTBGQlF5eERRVUZETzJsQ1FVTjJRanRuUWtGRFJDeG5Ra0ZCWjBJc1EwRkRaQ3hOUVVGTkxFTkJRVU1zVlVGQlZTeERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUTNKQ0xGVkJRVlVzUjBGQlJ5eEhRVUZITEVkQlFVY3NWVUZCVlN4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVOb1F6dHZRa0ZEUlN4clFrRkJhMElzUlVGQlJTeFhRVUZYTEVOQlFVTXNhMEpCUVd0Q08yOUNRVU5zUkN4WlFVRlpMRVZCUVVVc1YwRkJWeXhEUVVGRExGbEJRVms3YjBKQlEzUkRMSEZDUVVGeFFpeEZRVUZGTEZkQlFWY3NRMEZCUXl4eFFrRkJjVUk3YjBKQlEzaEVMRmRCUVZjc1JVRkJSU3hYUVVGWExFTkJRVU1zVjBGQlZ6dHZRa0ZEY0VNc1UwRkJVeXhGUVVGRkxGZEJRVmNzUTBGQlF5eFRRVUZUTzI5Q1FVTm9ReXhMUVVGTExFVkJRVVVzVjBGQlZ5eERRVUZETEV0QlFVc3NSMEZCUnl4RFFVRkRPMmxDUVVNM1FpeERRVU5HTEVOQlFVTTdZVUZEU0R0WlFVTkVMRWxCUVVrN1owSkJRMFlzZDBKQlFYZENMRU5CUTNSQ0xFMUJRVTBzUlVGRFRpeFZRVUZWTEVWQlExWXNWVUZCVlN4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVOaUxGZEJRVmNzUTBGRFdpeERRVUZETzJGQlEwZzdXVUZCUXl4UFFVRlBMRXRCUVVzc1JVRkJSVHRuUWtGRFpDeHBRa0ZCYVVJc1EwRkJReXhMUVVGTExFTkJRVU1zUTBGQlF6dGhRVU14UWp0VFFVTkdPMGxCUTBnc1EwRkJRenRKUVVORUxFbEJRVWtzVDBGQlR5eEZRVUZGTzFGQlExWXNUVUZCWXl4RFFVRkRMR2RDUVVGblFpeEhRVUZITEdkQ1FVRm5RaXhEUVVGRE8wdEJRM0pFTzBsQlJVUXNaME5CUVdkRE8wbEJRMmhETEhkRlFVRjNSVHRKUVVONFJTeDVSVUZCZVVVN1NVRkRla1VzZDBSQlFYZEVPMGxCUTNoRUxGTkJRVk1zYTBKQlFXdENMRU5CUVVNc1ZVRkJWU3hGUVVGRkxGVkJRVlVzUlVGQlJTeEpRVUZKTEVWQlFVVXNWMEZCVnp0UlFVTnVSU3hQUVVGUE8xbEJRMHdzVFVGQlRTeFhRVUZYTEVkQlFVY3NNa0pCUVRKQ0xFTkJRemRETEVOQlFVTXNRMEZCUXl4WFFVRlhMRU5CUVVNc1dVRkJXU3hEUVVNelFpeERRVUZETzFsQlEwWXNUMEZCVHl4RFFVTk1MRlZCUVZVc1IwRkJSeXhIUVVGSExFZEJRVWNzVlVGQlZTeEZRVU0zUWl4VFFVRlRMRVZCUTFRc1YwRkJWeXhGUVVOWUxGZEJRVmNzUTBGRFdpeERRVUZETzFsQlEwWXNUMEZCVHl4SlFVRkpMRU5CUVVNc1MwRkJTeXhEUVVGRExFbEJRVWtzUlVGQlJTeFRRVUZUTEVOQlFVTXNRMEZCUXp0UlFVTnlReXhEUVVGRExFTkJRVU03U1VGRFNpeERRVUZETzBsQlJVUXNNa05CUVRKRE8wbEJRek5ETEZOQlFWTXNkMEpCUVhkQ0xFTkJReTlDTEUxQlFVMHNSVUZEVGl4VlFVRlZMRVZCUTFZc1dVRkJXU3hGUVVOYUxHTkJRVEpDTEVWQlFVVTdVVUZGTjBJc2RVTkJRWFZETzFGQlEzWkRMRTFCUVUwc1VVRkJVU3hIUVVGSExFMUJRVTBzUTBGQlF5eHhRa0ZCY1VJc1EwRkJReXhOUVVGTkxFVkJRVVVzV1VGQldTeERRVUZETEVOQlFVTTdVVUZEY0VVc1NVRkJTU3hEUVVGRExGRkJRVkVzUlVGQlJUdFpRVU5pTEU5QlFVOHNRMEZCUXl4TFFVRkxMRU5CUTFnc2JVTkJRVzFETEVWQlEyNURMRlZCUVZVc1JVRkRWaXhaUVVGWkxFVkJRMW9zVFVGQlRTeERRVU5RTEVOQlFVTTdXVUZEUml4UFFVRlBPMU5CUTFJN1VVRkZSQ3h0UkVGQmJVUTdVVUZEYmtRc1RVRkJUU3hqUVVGakxFZEJRVWNzVVVGQlVTeERRVUZETEVkQlFVY3NRMEZCUXp0UlFVTndReXhOUVVGTkxHTkJRV01zUjBGQlJ5eFJRVUZSTEVOQlFVTXNSMEZCUnl4RFFVRkRPMUZCUTNCRExFbEJRVWtzWVVGQllTeEhRVUZITEZGQlFWRXNRMEZCUXl4TFFVRkxMRU5CUVVNN1VVRkZia01zYjBWQlFXOUZPMUZCUTNCRkxHOUNRVUZ2UWp0UlFVTndRaXhOUVVGTkxFTkJRVU1zWTBGQll5eERRVUZETEUxQlFVMHNSVUZCUlN4WlFVRlpMRVZCUVVVN1dVRkRNVU1zV1VGQldTeEZRVUZGTEVsQlFVazdXVUZEYkVJc1IwRkJSeXhGUVVGRkxFTkJRVU03WjBKQlEwb3NUMEZCVHp0dlFrRkRUQ3hKUVVGSkxGbEJRVmtzUTBGQlF6dHZRa0ZEYWtJc1RVRkJUU3hYUVVGWExFZEJRVWNzTWtKQlFUSkNMRU5CUXpkRExFTkJRVU1zUTBGQlF5eFhRVUZYTEVOQlFVTXNXVUZCV1N4RFFVTXpRaXhEUVVGRE8yOUNRVVZHTEhGQ1FVRnhRanR2UWtGRGNrSXNTVUZCU1N4alFVRmpMRVZCUVVVN2QwSkJRMnhDTEhWQ1FVRjFRanQzUWtGRGRrSXNXVUZCV1N4SFFVRkhMR05CUVdNc1EwRkJReXhKUVVGSkxFTkJRVU1zU1VGQlNTeERRVUZETEVOQlFVTTdjVUpCUXpGRE8zbENRVUZOTEVsQlFVa3NUMEZCVHl4SlFVRkpMRkZCUVZFc1JVRkJSVHQzUWtGRE9VSXNiVUpCUVcxQ08zZENRVU51UWl4WlFVRlpMRWRCUVVjc1lVRkJZU3hEUVVGRE8zRkNRVU01UWp0NVFrRkJUVHQzUWtGRFRDeFBRVUZQTEVOQlFVTXNTMEZCU3l4RFFVTllMSGxDUVVGNVFpeEZRVU42UWl4VlFVRlZMRWRCUVVjc1IwRkJSeXhIUVVGSExGbEJRVmtzUlVGREwwSXNLMEpCUVN0Q0xFTkJRMmhETEVOQlFVTTdkMEpCUTBZc1VVRkJVU3hEUVVOT0xGVkJRVlVzUjBGQlJ5eEhRVUZITEVkQlFVY3NXVUZCV1N4RlFVTXZRaXhGUVVGRkxFVkJRMFlzWVVGQllTeEZRVU5pTEZkQlFWY3NSVUZEV0N4WFFVRlhMRU5CUTFvc1EwRkJRenQzUWtGRFJpeFBRVUZQTzNGQ1FVTlNPMjlDUVVWRUxDdEVRVUVyUkR0dlFrRkRMMFFzTWtSQlFUSkVPMjlDUVVNelJDeHpSRUZCYzBRN2IwSkJRM1JFTEd0RlFVRnJSVHR2UWtGRGJFVXNTVUZCU1N4UFFVRlBMRmxCUVZrc1MwRkJTeXhWUVVGVkxFVkJRVVU3ZDBKQlEzUkRMRTlCUVU4c2EwSkJRV3RDTEVOQlEzWkNMRlZCUVZVc1JVRkRWaXhaUVVGWkxFVkJRMW9zV1VGQldTeEZRVU5hTEZkQlFWY3NRMEZEV2l4RFFVRkRPM0ZDUVVOSU8zbENRVUZOTEVsQlEwd3NUMEZCVHl4WlFVRlpMRXRCUVVzc1VVRkJVVHQzUWtGRGFFTXNRMEZCUXl4RFFVRkRMRmRCUVZjc1EwRkJReXhUUVVGVE8zZENRVU4yUWl4RFFVRkRMRU5CUVVNc1EwRkJReXhQUVVGUExFbEJRVWtzVjBGQlZ5eERRVUZETEVsQlFVa3NWMEZCVnl4RFFVRkRMRXRCUVVzc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGRGNFUTdkMEpCUTBFc1QwRkJUeXhaUVVGWkxFTkJRVU03Y1VKQlEzSkNPM2xDUVVGTk8zZENRVU5NTEZGQlFWRXNRMEZEVGl4VlFVRlZMRWRCUVVjc1IwRkJSeXhIUVVGSExGbEJRVmtzUlVGREwwSXNXVUZCV1N4RlFVTmFMRXRCUVVzc1JVRkRUQ3hYUVVGWExFVkJRMWdzVjBGQlZ5eERRVU5hTEVOQlFVTTdkMEpCUTBZc1QwRkJUeXhaUVVGWkxFTkJRVU03Y1VKQlEzSkNPMmRDUVVOSUxFTkJRVU1zUTBGQlF6dFpRVU5LTEVOQlFVTXNRMEZCUXl4RlFVRkZPMWxCUTBvc1IwRkJSeXhGUVVGRkxFTkJRVU03WjBKQlEwb3NUMEZCVHl4VlFVRlRMRXRCUVVzN2IwSkJRMjVDTEUxQlFVMHNWMEZCVnl4SFFVRkhMREpDUVVFeVFpeERRVU0zUXl4RFFVRkRMRU5CUVVNc1YwRkJWeXhEUVVGRExGbEJRVmtzUTBGRE0wSXNRMEZCUXp0dlFrRkRSaXhKUVVGSkxGZEJRVmNzUTBGQlF6dHZRa0ZGYUVJc2IwUkJRVzlFTzI5Q1FVTndSQ3hKUVVORkxFTkJRVU1zUTBGQlF5eFhRVUZYTEVOQlFVTXNWMEZCVnp0M1FrRkRla0lzUTBGQlF5eFBRVUZQTEdGQlFXRXNTMEZCU3l4VlFVRlZPelJDUVVOc1F5eFBRVUZQTEdGQlFXRXNTMEZCU3l4UlFVRlJMRU5CUVVNc1JVRkRjRU03ZDBKQlEwRXNVVUZCVVN4RFFVTk9MRlZCUVZVc1IwRkJSeXhIUVVGSExFZEJRVWNzV1VGQldTeEZRVU12UWl4TFFVRkxMRVZCUTB3c1owSkJRV2RDTEVWQlEyaENMRmRCUVZjc1JVRkRXQ3hYUVVGWExFTkJRMW9zUTBGQlF6dDNRa0ZEUml4UFFVRlBMRXRCUVVzc1EwRkJRenR4UWtGRFpEdHZRa0ZGUkN3MFEwRkJORU03YjBKQlF6VkRMRWxCUVVrc1kwRkJZeXhGUVVGRk8zZENRVU5zUWl4MVFrRkJkVUk3ZDBKQlEzWkNMRmRCUVZjc1IwRkJSeXhqUVVGakxFTkJRVU1zU1VGQlNTeERRVUZETEVsQlFVa3NSVUZCUlN4TFFVRkxMRU5CUVVNc1EwRkJRenR4UWtGRGFFUTdlVUpCUVUwc1NVRkJTU3hQUVVGUExFbEJRVWtzVVVGQlVTeEZRVUZGTzNkQ1FVTTVRaXhMUVVGTExFZEJRVWNzU1VGQlNTeERRVUZETzNkQ1FVTmlMRWxCUVVrc1RVRkJUU3hEUVVGRExHRkJRV0VzUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlRzMFFrRkRPVUlzVFVGQlRTeERRVUZETEdOQlFXTXNRMEZCUXl4SlFVRkpMRVZCUVVVc1dVRkJXU3hGUVVGRk8yZERRVU40UXl4TFFVRkxPelpDUVVOT0xFTkJRVU1zUTBGQlF6dDVRa0ZEU2pzMlFrRkJUVHMwUWtGRFRDeGhRVUZoTEVkQlFVY3NTMEZCU3l4RFFVRkRPM2xDUVVOMlFqdDNRa0ZEUkN4WFFVRlhMRWRCUVVjc1MwRkJTeXhEUVVGRE8zZENRVU53UWl4TFFVRkxMRWRCUVVjc1MwRkJTeXhEUVVGRE8zRkNRVU5tTzNsQ1FVRk5PM2RDUVVOTUxFOUJRVThzUTBGQlF5eExRVUZMTEVOQlExZ3NlVUpCUVhsQ0xFVkJRM3BDTEZWQlFWVXNSMEZCUnl4SFFVRkhMRWRCUVVjc1dVRkJXU3hGUVVNdlFpd3JRa0ZCSzBJc1EwRkRhRU1zUTBGQlF6dDNRa0ZEUml4UlFVRlJMRU5CUTA0c1ZVRkJWU3hIUVVGSExFZEJRVWNzUjBGQlJ5eFpRVUZaTEVWQlF5OUNMRXRCUVVzc1JVRkRUQ3hoUVVGaExFVkJRMklzVjBGQlZ5eEZRVU5ZTEZkQlFWY3NRMEZEV2l4RFFVRkRPM2RDUVVOR0xFOUJRVThzUzBGQlN5eERRVUZETzNGQ1FVTmtPMjlDUVVWRUxGVkJRVlU3YjBKQlExWXNVVUZCVVN4RFFVTk9MRlZCUVZVc1IwRkJSeXhIUVVGSExFZEJRVWNzV1VGQldTeEZRVU12UWl4TFFVRkxMRVZCUTB3c1MwRkJTeXhGUVVOTUxGZEJRVmNzUlVGRFdDeFhRVUZYTEVOQlExb3NRMEZCUXp0dlFrRkZSaXh0UWtGQmJVSTdiMEpCUTI1Q0xFOUJRVThzVjBGQlZ5eERRVUZETzJkQ1FVTnlRaXhEUVVGRExFTkJRVU03V1VGRFNpeERRVUZETEVOQlFVTXNSVUZCUlR0VFFVTk1MRU5CUVVNc1EwRkJRenRKUVVOTUxFTkJRVU03U1VGRlJEczdUMEZGUnp0SlFVTklMSGxFUVVGNVJEdEpRVVY2UkN4cFEwRkJhVU03U1VGRGFrTXNUVUZCVFN4dFFrRkJiVUlzUjBGQlJ6dFJRVU14UWl4aFFVRmhPMUZCUTJJc1UwRkJVenRSUVVOVUxGbEJRVms3VVVGRFdpeFRRVUZUTzFGQlExUXNaVUZCWlR0UlFVTm1MRmxCUVZrN1VVRkRXaXhoUVVGaE8xRkJRMklzVlVGQlZUdFJRVU5XTEZkQlFWYzdVVUZEV0N4UlFVRlJPMUZCUTFJc1QwRkJUenRSUVVOUUxGVkJRVlU3VVVGRFZpeFRRVUZUTzFGQlExUXNXVUZCV1R0UlFVTmFMRmRCUVZjN1VVRkRXQ3hYUVVGWE8xRkJRMWdzVVVGQlVUdExRVU5VTEVOQlFVTTdTVUZEUml4dFFrRkJiVUlzUTBGQlF5eFBRVUZQTEVOQlFVTXNWVUZCVXl4UlFVRlJPMUZCUXpORExIZENRVUYzUWl4RFFVRkRMRTFCUVUwc1EwRkJReXhUUVVGVExFVkJRVVVzYTBKQlFXdENMRVZCUVVVc1VVRkJVU3hEUVVGRExFTkJRVU03U1VGRE0wVXNRMEZCUXl4RFFVRkRMRU5CUVVNN1NVRkZTQ3c0UWtGQk9FSTdTVUZET1VJc2IwUkJRVzlFTzBsQlEzQkVMSGRFUVVGM1JEdEpRVU40UkN4TlFVRk5MR2RDUVVGblFpeEhRVUZITEVOQlFVTXNXVUZCV1N4RlFVRkZMRmxCUVZrc1EwRkJReXhEUVVGRE8wbEJRM1JFTEdkQ1FVRm5RaXhEUVVGRExFOUJRVThzUTBGQlF5eFZRVUZUTEZGQlFWRTdVVUZEZUVNc2QwSkJRWGRDTEVOQlFVTXNUVUZCVFN4RFFVRkRMRTFCUVUwc1JVRkJSU3hsUVVGbExFVkJRVVVzVVVGQlVTeERRVUZETEVOQlFVTTdTVUZEY2tVc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRlNDeHZRa0ZCYjBJN1NVRkRjRUlzVFVGQlRTeG5Ra0ZCWjBJc1IwRkJSenRSUVVOMlFpeE5RVUZOTzFGQlEwNHNWVUZCVlR0UlFVTldMR0ZCUVdFN1VVRkRZaXhUUVVGVE8xRkJRMVFzVVVGQlVUdExRVU5VTEVOQlFVTTdTVUZEUml4TFFVRkxMRWxCUVVrc1EwRkJReXhIUVVGSExFTkJRVU1zUlVGQlJTeERRVUZETEVkQlFVY3NUVUZCVFN4RFFVRkRMRk5CUVZNc1EwRkJReXhQUVVGUExFTkJRVU1zVFVGQlRTeEZRVUZGTEVOQlFVTXNSVUZCUlN4RlFVRkZPMUZCUTNoRUxFMUJRVTBzVlVGQlZTeEhRVUZITEUxQlFVMHNRMEZCUXl4VFFVRlRMRU5CUVVNc1QwRkJUeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVsQlFVa3NRMEZCUXp0UlFVTndSQ3huUWtGQlowSXNRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJVeXhSUVVGUk8xbEJRM2hETEhkQ1FVRjNRaXhEUVVOMFFpeE5RVUZOTEVOQlFVTXNVMEZCVXl4RFFVRkRMRTlCUVU4c1EwRkJReXhWUVVGVkxFTkJRVU1zUlVGRGNFTXNNa0pCUVRKQ0xFZEJRVWNzVlVGQlZTeEhRVUZITEVkQlFVY3NSVUZET1VNc1VVRkJVU3hEUVVOVUxFTkJRVU03VVVGRFNpeERRVUZETEVOQlFVTXNRMEZCUXp0TFFVTktPMGxCUlVRc2MwSkJRWE5DTzBsQlEzUkNMRTFCUVUwc2EwSkJRV3RDTEVkQlFVY3NRMEZCUXl4aFFVRmhMRVZCUVVVc1ZVRkJWU3hGUVVGRkxFMUJRVTBzUTBGQlF5eERRVUZETzBsQlF5OUVMRXRCUVVzc1NVRkJTU3hEUVVGRExFZEJRVWNzUTBGQlF5eEZRVUZGTEVOQlFVTXNSMEZCUnl4TlFVRk5MRU5CUVVNc1UwRkJVeXhEUVVGRExGTkJRVk1zUTBGQlF5eE5RVUZOTEVWQlFVVXNRMEZCUXl4RlFVRkZMRVZCUVVVN1VVRkRNVVFzVFVGQlRTeFpRVUZaTEVkQlFVc3NUVUZCVFN4RFFVRkRMRk5CUVZNc1EwRkJReXhUUVVGVExFTkJReTlETEVOQlFVTXNRMEZEZFVJc1EwRkJReXhKUVVGSkxFTkJRVU1zUTBGQlF5d3JRMEZCSzBNN1VVRkRhRVlzYTBKQlFXdENMRU5CUVVNc1QwRkJUeXhEUVVGRExGVkJRVk1zVVVGQlVUdFpRVU14UXl4M1FrRkJkMElzUTBGRGRFSXNUVUZCVFN4RFFVRkRMRk5CUVZNc1EwRkJReXhUUVVGVExFTkJRVU1zV1VGQldTeERRVUZETEVWQlEzaERMRFpDUVVFMlFpeEhRVUZITEZsQlFWa3NSMEZCUnl4SFFVRkhMRVZCUTJ4RUxGRkJRVkVzUTBGRFZDeERRVUZETzFGQlEwb3NRMEZCUXl4RFFVRkRMRU5CUVVNN1MwRkRTanRKUVVORUxHdEVRVUZyUkR0SlFVTnNSQ3hyUmtGQmEwWTdTVUZEYkVZc2IwWkJRVzlHTzBsQlEzQkdMSFZHUVVGMVJqdEpRVU4yUml3MlJrRkJOa1k3U1VGRE4wWXNUVUZCVFN4blFrRkJaMElzUjBGQlJ5eERRVUZETEUxQlFVMHNSVUZCUlN4alFVRmpMRVZCUVVVc1owSkJRV2RDTEVOQlFVTXNRMEZCUXp0SlFVTndSU3huUWtGQlowSXNRMEZCUXl4UFFVRlBMRU5CUVVNc1ZVRkJVeXhSUVVGUk8xRkJRM2hETEhkQ1FVRjNRaXhEUVVGRExFMUJRVTBzUlVGQlJTeFJRVUZSTEVWQlFVVXNVVUZCVVN4RFFVRkRMRU5CUVVNN1NVRkRka1FzUTBGQlF5eERRVUZETEVOQlFVTTdTVUZEU0N4blFrRkJaMElzUTBGQlF5eE5RVUZOTEVOQlFVTXNUMEZCVHl4RFFVRkRMRk5CUVZNc1JVRkJSU3huUWtGQlowSXNRMEZCUXl4RFFVRkRPMGxCUlRkRUxEUkNRVUUwUWp0SlFVTTFRaXgzUWtGQmQwSXNRMEZCUXl4TlFVRk5MRU5CUVVNc1VVRkJVU3hGUVVGRkxHbENRVUZwUWl4RlFVRkZMRkZCUVZFc1JVRkJSVHRSUVVOeVJTeFpRVUZaTEVWQlFVVXNTVUZCU1R0TFFVTnVRaXhEUVVGRExFTkJRVU03U1VGRlNDdzRRa0ZCT0VJN1NVRkRPVUlzZDBKQlFYZENMRU5CUVVNc1RVRkJUU3hEUVVGRExGRkJRVkVzUlVGQlJTeHBRa0ZCYVVJc1JVRkJSU3hWUVVGVkxFVkJRVVU3VVVGRGRrVXNXVUZCV1N4RlFVRkZMRWxCUVVrN1MwRkRia0lzUTBGQlF5eERRVUZETzBsQlJVZ3NiVUpCUVcxQ08wbEJRMjVDTEdkQ1FVRm5RaXhEUVVGRExFMUJRVTBzUTBGQlF5eHBRa0ZCYVVJc1EwRkJReXhUUVVGVExFVkJRVVVzYlVKQlFXMUNMRU5CUVVNc1EwRkJRenRKUVVVeFJTeE5RVUZOTEd0Q1FVRnJRaXhIUVVGSE8xRkJRM3BDTEd0Q1FVRnJRanRSUVVOc1FpeFJRVUZSTzFGQlExSXNWMEZCVnp0UlFVTllMR0ZCUVdFN1VVRkRZaXhSUVVGUk8xRkJRMUlzVjBGQlZ6dFJRVU5ZTEdOQlFXTTdVVUZEWkN4WFFVRlhPMUZCUTFnc1YwRkJWenRSUVVOWUxGZEJRVmM3VVVGRFdDeFJRVUZSTzFGQlExSXNWMEZCVnp0TFFVTmFMRU5CUVVNN1NVRkRSaXhuUWtGQlowSXNRMEZEWkN4TlFVRk5MRU5CUVVNc2QwSkJRWGRDTEVOQlFVTXNVMEZCVXl4RlFVTjZReXd3UWtGQk1FSXNSVUZETVVJc1JVRkJSU3hyUWtGQmEwSXNSVUZCUlN4RFFVTjJRaXhEUVVGRE8wbEJSVVlzYlVKQlFXMUNPMGxCUTI1Q0xHZENRVUZuUWl4RFFVRkRMRTFCUVUwc1EwRkJReXhwUWtGQmFVSXNRMEZCUXl4VFFVRlRMRVZCUVVVc2JVSkJRVzFDTEVOQlFVTXNRMEZCUXp0SlFVVXhSU3h6UWtGQmMwSTdTVUZEZEVJc1owSkJRV2RDTEVOQlFVTXNUVUZCVFN4RFFVRkRMRmxCUVZrc1EwRkJReXhUUVVGVExFVkJRVVVzWTBGQll5eERRVUZETEVOQlFVTTdTVUZEYUVVc1owSkJRV2RDTEVOQlFVTXNUVUZCVFN4RFFVRkRMRzFDUVVGdFFpeERRVUZETEZOQlFWTXNSVUZCUlN4eFFrRkJjVUlzUTBGQlF5eERRVUZETzBsQlF6bEZMR2RDUVVGblFpeERRVUZETEUxQlFVMHNRMEZCUXl4alFVRmpMRU5CUVVNc1UwRkJVeXhGUVVGRkxHZENRVUZuUWl4RFFVRkRMRU5CUVVNN1NVRkRjRVVzWjBKQlFXZENMRU5CUVVNc1RVRkJUU3hEUVVGRExGbEJRVmtzUTBGQlF5eFRRVUZUTEVWQlFVVXNZMEZCWXl4RFFVRkRMRU5CUVVNN1NVRkRhRVVzWjBKQlFXZENMRU5CUVVNc1RVRkJUU3hEUVVGRExGRkJRVkVzUTBGQlF5eFRRVUZUTEVWQlFVVXNWVUZCVlN4RFFVRkRMRU5CUVVNN1NVRkRlRVFzWjBKQlFXZENMRU5CUVVNc1RVRkJUU3hEUVVGRExHMUNRVUZ0UWl4RFFVRkRMRk5CUVZNc1JVRkJSU3h4UWtGQmNVSXNRMEZCUXl4RFFVRkRPMGxCUlRsRkxFbEJRVWtzVDBGQlR5eEZRVUZGTzFGQlExZ3NUMEZCVHl4RFFVRkRMRWRCUVVjc1EwRkRWQ3d3UkVGQk1FUXNSVUZETVVRc1NVRkJTU3hKUVVGSkxFVkJRVVVzUTBGQlF5eFhRVUZYTEVWQlFVVXNRMEZEZWtJc1EwRkJRenRMUVVOSU8wRkJRMGdzUTBGQlF5eERRVUZESW4wPSIsImV4cG9ydCAqIGZyb20gXCIuL2JhY2tncm91bmQvY29va2llLWluc3RydW1lbnRcIjtcbmV4cG9ydCAqIGZyb20gXCIuL2JhY2tncm91bmQvaHR0cC1pbnN0cnVtZW50XCI7XG5leHBvcnQgKiBmcm9tIFwiLi9iYWNrZ3JvdW5kL2phdmFzY3JpcHQtaW5zdHJ1bWVudFwiO1xuZXhwb3J0ICogZnJvbSBcIi4vYmFja2dyb3VuZC9uYXZpZ2F0aW9uLWluc3RydW1lbnRcIjtcbmV4cG9ydCAqIGZyb20gXCIuL2NvbnRlbnQvamF2YXNjcmlwdC1pbnN0cnVtZW50LWNvbnRlbnQtc2NvcGVcIjtcbmV4cG9ydCAqIGZyb20gXCIuL2xpYi9odHRwLXBvc3QtcGFyc2VyXCI7XG5leHBvcnQgKiBmcm9tIFwiLi9saWIvc3RyaW5nLXV0aWxzXCI7XG5leHBvcnQgKiBmcm9tIFwiLi9zY2hlbWFcIjtcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWFXNWtaWGd1YW5NaUxDSnpiM1Z5WTJWU2IyOTBJam9pSWl3aWMyOTFjbU5sY3lJNld5SXVMaTh1TGk5emNtTXZhVzVrWlhndWRITWlYU3dpYm1GdFpYTWlPbHRkTENKdFlYQndhVzVuY3lJNklrRkJRVUVzWTBGQll5eG5RMEZCWjBNc1EwRkJRenRCUVVNdlF5eGpRVUZqTERoQ1FVRTRRaXhEUVVGRE8wRkJRemRETEdOQlFXTXNiME5CUVc5RExFTkJRVU03UVVGRGJrUXNZMEZCWXl4dlEwRkJiME1zUTBGQlF6dEJRVU51UkN4alFVRmpMQ3REUVVFclF5eERRVUZETzBGQlF6bEVMR05CUVdNc2QwSkJRWGRDTEVOQlFVTTdRVUZEZGtNc1kwRkJZeXh2UWtGQmIwSXNRMEZCUXp0QlFVTnVReXhqUVVGakxGVkJRVlVzUTBGQlF5SjkiLCIvKipcbiAqIFRoaXMgZW5hYmxlcyB1cyB0byBrZWVwIGluZm9ybWF0aW9uIGFib3V0IHRoZSBvcmlnaW5hbCBvcmRlclxuICogaW4gd2hpY2ggZXZlbnRzIGFycml2ZWQgdG8gb3VyIGV2ZW50IGxpc3RlbmVycy5cbiAqL1xubGV0IGV2ZW50T3JkaW5hbCA9IDA7XG5leHBvcnQgY29uc3QgaW5jcmVtZW50ZWRFdmVudE9yZGluYWwgPSAoKSA9PiB7XG4gICAgcmV0dXJuIGV2ZW50T3JkaW5hbCsrO1xufTtcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaVpYaDBaVzV6YVc5dUxYTmxjM05wYjI0dFpYWmxiblF0YjNKa2FXNWhiQzVxY3lJc0luTnZkWEpqWlZKdmIzUWlPaUlpTENKemIzVnlZMlZ6SWpwYklpNHVMeTR1THk0dUwzTnlZeTlzYVdJdlpYaDBaVzV6YVc5dUxYTmxjM05wYjI0dFpYWmxiblF0YjNKa2FXNWhiQzUwY3lKZExDSnVZVzFsY3lJNlcxMHNJbTFoY0hCcGJtZHpJam9pUVVGQlFUczdPMGRCUjBjN1FVRkRTQ3hKUVVGSkxGbEJRVmtzUjBGQlJ5eERRVUZETEVOQlFVTTdRVUZGY2tJc1RVRkJUU3hEUVVGRExFMUJRVTBzZFVKQlFYVkNMRWRCUVVjc1IwRkJSeXhGUVVGRk8wbEJRekZETEU5QlFVOHNXVUZCV1N4RlFVRkZMRU5CUVVNN1FVRkRlRUlzUTBGQlF5eERRVUZESW4wPSIsImltcG9ydCB7IG1ha2VVVUlEIH0gZnJvbSBcIi4vdXVpZFwiO1xuLyoqXG4gKiBUaGlzIGVuYWJsZXMgdXMgdG8gYWNjZXNzIGEgdW5pcXVlIHJlZmVyZW5jZSB0byB0aGlzIGJyb3dzZXJcbiAqIHNlc3Npb24gLSByZWdlbmVyYXRlZCBhbnkgdGltZSB0aGUgYmFja2dyb3VuZCBwcm9jZXNzIGdldHNcbiAqIHJlc3RhcnRlZCAod2hpY2ggc2hvdWxkIG9ubHkgYmUgb24gYnJvd3NlciByZXN0YXJ0cylcbiAqL1xuZXhwb3J0IGNvbnN0IGV4dGVuc2lvblNlc3Npb25VdWlkID0gbWFrZVVVSUQoKTtcbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaVpYaDBaVzV6YVc5dUxYTmxjM05wYjI0dGRYVnBaQzVxY3lJc0luTnZkWEpqWlZKdmIzUWlPaUlpTENKemIzVnlZMlZ6SWpwYklpNHVMeTR1THk0dUwzTnlZeTlzYVdJdlpYaDBaVzV6YVc5dUxYTmxjM05wYjI0dGRYVnBaQzUwY3lKZExDSnVZVzFsY3lJNlcxMHNJbTFoY0hCcGJtZHpJam9pUVVGQlFTeFBRVUZQTEVWQlFVVXNVVUZCVVN4RlFVRkZMRTFCUVUwc1VVRkJVU3hEUVVGRE8wRkJSV3hET3pzN08wZEJTVWM3UVVGRFNDeE5RVUZOTEVOQlFVTXNUVUZCVFN4dlFrRkJiMElzUjBGQlJ5eFJRVUZSTEVWQlFVVXNRMEZCUXlKOSIsIi8vIEluY29ycG9yYXRlcyBjb2RlIGZyb206IGh0dHBzOi8vZ2l0aHViLmNvbS9yZWRsaW5lMTMvc2VsZW5pdW0tam1ldGVyL2Jsb2IvNjk2NmQ0YjMyNmNkNzgyNjFlMzFlNmUzMTcwNzY1NjkwNTFjYWMzNy9jb250ZW50L2xpYnJhcnkvcmVjb3JkZXIvSHR0cFBvc3RQYXJzZXIuanNcbmV4cG9ydCBjbGFzcyBIdHRwUG9zdFBhcnNlciB7XG4gICAgLypcbiAgICBwcml2YXRlIGhhc2hlYWRlcnM6IGJvb2xlYW47XG4gICAgcHJpdmF0ZSBzZWVrYWJsZXN0cmVhbTtcbiAgICBwcml2YXRlIHN0cmVhbTtcbiAgICBwcml2YXRlIHBvc3RCb2R5O1xuICAgIHByaXZhdGUgcG9zdExpbmVzO1xuICAgIHByaXZhdGUgcG9zdEhlYWRlcnM7XG4gICAgcHJpdmF0ZSBib2R5O1xuICAgICovXG4gICAgY29uc3RydWN0b3IoXG4gICAgLy8gb25CZWZvcmVTZW5kSGVhZGVyc0V2ZW50RGV0YWlsczogV2ViUmVxdWVzdE9uQmVmb3JlU2VuZEhlYWRlcnNFdmVudERldGFpbHMsXG4gICAgb25CZWZvcmVSZXF1ZXN0RXZlbnREZXRhaWxzLCBkYXRhUmVjZWl2ZXIpIHtcbiAgICAgICAgLy8gdGhpcy5vbkJlZm9yZVNlbmRIZWFkZXJzRXZlbnREZXRhaWxzID0gb25CZWZvcmVTZW5kSGVhZGVyc0V2ZW50RGV0YWlscztcbiAgICAgICAgdGhpcy5vbkJlZm9yZVJlcXVlc3RFdmVudERldGFpbHMgPSBvbkJlZm9yZVJlcXVlc3RFdmVudERldGFpbHM7XG4gICAgICAgIHRoaXMuZGF0YVJlY2VpdmVyID0gZGF0YVJlY2VpdmVyO1xuICAgICAgICAvKlxuICAgICAgICBjb25zb2xlLmxvZyhcbiAgICAgICAgICBcIkh0dHBQb3N0UGFyc2VyXCIsXG4gICAgICAgICAgLy8gb25CZWZvcmVTZW5kSGVhZGVyc0V2ZW50RGV0YWlscyxcbiAgICAgICAgICBvbkJlZm9yZVJlcXVlc3RFdmVudERldGFpbHMsXG4gICAgICAgICk7XG4gICAgICAgICovXG4gICAgfVxuICAgIC8qKlxuICAgICAqIEBwYXJhbSBlbmNvZGluZ1R5cGUgZnJvbSB0aGUgSFRUUCBSZXF1ZXN0IGhlYWRlcnNcbiAgICAgKi9cbiAgICBwYXJzZVBvc3RSZXF1ZXN0KCAvKmVuY29kaW5nVHlwZSovKSB7XG4gICAgICAgIC8vIGNvbnN0IHJlcXVlc3RIZWFkZXJzID0gdGhpcy5vbkJlZm9yZVNlbmRIZWFkZXJzRXZlbnREZXRhaWxzLnJlcXVlc3RIZWFkZXJzO1xuICAgICAgICBjb25zdCByZXF1ZXN0Qm9keSA9IHRoaXMub25CZWZvcmVSZXF1ZXN0RXZlbnREZXRhaWxzLnJlcXVlc3RCb2R5O1xuICAgICAgICBpZiAocmVxdWVzdEJvZHkuZXJyb3IpIHtcbiAgICAgICAgICAgIHRoaXMuZGF0YVJlY2VpdmVyLmxvZ0Vycm9yKFwiRXhjZXB0aW9uOiBVcHN0cmVhbSBmYWlsZWQgdG8gcGFyc2UgUE9TVDogXCIgKyByZXF1ZXN0Qm9keS5lcnJvcik7XG4gICAgICAgIH1cbiAgICAgICAgaWYgKHJlcXVlc3RCb2R5LmZvcm1EYXRhKSB7XG4gICAgICAgICAgICByZXR1cm4ge1xuICAgICAgICAgICAgICAgIC8vIFRPRE86IHJlcXVlc3RCb2R5LmZvcm1EYXRhIHNob3VsZCBwcm9iYWJseSBiZSB0cmFuc2Zvcm1lZCBpbnRvIGFub3RoZXIgZm9ybWF0XG4gICAgICAgICAgICAgICAgcG9zdF9ib2R5OiByZXF1ZXN0Qm9keS5mb3JtRGF0YSxcbiAgICAgICAgICAgIH07XG4gICAgICAgIH1cbiAgICAgICAgLy8gUmV0dXJuIGVtcHR5IHJlc3BvbnNlIHVudGlsIHdlIGhhdmUgYWxsIGluc3RydW1lbnRhdGlvbiBjb252ZXJ0ZWRcbiAgICAgICAgcmV0dXJuIHt9O1xuICAgICAgICAvKlxuICAgICAgICB0aGlzLmRhdGFSZWNlaXZlci5sb2dEZWJ1ZyhcbiAgICAgICAgICBcIkV4Y2VwdGlvbjogSW5zdHJ1bWVudGF0aW9uIHRvIHBhcnNlIFBPU1QgcmVxdWVzdHMgd2l0aG91dCBmb3JtRGF0YSBpcyBub3QgeWV0IHJlc3RvcmVkXCIsXG4gICAgICAgICk7XG4gICAgXG4gICAgICAgIC8vIFRPRE86IFJlZmFjdG9yIHRvIGNvcnJlc3BvbmRpbmcgd2ViZXh0IGxvZ2ljIG9yIGRpc2NhcmRcbiAgICAgICAgdHJ5IHtcbiAgICAgICAgICB0aGlzLnNldHVwU3RyZWFtKCk7XG4gICAgICAgICAgdGhpcy5wYXJzZVN0cmVhbSgpO1xuICAgICAgICB9IGNhdGNoIChlKSB7XG4gICAgICAgICAgdGhpcy5kYXRhUmVjZWl2ZXIubG9nRXJyb3IoXCJFeGNlcHRpb246IEZhaWxlZCB0byBwYXJzZSBQT1NUOiBcIiArIGUpO1xuICAgICAgICAgIHJldHVybiB7fTtcbiAgICAgICAgfVxuICAgIFxuICAgICAgICBjb25zdCBwb3N0Qm9keSA9IHRoaXMucG9zdEJvZHk7XG4gICAgXG4gICAgICAgIGlmICghcG9zdEJvZHkpIHtcbiAgICAgICAgICAvLyBzb21lIHNjcmlwdHMgc3RyYW5nZWx5IHNlbmRzIGVtcHR5IHBvc3QgYm9kaWVzIChjb25maXJtZWQgd2l0aCB0aGUgZGV2ZWxvcGVyIHRvb2xzKVxuICAgICAgICAgIHJldHVybiB7fTtcbiAgICAgICAgfVxuICAgIFxuICAgICAgICBsZXQgaXNNdWx0aVBhcnQgPSBmYWxzZTsgLy8gZW5jVHlwZTogbXVsdGlwYXJ0L2Zvcm0tZGF0YVxuICAgICAgICBjb25zdCBwb3N0SGVhZGVycyA9IHRoaXMucG9zdEhlYWRlcnM7IC8vIHJlcXVlc3QgaGVhZGVycyBmcm9tIHVwbG9hZCBzdHJlYW1cbiAgICAgICAgLy8gU2VlLCBodHRwOi8vc3RhY2tvdmVyZmxvdy5jb20vcXVlc3Rpb25zLzE2NTQ4NTE3L3doYXQtaXMtcmVxdWVzdC1oZWFkZXJzLWZyb20tdXBsb2FkLXN0cmVhbVxuICAgIFxuICAgICAgICAvLyBhZGQgZW5jb2RpbmdUeXBlIGZyb20gcG9zdEhlYWRlcnMgaWYgaXQncyBtaXNzaW5nXG4gICAgICAgIGlmICghZW5jb2RpbmdUeXBlICYmIHBvc3RIZWFkZXJzICYmIFwiQ29udGVudC1UeXBlXCIgaW4gcG9zdEhlYWRlcnMpIHtcbiAgICAgICAgICBlbmNvZGluZ1R5cGUgPSBwb3N0SGVhZGVyc1tcIkNvbnRlbnQtVHlwZVwiXTtcbiAgICAgICAgfVxuICAgIFxuICAgICAgICBpZiAoZW5jb2RpbmdUeXBlLmluZGV4T2YoXCJtdWx0aXBhcnQvZm9ybS1kYXRhXCIpICE9PSAtMSkge1xuICAgICAgICAgIGlzTXVsdGlQYXJ0ID0gdHJ1ZTtcbiAgICAgICAgfVxuICAgIFxuICAgICAgICBsZXQganNvblBvc3REYXRhID0gXCJcIjtcbiAgICAgICAgbGV0IGVzY2FwZWRKc29uUG9zdERhdGEgPSBcIlwiO1xuICAgICAgICBpZiAoaXNNdWx0aVBhcnQpIHtcbiAgICAgICAgICBqc29uUG9zdERhdGEgPSB0aGlzLnBhcnNlTXVsdGlQYXJ0RGF0YShwb3N0Qm9keSAvKiwgZW5jb2RpbmdUeXBlKiAvKTtcbiAgICAgICAgICBlc2NhcGVkSnNvblBvc3REYXRhID0gZXNjYXBlU3RyaW5nKGpzb25Qb3N0RGF0YSk7XG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAganNvblBvc3REYXRhID0gdGhpcy5wYXJzZUVuY29kZWRGb3JtRGF0YShwb3N0Qm9keSwgZW5jb2RpbmdUeXBlKTtcbiAgICAgICAgICBlc2NhcGVkSnNvblBvc3REYXRhID0gZXNjYXBlU3RyaW5nKGpzb25Qb3N0RGF0YSk7XG4gICAgICAgIH1cbiAgICAgICAgcmV0dXJuIHsgcG9zdF9oZWFkZXJzOiBwb3N0SGVhZGVycywgcG9zdF9ib2R5OiBlc2NhcGVkSnNvblBvc3REYXRhIH07XG4gICAgICAgICovXG4gICAgfVxufVxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pYUhSMGNDMXdiM04wTFhCaGNuTmxjaTVxY3lJc0luTnZkWEpqWlZKdmIzUWlPaUlpTENKemIzVnlZMlZ6SWpwYklpNHVMeTR1THk0dUwzTnlZeTlzYVdJdmFIUjBjQzF3YjNOMExYQmhjbk5sY2k1MGN5SmRMQ0p1WVcxbGN5STZXMTBzSW0xaGNIQnBibWR6SWpvaVFVRkJRU3huUzBGQlowczdRVUZsYUVzc1RVRkJUU3hQUVVGUExHTkJRV003U1VGSmVrSTdPenM3T3pzN08wMUJVVVU3U1VGRlJqdEpRVU5GTERoRlFVRTRSVHRKUVVNNVJTd3lRa0ZCYTBVc1JVRkRiRVVzV1VGQldUdFJRVVZhTERCRlFVRXdSVHRSUVVNeFJTeEpRVUZKTEVOQlFVTXNNa0pCUVRKQ0xFZEJRVWNzTWtKQlFUSkNMRU5CUVVNN1VVRkRMMFFzU1VGQlNTeERRVUZETEZsQlFWa3NSMEZCUnl4WlFVRlpMRU5CUVVNN1VVRkRha003T3pzN096dFZRVTFGTzBsQlEwb3NRMEZCUXp0SlFVVkVPenRQUVVWSE8wbEJRMGtzWjBKQlFXZENMRVZCUVVNc1owSkJRV2RDTzFGQlEzUkRMRGhGUVVFNFJUdFJRVU01UlN4TlFVRk5MRmRCUVZjc1IwRkJSeXhKUVVGSkxFTkJRVU1zTWtKQlFUSkNMRU5CUVVNc1YwRkJWeXhEUVVGRE8xRkJRMnBGTEVsQlFVa3NWMEZCVnl4RFFVRkRMRXRCUVVzc1JVRkJSVHRaUVVOeVFpeEpRVUZKTEVOQlFVTXNXVUZCV1N4RFFVRkRMRkZCUVZFc1EwRkRlRUlzTkVOQlFUUkRMRWRCUVVjc1YwRkJWeXhEUVVGRExFdEJRVXNzUTBGRGFrVXNRMEZCUXp0VFFVTklPMUZCUTBRc1NVRkJTU3hYUVVGWExFTkJRVU1zVVVGQlVTeEZRVUZGTzFsQlEzaENMRTlCUVU4N1owSkJRMHdzWjBaQlFXZEdPMmRDUVVOb1JpeFRRVUZUTEVWQlFVVXNWMEZCVnl4RFFVRkRMRkZCUVZFN1lVRkRhRU1zUTBGQlF6dFRRVU5JTzFGQlJVUXNiMFZCUVc5Rk8xRkJRM0JGTEU5QlFVOHNSVUZCUlN4RFFVRkRPMUZCUTFZN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3T3pzN096czdPenM3TzFWQk5FTkZPMGxCUTBvc1EwRkJRenREUVRKVVJpSjkiLCIvKipcbiAqIFRpZXMgdG9nZXRoZXIgdGhlIHR3byBzZXBhcmF0ZSBuYXZpZ2F0aW9uIGV2ZW50cyB0aGF0IHRvZ2V0aGVyIGhvbGRzIGluZm9ybWF0aW9uIGFib3V0IGJvdGggcGFyZW50IGZyYW1lIGlkIGFuZCB0cmFuc2l0aW9uLXJlbGF0ZWQgYXR0cmlidXRlc1xuICovXG5leHBvcnQgY2xhc3MgUGVuZGluZ05hdmlnYXRpb24ge1xuICAgIGNvbnN0cnVjdG9yKCkge1xuICAgICAgICB0aGlzLm9uQmVmb3JlTmF2aWdhdGVFdmVudE5hdmlnYXRpb24gPSBuZXcgUHJvbWlzZShyZXNvbHZlID0+IHtcbiAgICAgICAgICAgIHRoaXMucmVzb2x2ZU9uQmVmb3JlTmF2aWdhdGVFdmVudE5hdmlnYXRpb24gPSByZXNvbHZlO1xuICAgICAgICB9KTtcbiAgICAgICAgdGhpcy5vbkNvbW1pdHRlZEV2ZW50TmF2aWdhdGlvbiA9IG5ldyBQcm9taXNlKHJlc29sdmUgPT4ge1xuICAgICAgICAgICAgdGhpcy5yZXNvbHZlT25Db21taXR0ZWRFdmVudE5hdmlnYXRpb24gPSByZXNvbHZlO1xuICAgICAgICB9KTtcbiAgICB9XG4gICAgcmVzb2x2ZWQoKSB7XG4gICAgICAgIHJldHVybiBQcm9taXNlLmFsbChbXG4gICAgICAgICAgICB0aGlzLm9uQmVmb3JlTmF2aWdhdGVFdmVudE5hdmlnYXRpb24sXG4gICAgICAgICAgICB0aGlzLm9uQ29tbWl0dGVkRXZlbnROYXZpZ2F0aW9uLFxuICAgICAgICBdKTtcbiAgICB9XG4gICAgLyoqXG4gICAgICogRWl0aGVyIHJldHVybnMgb3IgdGltZXMgb3V0IGFuZCByZXR1cm5zIHVuZGVmaW5lZCBvclxuICAgICAqIHJldHVybnMgdGhlIHJlc3VsdHMgZnJvbSByZXNvbHZlZCgpIGFib3ZlXG4gICAgICogQHBhcmFtIG1zXG4gICAgICovXG4gICAgYXN5bmMgcmVzb2x2ZWRXaXRoaW5UaW1lb3V0KG1zKSB7XG4gICAgICAgIGNvbnN0IHJlc29sdmVkID0gYXdhaXQgUHJvbWlzZS5yYWNlKFtcbiAgICAgICAgICAgIHRoaXMucmVzb2x2ZWQoKSxcbiAgICAgICAgICAgIG5ldyBQcm9taXNlKHJlc29sdmUgPT4gc2V0VGltZW91dChyZXNvbHZlLCBtcykpLFxuICAgICAgICBdKTtcbiAgICAgICAgcmV0dXJuIHJlc29sdmVkO1xuICAgIH1cbn1cbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWRhdGE6YXBwbGljYXRpb24vanNvbjtiYXNlNjQsZXlKMlpYSnphVzl1SWpvekxDSm1hV3hsSWpvaWNHVnVaR2x1WnkxdVlYWnBaMkYwYVc5dUxtcHpJaXdpYzI5MWNtTmxVbTl2ZENJNklpSXNJbk52ZFhKalpYTWlPbHNpTGk0dkxpNHZMaTR2YzNKakwyeHBZaTl3Wlc1a2FXNW5MVzVoZG1sbllYUnBiMjR1ZEhNaVhTd2libUZ0WlhNaU9sdGRMQ0p0WVhCd2FXNW5jeUk2SWtGQlJVRTdPMGRCUlVjN1FVRkRTQ3hOUVVGTkxFOUJRVThzYVVKQlFXbENPMGxCU3pWQ08xRkJRMFVzU1VGQlNTeERRVUZETEN0Q1FVRXJRaXhIUVVGSExFbEJRVWtzVDBGQlR5eERRVUZETEU5QlFVOHNRMEZCUXl4RlFVRkZPMWxCUXpORUxFbEJRVWtzUTBGQlF5eHpRMEZCYzBNc1IwRkJSeXhQUVVGUExFTkJRVU03VVVGRGVFUXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRTQ3hKUVVGSkxFTkJRVU1zTUVKQlFUQkNMRWRCUVVjc1NVRkJTU3hQUVVGUExFTkJRVU1zVDBGQlR5eERRVUZETEVWQlFVVTdXVUZEZEVRc1NVRkJTU3hEUVVGRExHbERRVUZwUXl4SFFVRkhMRTlCUVU4c1EwRkJRenRSUVVOdVJDeERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTk1MRU5CUVVNN1NVRkRUU3hSUVVGUk8xRkJRMklzVDBGQlR5eFBRVUZQTEVOQlFVTXNSMEZCUnl4RFFVRkRPMWxCUTJwQ0xFbEJRVWtzUTBGQlF5d3JRa0ZCSzBJN1dVRkRjRU1zU1VGQlNTeERRVUZETERCQ1FVRXdRanRUUVVOb1F5eERRVUZETEVOQlFVTTdTVUZEVEN4RFFVRkRPMGxCUlVRN096czdUMEZKUnp0SlFVTkpMRXRCUVVzc1EwRkJReXh4UWtGQmNVSXNRMEZCUXl4RlFVRkZPMUZCUTI1RExFMUJRVTBzVVVGQlVTeEhRVUZITEUxQlFVMHNUMEZCVHl4RFFVRkRMRWxCUVVrc1EwRkJRenRaUVVOc1F5eEpRVUZKTEVOQlFVTXNVVUZCVVN4RlFVRkZPMWxCUTJZc1NVRkJTU3hQUVVGUExFTkJRVU1zVDBGQlR5eERRVUZETEVWQlFVVXNRMEZCUXl4VlFVRlZMRU5CUVVNc1QwRkJUeXhGUVVGRkxFVkJRVVVzUTBGQlF5eERRVUZETzFOQlEyaEVMRU5CUVVNc1EwRkJRenRSUVVOSUxFOUJRVThzVVVGQlVTeERRVUZETzBsQlEyeENMRU5CUVVNN1EwRkRSaUo5IiwiLyoqXG4gKiBUaWVzIHRvZ2V0aGVyIHRoZSB0d28gc2VwYXJhdGUgZXZlbnRzIHRoYXQgdG9nZXRoZXIgaG9sZHMgaW5mb3JtYXRpb24gYWJvdXQgYm90aCByZXF1ZXN0IGhlYWRlcnMgYW5kIGJvZHlcbiAqL1xuZXhwb3J0IGNsYXNzIFBlbmRpbmdSZXF1ZXN0IHtcbiAgICBjb25zdHJ1Y3RvcigpIHtcbiAgICAgICAgdGhpcy5vbkJlZm9yZVJlcXVlc3RFdmVudERldGFpbHMgPSBuZXcgUHJvbWlzZShyZXNvbHZlID0+IHtcbiAgICAgICAgICAgIHRoaXMucmVzb2x2ZU9uQmVmb3JlUmVxdWVzdEV2ZW50RGV0YWlscyA9IHJlc29sdmU7XG4gICAgICAgIH0pO1xuICAgICAgICB0aGlzLm9uQmVmb3JlU2VuZEhlYWRlcnNFdmVudERldGFpbHMgPSBuZXcgUHJvbWlzZShyZXNvbHZlID0+IHtcbiAgICAgICAgICAgIHRoaXMucmVzb2x2ZU9uQmVmb3JlU2VuZEhlYWRlcnNFdmVudERldGFpbHMgPSByZXNvbHZlO1xuICAgICAgICB9KTtcbiAgICB9XG4gICAgcmVzb2x2ZWQoKSB7XG4gICAgICAgIHJldHVybiBQcm9taXNlLmFsbChbXG4gICAgICAgICAgICB0aGlzLm9uQmVmb3JlUmVxdWVzdEV2ZW50RGV0YWlscyxcbiAgICAgICAgICAgIHRoaXMub25CZWZvcmVTZW5kSGVhZGVyc0V2ZW50RGV0YWlscyxcbiAgICAgICAgXSk7XG4gICAgfVxuICAgIC8qKlxuICAgICAqIEVpdGhlciByZXR1cm5zIG9yIHRpbWVzIG91dCBhbmQgcmV0dXJucyB1bmRlZmluZWQgb3JcbiAgICAgKiByZXR1cm5zIHRoZSByZXN1bHRzIGZyb20gcmVzb2x2ZWQoKSBhYm92ZVxuICAgICAqIEBwYXJhbSBtc1xuICAgICAqL1xuICAgIGFzeW5jIHJlc29sdmVkV2l0aGluVGltZW91dChtcykge1xuICAgICAgICBjb25zdCByZXNvbHZlZCA9IGF3YWl0IFByb21pc2UucmFjZShbXG4gICAgICAgICAgICB0aGlzLnJlc29sdmVkKCksXG4gICAgICAgICAgICBuZXcgUHJvbWlzZShyZXNvbHZlID0+IHNldFRpbWVvdXQocmVzb2x2ZSwgbXMpKSxcbiAgICAgICAgXSk7XG4gICAgICAgIHJldHVybiByZXNvbHZlZDtcbiAgICB9XG59XG4vLyMgc291cmNlTWFwcGluZ1VSTD1kYXRhOmFwcGxpY2F0aW9uL2pzb247YmFzZTY0LGV5SjJaWEp6YVc5dUlqb3pMQ0ptYVd4bElqb2ljR1Z1WkdsdVp5MXlaWEYxWlhOMExtcHpJaXdpYzI5MWNtTmxVbTl2ZENJNklpSXNJbk52ZFhKalpYTWlPbHNpTGk0dkxpNHZMaTR2YzNKakwyeHBZaTl3Wlc1a2FXNW5MWEpsY1hWbGMzUXVkSE1pWFN3aWJtRnRaWE1pT2x0ZExDSnRZWEJ3YVc1bmN5STZJa0ZCUzBFN08wZEJSVWM3UVVGRFNDeE5RVUZOTEU5QlFVOHNZMEZCWXp0SlFXRjZRanRSUVVORkxFbEJRVWtzUTBGQlF5d3lRa0ZCTWtJc1IwRkJSeXhKUVVGSkxFOUJRVThzUTBGQlF5eFBRVUZQTEVOQlFVTXNSVUZCUlR0WlFVTjJSQ3hKUVVGSkxFTkJRVU1zYTBOQlFXdERMRWRCUVVjc1QwRkJUeXhEUVVGRE8xRkJRM0JFTEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTBnc1NVRkJTU3hEUVVGRExDdENRVUVyUWl4SFFVRkhMRWxCUVVrc1QwRkJUeXhEUVVGRExFOUJRVThzUTBGQlF5eEZRVUZGTzFsQlF6TkVMRWxCUVVrc1EwRkJReXh6UTBGQmMwTXNSMEZCUnl4UFFVRlBMRU5CUVVNN1VVRkRlRVFzUTBGQlF5eERRVUZETEVOQlFVTTdTVUZEVEN4RFFVRkRPMGxCUTAwc1VVRkJVVHRSUVVOaUxFOUJRVThzVDBGQlR5eERRVUZETEVkQlFVY3NRMEZCUXp0WlFVTnFRaXhKUVVGSkxFTkJRVU1zTWtKQlFUSkNPMWxCUTJoRExFbEJRVWtzUTBGQlF5d3JRa0ZCSzBJN1UwRkRja01zUTBGQlF5eERRVUZETzBsQlEwd3NRMEZCUXp0SlFVVkVPenM3TzA5QlNVYzdTVUZEU1N4TFFVRkxMRU5CUVVNc2NVSkJRWEZDTEVOQlFVTXNSVUZCUlR0UlFVTnVReXhOUVVGTkxGRkJRVkVzUjBGQlJ5eE5RVUZOTEU5QlFVOHNRMEZCUXl4SlFVRkpMRU5CUVVNN1dVRkRiRU1zU1VGQlNTeERRVUZETEZGQlFWRXNSVUZCUlR0WlFVTm1MRWxCUVVrc1QwRkJUeXhEUVVGRExFOUJRVThzUTBGQlF5eEZRVUZGTEVOQlFVTXNWVUZCVlN4RFFVRkRMRTlCUVU4c1JVRkJSU3hGUVVGRkxFTkJRVU1zUTBGQlF6dFRRVU5vUkN4RFFVRkRMRU5CUVVNN1VVRkRTQ3hQUVVGUExGRkJRVkVzUTBGQlF6dEpRVU5zUWl4RFFVRkRPME5CUTBZaWZRPT0iLCJpbXBvcnQgeyBSZXNwb25zZUJvZHlMaXN0ZW5lciB9IGZyb20gXCIuL3Jlc3BvbnNlLWJvZHktbGlzdGVuZXJcIjtcbi8qKlxuICogVGllcyB0b2dldGhlciB0aGUgdHdvIHNlcGFyYXRlIGV2ZW50cyB0aGF0IHRvZ2V0aGVyIGhvbGRzIGluZm9ybWF0aW9uIGFib3V0IGJvdGggcmVzcG9uc2UgaGVhZGVycyBhbmQgYm9keVxuICovXG5leHBvcnQgY2xhc3MgUGVuZGluZ1Jlc3BvbnNlIHtcbiAgICBjb25zdHJ1Y3RvcigpIHtcbiAgICAgICAgdGhpcy5vbkJlZm9yZVJlcXVlc3RFdmVudERldGFpbHMgPSBuZXcgUHJvbWlzZShyZXNvbHZlID0+IHtcbiAgICAgICAgICAgIHRoaXMucmVzb2x2ZU9uQmVmb3JlUmVxdWVzdEV2ZW50RGV0YWlscyA9IHJlc29sdmU7XG4gICAgICAgIH0pO1xuICAgICAgICB0aGlzLm9uQ29tcGxldGVkRXZlbnREZXRhaWxzID0gbmV3IFByb21pc2UocmVzb2x2ZSA9PiB7XG4gICAgICAgICAgICB0aGlzLnJlc29sdmVPbkNvbXBsZXRlZEV2ZW50RGV0YWlscyA9IHJlc29sdmU7XG4gICAgICAgIH0pO1xuICAgIH1cbiAgICBhZGRSZXNwb25zZVJlc3BvbnNlQm9keUxpc3RlbmVyKGRldGFpbHMpIHtcbiAgICAgICAgdGhpcy5yZXNwb25zZUJvZHlMaXN0ZW5lciA9IG5ldyBSZXNwb25zZUJvZHlMaXN0ZW5lcihkZXRhaWxzKTtcbiAgICB9XG4gICAgcmVzb2x2ZWQoKSB7XG4gICAgICAgIHJldHVybiBQcm9taXNlLmFsbChbXG4gICAgICAgICAgICB0aGlzLm9uQmVmb3JlUmVxdWVzdEV2ZW50RGV0YWlscyxcbiAgICAgICAgICAgIHRoaXMub25Db21wbGV0ZWRFdmVudERldGFpbHMsXG4gICAgICAgIF0pO1xuICAgIH1cbiAgICAvKipcbiAgICAgKiBFaXRoZXIgcmV0dXJucyBvciB0aW1lcyBvdXQgYW5kIHJldHVybnMgdW5kZWZpbmVkIG9yXG4gICAgICogcmV0dXJucyB0aGUgcmVzdWx0cyBmcm9tIHJlc29sdmVkKCkgYWJvdmVcbiAgICAgKiBAcGFyYW0gbXNcbiAgICAgKi9cbiAgICBhc3luYyByZXNvbHZlZFdpdGhpblRpbWVvdXQobXMpIHtcbiAgICAgICAgY29uc3QgcmVzb2x2ZWQgPSBhd2FpdCBQcm9taXNlLnJhY2UoW1xuICAgICAgICAgICAgdGhpcy5yZXNvbHZlZCgpLFxuICAgICAgICAgICAgbmV3IFByb21pc2UocmVzb2x2ZSA9PiBzZXRUaW1lb3V0KHJlc29sdmUsIG1zKSksXG4gICAgICAgIF0pO1xuICAgICAgICByZXR1cm4gcmVzb2x2ZWQ7XG4gICAgfVxufVxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pY0dWdVpHbHVaeTF5WlhOd2IyNXpaUzVxY3lJc0luTnZkWEpqWlZKdmIzUWlPaUlpTENKemIzVnlZMlZ6SWpwYklpNHVMeTR1THk0dUwzTnlZeTlzYVdJdmNHVnVaR2x1WnkxeVpYTndiMjV6WlM1MGN5SmRMQ0p1WVcxbGN5STZXMTBzSW0xaGNIQnBibWR6SWpvaVFVRkpRU3hQUVVGUExFVkJRVVVzYjBKQlFXOUNMRVZCUVVVc1RVRkJUU3d3UWtGQk1FSXNRMEZCUXp0QlFVVm9SVHM3UjBGRlJ6dEJRVU5JTEUxQlFVMHNUMEZCVHl4bFFVRmxPMGxCWXpGQ08xRkJRMFVzU1VGQlNTeERRVUZETERKQ1FVRXlRaXhIUVVGSExFbEJRVWtzVDBGQlR5eERRVUZETEU5QlFVOHNRMEZCUXl4RlFVRkZPMWxCUTNaRUxFbEJRVWtzUTBGQlF5eHJRMEZCYTBNc1IwRkJSeXhQUVVGUExFTkJRVU03VVVGRGNFUXNRMEZCUXl4RFFVRkRMRU5CUVVNN1VVRkRTQ3hKUVVGSkxFTkJRVU1zZFVKQlFYVkNMRWRCUVVjc1NVRkJTU3hQUVVGUExFTkJRVU1zVDBGQlR5eERRVUZETEVWQlFVVTdXVUZEYmtRc1NVRkJTU3hEUVVGRExEaENRVUU0UWl4SFFVRkhMRTlCUVU4c1EwRkJRenRSUVVOb1JDeERRVUZETEVOQlFVTXNRMEZCUXp0SlFVTk1MRU5CUVVNN1NVRkRUU3dyUWtGQkswSXNRMEZEY0VNc1QwRkJPRU03VVVGRk9VTXNTVUZCU1N4RFFVRkRMRzlDUVVGdlFpeEhRVUZITEVsQlFVa3NiMEpCUVc5Q0xFTkJRVU1zVDBGQlR5eERRVUZETEVOQlFVTTdTVUZEYUVVc1EwRkJRenRKUVVOTkxGRkJRVkU3VVVGRFlpeFBRVUZQTEU5QlFVOHNRMEZCUXl4SFFVRkhMRU5CUVVNN1dVRkRha0lzU1VGQlNTeERRVUZETERKQ1FVRXlRanRaUVVOb1F5eEpRVUZKTEVOQlFVTXNkVUpCUVhWQ08xTkJRemRDTEVOQlFVTXNRMEZCUXp0SlFVTk1MRU5CUVVNN1NVRkZSRHM3T3p0UFFVbEhPMGxCUTBrc1MwRkJTeXhEUVVGRExIRkNRVUZ4UWl4RFFVRkRMRVZCUVVVN1VVRkRia01zVFVGQlRTeFJRVUZSTEVkQlFVY3NUVUZCVFN4UFFVRlBMRU5CUVVNc1NVRkJTU3hEUVVGRE8xbEJRMnhETEVsQlFVa3NRMEZCUXl4UlFVRlJMRVZCUVVVN1dVRkRaaXhKUVVGSkxFOUJRVThzUTBGQlF5eFBRVUZQTEVOQlFVTXNSVUZCUlN4RFFVRkRMRlZCUVZVc1EwRkJReXhQUVVGUExFVkJRVVVzUlVGQlJTeERRVUZETEVOQlFVTTdVMEZEYUVRc1EwRkJReXhEUVVGRE8xRkJRMGdzVDBGQlR5eFJRVUZSTEVOQlFVTTdTVUZEYkVJc1EwRkJRenREUVVOR0luMD0iLCJpbXBvcnQgeyBzaGEyNTZCdWZmZXIgfSBmcm9tIFwiLi9zaGEyNTZcIjtcbmV4cG9ydCBjbGFzcyBSZXNwb25zZUJvZHlMaXN0ZW5lciB7XG4gICAgY29uc3RydWN0b3IoZGV0YWlscykge1xuICAgICAgICB0aGlzLnJlc3BvbnNlQm9keSA9IG5ldyBQcm9taXNlKHJlc29sdmUgPT4ge1xuICAgICAgICAgICAgdGhpcy5yZXNvbHZlUmVzcG9uc2VCb2R5ID0gcmVzb2x2ZTtcbiAgICAgICAgfSk7XG4gICAgICAgIHRoaXMuY29udGVudEhhc2ggPSBuZXcgUHJvbWlzZShyZXNvbHZlID0+IHtcbiAgICAgICAgICAgIHRoaXMucmVzb2x2ZUNvbnRlbnRIYXNoID0gcmVzb2x2ZTtcbiAgICAgICAgfSk7XG4gICAgICAgIC8vIFVzZWQgdG8gcGFyc2UgUmVzcG9uc2Ugc3RyZWFtXG4gICAgICAgIGNvbnN0IGZpbHRlciA9IGJyb3dzZXIud2ViUmVxdWVzdC5maWx0ZXJSZXNwb25zZURhdGEoZGV0YWlscy5yZXF1ZXN0SWQpO1xuICAgICAgICBjb25zdCBkZWNvZGVyID0gbmV3IFRleHREZWNvZGVyKFwidXRmLThcIik7XG4gICAgICAgIC8vIGNvbnN0IGVuY29kZXIgPSBuZXcgVGV4dEVuY29kZXIoKTtcbiAgICAgICAgbGV0IHJlc3BvbnNlQm9keSA9IFwiXCI7XG4gICAgICAgIGZpbHRlci5vbmRhdGEgPSBldmVudCA9PiB7XG4gICAgICAgICAgICBzaGEyNTZCdWZmZXIoZXZlbnQuZGF0YSkudGhlbihkaWdlc3QgPT4ge1xuICAgICAgICAgICAgICAgIHRoaXMucmVzb2x2ZUNvbnRlbnRIYXNoKGRpZ2VzdCk7XG4gICAgICAgICAgICB9KTtcbiAgICAgICAgICAgIGNvbnN0IHN0ciA9IGRlY29kZXIuZGVjb2RlKGV2ZW50LmRhdGEsIHsgc3RyZWFtOiB0cnVlIH0pO1xuICAgICAgICAgICAgcmVzcG9uc2VCb2R5ID0gcmVzcG9uc2VCb2R5ICsgc3RyO1xuICAgICAgICAgICAgLy8gcGFzcyB0aHJvdWdoIGFsbCB0aGUgcmVzcG9uc2UgZGF0YVxuICAgICAgICAgICAgZmlsdGVyLndyaXRlKGV2ZW50LmRhdGEpO1xuICAgICAgICB9O1xuICAgICAgICBmaWx0ZXIub25zdG9wID0gX2V2ZW50ID0+IHtcbiAgICAgICAgICAgIHRoaXMucmVzb2x2ZVJlc3BvbnNlQm9keShyZXNwb25zZUJvZHkpO1xuICAgICAgICAgICAgZmlsdGVyLmRpc2Nvbm5lY3QoKTtcbiAgICAgICAgfTtcbiAgICB9XG4gICAgYXN5bmMgZ2V0UmVzcG9uc2VCb2R5KCkge1xuICAgICAgICByZXR1cm4gdGhpcy5yZXNwb25zZUJvZHk7XG4gICAgfVxuICAgIGFzeW5jIGdldENvbnRlbnRIYXNoKCkge1xuICAgICAgICByZXR1cm4gdGhpcy5jb250ZW50SGFzaDtcbiAgICB9XG59XG4vLyMgc291cmNlTWFwcGluZ1VSTD1kYXRhOmFwcGxpY2F0aW9uL2pzb247YmFzZTY0LGV5SjJaWEp6YVc5dUlqb3pMQ0ptYVd4bElqb2ljbVZ6Y0c5dWMyVXRZbTlrZVMxc2FYTjBaVzVsY2k1cWN5SXNJbk52ZFhKalpWSnZiM1FpT2lJaUxDSnpiM1Z5WTJWeklqcGJJaTR1THk0dUx5NHVMM055WXk5c2FXSXZjbVZ6Y0c5dWMyVXRZbTlrZVMxc2FYTjBaVzVsY2k1MGN5SmRMQ0p1WVcxbGN5STZXMTBzSW0xaGNIQnBibWR6SWpvaVFVRkRRU3hQUVVGUExFVkJRVVVzV1VGQldTeEZRVUZGTEUxQlFVMHNWVUZCVlN4RFFVRkRPMEZCUlhoRExFMUJRVTBzVDBGQlR5eHZRa0ZCYjBJN1NVRk5MMElzV1VGQldTeFBRVUU0UXp0UlFVTjRSQ3hKUVVGSkxFTkJRVU1zV1VGQldTeEhRVUZITEVsQlFVa3NUMEZCVHl4RFFVRkRMRTlCUVU4c1EwRkJReXhGUVVGRk8xbEJRM2hETEVsQlFVa3NRMEZCUXl4dFFrRkJiVUlzUjBGQlJ5eFBRVUZQTEVOQlFVTTdVVUZEY2tNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRFNDeEpRVUZKTEVOQlFVTXNWMEZCVnl4SFFVRkhMRWxCUVVrc1QwRkJUeXhEUVVGRExFOUJRVThzUTBGQlF5eEZRVUZGTzFsQlEzWkRMRWxCUVVrc1EwRkJReXhyUWtGQmEwSXNSMEZCUnl4UFFVRlBMRU5CUVVNN1VVRkRjRU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZGU0N4blEwRkJaME03VVVGRGFFTXNUVUZCVFN4TlFVRk5MRWRCUVZFc1QwRkJUeXhEUVVGRExGVkJRVlVzUTBGQlF5eHJRa0ZCYTBJc1EwRkRka1FzVDBGQlR5eERRVUZETEZOQlFWTXNRMEZEV0N4RFFVRkRPMUZCUlZRc1RVRkJUU3hQUVVGUExFZEJRVWNzU1VGQlNTeFhRVUZYTEVOQlFVTXNUMEZCVHl4RFFVRkRMRU5CUVVNN1VVRkRla01zY1VOQlFYRkRPMUZCUlhKRExFbEJRVWtzV1VGQldTeEhRVUZITEVWQlFVVXNRMEZCUXp0UlFVTjBRaXhOUVVGTkxFTkJRVU1zVFVGQlRTeEhRVUZITEV0QlFVc3NRMEZCUXl4RlFVRkZPMWxCUTNSQ0xGbEJRVmtzUTBGQlF5eExRVUZMTEVOQlFVTXNTVUZCU1N4RFFVRkRMRU5CUVVNc1NVRkJTU3hEUVVGRExFMUJRVTBzUTBGQlF5eEZRVUZGTzJkQ1FVTnlReXhKUVVGSkxFTkJRVU1zYTBKQlFXdENMRU5CUVVNc1RVRkJUU3hEUVVGRExFTkJRVU03V1VGRGJFTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1dVRkRTQ3hOUVVGTkxFZEJRVWNzUjBGQlJ5eFBRVUZQTEVOQlFVTXNUVUZCVFN4RFFVRkRMRXRCUVVzc1EwRkJReXhKUVVGSkxFVkJRVVVzUlVGQlJTeE5RVUZOTEVWQlFVVXNTVUZCU1N4RlFVRkZMRU5CUVVNc1EwRkJRenRaUVVONlJDeFpRVUZaTEVkQlFVY3NXVUZCV1N4SFFVRkhMRWRCUVVjc1EwRkJRenRaUVVOc1F5eHhRMEZCY1VNN1dVRkRja01zVFVGQlRTeERRVUZETEV0QlFVc3NRMEZCUXl4TFFVRkxMRU5CUVVNc1NVRkJTU3hEUVVGRExFTkJRVU03VVVGRE0wSXNRMEZCUXl4RFFVRkRPMUZCUlVZc1RVRkJUU3hEUVVGRExFMUJRVTBzUjBGQlJ5eE5RVUZOTEVOQlFVTXNSVUZCUlR0WlFVTjJRaXhKUVVGSkxFTkJRVU1zYlVKQlFXMUNMRU5CUVVNc1dVRkJXU3hEUVVGRExFTkJRVU03V1VGRGRrTXNUVUZCVFN4RFFVRkRMRlZCUVZVc1JVRkJSU3hEUVVGRE8xRkJRM1JDTEVOQlFVTXNRMEZCUXp0SlFVTktMRU5CUVVNN1NVRkZUU3hMUVVGTExFTkJRVU1zWlVGQlpUdFJRVU14UWl4UFFVRlBMRWxCUVVrc1EwRkJReXhaUVVGWkxFTkJRVU03U1VGRE0wSXNRMEZCUXp0SlFVVk5MRXRCUVVzc1EwRkJReXhqUVVGak8xRkJRM3BDTEU5QlFVOHNTVUZCU1N4RFFVRkRMRmRCUVZjc1EwRkJRenRKUVVNeFFpeERRVUZETzBOQlEwWWlmUT09IiwiLyoqXG4gKiBDb2RlIG9yaWdpbmFsbHkgZnJvbSB0aGUgZXhhbXBsZSBhdFxuICogaHR0cHM6Ly9kZXZlbG9wZXIubW96aWxsYS5vcmcvZW4tVVMvZG9jcy9XZWIvQVBJL1N1YnRsZUNyeXB0by9kaWdlc3RcbiAqXG4gKiBOb3RlOiBVc2luZyBTSEEyNTYgaW5zdGVhZCBvZiB0aGUgcHJldmlvdXNseSB1c2VkIE1ENSBkdWUgdG9cbiAqIHRoZSBmb2xsb3dpbmcgY29tbWVudCBmb3VuZCBhdCB0aGUgZG9jdW1lbnRhdGlvbiBwYWdlIGxpbmtlZCBhYm92ZTpcbiAqXG4gKiBXYXJuaW5nOiBPbGRlciBpbnNlY3VyZSBoYXNoIGZ1bmN0aW9ucywgbGlrZSBNRDUsIGFyZSBub3Qgc3VwcG9ydGVkXG4gKiBieSB0aGlzIG1ldGhvZC4gRXZlbiBhIHN1cHBvcnRlZCBtZXRob2QsIFNIQS0xLCBpcyBjb25zaWRlcmVkIHdlYWssXG4gKiBoYXMgYmVlbiBicm9rZW4gYW5kIHNob3VsZCBiZSBhdm9pZGVkIGZvciBjcnlwdG9ncmFwaGljIGFwcGxpY2F0aW9ucy5cbiAqL1xuZXhwb3J0IGZ1bmN0aW9uIHNoYTI1NihzdHIpIHtcbiAgICAvLyBXZSB0cmFuc2Zvcm0gdGhlIHN0cmluZyBpbnRvIGFuIGFycmF5YnVmZmVyLlxuICAgIGNvbnN0IGJ1ZmZlciA9IG5ldyBUZXh0RW5jb2RlcigpLmVuY29kZShzdHIpO1xuICAgIHJldHVybiBzaGEyNTZCdWZmZXIoYnVmZmVyKTtcbn1cbmV4cG9ydCBmdW5jdGlvbiBzaGEyNTZCdWZmZXIoYnVmZmVyKSB7XG4gICAgcmV0dXJuIGNyeXB0by5zdWJ0bGUuZGlnZXN0KFwiU0hBLTI1NlwiLCBidWZmZXIpLnRoZW4oZnVuY3Rpb24gKGhhc2gpIHtcbiAgICAgICAgcmV0dXJuIGhleChoYXNoKTtcbiAgICB9KTtcbn1cbmZ1bmN0aW9uIGhleChidWZmZXIpIHtcbiAgICBjb25zdCBoZXhDb2RlcyA9IFtdO1xuICAgIGNvbnN0IHZpZXcgPSBuZXcgRGF0YVZpZXcoYnVmZmVyKTtcbiAgICBmb3IgKGxldCBpID0gMDsgaSA8IHZpZXcuYnl0ZUxlbmd0aDsgaSArPSA0KSB7XG4gICAgICAgIC8vIFVzaW5nIGdldFVpbnQzMiByZWR1Y2VzIHRoZSBudW1iZXIgb2YgaXRlcmF0aW9ucyBuZWVkZWQgKHdlIHByb2Nlc3MgNCBieXRlcyBlYWNoIHRpbWUpXG4gICAgICAgIGNvbnN0IHZhbHVlID0gdmlldy5nZXRVaW50MzIoaSk7XG4gICAgICAgIC8vIHRvU3RyaW5nKDE2KSB3aWxsIGdpdmUgdGhlIGhleCByZXByZXNlbnRhdGlvbiBvZiB0aGUgbnVtYmVyIHdpdGhvdXQgcGFkZGluZ1xuICAgICAgICBjb25zdCBzdHJpbmdWYWx1ZSA9IHZhbHVlLnRvU3RyaW5nKDE2KTtcbiAgICAgICAgLy8gV2UgdXNlIGNvbmNhdGVuYXRpb24gYW5kIHNsaWNlIGZvciBwYWRkaW5nXG4gICAgICAgIGNvbnN0IHBhZGRpbmcgPSBcIjAwMDAwMDAwXCI7XG4gICAgICAgIGNvbnN0IHBhZGRlZFZhbHVlID0gKHBhZGRpbmcgKyBzdHJpbmdWYWx1ZSkuc2xpY2UoLXBhZGRpbmcubGVuZ3RoKTtcbiAgICAgICAgaGV4Q29kZXMucHVzaChwYWRkZWRWYWx1ZSk7XG4gICAgfVxuICAgIC8vIEpvaW4gYWxsIHRoZSBoZXggc3RyaW5ncyBpbnRvIG9uZVxuICAgIHJldHVybiBoZXhDb2Rlcy5qb2luKFwiXCIpO1xufVxuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pYzJoaE1qVTJMbXB6SWl3aWMyOTFjbU5sVW05dmRDSTZJaUlzSW5OdmRYSmpaWE1pT2xzaUxpNHZMaTR2TGk0dmMzSmpMMnhwWWk5emFHRXlOVFl1ZEhNaVhTd2libUZ0WlhNaU9sdGRMQ0p0WVhCd2FXNW5jeUk2SWtGQlFVRTdPenM3T3pzN096czdSMEZWUnp0QlFVVklMRTFCUVUwc1ZVRkJWU3hOUVVGTkxFTkJRVU1zUjBGQlJ6dEpRVU40UWl3clEwRkJLME03U1VGREwwTXNUVUZCVFN4TlFVRk5MRWRCUVVjc1NVRkJTU3hYUVVGWExFVkJRVVVzUTBGQlF5eE5RVUZOTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN1NVRkROME1zVDBGQlR5eFpRVUZaTEVOQlFVTXNUVUZCVFN4RFFVRkRMRU5CUVVNN1FVRkRPVUlzUTBGQlF6dEJRVVZFTEUxQlFVMHNWVUZCVlN4WlFVRlpMRU5CUVVNc1RVRkJUVHRKUVVOcVF5eFBRVUZQTEUxQlFVMHNRMEZCUXl4TlFVRk5MRU5CUVVNc1RVRkJUU3hEUVVGRExGTkJRVk1zUlVGQlJTeE5RVUZOTEVOQlFVTXNRMEZCUXl4SlFVRkpMRU5CUVVNc1ZVRkJVeXhKUVVGSk8xRkJReTlFTEU5QlFVOHNSMEZCUnl4RFFVRkRMRWxCUVVrc1EwRkJReXhEUVVGRE8wbEJRMjVDTEVOQlFVTXNRMEZCUXl4RFFVRkRPMEZCUTB3c1EwRkJRenRCUVVWRUxGTkJRVk1zUjBGQlJ5eERRVUZETEUxQlFVMDdTVUZEYWtJc1RVRkJUU3hSUVVGUkxFZEJRVWNzUlVGQlJTeERRVUZETzBsQlEzQkNMRTFCUVUwc1NVRkJTU3hIUVVGSExFbEJRVWtzVVVGQlVTeERRVUZETEUxQlFVMHNRMEZCUXl4RFFVRkRPMGxCUTJ4RExFdEJRVXNzU1VGQlNTeERRVUZETEVkQlFVY3NRMEZCUXl4RlFVRkZMRU5CUVVNc1IwRkJSeXhKUVVGSkxFTkJRVU1zVlVGQlZTeEZRVUZGTEVOQlFVTXNTVUZCU1N4RFFVRkRMRVZCUVVVN1VVRkRNME1zZVVaQlFYbEdPMUZCUTNwR0xFMUJRVTBzUzBGQlN5eEhRVUZITEVsQlFVa3NRMEZCUXl4VFFVRlRMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU03VVVGRGFFTXNPRVZCUVRoRk8xRkJRemxGTEUxQlFVMHNWMEZCVnl4SFFVRkhMRXRCUVVzc1EwRkJReXhSUVVGUkxFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTTdVVUZEZGtNc05rTkJRVFpETzFGQlF6ZERMRTFCUVUwc1QwRkJUeXhIUVVGSExGVkJRVlVzUTBGQlF6dFJRVU16UWl4TlFVRk5MRmRCUVZjc1IwRkJSeXhEUVVGRExFOUJRVThzUjBGQlJ5eFhRVUZYTEVOQlFVTXNRMEZCUXl4TFFVRkxMRU5CUVVNc1EwRkJReXhQUVVGUExFTkJRVU1zVFVGQlRTeERRVUZETEVOQlFVTTdVVUZEYmtVc1VVRkJVU3hEUVVGRExFbEJRVWtzUTBGQlF5eFhRVUZYTEVOQlFVTXNRMEZCUXp0TFFVTTFRanRKUVVWRUxHOURRVUZ2UXp0SlFVTndReXhQUVVGUExGRkJRVkVzUTBGQlF5eEpRVUZKTEVOQlFVTXNSVUZCUlN4RFFVRkRMRU5CUVVNN1FVRkRNMElzUTBGQlF5SjkiLCJleHBvcnQgZnVuY3Rpb24gZW5jb2RlX3V0Zjgocykge1xuICAgIHJldHVybiB1bmVzY2FwZShlbmNvZGVVUklDb21wb25lbnQocykpO1xufVxuZXhwb3J0IGNvbnN0IGVzY2FwZVN0cmluZyA9IGZ1bmN0aW9uIChzdHIpIHtcbiAgICAvLyBDb252ZXJ0IHRvIHN0cmluZyBpZiBuZWNlc3NhcnlcbiAgICBpZiAodHlwZW9mIHN0ciAhPSBcInN0cmluZ1wiKSB7XG4gICAgICAgIHN0ciA9IFN0cmluZyhzdHIpO1xuICAgIH1cbiAgICByZXR1cm4gZW5jb2RlX3V0Zjgoc3RyKTtcbn07XG5leHBvcnQgY29uc3QgZXNjYXBlVXJsID0gZnVuY3Rpb24gKHVybCwgc3RyaXBEYXRhVXJsRGF0YSA9IHRydWUpIHtcbiAgICB1cmwgPSBlc2NhcGVTdHJpbmcodXJsKTtcbiAgICAvLyBkYXRhOls8bWVkaWF0eXBlPl1bO2Jhc2U2NF0sPGRhdGE+XG4gICAgaWYgKHVybC5zdWJzdHIoMCwgNSkgPT09IFwiZGF0YTpcIiAmJlxuICAgICAgICBzdHJpcERhdGFVcmxEYXRhICYmXG4gICAgICAgIHVybC5pbmRleE9mKFwiLFwiKSA+IC0xKSB7XG4gICAgICAgIHVybCA9IHVybC5zdWJzdHIoMCwgdXJsLmluZGV4T2YoXCIsXCIpICsgMSkgKyBcIjxkYXRhLXN0cmlwcGVkPlwiO1xuICAgIH1cbiAgICByZXR1cm4gdXJsO1xufTtcbmV4cG9ydCBjb25zdCBib29sVG9JbnQgPSBmdW5jdGlvbiAoYm9vbCkge1xuICAgIHJldHVybiBib29sID8gMSA6IDA7XG59O1xuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZGF0YTphcHBsaWNhdGlvbi9qc29uO2Jhc2U2NCxleUoyWlhKemFXOXVJam96TENKbWFXeGxJam9pYzNSeWFXNW5MWFYwYVd4ekxtcHpJaXdpYzI5MWNtTmxVbTl2ZENJNklpSXNJbk52ZFhKalpYTWlPbHNpTGk0dkxpNHZMaTR2YzNKakwyeHBZaTl6ZEhKcGJtY3RkWFJwYkhNdWRITWlYU3dpYm1GdFpYTWlPbHRkTENKdFlYQndhVzVuY3lJNklrRkJRVUVzVFVGQlRTeFZRVUZWTEZkQlFWY3NRMEZCUXl4RFFVRkRPMGxCUXpOQ0xFOUJRVThzVVVGQlVTeERRVUZETEd0Q1FVRnJRaXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdRVUZEZWtNc1EwRkJRenRCUVVWRUxFMUJRVTBzUTBGQlF5eE5RVUZOTEZsQlFWa3NSMEZCUnl4VlFVRlRMRWRCUVZFN1NVRkRNME1zYVVOQlFXbERPMGxCUTJwRExFbEJRVWtzVDBGQlR5eEhRVUZITEVsQlFVa3NVVUZCVVN4RlFVRkZPMUZCUXpGQ0xFZEJRVWNzUjBGQlJ5eE5RVUZOTEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNN1MwRkRia0k3U1VGRlJDeFBRVUZQTEZkQlFWY3NRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJRenRCUVVNeFFpeERRVUZETEVOQlFVTTdRVUZGUml4TlFVRk5MRU5CUVVNc1RVRkJUU3hUUVVGVExFZEJRVWNzVlVGRGRrSXNSMEZCVnl4RlFVTllMRzFDUVVFMFFpeEpRVUZKTzBsQlJXaERMRWRCUVVjc1IwRkJSeXhaUVVGWkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTTdTVUZEZUVJc2NVTkJRWEZETzBsQlEzSkRMRWxCUTBVc1IwRkJSeXhEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVWQlFVVXNRMEZCUXl4RFFVRkRMRXRCUVVzc1QwRkJUenRSUVVNMVFpeG5Ra0ZCWjBJN1VVRkRhRUlzUjBGQlJ5eERRVUZETEU5QlFVOHNRMEZCUXl4SFFVRkhMRU5CUVVNc1IwRkJSeXhEUVVGRExFTkJRVU1zUlVGRGNrSTdVVUZEUVN4SFFVRkhMRWRCUVVjc1IwRkJSeXhEUVVGRExFMUJRVTBzUTBGQlF5eERRVUZETEVWQlFVVXNSMEZCUnl4RFFVRkRMRTlCUVU4c1EwRkJReXhIUVVGSExFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNSMEZCUnl4cFFrRkJhVUlzUTBGQlF6dExRVU12UkR0SlFVTkVMRTlCUVU4c1IwRkJSeXhEUVVGRE8wRkJRMklzUTBGQlF5eERRVUZETzBGQlJVWXNUVUZCVFN4RFFVRkRMRTFCUVUwc1UwRkJVeXhIUVVGSExGVkJRVk1zU1VGQllUdEpRVU0zUXl4UFFVRlBMRWxCUVVrc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRU5CUVVNN1FVRkRkRUlzUTBGQlF5eERRVUZESW4wPSIsIi8qIHRzbGludDpkaXNhYmxlOm5vLWJpdHdpc2UgKi9cbi8vIGZyb20gaHR0cHM6Ly9naXN0LmdpdGh1Yi5jb20vamVkLzk4Mjg4MyNnaXN0Y29tbWVudC0yNDAzMzY5XG5jb25zdCBoZXggPSBbXTtcbmZvciAobGV0IGkgPSAwOyBpIDwgMjU2OyBpKyspIHtcbiAgICBoZXhbaV0gPSAoaSA8IDE2ID8gXCIwXCIgOiBcIlwiKSArIGkudG9TdHJpbmcoMTYpO1xufVxuZXhwb3J0IGNvbnN0IG1ha2VVVUlEID0gKCkgPT4ge1xuICAgIGNvbnN0IHIgPSBjcnlwdG8uZ2V0UmFuZG9tVmFsdWVzKG5ldyBVaW50OEFycmF5KDE2KSk7XG4gICAgcls2XSA9IChyWzZdICYgMHgwZikgfCAweDQwO1xuICAgIHJbOF0gPSAocls4XSAmIDB4M2YpIHwgMHg4MDtcbiAgICByZXR1cm4gKGhleFtyWzBdXSArXG4gICAgICAgIGhleFtyWzFdXSArXG4gICAgICAgIGhleFtyWzJdXSArXG4gICAgICAgIGhleFtyWzNdXSArXG4gICAgICAgIFwiLVwiICtcbiAgICAgICAgaGV4W3JbNF1dICtcbiAgICAgICAgaGV4W3JbNV1dICtcbiAgICAgICAgXCItXCIgK1xuICAgICAgICBoZXhbcls2XV0gK1xuICAgICAgICBoZXhbcls3XV0gK1xuICAgICAgICBcIi1cIiArXG4gICAgICAgIGhleFtyWzhdXSArXG4gICAgICAgIGhleFtyWzldXSArXG4gICAgICAgIFwiLVwiICtcbiAgICAgICAgaGV4W3JbMTBdXSArXG4gICAgICAgIGhleFtyWzExXV0gK1xuICAgICAgICBoZXhbclsxMl1dICtcbiAgICAgICAgaGV4W3JbMTNdXSArXG4gICAgICAgIGhleFtyWzE0XV0gK1xuICAgICAgICBoZXhbclsxNV1dKTtcbn07XG4vLyMgc291cmNlTWFwcGluZ1VSTD1kYXRhOmFwcGxpY2F0aW9uL2pzb247YmFzZTY0LGV5SjJaWEp6YVc5dUlqb3pMQ0ptYVd4bElqb2lkWFZwWkM1cWN5SXNJbk52ZFhKalpWSnZiM1FpT2lJaUxDSnpiM1Z5WTJWeklqcGJJaTR1THk0dUx5NHVMM055WXk5c2FXSXZkWFZwWkM1MGN5SmRMQ0p1WVcxbGN5STZXMTBzSW0xaGNIQnBibWR6SWpvaVFVRkJRU3dyUWtGQkswSTdRVUZGTDBJc09FUkJRVGhFTzBGQlF6bEVMRTFCUVUwc1IwRkJSeXhIUVVGSExFVkJRVVVzUTBGQlF6dEJRVVZtTEV0QlFVc3NTVUZCU1N4RFFVRkRMRWRCUVVjc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eEhRVUZITEVWQlFVVXNRMEZCUXl4RlFVRkZMRVZCUVVVN1NVRkROVUlzUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRU5CUVVNc1EwRkJReXhIUVVGSExFVkJRVVVzUTBGQlF5eERRVUZETEVOQlFVTXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUjBGQlJ5eERRVUZETEVOQlFVTXNVVUZCVVN4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRE8wTkJReTlETzBGQlJVUXNUVUZCVFN4RFFVRkRMRTFCUVUwc1VVRkJVU3hIUVVGSExFZEJRVWNzUlVGQlJUdEpRVU16UWl4TlFVRk5MRU5CUVVNc1IwRkJSeXhOUVVGTkxFTkJRVU1zWlVGQlpTeERRVUZETEVsQlFVa3NWVUZCVlN4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRExFTkJRVU03U1VGRmNrUXNRMEZCUXl4RFFVRkRMRU5CUVVNc1EwRkJReXhIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4SFFVRkhMRWxCUVVrc1EwRkJReXhIUVVGSExFbEJRVWtzUTBGQlF6dEpRVU0xUWl4RFFVRkRMRU5CUVVNc1EwRkJReXhEUVVGRExFZEJRVWNzUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRMRWRCUVVjc1NVRkJTU3hEUVVGRExFZEJRVWNzU1VGQlNTeERRVUZETzBsQlJUVkNMRTlCUVU4c1EwRkRUQ3hIUVVGSExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXl4RFFVRkRPMUZCUTFRc1IwRkJSeXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTXNRMEZCUXp0UlFVTlVMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEVkN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlExUXNSMEZCUnp0UlFVTklMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEVkN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlExUXNSMEZCUnp0UlFVTklMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEVkN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlExUXNSMEZCUnp0UlFVTklMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETEVOQlFVTTdVVUZEVkN4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFTkJRVU1zUTBGQlF5eERRVUZETzFGQlExUXNSMEZCUnp0UlFVTklMRWRCUVVjc1EwRkJReXhEUVVGRExFTkJRVU1zUlVGQlJTeERRVUZETEVOQlFVTTdVVUZEVml4SFFVRkhMRU5CUVVNc1EwRkJReXhEUVVGRExFVkJRVVVzUTBGQlF5eERRVUZETzFGQlExWXNSMEZCUnl4RFFVRkRMRU5CUVVNc1EwRkJReXhGUVVGRkxFTkJRVU1zUTBGQlF6dFJRVU5XTEVkQlFVY3NRMEZCUXl4RFFVRkRMRU5CUVVNc1JVRkJSU3hEUVVGRExFTkJRVU03VVVGRFZpeEhRVUZITEVOQlFVTXNRMEZCUXl4RFFVRkRMRVZCUVVVc1EwRkJReXhEUVVGRE8xRkJRMVlzUjBGQlJ5eERRVUZETEVOQlFVTXNRMEZCUXl4RlFVRkZMRU5CUVVNc1EwRkJReXhEUVVOWUxFTkJRVU03UVVGRFNpeERRVUZETEVOQlFVTWlmUT09IiwiLy8gaHR0cHM6Ly93d3cudW5pY29kZS5vcmcvcmVwb3J0cy90cjM1L3RyMzUtZGF0ZXMuaHRtbCNEYXRlX0ZpZWxkX1N5bWJvbF9UYWJsZVxuZXhwb3J0IGNvbnN0IGRhdGVUaW1lVW5pY29kZUZvcm1hdFN0cmluZyA9IFwieXl5eS1NTS1kZCdUJ0hIOm1tOnNzLlNTU1hYXCI7XG4vLyMgc291cmNlTWFwcGluZ1VSTD1kYXRhOmFwcGxpY2F0aW9uL2pzb247YmFzZTY0LGV5SjJaWEp6YVc5dUlqb3pMQ0ptYVd4bElqb2ljMk5vWlcxaExtcHpJaXdpYzI5MWNtTmxVbTl2ZENJNklpSXNJbk52ZFhKalpYTWlPbHNpTGk0dkxpNHZjM0pqTDNOamFHVnRZUzUwY3lKZExDSnVZVzFsY3lJNlcxMHNJbTFoY0hCcGJtZHpJam9pUVVGSlFTd3JSVUZCSzBVN1FVRkRMMFVzVFVGQlRTeERRVUZETEUxQlFVMHNNa0pCUVRKQ0xFZEJRVWNzTmtKQlFUWkNMRU5CUVVNaWZRPT0iXSwic291cmNlUm9vdCI6IiJ9