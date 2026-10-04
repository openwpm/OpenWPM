import MessageSender = browser.runtime.MessageSender;
import { DataReceiver } from "../lib/data-receiver";
import { incrementedEventOrdinal } from "../lib/extension-session-event-ordinal";
import { extensionSessionUuid } from "../lib/extension-session-uuid";
import { boolToInt, escapeString, escapeUrl } from "../lib/string-utils";
import { JavascriptOperation } from "../schema";
import {
  JSInstrumentRequest,
  JSLogMessageContent,
} from "../lib/js-instruments";

/**
 * Message forwarded from the content script to the background page for each
 * instrumented call/value observation. The content script stamps `timeStamp`
 * before forwarding, so it is always present here.
 */
interface JsInstrumentationMessage {
  namespace?: string;
  type?: string;
  data: JSLogMessageContent & { timeStamp: string };
}

/**
 * Where a record came from.
 *
 * Legacy instrumentation delivers records over `runtime.sendMessage`, so the
 * sender is a real `MessageSender`. The stealth instrument runs in a privileged
 * actor with no extension messaging available, so `stealthInstrument.onRecord`
 * reconstructs the same few fields in the parent process from the record's
 * browsing context (see `privileged/stealthInstrument/api.js`, `resolveSender`).
 * Only these fields were ever read.
 */
type RecordSender = Pick<MessageSender, "tab" | "frameId" | "url">;

/** One record as delivered by the privileged stealth actor. */
interface StealthRecord {
  type: string;
  data: JSLogMessageContent & { timeStamp: string };
  sender: RecordSender;
}

export class JavascriptInstrument {
  /**
   * Converts received call and values data from the JS Instrumentation
   * into the format that the schema expects.
   *
   * @param data
   * @param sender
   */
  private static processCallsAndValues(
    data: JSLogMessageContent & { timeStamp: string },
    sender: RecordSender,
  ) {
    const tab = sender.tab;
    const update = {} as JavascriptOperation;
    update.extension_session_uuid = extensionSessionUuid;
    update.event_ordinal = incrementedEventOrdinal();
    update.page_scoped_event_ordinal = data.ordinal;
    update.window_id = tab?.windowId;
    update.tab_id = tab?.id;
    update.frame_id = sender.frameId;
    update.script_url = escapeUrl(data.scriptUrl);
    update.script_line = escapeString(data.scriptLine);
    update.script_col = escapeString(data.scriptCol);
    update.func_name = escapeString(data.funcName);
    update.script_loc_eval = escapeString(data.scriptLocEval);
    update.call_stack = escapeString(data.callStack);
    update.symbol = escapeString(data.symbol);
    // Concrete receiver interface for interface-attributed shared-prototype
    // capture (stealth). Null/absent for ordinary instrumentation and for value
    // gets/sets, in which case the ``receiver`` column stays NULL.
    if (data.receiver !== undefined && data.receiver !== null) {
      update.receiver = escapeString(data.receiver);
    }
    update.operation = escapeString(data.operation);
    update.value = escapeString(data.value);
    update.time_stamp = data.timeStamp;
    update.incognito = boolToInt(tab?.incognito ?? false);

    // document_url is the current frame's document href
    // top_level_url is the top-level frame's document href
    update.document_url = escapeUrl(sender.url);
    update.top_level_url = escapeUrl(tab?.url);

    if (data.operation === "call" && data.args && data.args.length > 0) {
      update.arguments = escapeString(JSON.stringify(data.args));
    }

    return update;
  }
  private readonly dataReceiver: DataReceiver;
  private onMessageListener?: (
    message: JsInstrumentationMessage,
    sender: MessageSender,
  ) => void;
  private configured: boolean = false;
  private legacy: boolean = true;
  private pendingRecords: JavascriptOperation[] = [];
  private crawlID?: number;
  private stealthRecordListener?: (record: StealthRecord) => void;

  constructor(dataReceiver: DataReceiver, legacy: boolean = true) {
    this.dataReceiver = dataReceiver;
    this.legacy = legacy;
  }

  /**
   * Start listening for messages from page/content/background scripts injected to instrument JavaScript APIs
   */
  public listen() {
    this.onMessageListener = (
      message: JsInstrumentationMessage,
      sender: MessageSender,
    ) => {
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
   *
   * @param message
   * @param sender
   */
  public handleJsInstrumentationMessage(
    message: JsInstrumentationMessage,
    sender: RecordSender,
  ) {
    switch (message.type) {
      case "logCall":
      case "logValue": {
        const update = JavascriptInstrument.processCallsAndValues(
          message.data,
          sender,
        );
        if (this.configured) {
          update.browser_id = this.crawlID;
          this.dataReceiver.saveRecord("javascript", update);
        } else {
          this.pendingRecords.push(update);
        }
        break;
      }
    }
  }

  /**
   * Starts listening if haven't done so already, sets the crawl ID,
   * marks the JS instrumentation as configured and sends any pending
   * records that have been received up until this point.
   *
   * @param crawlID
   */
  public run(crawlID: number) {
    if (!this.onMessageListener) {
      this.listen();
    }
    this.crawlID = crawlID;
    this.configured = true;
    this.pendingRecords.map((update) => {
      update.browser_id = this.crawlID;
      this.dataReceiver.saveRecord("javascript", update);
    });
  }

  /**
   * Starts collection: legacy registers content scripts, stealth enables the
   * privileged actor, which also reaches realms no content script runs in.
   */
  public async register(
    testing?: boolean,
    jsInstrumentationSettings?: JSInstrumentRequest[],
  ) {
    if (!this.legacy) {
      this.stealthRecordListener = (record: StealthRecord) => {
        this.handleJsInstrumentationMessage(
          { namespace: "javascript-instrumentation", ...record },
          record.sender,
        );
      };
      browser.stealthInstrument.onRecord.addListener(
        this.stealthRecordListener,
      );
      // Rejects if the actor could not be set up, which fails the browser's
      // start like a rejected content-script registration.
      try {
        await browser.stealthInstrument.enable(jsInstrumentationSettings);
      } catch (error) {
        this.dataReceiver.logError("Stealth instrument actor: " + error);
        throw error;
      }
      return;
    }

    const contentScriptConfig = {
      testing,
      jsInstrumentationSettings,
    };
    // TODO: Avoid using window to pass the content script config
    await browser.contentScripts.register({
      js: [
        {
          code: `window.openWpmContentScriptConfig = ${JSON.stringify(
            contentScriptConfig,
          )};`,
        },
      ],
      matches: ["<all_urls>"],
      allFrames: true,
      runAt: "document_start",
      matchAboutBlank: true,
    });
    return browser.contentScripts.register({
      js: [{ file: "/content.js" }],
      matches: ["<all_urls>"],
      allFrames: true,
      runAt: "document_start",
      matchAboutBlank: true,
    });
  }

  public cleanup() {
    this.pendingRecords = [];
    if (this.onMessageListener) {
      browser.runtime.onMessage.removeListener(this.onMessageListener);
    }
    if (this.stealthRecordListener) {
      browser.stealthInstrument.onRecord.removeListener(
        this.stealthRecordListener,
      );
    }
  }
}
