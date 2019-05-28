import MessageSender = browser.runtime.MessageSender;
import { incrementedEventOrdinal } from "../lib/extension-session-event-ordinal";
import { extensionSessionUuid } from "../lib/extension-session-uuid";
import { boolToInt, escapeString, escapeUrl } from "../lib/string-utils";
import { JavascriptOperation } from "../schema";

export class JavascriptInstrument {
  /**
   * Converts received call and values data from the JS Instrumentation
   * into the format that the schema expects.
   * @param data
   * @param sender
   */
  private static processCallsAndValues(data, sender: MessageSender) {
    const update = {} as JavascriptOperation;
    update.extension_session_uuid = extensionSessionUuid;
    update.event_ordinal = incrementedEventOrdinal();
    update.page_scoped_event_ordinal = data.ordinal;
    update.window_id = sender.tab.windowId;
    update.tab_id = sender.tab.id;
    update.frame_id = sender.frameId;
    update.script_url = escapeUrl(data.scriptUrl);
    update.script_line = escapeString(data.scriptLine);
    update.script_col = escapeString(data.scriptCol);
    update.func_name = escapeString(data.funcName);
    update.script_loc_eval = escapeString(data.scriptLocEval);
    update.call_stack = escapeString(data.callStack);
    update.symbol = escapeString(data.symbol);
    update.operation = escapeString(data.operation);
    update.value = escapeString(data.value);
    update.time_stamp = data.timeStamp;
    update.incognito = boolToInt(sender.tab.incognito);

    // document_url is the current frame's document href
    // top_level_url is the top-level frame's document href
    update.document_url = escapeUrl(sender.url);
    update.top_level_url = escapeUrl(sender.tab.url);

    if (data.operation === "call" && data.args.length > 0) {
      update.arguments = escapeString(JSON.stringify(data.args));
    }

    return update;
  }
  private readonly dataReceiver;
  private onMessageListener;
  private configured: boolean = false;
  private pendingRecords: JavascriptOperation[] = [];
  private crawlID;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  /**
   * Start listening for messages from page/content/background scripts injected to instrument JavaScript APIs
   */
  public listen() {
    this.onMessageListener = (message, sender) => {
      // console.debug("javascript-instrumentation background listener", {message, sender}, this.configured);
      if (
        message.namespace &&
        message.namespace === "javascript-instrumentation"
      ) {
        this.handleJsInstrumentationMessage(message, sender);
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
  public handleJsInstrumentationMessage(message, sender: MessageSender) {
    switch (message.type) {
      case "logCall":
      case "logValue":
        const update = JavascriptInstrument.processCallsAndValues(
          message.data,
          sender,
        );
        if (this.configured) {
          update.crawl_id = this.crawlID;
          this.dataReceiver.saveRecord("javascript", update);
        } else {
          this.pendingRecords.push(update);
        }
        break;
    }
  }

  /**
   * Starts listening if haven't done so already, sets the crawl ID,
   * marks the JS instrumentation as configured and sends any pending
   * records that have been received up until this point.
   * @param crawlID
   */
  public run(crawlID) {
    if (!this.onMessageListener) {
      this.listen();
    }
    this.crawlID = crawlID;
    this.configured = true;
    this.pendingRecords.map(update => {
      update.crawl_id = this.crawlID;
      this.dataReceiver.saveRecord("javascript", update);
    });
  }

  public cleanup() {
    this.pendingRecords = [];
    if (this.onMessageListener) {
      browser.runtime.onMessage.removeListener(this.onMessageListener);
    }
  }
}
