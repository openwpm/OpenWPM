import { incrementedEventOrdinal } from "../lib/extension-session-event-ordinal";
import { extensionSessionUuid } from "../lib/extension-session-uuid";
import { PendingNavigation } from "../lib/pending-navigation";
import { boolToInt, escapeString, escapeUrl } from "../lib/string-utils";
import { makeUUID } from "../lib/uuid";
import { Navigation } from "../schema";
import {
  WebNavigationBaseEventDetails,
  WebNavigationOnBeforeNavigateEventDetails,
  WebNavigationOnCommittedEventDetails,
} from "../types/browser-web-navigation-event-details";

export const transformWebNavigationBaseEventDetailsToOpenWPMSchema = async (
  crawlID,
  details: WebNavigationBaseEventDetails,
): Promise<Navigation> => {
  const tab =
    details.tabId > -1
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
  const navigation: Navigation = {
    browser_id: crawlID,
    incognito: boolToInt(tab.incognito),
    extension_session_uuid: extensionSessionUuid,
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
    tab_cookie_store_id: escapeString(tab.cookieStoreId),
    uuid: makeUUID(),
    url: escapeUrl(details.url),
  };
  return navigation;
};

export class NavigationInstrument {
  public static navigationId(processId, tabId, frameId): string {
    return `${processId}-${tabId}-${frameId}`;
  }
  private readonly dataReceiver;
  private onBeforeNavigateListener;
  private onCommittedListener;
  private pendingNavigations: {
    [navigationId: string]: PendingNavigation;
  } = {};

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID) {
    this.onBeforeNavigateListener = async (
      details: WebNavigationOnBeforeNavigateEventDetails,
    ) => {
      const navigationId = NavigationInstrument.navigationId(
        details.processId,
        details.tabId,
        details.frameId,
      );
      const pendingNavigation = this.instantiatePendingNavigation(navigationId);
      const navigation: Navigation =
        await transformWebNavigationBaseEventDetailsToOpenWPMSchema(
          crawlID,
          details,
        );
      navigation.parent_frame_id = details.parentFrameId;
      navigation.before_navigate_event_ordinal = incrementedEventOrdinal();
      navigation.before_navigate_time_stamp = new Date(
        details.timeStamp,
      ).toISOString();
      pendingNavigation.resolveOnBeforeNavigateEventNavigation(navigation);
    };
    browser.webNavigation.onBeforeNavigate.addListener(
      this.onBeforeNavigateListener,
    );
    this.onCommittedListener = async (
      details: WebNavigationOnCommittedEventDetails,
    ) => {
      const navigationId = NavigationInstrument.navigationId(
        details.processId,
        details.tabId,
        details.frameId,
      );
      const navigation: Navigation =
        await transformWebNavigationBaseEventDetailsToOpenWPMSchema(
          crawlID,
          details,
        );
      navigation.transition_qualifiers = escapeString(
        JSON.stringify(details.transitionQualifiers),
      );
      navigation.transition_type = escapeString(details.transitionType);
      navigation.committed_event_ordinal = incrementedEventOrdinal();
      navigation.committed_time_stamp = new Date(
        details.timeStamp,
      ).toISOString();

      // include attributes from the corresponding onBeforeNavigation event
      const pendingNavigation = this.getPendingNavigation(navigationId);
      if (pendingNavigation) {
        pendingNavigation.resolveOnCommittedEventNavigation(navigation);
        const resolved = await pendingNavigation.resolvedWithinTimeout(1000);
        if (resolved) {
          const onBeforeNavigateEventNavigation =
            await pendingNavigation.onBeforeNavigateEventNavigation;
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

  public cleanup() {
    if (this.onBeforeNavigateListener) {
      browser.webNavigation.onBeforeNavigate.removeListener(
        this.onBeforeNavigateListener,
      );
    }
    if (this.onCommittedListener) {
      browser.webNavigation.onCommitted.removeListener(
        this.onCommittedListener,
      );
    }
  }

  private instantiatePendingNavigation(
    navigationId: string,
  ): PendingNavigation {
    this.pendingNavigations[navigationId] = new PendingNavigation();
    return this.pendingNavigations[navigationId];
  }

  private getPendingNavigation(navigationId: string): PendingNavigation {
    return this.pendingNavigations[navigationId];
  }
}
