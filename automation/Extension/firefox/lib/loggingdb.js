import * as socket from './socket.js';
import { escapeString } from 'openwpm-webext-instrumentation';

var crawlID = null;
var visitID = null;
var debugging = false;
var dataAggregator = null;
var logAggregator = null;
var listeningSocket = null;

export const open = function(aggregatorAddress, logAddress, curr_crawlID) {
    if (aggregatorAddress == null && logAddress == null && curr_crawlID == '') {
        console.log("Debugging, everything will output to console");
        debugging = true;
        return;
    }
    crawlID = curr_crawlID;

    console.log("Opening socket connections...");

    // Connect to MPLogger for extension info/debug/error logging
    if (logAddress != null) {
        logAggregator = new socket.SendingSocket("log");
        var rv = logAggregator.connect();
        console.log("logSocket started?", rv)
    }

    // Connect to databases for saving data
    if (aggregatorAddress != null) {
        dataAggregator = new socket.SendingSocket("data");
        var rv = dataAggregator.connect();
        console.log("sqliteSocket started?",rv);
    }

    // Listen for incoming urls as visit ids
    listeningSocket = new socket.ListeningSocket("visits");
    console.log("Starting socket listening for incoming connections.");
    listeningSocket.startListening();

};

export const close = function() {
    if (dataAggregator != null) {
        dataAggregator.close();
    }
    if (logAggregator != null) {
        logAggregator.close();
    }
};

var makeLogJSON = function(lvl, msg) {
    var log_json = {
        'name': 'Extension-Logger',
        'level': lvl,
        'pathname': 'FirefoxExtension',
        'lineno': 1,
        'msg': escapeString(msg),
        'args': null,
        'exc_info': null,
        'func': null
    }
    return log_json;
}

export const logInfo = function(msg) {
    // Always log to browser console
    console.log(msg);

    if (debugging) {
        return;
    }

    // Log level INFO == 20 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(20, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export const logDebug = function(msg) {
    // Always log to browser console
    console.log(msg);

    if (debugging) {
        return;
    }

    // Log level DEBUG == 10 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(10, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export const logWarn = function(msg) {
    // Always log to browser console
    console.warn(msg);

    if (debugging) {
        return;
    }

    // Log level WARN == 30 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(30, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export const logError = function(msg) {
    // Always log to browser console
    console.error(msg);

    if (debugging) {
        return;
    }

    // Log level INFO == 40 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(40, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export const logCritical = function(msg) {
    // Always log to browser console
    console.error(msg);

    if (debugging) {
        return;
    }

    // Log level CRITICAL == 50 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(50, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export const saveRecord = function(instrument, record) {
    // Add visit id if changed
    while (!debugging && listeningSocket.queue.length != 0) {
        visitID = listeningSocket.queue.shift();
        logDebug("Visit Id: " + visitID);
    }
    record["visit_id"] = visitID;


    if (!visitID && !debugging) {
        logCritical(
            'Extension-' + crawlID + ' : visitID is null while attempting to insert ' +
                        JSON.stringify(record)
        );
        record["visit_id"] = -1;
    }

    // send to console if debugging
    if (debugging) {
      console.log("EXTENSION", instrument, JSON.stringify(record));
      return;
    }
    dataAggregator.send([instrument, record]);
};

export const saveContent = function(content, contentHash) {
  // Send page content to the data aggregator
  dataAggregator.send(['page_content', [content, contentHash]]);
};
