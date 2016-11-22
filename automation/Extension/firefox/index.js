const fileIO            = require("sdk/io/file");
const system            = require("sdk/system");
var loggingDB           = require("./lib/loggingdb.js");
var pageManager         = require("./lib/page-manager.js");
var cookieInstrument    = require("./lib/cookie-instrument.js");
var jsInstrument        = require("./lib/javascript-instrument.js");
var cpInstrument        = require("./lib/content-policy-instrument.js");

exports.main = function(options, callbacks) {

    // Read the browser configuration from file
    var path = system.pathFor("ProfD") + '/browser_params.json';
    if (fileIO.exists(path)) {
        var config = JSON.parse(fileIO.read(path, 'r'));
        console.log("Browser Config:",config);
    } else {
        console.log("WARNING: config not found. Assuming this is a test run of",
                    "the extension. Outputting all queries to console.");
        var config = {
          aggregator_address:['',''],
          cookie_instrument:true,
          js_instrument:true,
          cp_instrument:true,
          crawl_id:''
        };
    }

    loggingDB.open(config['aggregator_address'][0], // host
                   config['aggregator_address'][1], // port
                   config['crawl_id']);

    if (config['cookie_instrument']) {
        console.log("Cookie instrumentation enabled");
        cookieInstrument.run(config['crawl_id']);
    }
    if (config['js_instrument']) {
        console.log("Javascript instrumentation enabled");
        jsInstrument.run(config['crawl_id']);
    }
    if (config['cp_instrument']) {
        console.log("Content Policy instrumentation enabled");
        cpInstrument.run(config['crawl_id']);
    }
};
