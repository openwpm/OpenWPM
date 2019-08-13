import * as socket from "./socket.js";

let crawlID = null;
let visitID = null;
let debugging = false;
let dataAggregator = null;
let logAggregator = null;

export let open = async function(aggregatorAddress, logAddress, cId, vId, testing=false) {
    if (testing === true) {
        console.log("Debugging, everything will output to console");
        debugging = true;
        return;
    }

    crawlID = cId;
    visitID = vId;

    console.log("VisitID: ", visitID, "CrawlID: ", crawlID);
    console.log("Opening socket connections...");

    // Connect to MPLogger for extension info/debug/error logging
    if (!debugging && logAddress != null) {
        logAggregator = new socket.SendingSocket("log");
        let rv = await logAggregator.connect();
        console.log("log socket started?", rv)
    }

    // Connect to databases for saving data
    if (!debugging && aggregatorAddress != null) {
        dataAggregator = new socket.SendingSocket("data");
        let rv = await dataAggregator.connect();
        console.log("data socket started?",rv);
    }
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
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export let logDebug = function(msg) {
    // Always log to browser console
    console.log(msg);

    if (debugging) {
        return;
    }

    // Log level DEBUG == 10 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(10, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export let logWarn = function(msg) {
    // Always log to browser console
    console.warn(msg);

    if (debugging) {
        return;
    }

    // Log level WARN == 30 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(30, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export let logError = function(msg) {
    // Always log to browser console
    console.error(msg);

    if (debugging) {
        return;
    }

    // Log level INFO == 40 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(40, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export let logCritical = function(msg) {
    // Always log to browser console
    console.error(msg);

    if (debugging) {
        return;
    }

    // Log level CRITICAL == 50 (https://docs.python.org/2/library/logging.html#logging-levels)
    var log_json = makeLogJSON(50, msg);
    logAggregator.send(['EXT', JSON.stringify(log_json)]);
};

export let dataReceiver = {
    saveRecord(instrument_type, msg) {
        console.log(msg);
    },
};

export let saveRecord = function(instrument_type, record) {
    record["visit_id"] = visitID;

    if (!visitID && !debugging) {
        logCritical('Extension-' + crawlID + ' : visitID is null while attempting to insert ' +
                    JSON.stringify(record));
    }

    // send to console if debugging
    if (debugging) {
      console.log("EXTENSION", instrument_type, JSON.stringify(record));
      return;
    }
    dataAggregator.send([instrument_type, JSON.stringify(record)]);
};

// Stub for now
export let saveContent = async function(content, contentHash) {
  // Send page content to the data aggregator
  // deduplicated by contentHash in a levelDB database
  if (debugging) {
    console.log("LDB contentHash:",contentHash,"with length",content.length);
    return;
  }
  // Since the content might not be a valid utf8 string and it needs to be
  // json encoded later, it is encoded using base64 first.
  const b64 = Uint8ToBase64(content);
  dataAggregator.send(['page_content', [b64, contentHash]]);
};

function encode_utf8(s) {
  return unescape(encodeURIComponent(s));
}

// Base64 encoding, found on:
// https://stackoverflow.com/questions/12710001/how-to-convert-uint8-array-to-base64-encoded-string/25644409#25644409
function Uint8ToBase64(u8Arr){
  var CHUNK_SIZE = 0x8000; //arbitrary number
  var index = 0;
  var length = u8Arr.length;
  var result = '';
  var slice;
  while (index < length) {
    slice = u8Arr.subarray(index, Math.min(index + CHUNK_SIZE, length));
    result += String.fromCharCode.apply(null, slice);
    index += CHUNK_SIZE;
  }
  return btoa(result);
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
