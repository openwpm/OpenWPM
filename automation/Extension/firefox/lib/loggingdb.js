const fileIO            = require("sdk/io/file");
const system            = require("sdk/system");
var socket              = require("./socket.js");

var crawlID = null;
var visitID = null;
var debugging = false;
var sqliteAggregator = null;
var listeningSocket = null;

exports.open = function(sqliteAddress, crawlID) {
    if (sqliteAddress == null && crawlID == '') {
        console.log("Debugging, everything will output to console");
        debugging = true;
        return;
    }
    crawlID = crawlID;

    // Connect to databases for saving data
    console.log("Opening socket connections...");
    if (sqliteAddress != ['','']) {
        sqliteAggregator = new socket.SendingSocket();
        var rv = sqliteAggregator.connect(sqliteAddress[0], sqliteAddress[1]);
        console.log("sqliteSocket started?",rv);
    }

    // Listen for incomming urls as visit ids
    listeningSocket = new socket.ListeningSocket();
    var path = system.pathFor("ProfD") + '/extension_port.txt';
    var file = fileIO.open(path, 'w');
    if (!file.closed) {
        file.write(listeningSocket.port);
        file.close();
    }
    listeningSocket.startListening();
};

exports.close = function() {
    if (sqliteAggregator != null) {
        sqliteAggregator.close();
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
