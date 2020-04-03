// Intrumentation injection code is based on privacybadgerfirefox
// https://github.com/EFForg/privacybadgerfirefox/blob/master/data/fingerprinting.js

declare global {
  interface Object {
    getPropertyDescriptor(subject: any, name: any): PropertyDescriptor;
  }

  interface Object {
    getPropertyNames(subject: any): string[];
  }
}

interface LogSettings {
  propertiesToInstrument?: string[];
  nonExistingPropertiesToInstrument?: string[];
  excludedProperties?: string[];
  logCallStack?: boolean;
  logFunctionsAsStrings?: boolean;
  logFunctionGets?: boolean;
  preventSets?: boolean;
  recursive?: boolean;
  depth?: number;
}

export function jsInstruments(event_id, sendMessagesToLogger) {
  /*
   * Instrumentation helpers
   * (Inlined in order for jsInstruments to be easily exportable as a string)
   */

  // debounce - from Underscore v1.6.0
  function debounce(func, wait, immediate = false) {
    let timeout, args, context, timestamp, result;

    const later = function() {
      const last = Date.now() - timestamp;
      if (last < wait) {
        timeout = setTimeout(later, wait - last);
      } else {
        timeout = null;
        if (!immediate) {
          result = func.apply(context, args);
          context = args = null;
        }
      }
    };

    return function() {
      context = this;
      args = arguments;
      timestamp = Date.now();
      const callNow = immediate && !timeout;
      if (!timeout) {
        timeout = setTimeout(later, wait);
      }
      if (callNow) {
        result = func.apply(context, args);
        context = args = null;
      }

      return result;
    };
  }

  // Recursively generates a path for an element
  function getPathToDomElement(element, visibilityAttr = false) {
    if (element === document.body) {
      return element.tagName;
    }
    if (element.parentNode === null) {
      return "NULL/" + element.tagName;
    }

    let siblingIndex = 1;
    const siblings = element.parentNode.childNodes;
    for (let i = 0; i < siblings.length; i++) {
      const sibling = siblings[i];
      if (sibling === element) {
        let path = getPathToDomElement(element.parentNode, visibilityAttr);
        path += "/" + element.tagName + "[" + siblingIndex;
        path += "," + element.id;
        path += "," + element.className;
        if (visibilityAttr) {
          path += "," + element.hidden;
          path += "," + element.style.display;
          path += "," + element.style.visibility;
        }
        if (element.tagName === "A") {
          path += "," + element.href;
        }
        path += "]";
        return path;
      }
      if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
        siblingIndex++;
      }
    }
  }

  // Helper for JSONifying objects
  function serializeObject(object, stringifyFunctions = false) {
    // Handle permissions errors
    try {
      if (object === null) {
        return "null";
      }
      if (typeof object === "function") {
        if (stringifyFunctions) {
          return object.toString();
        } else {
          return "FUNCTION";
        }
      }
      if (typeof object !== "object") {
        return object;
      }
      const seenObjects = [];
      return JSON.stringify(object, function(key, value) {
        if (value === null) {
          return "null";
        }
        if (typeof value === "function") {
          if (stringifyFunctions) {
            return value.toString();
          } else {
            return "FUNCTION";
          }
        }
        if (typeof value === "object") {
          // Remove wrapping on content objects
          if ("wrappedJSObject" in value) {
            value = value.wrappedJSObject;
          }

          // Serialize DOM elements
          if (value instanceof HTMLElement) {
            return getPathToDomElement(value);
          }

          // Prevent serialization cycles
          if (key === "" || seenObjects.indexOf(value) < 0) {
            seenObjects.push(value);
            return value;
          } else {
            return typeof value;
          }
        }
        return value;
      });
    } catch (error) {
      console.log("OpenWPM: SERIALIZATION ERROR: " + error);
      return "SERIALIZATION ERROR: " + error;
    }
  }

  /*
   * Direct instrumentation of javascript objects
   */

  const sendFactory = function($event_id, $sendMessagesToLogger) {
    let messages = [];
    // debounce sending queued messages
    const _send = debounce(function() {
      $sendMessagesToLogger($event_id, messages);

      // clear the queue
      messages = [];
    }, 100);

    return function(msgType, msg) {
      // queue the message
      messages.push({ type: msgType, content: msg });
      _send();
    };
  };

  const send = sendFactory(event_id, sendMessagesToLogger);

  // Counter to cap # of calls logged for each script/api combination
  const maxLogCount = 500;
  const logCounter = new Object();

  function updateCounterAndCheckIfOver(scriptUrl, symbol) {
    const key = scriptUrl + "|" + symbol;
    if (key in logCounter && logCounter[key] >= maxLogCount) {
      return true;
    } else if (!(key in logCounter)) {
      logCounter[key] = 1;
    } else {
      logCounter[key] += 1;
    }
    return false;
  }

  // Prevent logging of gets arising from logging
  let inLog = false;

  // To keep track of the original order of events
  let ordinal = 0;

  // For gets, sets, etc. on a single value
  function logValue(
    instrumentedVariableName,
    value,
    operation,
    callContext,
    logSettings,
  ) {
    if (inLog) {
      return;
    }
    inLog = true;

    const overLimit = updateCounterAndCheckIfOver(
      callContext.scriptUrl,
      instrumentedVariableName,
    );
    if (overLimit) {
      inLog = false;
      return;
    }

    const msg = {
      operation,
      symbol: instrumentedVariableName,
      value: serializeObject(value, !!logSettings.logFunctionsAsStrings),
      scriptUrl: callContext.scriptUrl,
      scriptLine: callContext.scriptLine,
      scriptCol: callContext.scriptCol,
      funcName: callContext.funcName,
      scriptLocEval: callContext.scriptLocEval,
      callStack: callContext.callStack,
      ordinal: ordinal++,
    };

    try {
      send("logValue", msg);
    } catch (error) {
      console.log("OpenWPM: Unsuccessful value log!");
      logErrorToConsole(error);
    }

    inLog = false;
  }

  // For functions
  function logCall(instrumentedFunctionName, args, callContext, logSettings) {
    if (inLog) {
      return;
    }
    inLog = true;

    const overLimit = updateCounterAndCheckIfOver(
      callContext.scriptUrl,
      instrumentedFunctionName,
    );
    if (overLimit) {
      inLog = false;
      return;
    }

    try {
      // Convert special arguments array to a standard array for JSONifying
      const serialArgs = [];
      for (let i = 0; i < args.length; i++) {
        serialArgs.push(
          serializeObject(args[i], !!logSettings.logFunctionsAsStrings),
        );
      }
      const msg = {
        operation: "call",
        symbol: instrumentedFunctionName,
        args: serialArgs,
        value: "",
        scriptUrl: callContext.scriptUrl,
        scriptLine: callContext.scriptLine,
        scriptCol: callContext.scriptCol,
        funcName: callContext.funcName,
        scriptLocEval: callContext.scriptLocEval,
        callStack: callContext.callStack,
        ordinal: ordinal++,
      };
      send("logCall", msg);
    } catch (error) {
      console.log(
        "OpenWPM: Unsuccessful call log: " + instrumentedFunctionName,
      );
      logErrorToConsole(error);
    }
    inLog = false;
  }

  function logErrorToConsole(error, context: any = false) {
    console.log("OpenWPM: Error name: " + error.name);
    console.log("OpenWPM: Error message: " + error.message);
    console.log("OpenWPM: Error filename: " + error.fileName);
    console.log("OpenWPM: Error line number: " + error.lineNumber);
    console.log("OpenWPM: Error stack: " + error.stack);
    if (context) {
      console.log("OpenWPM: Error context: " + JSON.stringify(context));
    }
  }

  // Rough implementations of Object.getPropertyDescriptor and Object.getPropertyNames
  // See http://wiki.ecmascript.org/doku.php?id=harmony:extended_object_api
  Object.getPropertyDescriptor = function(subject, name) {
    if (subject === undefined) {
      throw new Error("Can't get property descriptor for undefined");
    }
    let pd = Object.getOwnPropertyDescriptor(subject, name);
    let proto = Object.getPrototypeOf(subject);
    while (pd === undefined && proto !== null) {
      pd = Object.getOwnPropertyDescriptor(proto, name);
      proto = Object.getPrototypeOf(proto);
    }
    return pd;
  };

  Object.getPropertyNames = function(subject) {
    if (subject === undefined) {
      throw new Error("Can't get property names for undefined");
    }
    let props = Object.getOwnPropertyNames(subject);
    let proto = Object.getPrototypeOf(subject);
    while (proto !== null) {
      props = props.concat(Object.getOwnPropertyNames(proto));
      proto = Object.getPrototypeOf(proto);
    }
    // FIXME: remove duplicate property names from props
    return props;
  };

  // Helper to get originating script urls
  function getStackTrace() {
    let stack;

    try {
      throw new Error();
    } catch (err) {
      stack = err.stack;
    }

    return stack;
  }

  // from http://stackoverflow.com/a/5202185
  const rsplit = function(source: string, sep, maxsplit) {
    const split = source.split(sep);
    return maxsplit
      ? [split.slice(0, -maxsplit).join(sep)].concat(split.slice(-maxsplit))
      : split;
  };

  function getOriginatingScriptContext(getCallStack = false) {
    const trace = getStackTrace()
      .trim()
      .split("\n");
    // return a context object even if there is an error
    const empty_context = {
      scriptUrl: "",
      scriptLine: "",
      scriptCol: "",
      funcName: "",
      scriptLocEval: "",
      callStack: "",
    };
    if (trace.length < 4) {
      return empty_context;
    }
    // 0, 1 and 2 are OpenWPM's own functions (e.g. getStackTrace), skip them.
    const callSite = trace[3];
    if (!callSite) {
      return empty_context;
    }
    /*
     * Stack frame format is simply: FUNC_NAME@FILENAME:LINE_NO:COLUMN_NO
     *
     * If eval or Function is involved we have an additional part after the FILENAME, e.g.:
     * FUNC_NAME@FILENAME line 123 > eval line 1 > eval:LINE_NO:COLUMN_NO
     * or FUNC_NAME@FILENAME line 234 > Function:LINE_NO:COLUMN_NO
     *
     * We store the part between the FILENAME and the LINE_NO in scriptLocEval
     */
    try {
      let scriptUrl = "";
      let scriptLocEval = ""; // for eval or Function calls
      const callSiteParts = callSite.split("@");
      const funcName = callSiteParts[0] || "";
      const items = rsplit(callSiteParts[1], ":", 2);
      const columnNo = items[items.length - 1];
      const lineNo = items[items.length - 2];
      const scriptFileName = items[items.length - 3] || "";
      const lineNoIdx = scriptFileName.indexOf(" line "); // line in the URL means eval or Function
      if (lineNoIdx === -1) {
        scriptUrl = scriptFileName; // TODO: sometimes we have filename only, e.g. XX.js
      } else {
        scriptUrl = scriptFileName.slice(0, lineNoIdx);
        scriptLocEval = scriptFileName.slice(
          lineNoIdx + 1,
          scriptFileName.length,
        );
      }
      const callContext = {
        scriptUrl,
        scriptLine: lineNo,
        scriptCol: columnNo,
        funcName,
        scriptLocEval,
        callStack: getCallStack
          ? trace
              .slice(3)
              .join("\n")
              .trim()
          : "",
      };
      return callContext;
    } catch (e) {
      console.log(
        "OpenWPM: Error parsing the script context",
        e.toString(),
        callSite,
      );
      return empty_context;
    }
  }

  function isObject(object, propertyName) {
    let property;
    try {
      property = object[propertyName];
    } catch (error) {
      return false;
    }
    if (property === null) {
      // null is type "object"
      return false;
    }
    return typeof property === "object";
  }

  function instrumentObject(object, objectName, logSettings: LogSettings = {}) {
    // Use for objects or object prototypes
    //
    // Parameters
    // ----------
    //   object : Object
    //     Object to instrument
    //   objectName : String
    //     Name of the object to be instrumented (saved to database)
    //   logSettings : Object
    //     (optional) object that can be used to specify additional logging
    //     configurations. See available options below.
    //
    // logSettings options (all optional)
    // -------------------
    //   propertiesToInstrument : Array
    //     An array of properties to instrument on this object. Default is
    //     all properties.
    //   nonExistingPropertiesToInstrument : Array
    //     An array of non-existing properties to instrument on this object.
    //   excludedProperties : Array
    //     Properties excluded from instrumentation. Default is an empty
    //     array.
    //   logCallStack : boolean
    //     Set to true save the call stack info with each property call.
    //     Default is `false`.
    //   logFunctionsAsStrings : boolean
    //     Set to true to save functional arguments as strings during
    //     argument serialization. Default is `false`.
    //   preventSets : boolean
    //     Set to true to prevent nested objects and functions from being
    //     overwritten (and thus having their instrumentation removed).
    //     Other properties (static values) can still be set with this is
    //     enabled. Default is `false`.
    //   recursive : boolean
    //     Set to `true` to recursively instrument all object properties of
    //     the given `object`. Default is `false`
    //     NOTE:
    //       (1)`logSettings['propertiesToInstrument']` does not propagate
    //           to sub-objects.
    //       (2) Sub-objects of prototypes can not be instrumented
    //           recursively as these properties can not be accessed
    //           until an instance of the prototype is created.
    //   depth : integer
    //     Recursion limit when instrumenting object recursively.
    //     Default is `5`.
    const properties = logSettings.propertiesToInstrument
      ? logSettings.propertiesToInstrument
      : Object.getPropertyNames(object);
    for (const propertyName of properties) {
      if (
        logSettings.excludedProperties &&
        logSettings.excludedProperties.indexOf(propertyName) > -1
      ) {
        continue;
      }
      // If `recursive` flag set we want to recursively instrument any
      // object properties that aren't the prototype object. Only recurse if
      // depth not set (at which point its set to default) or not at limit.
      if (
        !!logSettings.recursive &&
        propertyName !== "__proto__" &&
        isObject(object, propertyName) &&
        (!("depth" in logSettings) || logSettings.depth > 0)
      ) {
        // set recursion limit to default if not specified
        if (!("depth" in logSettings)) {
          logSettings.depth = 5;
        }
        instrumentObject(
          object[propertyName],
          objectName + "." + propertyName,
          {
            excludedProperties: logSettings.excludedProperties,
            logCallStack: logSettings.logCallStack,
            logFunctionsAsStrings: logSettings.logFunctionsAsStrings,
            preventSets: logSettings.preventSets,
            recursive: logSettings.recursive,
            depth: logSettings.depth - 1,
          },
        );
      }
      try {
        instrumentObjectProperty(object, objectName, propertyName, logSettings);
      } catch (error) {
        logErrorToConsole(error, { objectName, propertyName });
      }
    }
    const nonExistingProperties = logSettings.nonExistingPropertiesToInstrument;
    if (nonExistingProperties) {
      for (const propertyName of nonExistingProperties) {
        if (
          logSettings.excludedProperties &&
          logSettings.excludedProperties.indexOf(propertyName) > -1
        ) {
          continue;
        }
        try {
          instrumentObjectProperty(
            object,
            objectName,
            propertyName,
            logSettings,
          );
        } catch (error) {
          logErrorToConsole(error, { objectName, propertyName });
        }
      }
    }
  }

  // Log calls to a given function
  // This helper function returns a wrapper around `func` which logs calls
  // to `func`. `objectName` and `methodName` are used strictly to identify
  // which object method `func` is coming from in the logs
  function instrumentFunction(objectName, methodName, func, logSettings) {
    return function() {
      const callContext = getOriginatingScriptContext(
        !!logSettings.logCallStack,
      );
      logCall(
        objectName + "." + methodName,
        arguments,
        callContext,
        logSettings,
      );
      return func.apply(this, arguments);
    };
  }

  // Log properties of prototypes and objects
  function instrumentObjectProperty(
    object,
    objectName,
    propertyName,
    logSettings: LogSettings = {},
  ) {
    if (!object) {
      throw new Error("Invalid object: " + propertyName);
    }
    if (!objectName) {
      throw new Error("Invalid object name: " + propertyName);
    }
    if (!propertyName || propertyName === "undefined") {
      throw new Error("Invalid object property name: " + propertyName);
    }

    // Store original descriptor in closure
    const propDesc = Object.getPropertyDescriptor(object, propertyName);

    // Property descriptor must exist unless we are instrumenting a
    // non-existing property
    if (
      !propDesc &&
      (!logSettings.nonExistingPropertiesToInstrument ||
        logSettings.nonExistingPropertiesToInstrument.indexOf(propertyName) ==
          -1)
    ) {
      console.error(
        "Property descriptor not found for",
        objectName,
        propertyName,
        object,
      );
      return;
    }

    // Property descriptor for undefined properties
    let undefinedPropValue;
    const undefinedPropDesc = {
      get: () => {
        return undefinedPropValue;
      },
      set: value => {
        undefinedPropValue = value;
      },
      enumerable: false,
    };

    // Instrument data or accessor property descriptors
    const originalGetter = propDesc ? propDesc.get : undefinedPropDesc.get;
    const originalSetter = propDesc ? propDesc.set : undefinedPropDesc.set;
    let originalValue = propDesc ? propDesc.value : undefinedPropValue;

    // We overwrite both data and accessor properties as an instrumented
    // accessor property
    Object.defineProperty(object, propertyName, {
      configurable: true,
      get: (function() {
        return function() {
          let origProperty;
          const callContext = getOriginatingScriptContext(
            !!logSettings.logCallStack,
          );

          // get original value
          if (!propDesc) {
            // if undefined property
            origProperty = undefinedPropValue;
          } else if (originalGetter) {
            // if accessor property
            origProperty = originalGetter.call(this);
          } else if ("value" in propDesc) {
            // if data property
            origProperty = originalValue;
          } else {
            console.error(
              "Property descriptor for",
              objectName + "." + propertyName,
              "doesn't have getter or value?",
            );
            logValue(
              objectName + "." + propertyName,
              "",
              "get(failed)",
              callContext,
              logSettings,
            );
            return;
          }

          // Log `gets` except those that have instrumented return values
          // * All returned functions are instrumented with a wrapper
          // * Returned objects may be instrumented if recursive
          //   instrumentation is enabled and this isn't at the depth limit.
          if (typeof origProperty === "function") {
            if (logSettings.logFunctionGets) {
              logValue(
                objectName + "." + propertyName,
                origProperty,
                "get(function)",
                callContext,
                logSettings,
              );
            }
            const instrumentedFunctionWrapper = instrumentFunction(
              objectName,
              propertyName,
              origProperty,
              logSettings,
            );
            // Restore the original prototype and constructor so that instrumented classes remain intact
            // TODO: This may have introduced prototype pollution as per https://github.com/mozilla/OpenWPM/issues/471
            if (origProperty.prototype) {
              instrumentedFunctionWrapper.prototype = origProperty.prototype;
              if (origProperty.prototype.constructor) {
                instrumentedFunctionWrapper.prototype.constructor =
                  origProperty.prototype.constructor;
              }
            }
            return instrumentedFunctionWrapper;
          } else if (
            typeof origProperty === "object" &&
            !!logSettings.recursive &&
            (!("depth" in logSettings) || logSettings.depth > 0)
          ) {
            return origProperty;
          } else {
            logValue(
              objectName + "." + propertyName,
              origProperty,
              "get",
              callContext,
              logSettings,
            );
            return origProperty;
          }
        };
      })(),
      set: (function() {
        return function(value) {
          const callContext = getOriginatingScriptContext(
            !!logSettings.logCallStack,
          );
          let returnValue;

          // Prevent sets for functions and objects if enabled
          if (
            !!logSettings.preventSets &&
            (typeof originalValue === "function" ||
              typeof originalValue === "object")
          ) {
            logValue(
              objectName + "." + propertyName,
              value,
              "set(prevented)",
              callContext,
              logSettings,
            );
            return value;
          }

          // set new value to original setter/location
          if (originalSetter) {
            // if accessor property
            returnValue = originalSetter.call(this, value);
          } else if ("value" in propDesc) {
            inLog = true;
            if (object.isPrototypeOf(this)) {
              Object.defineProperty(this, propertyName, {
                value,
              });
            } else {
              originalValue = value;
            }
            returnValue = value;
            inLog = false;
          } else {
            console.error(
              "Property descriptor for",
              objectName + "." + propertyName,
              "doesn't have setter or value?",
            );
            logValue(
              objectName + "." + propertyName,
              value,
              "set(failed)",
              callContext,
              logSettings,
            );
            return value;
          }

          // log set
          logValue(
            objectName + "." + propertyName,
            value,
            "set",
            callContext,
            logSettings,
          );

          // return new value
          return returnValue;
        };
      })(),
    });
  }

  return { instrumentObject, instrumentObjectProperty };
}
