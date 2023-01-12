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

export interface WebRequestOnHeadersReceivedDetails extends browser.webRequest._OnHeadersReceivedDetails {
  /**
   * TODO: Does this actually exist?
   * The server IP address that the request was actually sent to. Note that it may be a literal IPv6 address.
   */
   ip?: string;
}
