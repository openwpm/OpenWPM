const {Cc, Ci, components} = require("chrome");
const data = require("sdk/self").data;
var { Class } = require('sdk/core/heritage');
var { xpcom, Unknown, Service } = require('sdk/platform/xpcom');
var uuid = require('sdk/util/uuid').uuid();
var loggingDB = require("./loggingdb.js");
var pageManager = require("./page-manager.js");

exports.run = function(crawlID) {

	// Set up logging
	var createContentPolicyTable = data.load("create_content_policy_table.sql");
	loggingDB.executeSQL(createContentPolicyTable, false);

	// Instrument content policy API
	// Provides additional information about what caused a request and what it's for
	var InstrumentContentPolicy = Class({
		extends: Unknown,
		interfaces: [ "nsIContentPolicy" ],

		shouldLoad: function(contentType, contentLocation, requestOrigin, context, mimeTypeGuess, extra) {
			var update = { };
			update["crawl_id"] = crawlID;
                        update["content_type"] = contentType;
			update["content_location"] = loggingDB.escapeString(contentLocation.spec);
			update["request_origin"] = loggingDB.escapeString(requestOrigin ? requestOrigin.spec : "");
			update["page_id"] = -1;
			if(context) {
				var domNode = null;
				var domWindow = null;
				try { domNode = context.QueryInterface(Ci.nsIDOMNode); }
				catch(error) { }
				try { domWindow = context.QueryInterface(Ci.nsIDOMWindow); }
				catch(error) { }
				var window = null;
				if(domNode && domNode.ownerDocument && domNode.ownerDocument.defaultView)
					window = domNode.ownerDocument.defaultView;
					//document = domNode.ownerDocument;
				if(domWindow)
					window = domWindow;
				if(window) {
					update["page_id"] = pageManager.pageIDFromWindow(window);
				}
			}
			update["mime_type_guess"] = loggingDB.escapeString(mimeTypeGuess ? mimeTypeGuess : "");

			loggingDB.executeSQL(loggingDB.createInsert("content_policy", update), true);

			return Ci.nsIContentPolicy.ACCEPT;
		},

		// Fires infrequently, instrumentation unused
		shouldProcess: function(contentType, contentLocation, requestOrigin, context, mimeType, extra) {
			return Ci.nsIContentPolicy.ACCEPT;
		}
	});

	var contractID = "@stanford.edu/instrument-content-policy;1";

	var instrumentContentPolicyService = Service({
		contract: contractID,
		Component: InstrumentContentPolicy
	});

	var categoryManager = Cc["@mozilla.org/categorymanager;1"].getService(Ci.nsICategoryManager);
	categoryManager.addCategoryEntry("content-policy", contractID, contractID, false, false);

};
