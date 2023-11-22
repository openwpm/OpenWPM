/* eslint-disable no-underscore-dangle */

/**
 * This file contains selected implicit interfaces copied from node_modules/@types/firefox-webext-browser/index.d.ts
 * Defined and exported here in order for our code to be able to reference them explicitly in helper functions
 * and class methods that accept arguments of these types.
 */

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
