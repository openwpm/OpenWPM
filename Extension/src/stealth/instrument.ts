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

/**
 * Shape of the window object as seen by this content script when a study has
 * injected a custom settings set. Scoped LOCALLY (not a `declare global`
 * augmentation) so it stays an internal detail of this module rather than
 * widening the global `Window` type for the whole codebase.
 */
interface WindowWithStealthSettings {
  openWpmStealthInstrumentSettings?: JSInstrumentSettings;
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
  const injected = (window as unknown as WindowWithStealthSettings)
    .openWpmStealthInstrumentSettings;
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

/**
 * Reads the INTERFACE NAME of a method's receiver (``this``) from the privileged
 * forwarder.
 *
 * Used for shared-prototype (inherited) methods such as
 * ``EventTarget.prototype.addEventListener``: the method is hooked ONCE on the
 * shared prototype, but at call time we want to attribute the call to the
 * concrete interface of the object it was invoked on (e.g. ``HTMLDivElement``,
 * ``XMLHttpRequest``), not to ``EventTarget``.
 *
 * Robustness / undetectability (verified against the Firefox source —
 * ``js/xpconnect/wrappers/XrayWrapper.cpp`` — and measured in a real Firefox
 * run): ``receiver`` is an Xray view of the page object as seen from the
 * privileged content-script compartment. Xray wrappers present a CLEAN NATIVE
 * view of a DOM reflector and hide any page-side modifications (expandos,
 * redefined ``constructor``). So ``Object.getPrototypeOf(receiver).constructor.name``
 * resolves to the native interface name even when the page has redefined
 * ``constructor`` on the instance AND on its prototype — both land in the page's
 * expando chain, which the Xray does not consult. The read is pure reflection on
 * the privileged side: it defines nothing on the page and triggers no page-side
 * getter, so it adds NO new detection surface.
 *
 * We read via the prototype's ``constructor`` first (the native interface
 * prototype carries the genuine constructor), falling back to the instance's own
 * ``constructor`` — both Xray-protected. Returns ``null`` when no interface name
 * can be resolved (e.g. a null-prototype object), in which case the caller does
 * not attribute/emit.
 */
/**
 * PROOF-OF-CONCEPT (ADR-0001 gap #2 — "lose the receiver"):
 *
 * Per-instance receiver attribution held ENTIRELY in the isolated content-script
 * world. The ADR implies that distinguishing two instances of the same interface
 * forces touching/mutating the page object (incompatible with clean
 * prototype-level instrumentation). This WeakMap refutes that by construction:
 *
 *   - The key is the Xray-wrapped page object (`this` at call time), exactly the
 *     value the wrapper already receives for free (functionGenerator's `temp`).
 *   - The map lives in the privileged content-script compartment — NOT on the
 *     page. No own-property is added to the instance, no global is leaked, the
 *     prototype wrapper is byte-for-byte the clean stealth wrapper. So every
 *     detection vector that passes for plain stealth still passes.
 *   - WeakMap holds keys weakly, so instances are not retained against GC.
 *
 * The crux this PoC tests EMPIRICALLY (see test_poc_receiver_attribution): is the
 * Xray wrapper for a given underlying page object STABLE across calls, so the
 * same instance maps to the same id and two distinct instances map to distinct
 * ids? If Xray re-created a fresh wrapper per crossing, the WeakMap key would be
 * unstable and this would not work — that is the obstacle that would VINDICATE
 * the ADR.
 */
const receiverInstanceIds = new WeakMap<object, number>();
let nextReceiverInstanceId = 0;
function getReceiverInstanceId(receiver: any): number | null {
  if (receiver === null || receiver === undefined) {
    return null;
  }
  try {
    let id = receiverInstanceIds.get(receiver as object);
    if (id === undefined) {
      id = nextReceiverInstanceId++;
      receiverInstanceIds.set(receiver as object, id);
    }
    return id;
  } catch {
    // Non-object receiver (primitive) — cannot be a WeakMap key.
    return null;
  }
}

function getReceiverInterfaceName(receiver: any): string | null {
  if (receiver === null || receiver === undefined) {
    return null;
  }
  try {
    const proto = Object.getPrototypeOf(receiver);
    if (
      proto &&
      proto.constructor &&
      typeof proto.constructor.name === "string"
    ) {
      return proto.constructor.name;
    }
  } catch {
    // fall through to the instance-level read
  }
  try {
    if (receiver.constructor && typeof receiver.constructor.name === "string") {
      return receiver.constructor.name;
    }
  } catch {
    return null;
  }
  return null;
}

// For functions
function logCall(
  instrumentedFunctionName,
  args,
  callContext,
  logFunctionsAsStrings = false,
  receiverInterfaces: string[] | undefined = undefined,
  receiver: any = undefined,
) {
  if (inLog) {
    return;
  }
  inLog = true;
  // Interface-attributed capture of a shared-prototype (inherited) method.
  // When ``receiverInterfaces`` is set, the method (e.g.
  // ``EventTarget.prototype.addEventListener``) is hooked once on the shared
  // prototype but should only be RECORDED when invoked on one of the configured
  // interfaces of interest. The recorded ``symbol`` stays STATIC — the shared
  // prototype method (e.g. ``EventTarget.addEventListener``) — and the concrete
  // receiver interface is attributed in a SEPARATE ``receiver`` field
  // (→ ``receiver`` column), leaving ``symbol`` stable across receivers.
  // This is a CONTENT-SCRIPT-SIDE filter: non-targeted receivers are dropped
  // before any record is emitted (no site-wide flood, nothing to discard later).
  // When ``receiverInterfaces`` is absent, ``receiver`` is null and behaviour is
  // unchanged from before.
  let receiverInterface: string | null = null;
  if (receiverInterfaces !== undefined) {
    const interfaceName = getReceiverInterfaceName(receiver);
    if (interfaceName === null || !receiverInterfaces.includes(interfaceName)) {
      inLog = false;
      return;
    }
    // PROOF-OF-CONCEPT: append a per-instance id to the interface name so the
    // `receiver` column distinguishes two instances of the SAME interface
    // (e.g. "XMLHttpRequest#3" vs "XMLHttpRequest#7"). The id is assigned from a
    // content-script-side WeakMap keyed on the Xray-wrapped page object — no
    // page mutation, no detection surface. Stable iff the Xray key is stable.
    const instanceId = getReceiverInstanceId(receiver);
    receiverInterface =
      instanceId === null ? interfaceName : interfaceName + "#" + instanceId;
  }
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
      serialArgs.push(serializeObject(arg, logFunctionsAsStrings));
    }
    const msg = {
      operation: JSOperation.call,
      symbol: instrumentedFunctionName,
      // Concrete receiver interface for shared-prototype (interface-attributed)
      // capture; null for ordinary instrumentation. Flows to the ``receiver``
      // column (see background/javascript-instrument.ts and storage schema).
      receiver: receiverInterface,
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
    // Merge collection elements that resolve to the SAME prototype object into a
    // single element. startInstrument gates instrumentation on needsWrapper(object)
    // — a WeakSet keyed on the prototype object — so two elements sharing one
    // prototype (e.g. several bare-string members of one interface, or a sweep's
    // consolidated shared-prototype entry) would otherwise have only the FIRST
    // element instrumented: the later elements hit the same already-wrapped
    // prototype and are silently skipped. Coalescing by prototype object means the
    // single needsWrapper call covers ALL of that prototype's listed members.
    const byObject = new Map();
    for (const propertyList of propertiesToInstrument) {
      const existing = byObject.get(propertyList.object);
      if (existing) {
        for (const name of propertyList.propertyNames) {
          if (!existing.propertyNames.includes(name)) {
            existing.propertyNames.push(name);
          }
        }
      } else {
        byObject.set(propertyList.object, propertyList);
      }
    }
    propertiesToInstrument = Array.from(byObject.values());
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
 * Export an instrumented accessor/method into the page compartment under its
 * spec-prefixed native name ("get <prop>" / "set <prop>") and install it on the
 * page object via `changeProperty`, so the page-visible function's `.name`
 * matches native and no detection tell is left behind.
 */

function injectFunction(
  instrumentedFunction,
  descriptor,
  functionType,
  pageObject,
  propertyName,
) {
  // Export with the spec-prefixed native name ("get <prop>" / "set <prop>") so
  // the PAGE-VISIBLE accessor matches native. `exportFunction` builds a fresh
  // forwarder in the page compartment and names it via `defineAs`; passing the
  // bare property name there would leave the page seeing `descriptor.get.name ===
  // "name"` where the native accessor reports "get name" — a one-line detector
  // latent on EVERY wrapped accessor. (`defineAs` is the only hook that names the
  // page-side forwarder; redefining `.name` on the privileged Xray reference
  // afterwards does NOT propagate to the page's view of the function.)
  const exportedFunction = exportCustomFunction(
    instrumentedFunction,
    window,
    functionType + " " + propertyName,
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
  _context,
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
 *
 * FOOTGUN (own-vs-inherited): the `descriptor` passed in may have been resolved
 * by `getPropertyDescriptor`, which walks UP the prototype chain — but this
 * installs it as an OWN property of `pageObject`. When `pageObject` is the exact
 * object that natively carries the property (the common case, and true for every
 * bundled-default entry), own-on-`pageObject` matches native. But a CUSTOM
 * `stealth_js_instrument_settings` entry whose `depth` resolves `pageObject` to
 * an object where the property is INHERITED (not own) would make
 * `pageObject.hasOwnProperty(name)` / `Reflect.ownKeys` / `getOwnPropertyDescriptor`
 * diverge from native — a page-observable tell. Author custom settings so each
 * instrumented property's `depth` lands on the object that genuinely OWNS it.
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

  // Guard on the accessor actually BEING a function, not merely on the
  // descriptor key existing. Object.getOwnPropertyDescriptor returns an accessor
  // descriptor with BOTH `get` and `set` keys present, even for a getter-only
  // property (e.g. window.localStorage / window.sessionStorage), where `set` is
  // `undefined`. A `hasOwnProperty(descriptor, "set")` check is therefore true
  // for such properties and would inject a synthetic setter where the native
  // accessor has none — a page-observable artifact (native localStorage has no
  // setter). Checking `typeof === "function"` instruments only the accessors the
  // native property genuinely exposes.
  if (typeof descriptor[getFuncType] === "function") {
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
  if (typeof descriptor[setFuncType] === "function") {
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
 * Build the replacement function for an instrumented method: it logs each call
 * (filtered by `receiverInterfaces` for shared-prototype methods), forwards the
 * call to the original with the page's `this` and arguments, and re-raises any
 * thrown error as a page-compartment object stripped of extension frames.
 */
function functionGenerator(
  _context,
  identifier,
  original,
  _funcName,
  logCallStack = false,
  logFunctionsAsStrings = false,
  receiverInterfaces: string[] | undefined = undefined,
) {
  /* eslint-disable prefer-rest-params -- `temp` masquerades as the native `original` once exported via exportFunction. Its native arity (.length) comes from the codegen forwarder built below (makeArityForwarder); `arguments` (not rest params) is used purely to forward the variadic call without an unused binding. */
  function temp() {
    let result;
    const callContext = getOriginatingScriptContext(logCallStack);
    logCall(
      identifier,
      arguments,
      callContext,
      logFunctionsAsStrings,
      receiverInterfaces,
      this,
    );
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
  // Wrap `temp` in a forwarder that NATIVELY declares the same number of
  // parameters as `original`, so the forwarder's OWN `.length` equals the native
  // arity. Xray computes a function's page-visible `.length` from the underlying
  // target, so a privileged-side `Object.defineProperty` redefine does NOT reach
  // the page — only the target's real declared arity does.
  const arity = getNativeArity(original);
  return makeArityForwarder(temp, arity);
}

/*
 * Read a native function's declared arity (.length) defensively. Returns 0 for
 * anything that is not a function or has no numeric `length`.
 */
function getNativeArity(original: unknown): number {
  try {
    if (typeof original !== "function") {
      return 0;
    }
    const d = Object.getOwnPropertyDescriptor(original, "length");
    return d && typeof d.value === "number" ? d.value : 0;
  } catch {
    return 0;
  }
}

// Upper bound on the parameter count we synthesize for a forwarder. No real DOM
// function approaches this; it only guards against a pathological/huge declared
// arity (e.g. a polyfill with a bogus `.length`) forcing us to codegen a huge
// parameter list. A value beyond the bound is clamped DOWN to the bound — never
// to 0 — so the page-visible `.length` is never mis-reported as 0 (which would
// itself be a detectable fingerprint).
const MAX_FORWARDER_ARITY = 256;

/*
 * Build a forwarder that NATIVELY declares `arity` parameters and delegates
 * every call (this + all args) to `impl`. The returned function's own `.length`
 * is `arity` by construction, so once exported via `exportFunction` the page
 * sees the native arity through Xray (which reads `.length` from the target).
 * Uses the `Function` constructor so the parameter count is real, not a
 * redefined property.
 */
const arityForwarderCache: Record<number, (impl: unknown) => unknown> = {};
function makeArityForwarder(impl: unknown, arity: number): unknown {
  if (!Number.isInteger(arity) || arity < 0) {
    arity = 0;
  } else if (arity > MAX_FORWARDER_ARITY) {
    arity = MAX_FORWARDER_ARITY;
  }
  let factory = arityForwarderCache[arity];
  if (!factory) {
    const params = [];
    for (let i = 0; i < arity; i++) {
      params.push("a" + i);
    }
    /* eslint-disable no-new-func -- the generated forwarder must declare exactly
       `arity` named params so its NATIVE `.length` matches the wrapped function;
       a redefined `.length` does not survive Xray. `arguments` forwards the real
       (possibly variadic) call. The script is a fixed template over an integer
       arity (0..MAX_FORWARDER_ARITY), never page-controlled input. */
    factory = new Function(
      "__impl",
      "return function (" +
        params.join(", ") +
        ") { return __impl.apply(this, arguments); };",
    ) as (impl: unknown) => unknown;
    /* eslint-enable no-new-func */
    arityForwarderCache[arity] = factory;
  }
  return factory(impl);
}

/*
 * Instrument a method on a page object: generate the logging replacement via
 * `functionGenerator` and inject it in place of the original with `injectFunction`,
 * preserving the native name and arity so the wrapped method is indistinguishable
 * from the original.
 */
function instrumentFunction(
  context,
  descriptor,
  identifier,
  pageObject,
  propertyName,
  logCallStack = false,
  logFunctionsAsStrings = false,
  receiverInterfaces: string[] | undefined = undefined,
) {
  const original = descriptor.value;
  const tempFunction = functionGenerator(
    context,
    identifier,
    original,
    propertyName,
    logCallStack,
    logFunctionsAsStrings,
    receiverInterfaces,
  );
  const exportedFunction = exportCustomFunction(
    tempFunction,
    context,
    original.name,
  );
  // Native arity (.length) is carried by the codegen forwarder built in
  // functionGenerator: `exportFunction` reflects the target's REAL declared
  // parameter count through Xray, so the page sees the correct `.length` without
  // any page-side `Object.defineProperty` (which does not cross Xray anyway).
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
 * on the target (a non-existing property). A closure variable backs a native-shaped
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
      // (a non-existing property); otherwise there is nothing to instrument and adding
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
        Boolean(logSettings.logFunctionsAsStrings),
        // Interface-attributed shared-prototype capture: when the entry carries
        // receiverInterfaces, only calls whose receiver interface is in the set
        // are recorded. The recorded ``symbol`` stays the STATIC shared-prototype
        // method ("<owner>.<method>", e.g. "EventTarget.addEventListener"); the
        // concrete receiver interface is written to the separate ``receiver``
        // column. Absent → unchanged (receiver is null, every call recorded).
        logSettings.receiverInterfaces,
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

function startInstrument(context) {
  for (const item of resolveInstrumentationSettings()) {
    // retrieve Object properties along the chain
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
    // Instrument non-existing properties: names that do not yet exist
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
