const fileIO            = require("sdk/io/file");
const system            = require("sdk/system");
var loggingDB           = require("./lib/loggingdb.js");
var pageManager         = require("./lib/page-manager.js");
var cookieInstrument    = require("./lib/cookie-instrument.js");
var jsInstrument        = require("./lib/javascript-instrument.js");
var cpInstrument        = require("./lib/content-policy-instrument.js");

exports.main = function(options, callbacks) {

    // Read the db address from file
    var path = system.pathFor("ProfD") + '/database_settings.txt';
    if (fileIO.exists(path)) {
        var dbstring = fileIO.read(path, 'r').split(',');
        var host = dbstring[0];
        var port = dbstring[1];
        var crawlID = dbstring[2];
        var enableCK = dbstring[3].trim() == 'True';
        var enableJS = dbstring[4].trim() == 'True';
        var enableCP = dbstring[5].trim() == 'True';
        console.log("Host:",host,"Port:",port,"CrawlID:",crawlID,"Cookie:",enableCK,"JS:",enableJS,"CP:",enableCP);
    } else {
        console.log("ERROR: database settings not found -- outputting all queries to console");
        var enableCK = true;
        var enableJS = true;
        var enableCP = true;
        var host = '';
        var port = '';
        var crawlID = '';
    }

    // Turn on instrumentation
    if (enableCK || enableJS || enableCP) {
        loggingDB.open(host, port, crawlID);
        //BROKEN
        //pageManager.setup(crawlID);
    }
    if (enableCK) {
        console.log("Cookie instrumentation enabled");
        cookieInstrument.run(crawlID);
    }
    if (enableJS) {
        console.log("Javascript instrumentation enabled");
        jsInstrument.run(crawlID);
    }
    if (enableCP) {
        console.log("Content Policy instrumentation enabled");
        cpInstrument.run(crawlID);
    }
};
