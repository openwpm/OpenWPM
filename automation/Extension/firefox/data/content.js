// Wrap in a function closure to hide variables
(function () {

// Bypass the Jetpack DOM wrapper
let(window = unsafeWindow) {

// Header guard workaround for Jetpack multiple script loading bug
if(typeof window.navigator.instrumented == "undefined") {
Object.defineProperty(window.navigator, "instrumented", { get: function() { return true; }});

// Debugging

// Default is off, to enable include in your script
Object.defineProperty(window.navigator, "instrumented_debugging", { get: function() { return true; }});
function debugging() { return window.navigator.instrumentation_debugging; }

// Debugging tool - last accessed variable
var last_accessed = "";
Object.defineProperty(window.navigator, "last_accessed", { get: function() { return last_accessed; }});

/*
 * Instrumentation helpers
 */

// Recursively generates a path for an element
function getPathToDomElement(element) {
	if(element == document.body)
		return element.tagName;
	if(element.parentNode == null)
		return 'NULL/' + element.tagName;
	
    var siblingIndex = 1;
    var siblings = element.parentNode.childNodes;
    for (var i = 0; i < siblings.length; i++) {
        var sibling = siblings[i];
        if (sibling == element) {
        	var path = getPathToDomElement(element.parentNode);
        	path += '/' + element.tagName + '[' + siblingIndex;
        	path += ',' + element.id;
        	path += ',' + element.className;
        	if(element.tagName == 'A')
        		path += ',' + element.href;
        	path += ']';
        	return path;
        }
        if (sibling.nodeType == 1 && sibling.tagName == element.tagName)
            siblingIndex++;
    }
}

// Helper for JSONifying objects
function serializeObject(object) {
	
	// Handle permissions errors
	try {
		if(object == null)
			return "null";
		if(typeof object == "function")
			return "FUNCTION";
		if(typeof object != "object")
			return object;
		var seenObjects = [];
		return JSON.stringify(object, function(key, value) {
			if(value == null)
				return "null";
			if(typeof value == "function")
				return "FUNCTION";
			if(typeof value == "object") {
				
				// Remove wrapping on content objects
				if("wrappedJSObject" in value) {
					value = value.wrappedJSObject;
				}
				
				// Serialize DOM elements
				if(value instanceof HTMLElement)
					return getPathToDomElement(value);

				// Prevent serialization cycles
				if(key == "" || seenObjects.indexOf(value) < 0) {
					seenObjects.push(value);
					return value;
				}
				else
					return typeof value;
			}
			return value;
		});
	}
	catch(error) {
		console.log("SERIALIZATION ERROR: " + error);
		return "SERIALIZATION ERROR: " + error;
	}
}

function logErrorToConsole(error) {
	console.log("Error name: " + error.name);
	console.log("Error message: " + error.message);
	console.log("Error filename: " + error.fileName);
	console.log("Error line number: " + error.lineNumber);
	console.log("Error stack: " + error.stack);
}

// Prevent logging of gets arising from logging
var inLog = false;

// For gets, sets, etc. on a single value
function logValue(instrumentedVariableName, value, operation) {
	if(inLog)
		return;
	inLog = true;
	try {
		self.port.emit("instrumentation", {
			operation: operation,
			symbol: instrumentedVariableName,
			value: serializeObject(value)
		});
	}
	catch(error) {
		console.log("Unsuccessful value log!");
		console.log("Operation: " + operation);
		console.log("Symbol: " + instrumentedVariableName);
		console.log("String Value: " + value);
		console.log("Serialized Value: " + serializeObject(value));
		logErrorToConsole(error);
	}
	inLog = false;
}

// For functions
function logCall(instrumentedFunctionName, args) {
	if(inLog)
		return;
	inLog = true;
	try {	
		//console.log("logCall");
		//console.log("Function Name: " + instrumentedFunctionName);
		//console.log("Args: " + args.length);
		for(var i = 0; i < args.length; i++) {
			var logLine = "Arg " + i + ": ";
			console.log(logLine + typeof args[i]);
			if(typeof args[i] == "string")
				console.log(logLine + args[i]);
			if(typeof args[i] == "object") {
				console.log("" + args[i]);
				console.log("" + args[i].wrappedJSObject);
				console.log(logLine + Object.keys(args[i]));
			}
                }

                // Convert special arguments array to a standard array for JSONifying
		var serialArgs = [ ];
		for(var i = 0; i < args.length; i++)
			serialArgs.push(serializeObject(args[i]));
		self.port.emit("instrumentation", {
			operation: "call",
			symbol: instrumentedFunctionName,
			args: serialArgs,
			value: ""
		});
	}
	catch(error) {
		console.log("Unsuccessful call log: " + instrumentedFunctionName);
		logErrorToConsole(error);
	}
	inLog = false;
}

// Rough implementations of Object.getPropertyDescriptor and Object.getPropertyNames
// See http://wiki.ecmascript.org/doku.php?id=harmony:extended_object_api
Object.getPropertyDescriptor = function (subject, name) {
	var pd = Object.getOwnPropertyDescriptor(subject, name);
	var proto = Object.getPrototypeOf(subject);
	while (pd === undefined && proto !== null) {
		pd = Object.getOwnPropertyDescriptor(proto, name);
		proto = Object.getPrototypeOf(proto);
	}
	return pd;
};

Object.getPropertyNames = function (subject, name) {
	var props = Object.getOwnPropertyNames(subject);
	var proto = Object.getPrototypeOf(subject);
	while (proto !== null) {
		props = props.concat(Object.getOwnPropertyNames(proto));
		proto = Object.getPrototypeOf(proto);
	}
	// FIXME: remove duplicate property names from props
	return props;
};

/*
 *  Direct instrumentation of javascript objects
 */

// Use for direct objects
function instrumentObject(object, objectName) {
    var properties = Object.getPropertyNames(object);
    for (var i = 0; i < properties.length; i++) {
        instrumentObjectProperty(object, objectName, properties[i]);
    }
}
        
function instrumentObjectProperty(object, objectName, propertyName) {
    try {
        var property = object[propertyName];
        if (typeof property == 'function') {
            logFunction(object, objectName, propertyName);
        } else {
            logProperty(object, objectName, propertyName);
        }
    } catch(err) {
        //console.log(err);
    }
}

// Use for prototypes of Objects
function instrumentPrototype(object, objectName) {
    var properties = Object.getPropertyNames(object);
    for (var i = 0; i < properties.length; i++) {
        instrumentPrototypeProperty(object, objectName, properties[i]);
    }
}

function instrumentPrototypeProperty(object, objectName, propertyName) {
    try {
        var property = object[propertyName];
        if (typeof property == 'function') {
            logFunction(object, objectName, propertyName);
        }
    } catch(err) {
        logPropertyPrototype(object, objectName, propertyName);
    }
}

// Log calls to methods
function logFunction(object, objectName, method) {
  var originalMethod = object[method];
  object[method] = function () {
    //console.log(objectName, method, arguments);
    logCall(objectName + '.' + method, arguments);
    return originalMethod.apply(this, arguments);
  };
}

// Logging for properties of prototype objects
var instrumentedData = {};
function logPropertyPrototype(object, objectName, property) {
    instrumentedData[objectName + property] = undefined;
    Object.defineProperty(object, property, {
        configurable: true,
        get: function() {
            //console.log(objectName, property, "get", instrumentedData[objectName + property]);
            logValue(objectName + '.' + property, instrumentedData[objectName + property], "get");
            return instrumentedData[objectName + property];
        },
        set: function(value) {
            //console.log(objectName, property, "set", value);
            logValue(objectName + '.' + property, value, "set");
            instrumentedData[objectName + property] = value;
        }
    });
}

// Logging properties of objects
function logProperty(object, objectName, property) {
    var originalProperty = object[property];
    Object.defineProperty(object, property, {
        configurable: true,
        get: function() {
            //console.log(objectName, property, originalProperty, "get");
            logValue(objectName + '.' + property, originalProperty, "get");
            return originalProperty;
        },
        set: function(value) {
            //console.log(objectName, property, value, "set");
            logValue(objectName + '.' + property, value, "set");
            originalProperty = value;
        }
    });
}

/*
 * Start Instrumentation
 */

// Access to navigator/screen properties
var navigatorProperties = [ "appCodeName", "appMinorVersion", "appName", "appVersion", "cookieEnabled", "cpuClass", "geolocation", "onLine", "opsProfile", "platform", "product", "systemLanguage", "userAgent", "userLanguage", "userProfile" ];
navigatorProperties.forEach(function(property) {
    instrumentObjectProperty(window.navigator, "window.navigator", property);
});
instrumentObject(window.screen, "window.screen");

// Access to plugins
for (var i = 0; i < window.navigator.plugins.length; i++) {
    instrumentObject(window.navigator.plugins[i], "window.navigator.plugins[" + i + "]");
}

// Name, localStorage, and sessionsStorage logging
// Instrumenting window.localStorage directly doesn't seem to work, so the Storage 
// prototype must be instrumented instead. Unfortunately this fails to differentiate 
// between sessionStorage and localStorage. Instead, you'll have to look for a sequence 
// of a get for the localStorage object followed by a getItem/setItem for the Storage object.
windowProperties = [ "name", "localStorage", "sessionStorage" ];
windowProperties.forEach(function(property) {
    instrumentObjectProperty(window, "window", property);
});
instrumentPrototype(window.Storage.prototype, "window.Storage")

// Access to canvas
instrumentPrototype(window.HTMLCanvasElement.prototype,"HTMLCanvasElement");
instrumentPrototype(window.CanvasRenderingContext2D.prototype, "CanvasRenderingContext2D");

// Access to webRTC
instrumentPrototype(window.mozRTCPeerConnection.prototype,"mozRTCPeerConnection");

}

}

})();
