/**
 * This file contains selected implicit interfaces copied from node_modules/@types/firefox-webext-browser/index.d.ts
 * Defined and exported here in order for our code to be able to reference them explicitly in helper functions
 * and class methods that accept arguments of these types.
 */

import ResourceType = browser.webRequest.ResourceType;
import UploadData = browser.webRequest.UploadData;
import HttpHeaders = browser.webRequest.HttpHeaders;

export interface FrameAncestor {
  /** The URL that the document was loaded from. */
  url: string;
  /** The frameId of the document. details.frameAncestors[0].frameId is the same as details.parentFrameId. */
  frameId: number;
  0;
}

export interface WebRequestOnBeforeSendHeadersEventDetails {
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
  /** Contains information for each document in the frame hierarchy up to the top-level document. The first element in the array contains information about the immediate parent of the document being requested, and the last element contains information about the top-level document. If the load is actually for the top-level document, then this array is empty. */
  frameAncestors: FrameAncestor[];
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
}

export interface WebRequestOnBeforeRequestEventDetails {
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
}

export interface WebRequestOnBeforeRedirectEventDetails {
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
}

export interface WebRequestOnCompletedEventDetails {
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
}
