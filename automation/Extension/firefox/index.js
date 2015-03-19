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
        var enableCK = dbstring[3];
        var enableJS = dbstring[4];
        var enableCP = dbstring[5];
        console.log("Host:",host,"Port:",port,"CrawlID:",crawlID,"Cookie:",enableCK,"JS:",enableJS,"CP:",enableCP); 
    } else {
        console.log("ERROR: database settings not found");
        var host = '127.0.0.1';
        var port = '56090';
        var crawlID = '1';
        var enableCK = true;
        var enableJS = true;
        var enableCP = true;
    }
    
    // Turn on instrumentation
    if (enableCK || enableJS || enableCP) {
        loggingDB.open(host, port, crawlID);
        pageManager.setup(crawlID);
    }
    if (enableCK) {
        cookieInstrument.run(crawlID);
    }
    if (enableJS) {
        jsInstrument.run(crawlID);
    }
    if (enableCP) {
        cpInstrument.run(crawlID);
    }
};
