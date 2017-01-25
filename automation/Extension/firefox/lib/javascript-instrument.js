var pageMod = require("sdk/page-mod");
const data = require("sdk/self").data;
var loggingDB = require("./loggingdb.js");
var pageManager = require("./page-manager.js");

exports.run = function(crawlID, testing) {

  // Set up tables
  var createJavascriptTable = data.load("create_javascript_table.sql");
  loggingDB.executeSQL(createJavascriptTable, false);

  // Inject content script to instrument JavaScript API
  pageMod.PageMod({
    include: "*",
    contentScriptWhen: "start",
    contentScriptFile: data.url("./content.js"),
    contentScriptOptions: {
      'testing': testing
    },
    onAttach: function onAttach(worker) {
      var url = worker.url;
      function processCallsAndValues(data) {
        var update = {};
        update["crawl_id"] = crawlID;
        update["script_url"] = loggingDB.escapeString(data.scriptUrl);
        update["script_line"] = loggingDB.escapeString(data.scriptLine);
        update["script_col"] = loggingDB.escapeString(data.scriptCol);
        update["func_name"] = loggingDB.escapeString(data.funcName);
        update["script_loc_eval"] = loggingDB.escapeString(data.scriptLocEval);
        update["call_stack"] = loggingDB.escapeString(data.callStack);
        update["symbol"] = loggingDB.escapeString(data.symbol);
        update["operation"] = loggingDB.escapeString(data.operation);
        update["value"] = loggingDB.escapeString(data.value);
        update["time_stamp"] = data.timeStamp;

        // Create a json object for function arguments
        // We create an object that maps array positon to argument
        // e.g. someFunc('a',123,'b') --> {0: a, 1: 123, 2: 'b'}
        // to make it easier to query the data, using something like the
        // sqlite3 json1 extension.
        var args = {};
        if (data.operation == 'call' && data.args.length > 0) {
          for(var i = 0; i < data.args.length; i++) {
            args[i] = data.args[i]
          }
          update["arguments"] = loggingDB.escapeString(JSON.stringify(args));
        }

        loggingDB.executeSQL(loggingDB.createInsert("javascript", update), true);
      }
      worker.port.on("logCall", function(data){processCallsAndValues(data)});
      worker.port.on("logValue", function(data){processCallsAndValues(data)});
    }
  });
};
