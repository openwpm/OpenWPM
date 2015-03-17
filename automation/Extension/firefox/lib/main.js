var loggingDB = require("logging-db");
var pageManager = require("page-manager");
var httpInstrument = require("http-instrument");
var cookieInstrument = require("cookie-instrument");
var jsInstrument = require("javascript-instrument");
var cpInstrument = require("content-policy-instrument");

exports.main = function(options, callbacks) {
	loggingDB.open();
	pageManager.setup();
	httpInstrument.run();
	cookieInstrument.run();
        jsInstrument.run();
        cpInstrument.run();
};
