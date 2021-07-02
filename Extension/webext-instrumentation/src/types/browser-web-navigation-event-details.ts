/**
 * This file contains selected implicit interfaces copied from node_modules/@types/firefox-webext-browser/index.d.ts
 * Defined and exported here in order for our code to be able to reference them explicitly in helper functions
 * and class methods that accept arguments of these types.
 */

import TransitionType = browser.webNavigation.TransitionType;
import TransitionQualifier = browser.webNavigation.TransitionQualifier;

export interface WebNavigationBaseEventDetails {
  /** The ID of the tab in which the navigation is about to occur. */
  tabId: number;
  url: string;
  /**
   * The ID of the process runs the renderer for this tab.
   *
   * @deprecated Unsupported on Firefox at this time.
   */
  processId?: number;
  /**
   * 0 indicates the navigation happens in the tab content window; a positive value indicates navigation in a
   * subframe. Frame IDs are unique for a given tab and process.
   */
  frameId: number;
  /** The time when the page's DOM was fully constructed, in milliseconds since the epoch. */
  timeStamp: number;
}

export interface WebNavigationOnBeforeNavigateEventDetails
  extends WebNavigationBaseEventDetails {
  /** ID of frame that wraps the frame. Set to -1 of no parent frame exists. */
  parentFrameId: number;
}

export interface WebNavigationOnCommittedEventDetails
  extends WebNavigationBaseEventDetails {
  /**
   * Cause of the navigation.
   *
   * @deprecated Unsupported on Firefox at this time.
   */
  transitionType?: TransitionType;
  /**
   * A list of transition qualifiers.
   *
   * @deprecated Unsupported on Firefox at this time.
   */
  transitionQualifiers?: TransitionQualifier[];
}

/*
export interface WebNavigationOnDOMContentLoadedEventDetails
  extends WebNavigationBaseEventDetails {}

export interface WebNavigationOnCompletedEventDetails
  extends WebNavigationBaseEventDetails {}
*/

export interface WebNavigationOnErrorOccurredEventDetails
  extends WebNavigationBaseEventDetails {
  /**
   * The error description.
   *
   * @deprecated Unsupported on Firefox at this time.
   */
  error?: string;
}
