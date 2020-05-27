import MessageSender = browser.runtime.MessageSender;
import { UiInstrumentMetadata, UiInstrumentTimeStampedMessage } from "..";
import {
  OpenWPMUiInteractionData,
  OpenWPMUiStateData,
} from "../content/ui-instrument-page-scope";
import { incrementedEventOrdinal } from "../lib/extension-session-event-ordinal";
import { extensionSessionUuid } from "../lib/extension-session-uuid";
import { boolToInt, escapeString, escapeUrl } from "../lib/string-utils";
import { UiInteraction, UiState } from "../schema";

export class UiInstrument {
  /**
   * Converts received call and values data from the UI Instrumentation
   * into the format that the schema expects.
   * @param data
   * @param sender
   */
  private static processMetadata(
    data: (OpenWPMUiInteractionData | OpenWPMUiStateData) &
      UiInstrumentTimeStampedMessage,
    sender: MessageSender,
  ): UiInstrumentMetadata {
    const update = {} as UiInstrumentMetadata;
    update.extension_session_uuid = extensionSessionUuid;
    update.event_ordinal = incrementedEventOrdinal();
    update.page_scoped_event_ordinal = data.ordinal;
    update.window_id = sender.tab.windowId;
    update.tab_id = sender.tab.id;
    update.frame_id = sender.frameId;
    update.time_stamp = data.timeStamp;
    update.incognito = boolToInt(sender.tab.incognito);

    // document_url is the current frame's document href
    update.document_url = escapeUrl(sender.url);
    // top_level_url is the tab's document href (requires tabs permission in manifest)
    update.top_level_url = escapeUrl(sender.tab.url);

    return update;
  }
  private static processUiClickEvents(
    data: OpenWPMUiInteractionData & UiInstrumentTimeStampedMessage,
    sender: MessageSender,
  ): UiInteraction {
    return {
      ...this.processMetadata(data, sender),
      type: "click",
      target: escapeString(JSON.stringify(data.target)),
      composed_path: escapeString(JSON.stringify(data.composedPath)),
    };
  }
  private static processUiStateEvents(
    data: OpenWPMUiStateData & UiInstrumentTimeStampedMessage,
    sender: MessageSender,
  ): UiState {
    return {
      ...this.processMetadata(data, sender),
      document_hidden: boolToInt(data.documentHidden),
      audio_element_is_playing: boolToInt(data.audioElementIsPlaying),
      video_element_is_playing: boolToInt(data.videoElementIsPlaying),
      interval_ms: data.intervalMs,
    };
  }
  private readonly dataReceiver;
  private onMessageListener;
  private configured: boolean = false;
  private pendingUiInteractionRecords: UiInteraction[] = [];
  private pendingUiStateRecords: UiState[] = [];
  private crawlID;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  /**
   * Start listening for messages from page/content/background scripts injected to instrument the ui
   */
  public listen() {
    this.onMessageListener = (message, sender) => {
      // console.debug("ui-instrument background listener", {message, sender}, this.configured);
      if (message.namespace && message.namespace === "ui-instrument") {
        this.handleUiInstrumentationMessage(message, sender);
      }
    };
    browser.runtime.onMessage.addListener(this.onMessageListener);
  }

  /**
   * Either sends the log data to the dataReceiver or store it in memory
   * as a pending record if the JS instrumentation is not yet configured
   * @param message
   * @param sender
   */
  public handleUiInstrumentationMessage(message, sender: MessageSender) {
    switch (message.type) {
      case "click":
        const UiInteractionUpdate = UiInstrument.processUiClickEvents(
          message.data,
          sender,
        );
        if (this.configured) {
          UiInteractionUpdate.crawl_id = this.crawlID;
          this.dataReceiver.saveRecord("ui_interactions", UiInteractionUpdate);
        } else {
          this.pendingUiInteractionRecords.push(UiInteractionUpdate);
        }
        break;
      case "state":
        const UiStateUpdate = UiInstrument.processUiStateEvents(
          message.data,
          sender,
        );
        if (this.configured) {
          UiStateUpdate.crawl_id = this.crawlID;
          this.dataReceiver.saveRecord("ui_states", UiStateUpdate);
        } else {
          this.pendingUiStateRecords.push(UiStateUpdate);
        }
        break;
      default:
        console.error("Unexpected ui instrument type in message", { message });
        return;
    }
  }

  /**
   * Starts listening if haven't done so already, sets the crawl ID,
   * marks the user interaction instrumentation as configured and sends any pending
   * records that have been received up until this point.
   * @param crawlID
   */
  public run(crawlID) {
    if (!this.onMessageListener) {
      this.listen();
    }
    this.crawlID = crawlID;
    this.configured = true;
    this.pendingUiInteractionRecords.map(update => {
      update.crawl_id = this.crawlID;
      this.dataReceiver.saveRecord("ui_interactions", update);
    });
    this.pendingUiStateRecords.map(update => {
      update.crawl_id = this.crawlID;
      this.dataReceiver.saveRecord("ui_states", update);
    });
  }

  public async registerContentScript(
    contentScriptConfig: {
      testing: boolean;
      clicks?: string;
      state?: string;
      state_interval_ms?: string;
    },
    registerContentScriptOptions = {},
  ) {
    if (contentScriptConfig) {
      // TODO: Avoid using window to pass the content script config
      await browser.contentScripts.register({
        js: [
          {
            code: `window.openWpmUiInstrumentContentScriptConfig = ${JSON.stringify(
              contentScriptConfig,
            )};`,
          },
        ],
        matches: ["<all_urls>"],
        allFrames: true,
        runAt: "document_start",
        matchAboutBlank: true,
        ...registerContentScriptOptions,
      });
    }
    return browser.contentScripts.register({
      js: [{ file: "/ui-instrument-content-script.js" }],
      matches: ["<all_urls>"],
      allFrames: true,
      runAt: "document_start",
      matchAboutBlank: true,
      ...registerContentScriptOptions,
    });
  }

  public cleanup() {
    this.pendingUiInteractionRecords = [];
    this.pendingUiStateRecords = [];
    if (this.onMessageListener) {
      browser.runtime.onMessage.removeListener(this.onMessageListener);
    }
  }
}
