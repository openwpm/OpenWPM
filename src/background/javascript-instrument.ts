interface Update {
  crawl_id?: string;
  script_url?: string;
  script_line?: string;
  script_col?: string;
  func_name?: string;
  script_loc_eval?: string;
  call_stack?: string;
  symbol?: string;
  operation?: string;
  value?: string;
  time_stamp?: string;
  document_url?: string;
  top_level_url?: string;
  arguments?: string;
}

export class JavascriptInstrument {
  private readonly loggingDB;

  constructor(loggingDB) {
    this.loggingDB = loggingDB;
  }

  public run(crawlID) {
    const self = this;
    console.log("JavascriptInstrument", crawlID, self.loggingDB);

    function processCallsAndValues(data, sender) {
      const update: Update = {};
      update.crawl_id = crawlID;
      update.script_url = self.loggingDB.escapeString(data.scriptUrl);
      update.script_line = self.loggingDB.escapeString(data.scriptLine);
      update.script_col = self.loggingDB.escapeString(data.scriptCol);
      update.func_name = self.loggingDB.escapeString(data.funcName);
      update.script_loc_eval = self.loggingDB.escapeString(data.scriptLocEval);
      update.call_stack = self.loggingDB.escapeString(data.callStack);
      update.symbol = self.loggingDB.escapeString(data.symbol);
      update.operation = self.loggingDB.escapeString(data.operation);
      update.value = self.loggingDB.escapeString(data.value);
      update.time_stamp = data.timeStamp;

      // document_url is the current frame's document href
      // top_level_url is the top-level frame's document href
      update.document_url = self.loggingDB.escapeString(sender.url);
      update.top_level_url = self.loggingDB.escapeString(sender.tab.url);

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
        update.arguments = self.loggingDB.escapeString(JSON.stringify(args));
      }

      self.loggingDB.saveRecord("javascript", update);
    }

    // Listen for messages from content script injected to instrument JavaScript API
    browser.runtime.onMessage.addListener(function(msg, sender) {
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
