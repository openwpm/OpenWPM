import * as socket from "./socket.js";

let crawlID = null;
let visitID = null;
let debugging = false;
let dataAggregator = null;
let logAggregator = null;
let listeningSocket = null;

export let open = async function(aggregatorAddress, logAddress, curr_crawlID) {
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
        let rv = await logAggregator.connect(logAddress[0], logAddress[1]);
        console.log("logSocket started?", rv)
    }

    // Connect to databases for saving data
    if (aggregatorAddress != null) {
        dataAggregator = new socket.SendingSocket();
        let rv = await dataAggregator.connect(aggregatorAddress[0], aggregatorAddress[1]);
        console.log("sqliteSocket started?",rv);
    }

    // Listen for incomming urls as visit ids
    listeningSocket = new socket.ListeningSocket();
    console.log("Starting socket listening for incomming connections.");
    listeningSocket.startListening().then(() => {
        browser.profileDirIO.writeFile("extension_port.txt", `${listeningSocket.port}`);
    });
};

export let close = function() {
    if (dataAggregator != null) {
        dataAggregator.close();
    }
    if (logAggregator != null) {
        logAggregator.close();
    }
};

let makeLogJSON = function(lvl, msg) {
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

export let logInfo = function(msg) {
    // Always log to browser console
    console.log(msg);

    if (debugging) {
        return;
    }

    // Log level INFO == 20 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(20, msg);
    logAggregator.send(JSON.stringify(['EXT', JSON.stringify(log_json)]));
};

export let logDebug = function(msg) {
    // Always log to browser console
    console.log(msg);

    if (debugging) {
        return;
    }

    // Log level DEBUG == 10 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(10, msg);
    logAggregator.send(JSON.stringify(['EXT', JSON.stringify(log_json)]));
};

export let logWarn = function(msg) {
    // Always log to browser console
    console.warn(msg);

    if (debugging) {
        return;
    }

    // Log level WARN == 30 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(30, msg);
    logAggregator.send(JSON.stringify(['EXT', JSON.stringify(log_json)]));
};

export let logError = function(msg) {
    // Always log to browser console
    console.error(msg);

    if (debugging) {
        return;
    }

    // Log level INFO == 40 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(40, msg);
    logAggregator.send(JSON.stringify(['EXT', JSON.stringify(log_json)]));
};

export let logCritical = function(msg) {
    // Always log to browser console
    console.error(msg);

    if (debugging) {
        return;
    }

    // Log level CRITICAL == 50 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(50, msg);
    logAggregator.send(JSON.stringify(['EXT', JSON.stringify(log_json)]));
};

export let dataReceiver = {
    saveRecord(a, b) {
        console.log(b);
    },
};

export let saveRecord = function(instrument, record) {
    // Add visit id if changed
    while (!debugging && listeningSocket.queue.length != 0) {
        visitID = listeningSocket.queue.shift();
        logDebug("Visit Id: " + visitID);
    }
    record["visit_id"] = visitID;


    if (!visitID && !debugging) {
        logCritical('Extension-' + crawlID + ' : visitID is null while attempting to insert ' +
                    JSON.stringify(record));
        record["visit_id"] = -1;
    }

    // send to console if debugging
    if (debugging) {
      console.log("EXTENSION", instrument, JSON.stringify(record));
      return;
    }
    dataAggregator.send(JSON.stringify([instrument, record]));
};

// Stub for now
export let saveContent = async function(content, contentHash) {
  // Send page content to the data aggregator
  // deduplicated by contentHash in a levelDB database
  if (debugging) {
    console.log("LDB contentHash:",contentHash,"with length",content.length);
    return;
  }
  dataAggregator.send(JSON.stringify(['page_content', [content, contentHash]]));
};

function encode_utf8(s) {
  return unescape(encodeURIComponent(s));
}

export let escapeString = function(string) {
    // Convert to string if necessary
    if(typeof string != "string")
        string = "" + string;

    return encode_utf8(string);
};

export let boolToInt = function(bool) {
    return bool ? 1 : 0;
};
