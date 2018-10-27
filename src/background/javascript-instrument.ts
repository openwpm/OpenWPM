import { escapeString } from "../lib/string-utils";
import { JavascriptOperation } from "../types/schema";

export class JavascriptInstrument {
  private readonly dataReceiver;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID) {
    const processCallsAndValues = (data, sender) => {
      const update = {} as JavascriptOperation;
      update.crawl_id = crawlID;
      update.script_url = escapeString(data.scriptUrl);
      update.script_line = escapeString(data.scriptLine);
      update.script_col = escapeString(data.scriptCol);
      update.func_name = escapeString(data.funcName);
      update.script_loc_eval = escapeString(data.scriptLocEval);
      update.call_stack = escapeString(data.callStack);
      update.symbol = escapeString(data.symbol);
      update.operation = escapeString(data.operation);
      update.value = escapeString(data.value);
      update.time_stamp = data.timeStamp;

      // document_url is the current frame's document href
      // top_level_url is the top-level frame's document href
      update.document_url = escapeString(sender.url);
      update.top_level_url = escapeString(sender.tab.url);

      // Create a json object for function arguments
      // We create an object that maps array positon to argument
      // e.g. someFunc('a',123,'b') --> {0: a, 1: 123, 2: 'b'}
      // to make it easier to query the data, using something like the
      // sqlite3 json1 extension.
      const args = {};
      if (data.operation === "call" && data.args.length > 0) {
        for (let i = 0; i < data.args.length; i++) {
          args[i] = data.args[i];
        }
        update.arguments = escapeString(JSON.stringify(args));
      }

      this.dataReceiver.saveRecord("javascript", update);
    };

    // Listen for messages from content script injected to instrument JavaScript API
    browser.runtime.onMessage.addListener((msg, sender) => {
      // console.debug("javascript-instrumentation background listener - msg, sender, sendReply", msg, sender, sendReply);
      if (msg.namespace && msg.namespace === "javascript-instrumentation") {
        switch (msg.type) {
          case "logCall":
          case "logValue":
            processCallsAndValues(msg.data, sender);
            break;
        }
      }
    });
  }
}
