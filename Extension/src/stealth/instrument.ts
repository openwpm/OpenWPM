import { jsInstrumentationSettings as defaultSettings } from "./settings";
import {
  filterExtensionFrames,
  generateErrorObject,
  getBeginOfScriptCalls,
  getStackTrace,
} from "./error";
import {
  JSInstrumentSettings,
  LogSettings,
} from "../types/js_instrument_settings";

declare global {
  interface Window {
    openWpmStealthInstrumentSettings?: JSInstrumentSettings;
  }
}

/**
 * Resolves the stealth instrumentation settings.
 *
 * When a study configures a custom set, the background script injects it into
 * the page as ``window.openWpmStealthInstrumentSettings`` (see
 * ``background/javascript-instrument.ts``). When absent, fall back to the
 * bundled default (``settings.ts``), so the out-of-the-box behaviour is the
 * curated fingerprinting surface.
 */
function resolveInstrumentationSettings(): JSInstrumentSettings {
  const injected = window.openWpmStealthInstrumentSettings;
  return injected && injected.length ? injected : defaultSettings;
}

/** ************************************
 * OpenWPM legacy code
 ***************************************/
// Counter to cap # of calls logged for each script/api combination
const maxLogCount = 500;
// logCounter
const logCounter = {};
// Prevent logging of gets arising from logging
let inLog: boolean = false;
// To keep track of the original order of events
let ordinal = 0;

// Options for JSOperation
const JSOperation = {
  call: "call",
  get: "get",
  get_failed: "get(failed)",
  get_function: "get(function)",
  set: "set",
  set_failed: "set(failed)",
  set_prevented: "set(prevented)",
};

// from http://stackoverflow.com/a/5202185
function rsplit(source: string, sep: string, maxsplit: number) {
  const split = source.split(sep);
  return maxsplit
    ? [split.slice(0, -maxsplit).join(sep)].concat(split.slice(-maxsplit))
    : split;
}

