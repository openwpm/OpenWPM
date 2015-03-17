var loggingDB           = require("./lib/loggingdb.js");
var pageManager         = require("./lib/page-manager.js");
var cookieInstrument    = require("./lib/cookie-instrument.js");
var jsInstrument        = require("./lib/javascript-instrument.js");
var cpInstrument        = require("./lib/content-policy-instrument.js");

exports.main = function(options, callbacks) {
        loggingDB.open();
	pageManager.setup();
	cookieInstrument.run();
        jsInstrument.run();
        cpInstrument.run();
};
