var socket              = require("./socket.js");

var crawlID = null;
var visitID = null;
var visit_id_queue = null;
var debugging = false;

exports.open = function(host, port, crawlID) {
    if (host == '' && port == '' && crawlID == '') {
        debugging = true;
        return;
    }

    console.log("Opening socket connections")
    crawlID = crawlID;

    // Connect to database for saving data
    socket.connect(host, port);

    // Listen for incomming urls as visit ids
    visit_id_queue = socket.createListeningSocket();
};

exports.close = function() {
    socket.close();
};

// async statement kept around for API compatibility
exports.executeSQL = function(statement, async) {
    // send to console if debugging
    if (debugging) {
        if (typeof statement == 'string')
            console.log(statement);
        else
            console.log(statement[1]);
        return;
    }
    // catch statements without arguments
    if (typeof statement == "string") {
        var statement = [statement, []];
    }
    socket.send(statement);
};

exports.escapeString = function(string) {
    // Convert to string if necessary
    if(typeof string != "string")
        string = "" + string;

    return string;
};

exports.boolToInt = function(bool) {
    return bool ? 1 : 0;
};

exports.createInsert = function(table, update) {
    // Add top url visit id if changed
    while (!debugging && visit_id_queue.length != 0) {
        visitID = visit_id_queue.shift();
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
