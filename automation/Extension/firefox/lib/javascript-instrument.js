var pageMod = require("sdk/page-mod");
const data = require("sdk/self").data;
var loggingDB = require("./loggingdb.js");
var pageManager = require("./page-manager.js");

exports.run = function(crawlID) {

    // Set up tables
    var createJavascriptTable = data.load("create_javascript_table.sql");
    loggingDB.executeSQL(createJavascriptTable, false);

    // Inject content script to instrument JavaScript API
    pageMod.PageMod({
        include: "*",
        contentScriptWhen: "start",
        contentScriptFile: data.url("./content.js"),
        onAttach: function onAttach(worker) {
            var url = worker.url;
            function processCallsAndValues(data) {
                var update = {};
                update["crawl_id"] = crawlID;
                update["script_url"] = loggingDB.escapeString(data.scriptUrl);
                update["script_line"] = loggingDB.escapeString(data.scriptLine);
                update["script_col"] = loggingDB.escapeString(data.scriptCol);
                update["call_stack"] = loggingDB.escapeString(data.callStack);
                update["symbol"] = loggingDB.escapeString(data.symbol);
                update["operation"] = loggingDB.escapeString(data.operation);
                update["value"] = loggingDB.escapeString(data.value);

                if (data.operation == 'call' && data.args.length > 0) {
                    for(var i = 0; i < data.args.length; i++) {
                        update["parameter_index"] = i;
                        update["parameter_value"] = loggingDB.escapeString(data.args[i]);
                        loggingDB.executeSQL(loggingDB.createInsert("javascript", update), true);
                    }
                } else {
                    loggingDB.executeSQL(loggingDB.createInsert("javascript", update), true);
                }
            }
            worker.port.on("logCall", function(data){processCallsAndValues(data)});
            worker.port.on("logValue", function(data){processCallsAndValues(data)});
        }
    });
};
