import { incrementedEventOrdinal } from "../lib/extension-session-event-ordinal";
import { extensionSessionUuid } from "../lib/extension-session-uuid";
import { HttpPostParser, ParsedPostRequest } from "../lib/http-post-parser";
import { PendingRequest } from "../lib/pending-request";
import { PendingResponse } from "../lib/pending-response";
import ResourceType = browser.webRequest.ResourceType;
import RequestFilter = browser.webRequest.RequestFilter;
import BlockingResponse = browser.webRequest.BlockingResponse;
import { boolToInt, escapeString, escapeUrl } from "../lib/string-utils";
import { HttpRedirect, HttpRequest, HttpResponse } from "../schema";
import {
  WebRequestOnBeforeRedirectEventDetails,
  WebRequestOnBeforeRequestEventDetails,
  WebRequestOnBeforeSendHeadersEventDetails,
  WebRequestOnCompletedEventDetails,
} from "../types/browser-web-request-event-details";

type SaveContentOption = boolean | string;

/**
 * Note: Different parts of the desired information arrives in different events as per below:
 * request = headers in onBeforeSendHeaders + body in onBeforeRequest
 * response = headers in onCompleted + body via a onBeforeRequest filter
 * redirect = original request headers+body, followed by a onBeforeRedirect and then a new set of request headers+body and response headers+body
 * Docs: https://developer.mozilla.org/en-US/docs/User:wbamberg/webRequest.RequestDetails
 */

