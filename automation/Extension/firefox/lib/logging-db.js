var socket              = require("./socket.js");

exports.open = function() {
    // Read the db address from file
    var path = system.pathFor("ProfD") + '/database_settings.txt';
    if (fileIO.exists(path)) {
        var dbstring = fileIO.read(path, 'r').split(',');
        var host = dbstring[0];
        var port = dbstring[1];
        crawlID = dbstring[2];
        console.log("Host:",host,"Port:",port,"CrawlID:",crawlID); 
    } else {
        console.log("ERROR: database settings not found");
    }

    // Connect to database
    socket.connect(host, port);
};

exports.close = function() {
    socket.close();
};

// async statement kept around for API compatibility
exports.executeSQL = function(statement, async) {
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

	// Go character by character doubling 's
	var escapedString = [ ];
	escapedString.push("'");
	for(var i = 0; i < string.length; i++) {
		var currentChar = string.charAt(i);
		if(currentChar == "'")
			escapedString.push("''");
		else
			escapedString.push(currentChar);
	}
	escapedString.push("'");
	return escapedString.join("");
};

exports.boolToInt = function(bool) {
	return bool ? 1 : 0;
};

exports.createInsert = function(table, update) {
	var statement = "INSERT INTO " + table + "(";
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
