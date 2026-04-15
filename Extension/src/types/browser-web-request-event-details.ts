/* eslint-disable no-underscore-dangle */

export interface FrameAncestor {
  /** The URL that the document was loaded from. */
  url: string;
  /** The frameId of the document. details.frameAncestors[0].frameId is the same as details.parentFrameId. */
  frameId: number;
}

export interface WebRequestOnBeforeSendHeadersEventDetails
  extends browser.webRequest._OnBeforeSendHeadersDetails {
  /** Contains information for each document in the frame hierarchy up to the top-level document. The first element in the array contains information about the immediate parent of the document being requested, and the last element contains information about the top-level document. If the load is actually for the top-level document, then this array is empty. */
  frameAncestors: FrameAncestor[];
}

export interface WebRequestOnHeadersReceivedDetails
  extends browser.webRequest._OnHeadersReceivedDetails {
  /**
   * The server IP address that the request was actually sent to.
   * Present in Firefox's onHeadersReceived per MDN but not in @types/firefox-webext-browser.
   * May be undefined if the IP has not yet been resolved (e.g. cached responses);
   * undefined maps to NULL in dns_responses.used_address, which is valid signal.
   */
  ip?: string;
}

export type WebRequestOnErrorOccurredDetails =
  browser.webRequest._OnErrorOccurredDetails;
