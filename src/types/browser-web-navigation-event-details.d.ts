/**
 * This file contains selected implicit interfaces copied from node_modules/@types/firefox-webext-browser/index.d.ts
 * Defined and exported here in order for our code to be able to reference them explicitly in helper functions
 * and class methods that accept arguments of these types.
 */

import TransitionType = browser.webNavigation.TransitionType;
import TransitionQualifier = browser.webNavigation.TransitionQualifier;

export interface WebNavigationOnCommittedEventDetails {
  /** The ID of the tab in which the navigation occurs. */
  tabId: number;
  url: string;
  /**
   * The ID of the process runs the renderer for this tab.
   * @deprecated Unsupported on Firefox at this time.
   */
  processId?: number;
  /**
   * 0 indicates the navigation happens in the tab content window; a positive value indicates navigation in a
   * subframe. Frame IDs are unique within a tab.
   */
  frameId: number;
  /**
   * Cause of the navigation.
   * @deprecated Unsupported on Firefox at this time.
   */
  transitionType?: TransitionType;
  /**
   * A list of transition qualifiers.
   * @deprecated Unsupported on Firefox at this time.
   */
  transitionQualifiers?: TransitionQualifier[];
  /** The time when the navigation was committed, in milliseconds since the epoch. */
  timeStamp: number;
}

export interface WebNavigationOnDOMContentLoadedEventDetails {
  /** The ID of the tab in which the navigation occurs. */
  tabId: number;
  url: string;
  /**
   * The ID of the process runs the renderer for this tab.
   * @deprecated Unsupported on Firefox at this time.
   */
  processId?: number;
  /**
   * 0 indicates the navigation happens in the tab content window; a positive value indicates navigation in a
   * subframe. Frame IDs are unique within a tab.
   */
  frameId: number;
  /** The time when the page's DOM was fully constructed, in milliseconds since the epoch. */
  timeStamp: number;
}

export interface WebNavigationOnCompletedEventDetails {
  /** The ID of the tab in which the navigation occurs. */
  tabId: number;
  url: string;
  /**
   * The ID of the process runs the renderer for this tab.
   * @deprecated Unsupported on Firefox at this time.
   */
  processId?: number;
  /**
   * 0 indicates the navigation happens in the tab content window; a positive value indicates navigation in a
   * subframe. Frame IDs are unique within a tab.
   */
  frameId: number;
  /** The time when the document finished loading, in milliseconds since the epoch. */
  timeStamp: number;
}

export interface WebNavigationOnErrorOccurredEventDetails {
  /** The ID of the tab in which the navigation occurs. */
  tabId: number;
  url: string;
  /**
   * The ID of the process runs the renderer for this tab.
   * @deprecated Unsupported on Firefox at this time.
   */
  processId?: number;
  /**
   * 0 indicates the navigation happens in the tab content window; a positive value indicates navigation in a
   * subframe. Frame IDs are unique within a tab.
   */
  frameId: number;
  /**
   * The error description.
   * @deprecated Unsupported on Firefox at this time.
   */
  error?: string;
  /** The time when the error occurred, in milliseconds since the epoch. */
  timeStamp: number;
}
