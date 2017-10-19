const fileIO            = require("sdk/io/file");
const system            = require("sdk/system");
const pageMod           = require("sdk/page-mod");
const data              = require("sdk/self").data;
var loggingDB           = require("./lib/loggingdb.js");
var pageManager         = require("./lib/page-manager.js");
var cookieInstrument    = require("./lib/cookie-instrument.js");
var jsInstrument        = require("./lib/javascript-instrument.js");
var cpInstrument        = require("./lib/content-policy-instrument.js");
var httpInstrument      = require("./lib/http-instrument.js");


exports.main = function(options, callbacks) {

  // Read the browser configuration from file
  var path = system.pathFor("ProfD") + '/browser_params.json';
  if (fileIO.exists(path)) {
    var config = JSON.parse(fileIO.read(path, 'r'));
    console.log("Browser Config:", config);
  } else {
    console.log("WARNING: config not found. Assuming this is a test run of",
                "the extension. Outputting all queries to console.");
    var config = {
      sqlite_address:null,
      leveldb_address:null,
      logger_address:null,
      cookie_instrument:true,
      js_instrument:true,
      cp_instrument:true,
      http_instrument:true,
      save_javascript:true,
      save_all_content:true,
      testing:true,
      crawl_id:''
    };
  }

  loggingDB.open(config['sqlite_address'],
                 config['leveldb_address'],
                 config['logger_address'],
                 config['crawl_id']);

  if (config['cookie_instrument']) {
    loggingDB.logDebug("Cookie instrumentation enabled");
    cookieInstrument.run(config['crawl_id']);
  }
  if (config['js_instrument']) {
    loggingDB.logDebug("Javascript instrumentation enabled");
    jsInstrument.run(config['crawl_id'], config['testing']);
  }
  if (config['cp_instrument']) {
    loggingDB.logDebug("Content Policy instrumentation enabled");
    cpInstrument.run(config['crawl_id']);
  }
  if (config['http_instrument']) {
    loggingDB.logDebug("HTTP Instrumentation enabled");
    httpInstrument.run(config['crawl_id'], config['save_javascript'],
                       config['save_all_content']);
  }
};
