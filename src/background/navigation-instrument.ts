import { extensionSessionUuid } from "../lib/extension-session-uuid";
import {boolToInt, escapeString} from "../lib/string-utils";
import { makeUUID } from "../lib/uuid";
import { Navigation } from "../schema";
import { WebNavigationOnCommittedEventDetails } from "../types/browser-web-navigation-event-details";
export class NavigationInstrument {
  private readonly dataReceiver;
  private onCommittedListener;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID) {
    this.onCommittedListener = async (
      details: WebNavigationOnCommittedEventDetails,
    ) => {
      const tab =
        details.tabId > -1
          ? await browser.tabs.get(details.tabId)
          : {
              windowId: undefined,
              incognito: undefined,
              cookieStoreId: undefined,
              openerTabId: undefined,
            };
      // const window = browser.windows.get(tab.windowId);
      const navigation: Navigation = {
        crawl_id: crawlID,
        incognito: boolToInt(tab.incognito),
        extension_session_uuid: extensionSessionUuid,
        process_id: details.processId,
        window_id: tab.windowId,
        tab_id: details.tabId,
        tab_opener_tab_id: tab.openerTabId,
        frame_id: details.frameId,
        parent_frame_id: (details as any).parent_frame_id, // An undocumented property
        tab_cookie_store_id: escapeString(tab.cookieStoreId),
        uuid: makeUUID(),
        url: escapeString(details.url),
        transition_qualifiers: escapeString(
          JSON.stringify(details.transitionQualifiers),
        ),
        transition_type: escapeString(details.transitionType),
        committed_time_stamp: new Date(details.timeStamp).toISOString(),
      };
      this.dataReceiver.saveRecord("navigations", navigation);
    };
    browser.webNavigation.onCommitted.addListener(this.onCommittedListener);
  }

  public cleanup() {
    if (this.onCommittedListener) {
      browser.webNavigation.onCommitted.removeListener(
        this.onCommittedListener,
      );
    }
  }
}