// Helper for JSONifying objects
function serializeObject(
  object,
  // stringifyFunctions: boolean = false,
  stringifyFunctions: boolean,
  // ): string {
) {
  // Handle permissions errors
  try {
    if (object === null) {
      return "null";
    }
    if (typeof object === "function") {
      return stringifyFunctions ? object.toString() : "FUNCTION";
    }
    if (typeof object !== "object") {
      return object;
    }
    const seenObjects = [];
    return JSON.stringify(object, function (key, value) {
      if (value === null) {
        return "null";
      }
      if (typeof value === "function") {
        return stringifyFunctions ? value.toString() : "FUNCTION";
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
        if (key === "" || !seenObjects.includes(value)) {
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

// Rough implementations of getPropertyDescriptor and getPropertyNames.
// See http://wiki.ecmascript.org/doku.php?id=harmony:extended_object_api
//
// These are module-local helpers — deliberately NOT installed on the page's
// (or the content-script's) Object/Object.prototype. Defining them on a
// prototype would be observable to a hostile page and defeat the whole point
// of the stealth instrument. See the ``no_instrument_helpers_leaked``
// detection vector (test/test_pages/stealth_detection.html) which locks in
// that the page cannot observe them.
function getPropertyDescriptor(
  subject: any,
  name: string,
): PropertyDescriptor | undefined {
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
}

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

// Recursively generates a path for an element
function getPathToDomElement(element, visibilityAttr: boolean = false) {
  if (element === document.body) {
    return element.tagName;
  }
  if (element.parentNode === null) {
    return "NULL/" + element.tagName;
  }

  let siblingIndex = 1;
  const siblings = element.parentNode.childNodes;
  for (const sibling of siblings) {
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

function getOriginatingScriptContext(getCallStack = false) {
  const trace = getStackTrace().trim().split("\n");
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

  const traceStart = getBeginOfScriptCalls(trace);
  if (traceStart === -1) {
    // Every frame is an extension frame (e.g. an API invoked purely from
    // within instrumentation, or a stack truncated to extension frames).
    // There is no honest page attribution, so emit a blank context rather
    // than guessing a fixed offset — guessing would slice extension frames
    // into the recorded call_stack and re-leak moz-extension:// URLs.
    return empty_context;
  }
  const callSite: string | null = trace[traceStart];
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
      // Record only page frames. Slicing from traceStart (the first
      // non-extension frame) drops the leading extension prefix, but the page
      // can call back into instrumented APIs, interleaving extension frames
      // deeper in the stack — so additionally filter EVERY moz-extension://
      // frame out. If nothing remains, emit "" rather than an extension frame.
      // This keeps call_stack consistent with script_url and never re-leaks
      // the extension origin.
      callStack: getCallStack
        ? filterExtensionFrames(trace.slice(traceStart)).join("\n").trim()
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

// function logErrorToConsole(error, context = false) {
//     console.error("OpenWPM: Error name: " + error.name);
//     console.error("OpenWPM: Error message: " + error.message);
//     console.error("OpenWPM: Error filename: " + error.fileName);
//     console.error("OpenWPM: Error line number: " + error.lineNumber);
//     console.error("OpenWPM: Error stack: " + error.stack);
//     if (context) {
//         console.error("OpenWPM: Error context: " + JSON.stringify(context));
//     }
// }

// For gets, sets, etc. on a single value
function logValue(
  instrumentedVariableName, // : string,
  value, // : any,
  operation, // : string, // from JSOperation object please
  callContext, // : any,
  logSettings: LogSettings = {
    depth: 0,
    excludedProperties: [],
    logCallStack: false,
    logFunctionGets: false,
    nonExistingPropertiesToInstrument: [],
    preventSets: false,
    propertiesToInstrument: [],
    recursive: false,
    logFunctionsAsStrings: false,
  }, // : LogSettings,
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
    value: serializeObject(value, logSettings.logFunctionsAsStrings),
    scriptUrl: callContext.scriptUrl,
    scriptLine: callContext.scriptLine,
    scriptCol: callContext.scriptCol,
    funcName: callContext.funcName,
    scriptLocEval: callContext.scriptLocEval,
    callStack: callContext.callStack,
    ordinal: ordinal++,
  };

  try {
    notify("logValue", msg);
  } catch {
    console.log("OpenWPM: Unsuccessful value log!");
    // Activate for debugging purpose
    // logErrorToConsole(error);
  }

  inLog = false;
}

// For functions
function logCall(instrumentedFunctionName, args, callContext) {
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
    for (const arg of args) {
      serialArgs.push(serializeObject(arg, false)); // TODO: Get back to logSettings.logFunctionsAsStrings));
    }
    const msg = {
      operation: JSOperation.call,
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
    notify("logCall", msg);
  } catch {
    console.log("OpenWPM: Unsuccessful call log: " + instrumentedFunctionName);
    // Activate for debugging purpose
    // console.log(error);
    // logErrorToConsole(error);
  }
  inLog = false;
}

/** *******************************************************************************
 * New functionality
 **********************************************************************************/

/**
 * Provides the properties per prototype object.
 *
 * The three helpers below (``getPrototypeByDepth``, ``getPropertyNamesPerDepth``,
 * ``findPropertyInChain``) used to be installed on ``Object.prototype`` and
 * called as if they were statics. They are now plain module-local functions:
 * defining them on a prototype is observable to a hostile page (see the
 * ``no_instrument_helpers_leaked`` detection vector) and there is no reason for
 * the prototype indirection — every call site already passed the subject
 * explicitly.
 */

/**
 * Walks ``depth`` steps up the prototype chain of ``subject``.
 */
function getPrototypeByDepth(subject: any, depth: number): any {
  if (subject === undefined) {
    throw new Error("Can't get property names for undefined");
  }
  if (depth === undefined || typeof depth !== "number") {
    throw new Error("Depth " + depth + " is invalid");
  }
  let proto = subject;
  for (let i = 1; i <= depth; i++) {
    proto = Object.getPrototypeOf(proto);
  }
  if (proto === undefined) {
    throw new Error("Prototype was undefined. Too deep iteration?");
  }
  return proto;
}

/**
 * Traverses the prototype chain to collect properties. Returns an array containing
 * an object with the depth, propertyNames and scanned subject
 */
function getPropertyNamesPerDepth(subject: any, maxDepth = 0): any {
  if (subject === undefined) {
    throw new Error("Can't get property names for undefined");
  }
  const res = [];
  let depth = 0;
  let properties = Object.getOwnPropertyNames(subject);
  res.push({ depth, propertyNames: properties, object: subject });
  let proto = Object.getPrototypeOf(subject);

  while (proto !== null && depth < maxDepth) {
    depth++;
    properties = Object.getOwnPropertyNames(proto);
    res.push({ depth, propertyNames: properties, object: proto });
    proto = Object.getPrototypeOf(proto);
  }
  return res;
}

/**
 * Finds a property along the prototype chain
 */
function findPropertyInChain(subject: any, propertyName: string) {
  if (subject === undefined || propertyName === undefined) {
    throw new Error("Object and property name must be defined");
  }
  let properties = [];
  let depth = 0;
  while (subject !== null) {
    properties = Object.getOwnPropertyNames(subject);
    if (properties.includes(propertyName)) {
      return { depth, propertyName };
    }
    depth++;
    subject = Object.getPrototypeOf(subject);
  }
  throw Error("Property not found. Check whether configuration is correct!");
}

/*
 * Get all keys for properties that shall be overwritten
 */
function getPropertyKeysToOverwrite(item) {
  const res = [];
  (item.logSettings.overwrittenProperties || []).forEach((obj) => {
    res.push(obj.key);
  });
  return res;
}

function getContextualPrototypeFromString(context, objectAsString) {
  const obj = context[objectAsString];
  if (obj) {
    return obj.prototype ? obj.prototype : Object.getPrototypeOf(obj);
  } else {
    return undefined;
  }
}

/**
 * Prepares a list of properties that need to be instrumented
 * Here, this can be a previous created list (settings.js: propertiesToInstrument)
 * or all properties of a given object (settings.js: propertiesToInstrument is empty)
 */
function getObjectProperties(context, item) {
  let propertiesToInstrument = item.logSettings.propertiesToInstrument;
  const proto = getContextualPrototypeFromString(context, item.object);
  if (!proto) {
    throw Error("Object " + item.object + " was undefined.");
  }

  if (propertiesToInstrument === undefined || !propertiesToInstrument.length) {
    propertiesToInstrument = getPropertyNamesPerDepth(proto, item.depth);
    // filter excluded and overwritten properties
    const excluded = getPropertyKeysToOverwrite(item).concat(
      item.logSettings.excludedProperties,
    );
    propertiesToInstrument = filterPropertiesPerDepth(
      propertiesToInstrument,
      excluded,
    );
  } else {
    // The schema allows each entry to be either a {depth, propertyNames}
    // object or a bare property-name string. Normalise bare strings to the
    // object shape (depth 0) so the rest of the pipeline — which assumes
    // .depth / .propertyNames / .object — does not crash on them.
    propertiesToInstrument = propertiesToInstrument.map((propertyList) =>
      typeof propertyList === "string"
        ? { depth: 0, propertyNames: [propertyList] }
        : propertyList,
    );
    // Apply the same excluded/overwritten filtering as the instrument-everything
    // branch above. Without this, excludedProperties was silently ignored for
    // named-list entries (e.g. the document/window settings), a trap where a
    // configured exclusion had no effect.
    const excluded = getPropertyKeysToOverwrite(item).concat(
      item.logSettings.excludedProperties,
    );
    propertiesToInstrument = filterPropertiesPerDepth(
      propertiesToInstrument,
      excluded,
    );
    // include the object to each item
    propertiesToInstrument.forEach((propertyList) => {
      propertyList.object = getPrototypeByDepth(proto, propertyList.depth);
    });
  }
  return propertiesToInstrument;
}

/*
 * Enables communication with a background script
 * Must be injected in a private scope to the
 * page context!
 *
 * @param details: property access details
 */
function notify(type, content) {
  content.timeStamp = new Date().toISOString();
  browser.runtime.sendMessage({
    namespace: "javascript-instrumentation",
    type,
    data: content,
  });
}

function filterPropertiesPerDepth<T>(
  collection: { propertyNames: T[] }[],
  excluded: T[],
) {
  for (const elem of collection) {
    elem.propertyNames = elem.propertyNames.filter(
      (p) => !excluded.includes(p),
    );
  }
  return collection;
}

/*
 * Injects a function into the page context
 *
 * @param func: Function that shall be exported
 * @param context: target DOM
 * @param name: Name of the function (e.g., get width)
 */
function exportCustomFunction(func, context, name) {
  const targetObject = context.wrappedJSObject.Object.create(null);
  const exportedTry = exportFunction(func, targetObject, {
    allowCrossOriginArguments: true,
    defineAs: name,
  });
  return exportedTry;
}

/*
 * TODO: Add description
 */

function injectFunction(
  instrumentedFunction,
  descriptor,
  functionType,
  pageObject,
  propertyName,
) {
  const exportedFunction = exportCustomFunction(
    instrumentedFunction,
    window,
    propertyName,
  );
  changeProperty(
    descriptor,
    pageObject,
    propertyName,
    functionType,
    exportedFunction,
  );
}

/*
 * Add notifications when a property is requested
 * TODO: Bring everything together at this point
 *
 * @param original: the original getter/setter function
 * @param object:
 * @param args:
 */
function instrumentGetObjectProperty(
  context,
  identifier,
  original,
  newValue,
  object,
  args,
  logSettings: LogSettings,
) {
  const originalValue = original.call(object, ...args);
  const callContext = getOriginatingScriptContext(logSettings.logCallStack);
  const returnValue = newValue !== undefined ? newValue : originalValue;
  // Match legacy semantics for function-valued gets: a plain `get` is only
  // logged for non-function values. When the property resolves to a function,
  // legacy emits a `get(function)` row IFF logFunctionGets is enabled, and
  // never a plain `get`. (Accessing `obj.method` without calling it.)
  if (typeof returnValue === "function") {
    if (logSettings.logFunctionGets) {
      logValue(
        identifier,
        returnValue,
        JSOperation.get_function,
        callContext,
        logSettings,
      );
    }
    return returnValue;
  }
  // Recursive instrumentation (legacy `recursive` + `depth`): when the getter
  // returns an OBJECT and recursion is enabled, instrument that returned
  // object's properties one level down and return it raw WITHOUT logging a plain
  // `get` — exactly like legacy, which returns instrumented sub-objects without
  // a get row. Done lazily at access time so page-built nested objects are
  // reachable (unlike a document_start prototype walk).
  if (
    typeof returnValue === "object" &&
    returnValue !== null &&
    logSettings.recursive &&
    logSettings.depth > 0
  ) {
    instrumentReturnedObject(
      context,
      identifier,
      returnValue,
      logSettings,
      logSettings.depth,
    );
    return returnValue;
  }
  logValue(identifier, returnValue, JSOperation.get, callContext, logSettings);
  return returnValue;
}
/*
 * Add notifications when a property is set
 *
 * Honors ``preventSets``: matching legacy, when ``preventSets`` is enabled and
 * the property currently holds a function or object value, the assignment is
 * LOGGED (as ``set(prevented)``) but the original setter is NOT invoked, so the
 * page cannot clobber an instrumented nested object/function. Plain (string,
 * number, …) values are still written through, exactly like legacy.
 *
 * @param original: the original getter/setter function
 * @param originalGetter: the native getter (used only to type-check the current
 *   value when preventSets is on); undefined when the property has no getter.
 * @param object:
 * @param args:
 */
function instrumentSetObjectProperty(
  identifier,
  original,
  originalGetter,
  newValue,
  object,
  _args,
  logSettings: LogSettings,
) {
  const callContext = getOriginatingScriptContext(logSettings.logCallStack);

  if (logSettings.preventSets && originalGetter) {
    let currentValue;
    try {
      currentValue = originalGetter.call(object);
    } catch {
      currentValue = undefined;
    }
    const t = typeof currentValue;
    if (t === "function" || (t === "object" && currentValue !== null)) {
      logValue(
        identifier,
        newValue,
        JSOperation.set_prevented,
        callContext,
        logSettings,
      );
      return newValue;
    }
  }

  logValue(
    identifier,
    newValue,
    original ? JSOperation.set : JSOperation.set_failed,
    callContext,
    logSettings,
  );
  return !original ? newValue : original.call(object, newValue);
}

/*
 * Creates a getter function
 *
 * @param descriptor: the descriptor of the original function
 * @param funcName: Name of property/function that shall be overwritten
 * @param newValue: in Case the value shall be changed
 */
function generateGetter(
  context,
  identifier,
  descriptor,
  propertyName,
  newValue = undefined,
  logSettings: LogSettings,
) {
  const original = descriptor.get;
  return Object.getOwnPropertyDescriptor(
    {
      get [propertyName]() {
        return instrumentGetObjectProperty(
          context,
          identifier,
          original,
          newValue,
          this,
          // eslint-disable-next-line prefer-rest-params -- this is a computed-accessor getter (`get [propertyName]()`), so its arity is 0 by construction — matching native getters — regardless of `arguments`. Rest params are a syntax error in a getter. `arguments` only forwards any call args into the instrumentation helper.
          arguments,
          logSettings,
        );
      },
    },
    propertyName,
  ).get;
}

/*
 * Creates a setter function
 *
 * @param descriptor: the descriptor of the original function
 * @param funcName: Name of property/function that shall be overwritten
 * @param newValue: in Case the value shall be changed
 */
function generateSetter(
  identifier,
  descriptor,
  propertyName,
  _newValue: any | undefined = undefined,
  logSettings: LogSettings,
) {
  const original = descriptor.set;
  // The native getter is captured so the setter can type-check the current
  // value when preventSets is enabled (see instrumentSetObjectProperty).
  const originalGetter = descriptor.get;
  return Object.getOwnPropertyDescriptor(
    {
      set [propertyName](value) {
        instrumentSetObjectProperty(
          identifier,
          original,
          originalGetter,
          value,
          this,
          // eslint-disable-next-line prefer-rest-params -- this is a computed-accessor setter (`set [propertyName](value)`), so its arity is 1 by construction — matching native setters — regardless of `arguments`. `arguments` only forwards the assigned value into the instrumentation helper.
          arguments,
          logSettings,
        );
      },
    },
    propertyName,
  ).set;
}

/*
 * Overwrites the prototype to access a property
 * @param
 */
function changeProperty(descriptor, pageObject, name, method, changed) {
  descriptor[method] = changed;
  Object.defineProperty(pageObject, name, descriptor);
}

/*
 * Retrieves an object in a context
 *
 * @param context: the window object that is currently instrumented
 * @param object: the subobject needed
 */
function getPageObjectInContext(context, context_object) {
  if (context === undefined || context_object === undefined) {
    return;
  }
  return context[context_object].prototype || context[context_object];
}

/*
 * Entry point to creates (g/s)etter functions,
 * instrument them and inject them to the page
 * context
 */
function instrumentGetterSetter(
  context,
  descriptor,
  identifier,
  pageObject,
  propertyName,
  newValue = undefined,
  logSettings: LogSettings,
) {
  let instrumentedFunction;
  const getFuncType = "get";
  const setFuncType = "set";

  if (Object.prototype.hasOwnProperty.call(descriptor, getFuncType)) {
    instrumentedFunction = generateGetter(
      context,
      identifier,
      descriptor,
      propertyName,
      newValue,
      logSettings,
    );
    injectFunction(
      instrumentedFunction,
      descriptor,
      getFuncType,
      pageObject,
      propertyName,
    );
  }
  if (Object.prototype.hasOwnProperty.call(descriptor, setFuncType)) {
    instrumentedFunction = generateSetter(
      identifier,
      descriptor,
      propertyName,
      undefined,
      logSettings,
    );
    injectFunction(
      instrumentedFunction,
      descriptor,
      setFuncType,
      pageObject,
      propertyName,
    );
  }
}

/*
 * Copies a native function's arity onto an instrumented wrapper.
 *
 * A real function exposes ``.length`` (its declared arity) as a
 * ``{ writable: false, enumerable: false, configurable: true }`` data
 * property — e.g. ``CanvasRenderingContext2D.prototype.getContext.length === 1``.
 * Our wrappers are declared with no parameters and forward via ``arguments``, so
 * their ``.length`` is 0. A page that compares ``fn.length`` against the known
 * native arity would therefore detect the instrument.
 *
 * We redefine ``.length`` on the wrapper to the original's value using the SAME
 * descriptor shape the engine uses for native functions, so the property is
 * indistinguishable from a genuine one. ``.length`` is ``configurable: true`` on
 * functions, so this redefinition is always permitted.
 */
function copyFunctionArity(wrapper, original) {
  try {
    if (typeof original !== "function") {
      return;
    }
    const arityDescriptor = Object.getOwnPropertyDescriptor(original, "length");
    if (!arityDescriptor || typeof arityDescriptor.value !== "number") {
      return;
    }
    Object.defineProperty(wrapper, "length", {
      value: arityDescriptor.value,
      writable: false,
      enumerable: false,
      configurable: true,
    });
  } catch {
    // Defensive: if length is somehow non-configurable, leave it. Failing to
    // copy arity is a minor fidelity loss, never a crash.
  }
}

/*
 * TODO: Add description
 */
function functionGenerator(
  _context,
  identifier,
  original,
  _funcName,
  logCallStack = false,
) {
  /* eslint-disable prefer-rest-params -- `temp` masquerades as the native `original` once exported via exportFunction. Its arity (.length) is restored from the original by copyFunctionArity() below; `arguments` (not rest params) is used purely to forward the variadic call without an unused binding. */
  function temp() {
    let result;
    const callContext = getOriginatingScriptContext(logCallStack);
    logCall(identifier, arguments, callContext);
    try {
      result =
        arguments.length > 0
          ? original.call(this, ...arguments)
          : original.call(this);
    } catch (err) {
      const fakeError = generateErrorObject(err);
      throw fakeError;
    }
    return result;
  }
  /* eslint-enable prefer-rest-params */
  // Match the native function's arity so `fn.length` is not a fingerprint.
  // Set on the source function too (cheap, and `exportFunction` may copy it),
  // but the authoritative copy is on the EXPORTED page-visible function — see
  // instrumentFunction below.
  copyFunctionArity(temp, original);
  return temp;
}

/*
 * TODO: Add description
 */
function instrumentFunction(
  context,
  descriptor,
  identifier,
  pageObject,
  propertyName,
  logCallStack = false,
) {
  const original = descriptor.value;
  const tempFunction = functionGenerator(
    context,
    identifier,
    original,
    propertyName,
    logCallStack,
  );
  const exportedFunction = exportCustomFunction(
    tempFunction,
    context,
    original.name,
  );
  // Restore the native arity (.length) on the PAGE-VISIBLE exported function.
  // `exportFunction` builds a fresh forwarder whose declared arity is 0, so the
  // page would otherwise see `fn.length === 0` where the native function has a
  // specific arity (e.g. getContext.length === 1) — a fingerprint. Defining it
  // here, through the privileged compartment, lands it on the object the page
  // actually inspects.
  copyFunctionArity(exportedFunction, original);
  changeProperty(
    descriptor,
    pageObject,
    propertyName,
    "value",
    exportedFunction,
  );
}

/*
 * Builds a synthetic accessor descriptor for a property that does not yet exist
 * on the target ("honey" property). A closure variable backs a native-shaped
 * get/set pair; ``instrumentGetterSetter`` then wraps both with
 * ``exportFunction`` so the page sees getters/setters that report
 * ``[native code]`` — indistinguishable from a real accessor of that name. This
 * mirrors legacy ``nonExistingPropertiesToInstrument`` (``undefinedPropDesc`` in
 * ``lib/js-instruments.ts``), letting a study capture access to decoy property
 * names a tracker might probe.
 */
function makeNonExistingPropertyDescriptor(): PropertyDescriptor {
  let backingValue: any;
  return {
    get() {
      return backingValue;
    },
    set(value) {
      backingValue = value;
    },
    enumerable: false,
    configurable: true,
  };
}

/*
 * Helper class to perform all needed functionality
 *
 * @param context: the window object that is currently instrumented
 * @param object: child object that shall be instumented
 */
function instrument(context, item, depth, propertyName, newValue = undefined) {
  try {
    const identifier = item.instrumentedName + "." + propertyName;
    const initialPageObject = getPageObjectInContext(
      context.wrappedJSObject,
      item.object,
    );
    const pageObject = getPrototypeByDepth(initialPageObject, depth);
    let descriptor = getPropertyDescriptor(pageObject, propertyName);
    const logSettings: LogSettings = item.logSettings;
    if (descriptor === undefined) {
      // The property does not exist on the target. Only instrument it when the
      // study explicitly opted this name in via nonExistingPropertiesToInstrument
      // (a honey property); otherwise there is nothing to instrument and adding
      // an accessor would be a gratuitous, page-observable artifact.
      const nonExisting = logSettings.nonExistingPropertiesToInstrument || [];
      if (!nonExisting.includes(propertyName)) {
        return;
      }
      descriptor = makeNonExistingPropertyDescriptor();
    }
    if (typeof descriptor.value === "function") {
      instrumentFunction(
        context,
        descriptor,
        identifier,
        pageObject,
        propertyName,
        Boolean(logSettings.logCallStack),
      );
    } else {
      instrumentGetterSetter(
        context,
        descriptor,
        identifier,
        pageObject,
        propertyName,
        newValue,
        logSettings,
      );
    }
  } catch (error) {
    console.error(error);
    console.error(error.stack);
    return;
  }
}

/*
 * Checks if an object was already wrapped
 * Unwrapped objects should be wrapped immediately
 */
const wrappedObjects = new WeakSet();
function needsWrapper(object) {
  if (wrappedObjects.has(object)) {
    return false;
  }
  wrappedObjects.add(object);
  return true;
}

/*
 * Converts a plain data property into an instrumented accessor IN PLACE,
 * capturing its get/set while preserving the stored value. Used by recursive
 * instrumentation for scalar (non-function, non-object) data properties of a
 * page object — mirroring legacy, which routes every property (data or accessor)
 * through an instrumented accessor (``instrumentObjectProperty`` in
 * ``lib/js-instruments.ts``).
 */
function instrumentDataProperty(
  pageObject,
  identifier,
  propertyName,
  logSettings: LogSettings,
) {
  const descriptor = Object.getOwnPropertyDescriptor(pageObject, propertyName);
  if (
    !descriptor ||
    !("value" in descriptor) ||
    descriptor.configurable === false
  ) {
    return;
  }
  let backingValue = descriptor.value;
  Object.defineProperty(pageObject, propertyName, {
    configurable: true,
    enumerable: descriptor.enumerable,
    get() {
      const callContext = getOriginatingScriptContext(logSettings.logCallStack);
      logValue(
        identifier,
        backingValue,
        JSOperation.get,
        callContext,
        logSettings,
      );
      return backingValue;
    },
    set(value) {
      const callContext = getOriginatingScriptContext(logSettings.logCallStack);
      if (
        logSettings.preventSets &&
        (typeof backingValue === "function" ||
          (typeof backingValue === "object" && backingValue !== null))
      ) {
        logValue(
          identifier,
          value,
          JSOperation.set_prevented,
          callContext,
          logSettings,
        );
        return;
      }
      logValue(identifier, value, JSOperation.set, callContext, logSettings);
      backingValue = value;
    },
  });
}

/*
 * Lazily instruments the own properties of an object RETURNED by an
 * instrumented getter, mirroring legacy's ``recursive``/``depth`` semantics
 * (``instrumentObject`` in ``lib/js-instruments.ts``). Unlike a document_start
 * walk, this runs at ACCESS time, so page-built nested objects are reachable.
 * For each own property: functions are wrapped, accessors are instrumented,
 * scalar data properties become instrumented accessors, and nested object values
 * are recursed into with ``depth`` decremented. Every property is instrumented
 * IN PLACE with the same native-looking technique used at the top level, so no
 * new detection surface is introduced beyond the instrumented properties.
 */
function instrumentReturnedObject(
  context,
  instrumentedName,
  pageObject,
  logSettings: LogSettings,
  depth: number,
) {
  if (depth <= 0 || pageObject === null || typeof pageObject !== "object") {
    return;
  }
  if (!needsWrapper(pageObject)) {
    return;
  }
  let propertyNames: string[];
  try {
    propertyNames = Object.getOwnPropertyNames(pageObject);
  } catch {
    return;
  }
  for (const propertyName of propertyNames) {
    if (
      propertyName === "__proto__" ||
      propertyName === "constructor" ||
      logSettings.excludedProperties.includes(propertyName)
    ) {
      continue;
    }
    let descriptor;
    try {
      descriptor = getPropertyDescriptor(pageObject, propertyName);
    } catch {
      continue;
    }
    if (descriptor === undefined) {
      continue;
    }
    const identifier = instrumentedName + "." + propertyName;
    try {
      if (typeof descriptor.value === "function") {
        instrumentFunction(
          context,
          descriptor,
          identifier,
          pageObject,
          propertyName,
          Boolean(logSettings.logCallStack),
        );
      } else if (descriptor.get || descriptor.set) {
        instrumentGetterSetter(
          context,
          descriptor,
          identifier,
          pageObject,
          propertyName,
          undefined,
          logSettings,
        );
      } else if (
        typeof descriptor.value === "object" &&
        descriptor.value !== null
      ) {
        // Recurse one level down into the nested object (legacy recurses on the
        // live nested value before instrumenting the property itself).
        instrumentReturnedObject(
          context,
          identifier,
          descriptor.value,
          logSettings,
          depth - 1,
        );
        // Instrument the property slot too, so reassignments are captured.
        instrumentDataProperty(
          pageObject,
          identifier,
          propertyName,
          logSettings,
        );
      } else {
        instrumentDataProperty(
          pageObject,
          identifier,
          propertyName,
          logSettings,
        );
      }
    } catch (error) {
      console.error(error);
    }
  }
}

function startInstrument(context) {
  for (const item of resolveInstrumentationSettings()) {
    // retrieve Object properties alont the chain
    let propertyCollection;
    try {
      propertyCollection = getObjectProperties(context, item);
    } catch (err) {
      console.error(err);
      continue;
    }
    // Instrument each Property per object/prototype
    if (propertyCollection.length > 0) {
      propertyCollection.forEach(({ depth, propertyNames, object }) => {
        if (needsWrapper(object)) {
          propertyNames.forEach((propertyName) =>
            instrument(context, item, depth, propertyName),
          );
        }
      });
    }
    // Instrument honey ("non-existing") properties: names that do not yet exist
    // on the target. instrument() synthesizes a native-looking accessor for any
    // name listed here (see makeNonExistingPropertyDescriptor). Mirrors legacy's
    // dedicated nonExistingPropertiesToInstrument loop.
    const nonExisting =
      item.logSettings.nonExistingPropertiesToInstrument || [];
    if (nonExisting.length) {
      nonExisting.forEach((propertyName) => {
        if (item.logSettings.excludedProperties.includes(propertyName)) {
          return;
        }
        instrument(context, item, item.depth || 0, propertyName);
      });
    }
    // Instrument properties and overwrite their return value
    if (item.logSettings.overwrittenProperties) {
      item.logSettings.overwrittenProperties.forEach(({ key: name, value }) => {
        const proto = getContextualPrototypeFromString(context, item.object);
        if (proto) {
          const { depth, propertyName } = findPropertyInChain(proto, name);
          instrument(context, item, depth, propertyName, value);
        } else {
          console.error(
            "Could not instrument " +
              item.object +
              ". Encountered undefined object.",
          );
        }
      });
    }
  }
}

export { startInstrument, exportCustomFunction };
