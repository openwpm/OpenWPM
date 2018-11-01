import { escapeString } from "../lib/string-utils";
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
      const tab = await browser.tabs.get(details.tabId);
      // const window = browser.windows.get(tab.windowId);
      const navigation: Navigation = {
        crawl_id: crawlID,
        process_id: details.processId,
        window_id: tab.windowId,
        tab_id: details.tabId,
        frame_id: details.frameId,
        parent_frame_id: (details as any).parent_frame_id, // An undocumented property
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
