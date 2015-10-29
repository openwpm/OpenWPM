const {Cc, Ci} = require("chrome");
var events = require("sdk/system/events");
const data = require("sdk/self").data;
var loggingDB = require("./loggingdb.js");

exports.run = function(crawlID) {

    // Set up logging
    var createCookiesTable = data.load("create_cookies_table.sql");
    loggingDB.executeSQL(createCookiesTable, false);

    // Instrument cookie changes
    events.on("cookie-changed", function(event) {
        console.log("COOKIE CHANGED");
        var data = event.data;
        // TODO: Support other cookie operations
        if(data == "deleted" || data == "added" || data == "changed") {    
            var update = {};
            update["change"] = loggingDB.escapeString(data);
            update["crawl_id"] = crawlID;

            var cookie = event.subject.QueryInterface(Ci.nsICookie2);
            update["creationTime"] = cookie.creationTime;
            update["expiry"] = cookie.expiry;
            update["is_http_only"] = loggingDB.boolToInt(cookie.isHttpOnly);
            update["is_session"] = loggingDB.boolToInt(cookie.isSession);
            update["last_accessed"] = cookie.lastAccessed;
            update["raw_host"] = loggingDB.escapeString(cookie.rawHost);
            
            cookie = cookie.QueryInterface(Ci.nsICookie);
            update["expires"] = cookie.expires;
            update["host"] = loggingDB.escapeString(cookie.host);
            update["is_domain"] = loggingDB.boolToInt(cookie.isDomain);
            update["is_secure"] = loggingDB.boolToInt(cookie.isSecure);
            update["name"] = loggingDB.escapeString(cookie.name);
            update["path"] = loggingDB.escapeString(cookie.path);
            update["policy"] = cookie.policy;
            update["status"] = cookie.status;
            update["value"] = loggingDB.escapeString(cookie.value);
            
            loggingDB.executeSQL(loggingDB.createInsert("javascript_cookies", update), true);
        }
    }, true);
    
};
