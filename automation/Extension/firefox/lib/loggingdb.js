const fileIO            = require("sdk/io/file");
const system            = require("sdk/system");
var socket              = require("./socket.js");

var crawlID = null;
var visitID = null;
var debugging = false;
var sqliteAggregator = null;
var ldbAggregator = null;
var listeningSocket = null;

exports.open = function(sqliteAddress, ldbAddress, crawlID) {
    if (sqliteAddress == null && ldbAddress == null && crawlID == '') {
        console.log("Debugging, everything will output to console");
        debugging = true;
        return;
    }
    crawlID = crawlID;

    // Connect to databases for saving data
    console.log("Opening socket connections...");
    if (sqliteAddress != null) {
        sqliteAggregator = new socket.SendingSocket();
        var rv = sqliteAggregator.connect(sqliteAddress[0], sqliteAddress[1]);
        console.log("sqliteSocket started?",rv);
    }
    if (ldbAddress != null) {
        ldbAggregator = new socket.SendingSocket();
        var rv = ldbAggregator.connect(ldbAddress[0], ldbAddress[1]);
        console.log("ldbSocket started?",rv);
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
    if (sqliteAggregator != null) {
        sqliteAggregator.close();
    }
    if (ldbAggregator != null) {
        ldbAggregator.close();
    }
};

exports.executeSQL = function(statement, async) {
    // send to console if debugging
    // TODO remove async argument
    if (debugging) {
        if (typeof statement == 'string')
            console.log("SQLite",statement);
        else
            console.log("SQLite",statement[1]);
        return;
    }
    // catch statements without arguments
    if (typeof statement == "string") {
        var statement = [statement, []];
    }
    sqliteAggregator.send(statement);
};

exports.saveContent = function(content, contentHash) {
  // send content to levelDBAggregator which stores content
  // deduplicated by contentHash in a levelDB database
  if (debugging) {
    console.log("LDB contentHash:",contentHash,"with length",content.length);
    return;
  }
  ldbAggregator.send([content, contentHash]);
}

function encode_utf8(s) {
  return unescape(encodeURIComponent(s));
}

exports.escapeString = function(string) {
    // Convert to string if necessary
    if(typeof string != "string")
        string = "" + string;

    return encode_utf8(string);
};

exports.boolToInt = function(bool) {
    return bool ? 1 : 0;
};

exports.createInsert = function(table, update) {
    // Add top url visit id if changed
    while (!debugging && listeningSocket.queue.length != 0) {
        visitID = listeningSocket.queue.shift();
        console.log("Visit Id:",visitID);
    }

    update["visit_id"] = visitID;

    var statement = "INSERT INTO " + table + " (";
    var value_str = "VALUES (";
        var values = [];
    var first = true;
    for(var field in update) {
        statement += (first ? "" : ", ") + field;
        value_str += (first ? "?" : ",?");
                values.push(update[field]);
        first = false;
    }
    statement = statement + ") " + value_str + ")";
    return [statement, values];
}