export class HttpInstrument {
  private readonly dataReceiver;
  private pendingRequests: {
    [requestId: number]: PendingRequest;
  } = {};
  private pendingResponses: {
    [requestId: number]: PendingResponse;
  } = {};
  private onBeforeRequestListener;
  private onBeforeSendHeadersListener;
  private onBeforeRedirectListener;
  private onCompletedListener;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID, saveContentOption: SaveContentOption) {
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
      "speculative",
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

    const filter: RequestFilter = { urls: ["<all_urls>"], types: allTypes };

    const requestStemsFromExtension = details => {
      return (
        details.originUrl && details.originUrl.indexOf("moz-extension://") > -1
      );
    };

    /*
     * Attach handlers to event listeners
     */

    this.onBeforeRequestListener = (
      details: WebRequestOnBeforeRequestEventDetails,
    ) => {
      const blockingResponseThatDoesNothing: BlockingResponse = {};
      // Ignore requests made by extensions
      if (requestStemsFromExtension(details)) {
        return blockingResponseThatDoesNothing;
      }
      const pendingRequest = this.getPendingRequest(details.requestId);
      pendingRequest.resolveOnBeforeRequestEventDetails(details);
      const pendingResponse = this.getPendingResponse(details.requestId);
      pendingResponse.resolveOnBeforeRequestEventDetails(details);
      if (this.shouldSaveContent(saveContentOption, details.type)) {
        pendingResponse.addResponseResponseBodyListener(details);
      }
      return blockingResponseThatDoesNothing;
    };
    browser.webRequest.onBeforeRequest.addListener(
      this.onBeforeRequestListener,
      filter,
      this.isContentSavingEnabled(saveContentOption)
        ? ["requestBody", "blocking"]
        : ["requestBody"],
    );

    this.onBeforeSendHeadersListener = details => {
      // Ignore requests made by extensions
      if (requestStemsFromExtension(details)) {
        return;
      }
      const pendingRequest = this.getPendingRequest(details.requestId);
      pendingRequest.resolveOnBeforeSendHeadersEventDetails(details);
      this.onBeforeSendHeadersHandler(
        details,
        crawlID,
        incrementedEventOrdinal(),
      );
    };
    browser.webRequest.onBeforeSendHeaders.addListener(
      this.onBeforeSendHeadersListener,
      filter,
      ["requestHeaders"],
    );

    this.onBeforeRedirectListener = details => {
      // Ignore requests made by extensions
      if (requestStemsFromExtension(details)) {
        return;
      }
      this.onBeforeRedirectHandler(details, crawlID, incrementedEventOrdinal());
    };
    browser.webRequest.onBeforeRedirect.addListener(
      this.onBeforeRedirectListener,
      filter,
      ["responseHeaders"],
    );

    this.onCompletedListener = details => {
      // Ignore requests made by extensions
      if (requestStemsFromExtension(details)) {
        return;
      }
      const pendingResponse = this.getPendingResponse(details.requestId);
      pendingResponse.resolveOnCompletedEventDetails(details);
      this.onCompletedHandler(
        details,
        crawlID,
        incrementedEventOrdinal(),
        saveContentOption,
      );
    };
    browser.webRequest.onCompleted.addListener(
      this.onCompletedListener,
      filter,
      ["responseHeaders"],
    );
  }

  public cleanup() {
    if (this.onBeforeRequestListener) {
      browser.webRequest.onBeforeRequest.removeListener(
        this.onBeforeRequestListener,
      );
    }
    if (this.onBeforeSendHeadersListener) {
      browser.webRequest.onBeforeSendHeaders.removeListener(
        this.onBeforeSendHeadersListener,
      );
    }
    if (this.onBeforeRedirectListener) {
      browser.webRequest.onBeforeRedirect.removeListener(
        this.onBeforeRedirectListener,
      );
    }
    if (this.onCompletedListener) {
      browser.webRequest.onCompleted.removeListener(this.onCompletedListener);
    }
  }

  private isContentSavingEnabled(saveContentOption: SaveContentOption) {
    if (saveContentOption === true) {
      return true;
    }
    if (saveContentOption === false) {
      return false;
    }
    return this.saveContentResourceTypes(saveContentOption).length > 0;
  }

  private saveContentResourceTypes(saveContentOption: string): ResourceType[] {
    return saveContentOption.split(",") as ResourceType[];
  }

  /**
   * We rely on the resource type to filter responses
   * See: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/ResourceType
   *
   * @param saveContentOption
   * @param resourceType
   */
  private shouldSaveContent(
    saveContentOption: SaveContentOption,
    resourceType: ResourceType,
  ) {
    if (saveContentOption === true) {
      return true;
    }
    if (saveContentOption === false) {
      return false;
    }
    return this.saveContentResourceTypes(saveContentOption).includes(
      resourceType,
    );
  }

  private getPendingRequest(requestId): PendingRequest {
    if (!this.pendingRequests[requestId]) {
      this.pendingRequests[requestId] = new PendingRequest();
    }
    return this.pendingRequests[requestId];
  }

  private getPendingResponse(requestId): PendingResponse {
    if (!this.pendingResponses[requestId]) {
      this.pendingResponses[requestId] = new PendingResponse();
    }
    return this.pendingResponses[requestId];
  }

  /*
   * HTTP Request Handler
   */

  private async onBeforeSendHeadersHandler(
    details: WebRequestOnBeforeSendHeadersEventDetails,
    crawlID,
    eventOrdinal: number,
  ) {

    const tab =
      details.tabId > -1
        ? await browser.tabs.get(details.tabId)
        : { windowId: undefined, incognito: undefined, url: undefined };

    const update = {} as HttpRequest;

    update.incognito = boolToInt(tab.incognito);
    update.crawl_id = crawlID;
    update.extension_session_uuid = extensionSessionUuid;
    update.event_ordinal = eventOrdinal;
    update.window_id = tab.windowId;
    update.tab_id = details.tabId;
    update.frame_id = details.frameId;

    // requestId is a monotonically increasing integer that is constant
    // through a redirect chain. It is not unique across page visits.
    update.request_id = details.requestId;

    const url = details.url;
    update.url = escapeUrl(url);

    const requestMethod = details.method;
    update.method = escapeString(requestMethod);

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
        header_pair.push(escapeString(name));
        header_pair.push(escapeString(value));
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

    update.referrer = escapeString(referrer);

    if (requestMethod === "POST" && !isOcsp /* don't process OCSP requests */) {
      const pendingRequest = this.getPendingRequest(details.requestId);
      const resolved = await pendingRequest.resolvedWithinTimeout(1000);
      if (!resolved) {
        this.dataReceiver.logError(
          "Pending request timed out waiting for data from both onBeforeRequest and onBeforeSendHeaders events",
        );
      } else {
        const onBeforeRequestEventDetails = await pendingRequest.onBeforeRequestEventDetails;
        const requestBody = onBeforeRequestEventDetails.requestBody;

        if (requestBody) {
          const postParser = new HttpPostParser(
            onBeforeRequestEventDetails,
            this.dataReceiver,
          );
          const postObj: ParsedPostRequest = postParser.parsePostRequest();

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
                header_pair.push(escapeString(postObj.post_headers[name]));
                headers.push(header_pair);
              }
            }
          }
          // we store POST body in JSON format, except when it's a string without a (key-value) structure
          if ("post_body" in postObj) {
            update.post_body = postObj.post_body;
          }
          if ("post_body_raw" in postObj) {
            update.post_body_raw = postObj.post_body_raw;
          }
        }
      }
    }

    update.headers = JSON.stringify(headers);

    // Check if xhr
    const isXHR = details.type === "xmlhttprequest";
    update.is_XHR = boolToInt(isXHR);

    // Check if frame OR full page load
    const isFullPageLoad = details.frameId === 0;
    const isFrameLoad = details.type === "sub_frame";
    update.is_full_page = boolToInt(isFullPageLoad);
    update.is_frame_load = boolToInt(isFrameLoad);

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
    update.triggering_origin = escapeString(triggeringOrigin);
    update.loading_origin = escapeString(loadingOrigin);

    // loadingDocument's href
    // The loadingDocument is the document the element resides, regardless of
    // how the load was triggered.
    const loadingHref = details.documentUrl;
    update.loading_href = escapeString(loadingHref);

    // resourceType of the requesting node. This is set by the type of
    // node making the request (i.e. an <img src=...> node will set to type "image").
    // Documentation:
    // https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/ResourceType
    update.resource_type = details.type;

    update.top_level_url = escapeUrl(this.getDocumentUrlForRequest(details));
    update.parent_frame_id = details.parentFrameId;
    update.frame_ancestors = escapeString(
      JSON.stringify(details.frameAncestors),
    );
    this.dataReceiver.saveRecord("http_requests", update);
  }

  /**
   * Code taken and adapted from
   * https://github.com/EFForg/privacybadger/pull/2198/files
   *
   * Gets the URL for a given request's top-level document.
   *
   * The request's document may be different from the current top-level document
   * loaded in tab as requests can come out of order:
   *
   * @param {WebRequestOnBeforeSendHeadersEventDetails} details
   *
   * @return {?String} the URL for the request's top-level document
   */
  private getDocumentUrlForRequest(
    details: WebRequestOnBeforeSendHeadersEventDetails,
  ) {
    let url = "";

    if (details.type === "main_frame") {
      // Url of the top-level document itself.
      url = details.url;
    } else if (details.hasOwnProperty("frameAncestors")) {
      // In case of nested frames, retrieve url from top-most ancestor.
      // If frameAncestors == [], request comes from the top-level-document.
      url = details.frameAncestors.length
        ? details.frameAncestors[details.frameAncestors.length - 1].url
        : details.documentUrl;
    } else {
      // type != 'main_frame' and frameAncestors == undefined
      // For example service workers: https://bugzilla.mozilla.org/show_bug.cgi?id=1470537#c13
      url = details.documentUrl;
    }
    return url;
  }

  private async onBeforeRedirectHandler(
    details: WebRequestOnBeforeRedirectEventDetails,
    crawlID,
    eventOrdinal: number,
  ) {
    // Save HTTP redirect events
    // Events are saved to the `http_redirects` table

    const responseStatus = details.statusCode;
    const responseStatusText = details.statusLine;

    const tab =
      details.tabId > -1
        ? await browser.tabs.get(details.tabId)
        : { windowId: undefined, incognito: undefined };
    const httpRedirect: HttpRedirect = {
      incognito: boolToInt(tab.incognito),
      crawl_id: crawlID,
      request_id: details.requestId,
      old_request_url: escapeUrl(details.url),
      new_request_url: escapeUrl(details.redirectUrl),
      extension_session_uuid: extensionSessionUuid,
      event_ordinal: eventOrdinal,
      window_id: tab.windowId,
      tab_id: details.tabId,
      frame_id: details.frameId,
      response_status: responseStatus,
      response_status_text: escapeString(responseStatusText),
      time_stamp: new Date(details.timeStamp).toISOString(),
    };

    this.dataReceiver.saveRecord("http_redirects", httpRedirect);
  }

  /*
   * HTTP Response Handlers and Helper Functions
   */

  private async logWithResponseBody(
    details: WebRequestOnBeforeRequestEventDetails,
    update,
  ) {
    const pendingResponse = this.getPendingResponse(details.requestId);
    try {
      const responseBodyListener = pendingResponse.responseBodyListener;
      const respBody = await responseBodyListener.getResponseBody();
      const contentHash = await responseBodyListener.getContentHash();
      this.dataReceiver.saveContent(respBody, escapeString(contentHash));
      update.content_hash = contentHash;
      this.dataReceiver.saveRecord("http_responses", update);
    } catch (err) {
      this.dataReceiver.logError(
        "Unable to retrieve response body." +
          "Likely caused by a programming error. Error Message:" +
          err.name +
          err.message +
          "\n" +
          err.stack,
      );
      update.content_hash = "<error>";
      this.dataReceiver.saveRecord("http_responses", update);
    }
  }

  // Instrument HTTP responses
  private async onCompletedHandler(
    details: WebRequestOnCompletedEventDetails,
    crawlID,
    eventOrdinal,
    saveContent,
  ) {
    const tab =
      details.tabId > -1
        ? await browser.tabs.get(details.tabId)
        : { windowId: undefined, incognito: undefined };

    const update = {} as HttpResponse;

    update.incognito = boolToInt(tab.incognito);
    update.crawl_id = crawlID;
    update.extension_session_uuid = extensionSessionUuid;
    update.event_ordinal = eventOrdinal;
    update.window_id = tab.windowId;
    update.tab_id = details.tabId;
    update.frame_id = details.frameId;

    // requestId is a monotonically increasing integer that is constant
    // through a redirect chain. It is not unique across page visits.
    update.request_id = details.requestId;

    const isCached = details.fromCache;
    update.is_cached = boolToInt(isCached);

    const url = details.url;
    update.url = escapeUrl(url);

    const requestMethod = details.method;
    update.method = escapeString(requestMethod);

    const responseStatus = details.statusCode;
    update.response_status = responseStatus;

    const responseStatusText = details.statusLine;
    update.response_status_text = escapeString(responseStatusText);

    const current_time = new Date(details.timeStamp);
    update.time_stamp = current_time.toISOString();

    const headers = [];
    let location = "";
    if (details.responseHeaders) {
      details.responseHeaders.map(responseHeader => {
        const { name, value } = responseHeader;
        const header_pair = [];
        header_pair.push(escapeString(name));
        header_pair.push(escapeString(value));
        headers.push(header_pair);
        if (name.toLowerCase() === "location") {
          location = value;
        }
      });
    }
    update.headers = JSON.stringify(headers);
    update.location = escapeString(location);

    if (this.shouldSaveContent(saveContent, details.type)) {
      this.logWithResponseBody(details, update);
    } else {
      this.dataReceiver.saveRecord("http_responses", update);
    }
  }
}
