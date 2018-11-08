const fileIO            = require("sdk/io/file");
const system            = require("sdk/system");
var socket              = require("./socket.js");

var crawlID = null;
var visitID = null;
var debugging = false;
var dataAggregator = null;
var logAggregator = null;
var listeningSocket = null;

exports.open = function(aggregatorAddress, logAddress, curr_crawlID) {
    if (aggregatorAddress == null && logAddress == null && curr_crawlID == '') {
        console.log("Debugging, everything will output to console");
        debugging = true;
        return;
    }
    crawlID = curr_crawlID;

    console.log("Opening socket connections...");

    // Connect to MPLogger for extension info/debug/error logging
    if (logAddress != null) {
        logAggregator = new socket.SendingSocket();
        var rv = logAggregator.connect(logAddress[0], logAddress[1]);
        console.log("logSocket started?", rv)
    }

    // Connect to databases for saving data
    if (aggregatorAddress != null) {
        dataAggregator = new socket.SendingSocket();
        var rv = dataAggregator.connect(aggregatorAddress[0], aggregatorAddress[1]);
        console.log("sqliteSocket started?",rv);
    }

    // Listen for incomming urls as visit ids
    listeningSocket = new socket.ListeningSocket();
    var path = system.pathFor("ProfD") + '/extension_port.txt';
    console.log("Writing listening socket port to disk at:", path);
    var file = fileIO.open(path, 'w');
    if (!file.closed) {
        file.write(listeningSocket.port);
        file.close();
        console.log("Port",listeningSocket.port,"written to disk.");
    }
    console.log("Starting socket listening for incomming connections.");
    listeningSocket.startListening();
};

exports.close = function() {
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

exports.logInfo = function(msg) {
    // Always log to browser console
    console.log(msg);

    if (debugging) {
        return;
    }

    // Log level INFO == 20 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(20, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

exports.logDebug = function(msg) {
    // Always log to browser console
    console.log(msg);

    if (debugging) {
        return;
    }

    // Log level DEBUG == 10 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(10, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

exports.logWarn = function(msg) {
    // Always log to browser console
    console.warn(msg);

    if (debugging) {
        return;
    }

    // Log level WARN == 30 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(30, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

exports.logError = function(msg) {
    // Always log to browser console
    console.error(msg);

    if (debugging) {
        return;
    }

    // Log level INFO == 40 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(40, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

exports.logCritical = function(msg) {
    // Always log to browser console
    console.error(msg);

    if (debugging) {
        return;
    }

    // Log level CRITICAL == 50 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(50, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

exports.saveRecord = function(instrument, record) {
    // Add visit id if changed
    while (!debugging && listeningSocket.queue.length != 0) {
        visitID = listeningSocket.queue.shift();
        exports.logDebug("Visit Id: " + visitID);
    }
    record["visit_id"] = visitID;


    if (!visitID && !debugging) {
        exports.logCritical('Extension-' + crawlID + ' : visitID is null while attempting to insert ' +
                    JSON.stringify(record));
        record["visit_id"] = -1;
    }

    // send to console if debugging
    if (debugging) {
      console.log("EXTENSION", instrument, JSON.stringify(record));
      return;
    }
    dataAggregator.send([instrument, record]);
}

exports.saveContent = function(content, contentHash) {
  // Send page content to the data aggregator
  // deduplicated by contentHash in a levelDB database
  if (debugging) {
    console.log("LDB contentHash:",contentHash,"with length",content.length);
    return;
  }
  dataAggregator.send(['page_content', [content, contentHash]]);
}

function encode_utf8(s) {
  return unescape(encodeURIComponent(s));
}

var escapeString = function(string) {
    // Convert to string if necessary
    if(typeof string != "string")
        string = "" + string;

    return encode_utf8(string);
};
exports.escapeString = escapeString;

exports.boolToInt = function(bool) {
    return bool ? 1 : 0;
};
