import { jsInstrumentationSettings as defaultSettings } from "./settings";
import {
  filterExtensionFrames,
  getBeginOfScriptCalls,
  getStackTrace,
} from "./error";
import {
  JSInstrumentSettings,
  LogSettings,
  SettingsObjects,
} from "../types/js_instrument_settings";
import { getHost } from "./host";

/**
 * Resolves the stealth instrumentation settings.
 *
 * When a study configures a custom set the host supplies it (an empty list
 * means an empty surface); when it does not, fall back to the bundled default
 * (``settings.ts``), so the out-of-the-box behaviour is the curated
 * fingerprinting surface.
 */
function resolveInstrumentationSettings(): JSInstrumentSettings {
  const injected = getHost().settings();
  return injected !== undefined ? injected : defaultSettings;
}

// Captured from the instrument's sandbox at load: page script can neither
// observe nor replace them.
const reflectApply = Reflect.apply;
const functionToString = Function.prototype.toString;
const objectToString = Object.prototype.toString;

type Invoker = (thisArg: unknown, args: ArrayLike<unknown>) => any;

// Accessors of non-existing properties: sandbox functions, not page natives.
const ownAccessors = new WeakSet<object>();

/**
 * A caller for the page native ``original``, or undefined if there is none.
 *
 * Never a reference held by this sandbox: Firefox cuts the wrappers a
 * privileged compartment holds into a window shortly after that window is
 * destroyed, which would break every member a page took from a removed frame.
 * The host pins the native in a compartment Firefox leaves alone. Arguments are
 * unpacked here, so no sandbox object reaches the native.
 */
// The page's window, through the waiver; set when the realm is instrumented.
let pageGlobal: any;
const SANDBOX_ERROR = new Error();
const PAGE_ERROR_NAMES = [
  "InternalError",
  "RangeError",
  "TypeError",
  "ReferenceError",
  "SyntaxError",
  "EvalError",
  "URIError",
];

/**
 * ``error`` itself, unless it was created in one of the instrument's own realms
 * (this sandbox, or the one natives are called from: near the stack limit the
 * call itself throws there). Such an error is replaced by the page-realm error
 * of the same name and message, so the page never holds an object of either.
 */
function toPageError(error: unknown): unknown {
  try {
    if (
      typeof error !== "object" ||
      error === null ||
      !(error instanceof Error || getHost().isPinnerError(error))
    ) {
      return error;
    }
    const name = String((error as any).name);
    const Ctor = PAGE_ERROR_NAMES.includes(name)
      ? pageGlobal[name]
      : pageGlobal.Error;
    return new Ctor(String((error as any).message));
  } catch {
    // Near the stack limit the checks above can fail too; a sandbox error
    // reaches the page as the boundary's own DOMException, never as itself.
    return SANDBOX_ERROR;
  }
}

function pinNative(original: unknown): Invoker | undefined {
  if (typeof original !== "function") {
    return undefined;
  }
  if (ownAccessors.has(original)) {
    return (thisArg, args) => reflectApply(original as any, thisArg, args);
  }
  const pinned = getHost().pinNative(original);
  return (thisArg, args) =>
    reflectApply(pinned as any, undefined, [thisArg, ...Array.from(args)]);
}

// Counter to cap # of calls logged for each script/api combination
const maxLogCount = 500;
// logCounter
const logCounter: { [key: string]: number } = {};
// To keep track of the original order of events
let ordinal = 0;

// Options for JSOperation
const JSOperation = {
  call: "call",
  get: "get",
  get_function: "get(function)",
  set: "set",
  set_prevented: "set(prevented)",
};

// from http://stackoverflow.com/a/5202185
function rsplit(source: string, sep: string, maxsplit: number) {
  const split = source.split(sep);
  return maxsplit
    ? [split.slice(0, -maxsplit).join(sep)].concat(split.slice(-maxsplit))
    : split;
}

// Page objects arrive as Xrays and are never waived. Plain objects, arrays and
// typed arrays are copied from own enumerable data properties, so recording
// runs no page getter, toJSON or Proxy trap; the Xray hides entries whose
// values are functions, accessors or Proxies. Every other object is recorded as
// its brand ("[object Storage]"): reading a host object's named properties can
// change its state. Symbols and BigInts become strings.
// The page chooses the arguments' size, so the object arguments of one call
// share a budget of MAX_SERIALIZED_VALUES values, MAX_SERIALIZED_DEPTH deep,
// and strings of at most MAX_SERIALIZED_STRING characters; the rest is
// TRUNCATED.
const MAX_SERIALIZED_VALUES = 128;
const MAX_SERIALIZED_DEPTH = 16;
const MAX_SERIALIZED_STRING = 65536;
const TRUNCATED = "TRUNCATED";
const TYPED_ARRAY_BRAND =
  /^\[object (Big)?(Int|Uint|Float)\d+(Clamped)?Array\]$/;
function truncate(value: string): string {
  return value.length > MAX_SERIALIZED_STRING
    ? value.slice(0, MAX_SERIALIZED_STRING) + TRUNCATED
    : value;
}
interface SerializationState {
  seen: Set<unknown>;
  budget: number;
}
function newSerializationState(): SerializationState {
  return { seen: new Set(), budget: MAX_SERIALIZED_VALUES };
}

function toPlainData(
  value: any,
  stringifyFunctions: boolean,
  state: SerializationState,
  depth = 0,
): any {
  if (state.budget <= 0 || depth > MAX_SERIALIZED_DEPTH) {
    state.budget = 0;
    return TRUNCATED;
  }
  state.budget--;
  if (value === null) {
    return "null";
  }
  if (typeof value === "symbol") {
    return String(value);
  }
  if (typeof value === "bigint") {
    return value + "n";
  }
  if (typeof value === "function") {
    return stringifyFunctions
      ? truncate(reflectApply(functionToString, value, []))
      : "FUNCTION";
  }
  if (typeof value === "string") {
    return truncate(value);
  }
  if (typeof value !== "object") {
    return value;
  }
  // An opaque Xray shows a Proxy as an empty object or array.
  if (getHost().isProxy(value)) {
    return "[object Proxy]";
  }
  if (value instanceof HTMLElement) {
    return getPathToDomElement(value);
  }
  const isArray = Array.isArray(value);
  const brand = reflectApply(objectToString, value, []);
  const isTypedArray = TYPED_ARRAY_BRAND.test(brand);
  if (!isArray && !isTypedArray && brand !== "[object Object]") {
    return brand;
  }
  // Prevent serialization cycles
  if (state.seen.has(value)) {
    return typeof value;
  }
  state.seen.add(value);
  const copy: any = isArray ? [] : {};
  // Indices are not listed: Object.keys would cost the length.
  const keys =
    isArray || isTypedArray
      ? Array.from(
          { length: Math.min(value.length, state.budget + 1) },
          (_, i) => String(i),
        )
      : Object.keys(value);
  for (const key of keys) {
    if (state.budget <= 0) {
      copy[key] = TRUNCATED;
      break;
    }
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (descriptor && "value" in descriptor) {
      copy[truncate(key)] = toPlainData(
        descriptor.value,
        stringifyFunctions,
        state,
        depth + 1,
      );
    }
  }
  return copy;
}

// Top-level arguments that are not objects cost no budget, so a large argument
// does not blank the ones after it.
function serializeObject(
  object: any,
  stringifyFunctions: boolean,
  state: SerializationState = newSerializationState(),
) {
  // Handle permissions errors
  try {
    if (object === null) {
      return "null";
    }
    if (typeof object === "function") {
      return stringifyFunctions
        ? truncate(reflectApply(functionToString, object, []))
        : "FUNCTION";
    }
    if (typeof object !== "object") {
      return toPlainData(object, stringifyFunctions, newSerializationState());
    }
    if (state.budget <= 0) {
      return TRUNCATED;
    }
    return JSON.stringify(toPlainData(object, stringifyFunctions, state));
  } catch (error) {
    console.log("OpenWPM: SERIALIZATION ERROR: " + error);
    return "SERIALIZATION ERROR: " + error;
  }
}

// Module-local, not on any Object: the page could observe them there
// (``no_instrument_helpers_leaked``).
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

function updateCounterAndCheckIfOver(scriptUrl: string, symbol: string) {
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
function getPathToDomElement(element: any): string | undefined {
  if (element === element.ownerDocument?.body) {
    return element.tagName;
  }
  if (element.parentNode === null) {
    return "NULL/" + element.tagName;
  }

  let siblingIndex = 1;
  const siblings = element.parentNode.childNodes;
  for (const sibling of siblings) {
    if (sibling === element) {
      let path = getPathToDomElement(element.parentNode);
      path += "/" + element.tagName + "[" + siblingIndex;
      path += "," + element.id;
      path += "," + element.className;
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
  return undefined;
}

function getOriginatingScriptContext(getCallStack: boolean) {
  const trace = getStackTrace().trim().split("\n");
  const traceStart = getBeginOfScriptCalls(trace);
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
    // Names and URLs may both contain "@"; whatever follows the first one
    // still ends in the frame's real location.
    const at = callSite.indexOf("@");
    if (at === -1) {
      return empty_context;
    }
    const funcName = callSite.slice(0, at);
    const items = rsplit(callSite.slice(at + 1), ":", 2);
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
      // Page frames only: the page can call back into instrumented APIs,
      // interleaving the instrument's frames. Built only for a record that
      // is under the cap.
      get callStack() {
        return getCallStack
          ? filterExtensionFrames(trace.slice(traceStart)).join("\n").trim()
          : "";
      },
    };
    return callContext;
  } catch (e) {
    console.log(
      "OpenWPM: Error parsing the script context",
      (e as Error).toString(),
      callSite,
    );
    return empty_context;
  }
}

function deliver(
  type: string,
  scriptUrl: string,
  symbol: string,
  build: () => any,
) {
  if (!updateCounterAndCheckIfOver(scriptUrl, symbol)) {
    send(type, build());
  }
}

function send(type: string, msg: any) {
  msg.ordinal = ordinal++;
  notify(type, msg);
}

// For gets, sets, etc. on a single value
function logValue(
  instrumentedVariableName: string,
  value: any,
  operation: string, // from JSOperation object please
  callContext: any,
  logSettings: LogSettings,
) {
  deliver("logValue", callContext.scriptUrl, instrumentedVariableName, () => ({
    operation,
    symbol: instrumentedVariableName,
    value: serializeObject(value, logSettings.logFunctionsAsStrings),
    scriptUrl: callContext.scriptUrl,
    scriptLine: callContext.scriptLine,
    scriptCol: callContext.scriptCol,
    funcName: callContext.funcName,
    scriptLocEval: callContext.scriptLocEval,
    callStack: callContext.callStack,
  }));
}

/**
 * The interface name of a method's receiver, or null. Read through the Xray,
 * which shows the native ``constructor`` whatever the page redefined, and runs
 * no page getter.
 */
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
  instrumentedFunctionName: any,
  args: any,
  callContext: any,
  logFunctionsAsStrings = false,
  receiverInterfaces: string[] | undefined = undefined,
  receiver: any = undefined,
) {
  // With ``receiverInterfaces``, a method hooked once on a shared prototype is
  // recorded only for receivers of those interfaces; the symbol stays the
  // shared one and the receiver's interface goes to the ``receiver`` column.
  let receiverInterface: string | null = null;
  if (receiverInterfaces !== undefined) {
    const interfaceName = getReceiverInterfaceName(receiver);
    if (interfaceName === null || !receiverInterfaces.includes(interfaceName)) {
      return;
    }
    receiverInterface = interfaceName;
  }
  deliver("logCall", callContext.scriptUrl, instrumentedFunctionName, () => {
    // One budget for all arguments, however many the page passes.
    const state = newSerializationState();
    const serialArgs = [];
    for (const arg of args) {
      serialArgs.push(serializeObject(arg, logFunctionsAsStrings, state));
    }
    return {
      operation: JSOperation.call,
      symbol: instrumentedFunctionName,
      receiver: receiverInterface,
      args: serialArgs,
      value: "",
      scriptUrl: callContext.scriptUrl,
      scriptLine: callContext.scriptLine,
      scriptCol: callContext.scriptCol,
      funcName: callContext.funcName,
      scriptLocEval: callContext.scriptLocEval,
      callStack: callContext.callStack,
    };
  });
}

/**
 * Provides the properties per prototype object.
 *
 * The three helpers below (``getPrototypeByDepth``, ``getPropertyNamesPerDepth``,
 * ``findPropertyInChain``) are module-local functions: defining them on a
 * prototype would be observable to a hostile page (see the
 * ``no_instrument_helpers_leaked`` detection vector).
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
  let properties: string[];
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
function getPropertyKeysToOverwrite(item: SettingsObjects) {
  const res: any[] = [];
  (item.logSettings.overwrittenProperties || []).forEach((obj: any) => {
    res.push(obj.key);
  });
  return res;
}

/**
 * Prepares a list of properties that need to be instrumented
 * Here, this can be a previous created list (settings.js: propertiesToInstrument)
 * or all properties of a given object (settings.js: propertiesToInstrument is empty)
 */
function getObjectProperties(
  context: any,
  item: SettingsObjects,
  pageObjectAt: (depth: number) => any,
) {
  // Normalised below to {depth, propertyNames, object} entries.
  let propertiesToInstrument: any = item.logSettings.propertiesToInstrument;
  const root = getPageObjectInContext(context, item.object);
  if (!root) {
    throw Error("Object " + item.object + " was undefined.");
  }

  if (propertiesToInstrument === undefined || !propertiesToInstrument.length) {
    propertiesToInstrument = getPropertyNamesPerDepth(root, item.depth);
    // filter excluded and overwritten properties
    const excluded = getPropertyKeysToOverwrite(item).concat(
      item.logSettings.excludedProperties,
    );
    propertiesToInstrument = filterPropertiesPerDepth(
      propertiesToInstrument,
      excluded,
    );
  } else {
    // Copies: the list may be the shared default surface, which must not
    // collect this realm's objects.
    propertiesToInstrument = propertiesToInstrument.map((propertyList: any) =>
      typeof propertyList === "string"
        ? { depth: 0, propertyNames: [propertyList] }
        : { ...propertyList, propertyNames: [...propertyList.propertyNames] },
    );
    const excluded = getPropertyKeysToOverwrite(item).concat(
      item.logSettings.excludedProperties,
    );
    propertiesToInstrument = filterPropertiesPerDepth(
      propertiesToInstrument,
      excluded,
    );
  }
  // The object each depth installs on, which is also what claims are keyed by.
  propertiesToInstrument.forEach((propertyList: any) => {
    propertyList.object = pageObjectAt(propertyList.depth);
  });
  return propertiesToInstrument;
}

function notify(type: any, content: any) {
  content.timeStamp = new Date().toISOString();
  getHost().send(type, content);
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
// One page-compartment object per realm receives every `defineAs`; the page
// never reaches it.
let exportTarget: any;
function exportCustomFunction(func: any, context: any, name: any) {
  exportTarget ??= context.wrappedJSObject.Object.create(null);
  const exportedTry = getHost().exportFunction(func, exportTarget, {
    allowCrossOriginArguments: true,
    defineAs: name,
  });
  return exportedTry;
}

/*
 * Export an instrumented accessor into the page compartment under its
 * spec-prefixed native name ("get <prop>" / "set <prop>"): `defineAs` is the
 * only hook that names the page-side forwarder, and a bare property name would
 * leave `descriptor.get.name === "name"` where the native reports "get name".
 * The accessor literal already declares the native arity (0 or 1).
 */
function exportAccessor(
  context: any,
  accessor: any,
  functionType: "get" | "set",
  propertyName: any,
) {
  return exportCustomFunction(
    accessor,
    context,
    functionType + " " + propertyName,
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
  identifier: string,
  original: Invoker,
  newValue: any,
  object: any,
  logSettings: LogSettings,
) {
  const originalValue = original(object, []);
  const returnValue = newValue !== undefined ? newValue : originalValue;
  try {
    logGet(identifier, returnValue, logSettings);
  } catch {
    // never surface instrumentation failures
  }
  return returnValue;
}

function logGet(
  identifier: string,
  returnValue: any,
  logSettings: LogSettings,
) {
  const callContext = getOriginatingScriptContext(
    Boolean(logSettings.logCallStack),
  );
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
    return;
  }
  logValue(identifier, returnValue, JSOperation.get, callContext, logSettings);
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
  identifier: string,
  original: Invoker,
  originalGetter: Invoker | undefined,
  newValue: any,
  object: any,
  logSettings: LogSettings,
) {
  let prevented = false;
  if (logSettings.preventSets && originalGetter) {
    let currentValue;
    try {
      currentValue = originalGetter(object, []);
    } catch {
      currentValue = undefined;
    }
    const t = typeof currentValue;
    prevented = t === "function" || (t === "object" && currentValue !== null);
  }
  try {
    logValue(
      identifier,
      newValue,
      prevented ? JSOperation.set_prevented : JSOperation.set,
      getOriginatingScriptContext(Boolean(logSettings.logCallStack)),
      logSettings,
    );
  } catch {
    // never surface instrumentation failures
  }
  if (prevented) {
    return newValue;
  }
  return original(object, [newValue]);
}

/*
 * Creates a getter function
 *
 * @param descriptor: the descriptor of the original function
 * @param funcName: Name of property/function that shall be overwritten
 * @param newValue: in Case the value shall be changed
 */
function generateGetter(
  identifier: string,
  descriptor: any,
  propertyName: any,
  newValue = undefined,
  logSettings: LogSettings,
) {
  const original = pinNative(descriptor.get)!;
  return Object.getOwnPropertyDescriptor(
    {
      get [propertyName]() {
        try {
          return instrumentGetObjectProperty(
            identifier,
            original,
            newValue,
            this,
            logSettings,
          );
        } catch (error) {
          throw toPageError(error);
        }
      },
    },
    propertyName,
  )!.get;
}

/*
 * Creates a setter function
 *
 * @param descriptor: the descriptor of the original function
 * @param funcName: Name of property/function that shall be overwritten
 * @param newValue: in Case the value shall be changed
 */
function generateSetter(
  identifier: string,
  descriptor: any,
  propertyName: any,
  logSettings: LogSettings,
) {
  const original = pinNative(descriptor.set)!;
  // The native getter is captured so the setter can type-check the current
  // value when preventSets is enabled (see instrumentSetObjectProperty).
  const originalGetter = logSettings.preventSets
    ? pinNative(descriptor.get)
    : undefined;
  return Object.getOwnPropertyDescriptor(
    {
      set [propertyName](value: any) {
        try {
          instrumentSetObjectProperty(
            identifier,
            original,
            originalGetter,
            value,
            this,
            logSettings,
          );
        } catch (error) {
          throw toPageError(error);
        }
      },
    },
    propertyName,
  )!.set;
}

/*
 * Retrieves an object in a context
 *
 * @param context: the window object that is currently instrumented
 * @param object: the subobject needed
 */
function getPageObjectInContext(context: any, context_object: any) {
  const object = context[context_object];
  return object?.prototype || object;
}

/*
 * Entry point to creates (g/s)etter functions,
 * instrument them and inject them to the page
 * context
 */
function instrumentGetterSetter(
  context: any,
  descriptor: any,
  identifier: string,
  pageObject: any,
  propertyName: any,
  newValue = undefined,
  logSettings: LogSettings,
) {
  // A getter-only property's descriptor still has a `set` key (undefined): only
  // the accessors the native property exposes are replaced, so no synthetic
  // setter appears (native localStorage has none).
  const get =
    typeof descriptor.get === "function"
      ? exportAccessor(
          context,
          generateGetter(
            identifier,
            descriptor,
            propertyName,
            newValue,
            logSettings,
          ),
          "get",
          propertyName,
        )
      : undefined;
  const set =
    typeof descriptor.set === "function"
      ? exportAccessor(
          context,
          generateSetter(identifier, descriptor, propertyName, logSettings),
          "set",
          propertyName,
        )
      : undefined;
  if (get) {
    descriptor.get = get;
  }
  if (set) {
    descriptor.set = set;
  }
  Object.defineProperty(pageObject, propertyName, descriptor);
}

/*
 * Build the replacement function for an instrumented method: it logs each call
 * (filtered by `receiverInterfaces` for shared-prototype methods) and forwards
 * the call to the original with the page's `this` and arguments.
 *
 * Exceptions from the original are page-realm objects (the native runs in the
 * page realm) and propagate untouched: exportFunction hands page-realm
 * exceptions back to the page as the identical object. Logging failures are
 * swallowed so they can never surface to the page.
 */
function functionGenerator(
  identifier: string,
  original: any,
  logCallStack = false,
  logFunctionsAsStrings = false,
  receiverInterfaces: string[] | undefined = undefined,
) {
  const invoke = pinNative(original)!;
  /* eslint-disable prefer-rest-params -- the page-visible arity comes from makeArityForwarder; `arguments` forwards the variadic call. */
  function temp(this: any) {
    try {
      logCall(
        identifier,
        arguments,
        getOriginatingScriptContext(logCallStack),
        logFunctionsAsStrings,
        receiverInterfaces,
        this,
      );
    } catch {
      // never surface instrumentation failures
    }
    try {
      return invoke(this, arguments);
    } catch (error) {
      throw toPageError(error);
    }
  }
  /* eslint-enable prefer-rest-params */
  const arity = getNativeArity(original);
  return makeArityForwarder(temp, arity);
}

/** Throws before touching `f` unless `f` is a constructor. */
function isConstructor(f: unknown): boolean {
  try {
    Reflect.construct(String, [], f as any);
    return true;
  } catch {
    return false;
  }
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

// Bounds the generated parameter list; no native function comes close.
const MAX_FORWARDER_ARITY = 256;

/*
 * A forwarder to `impl` that declares `arity` parameters, so the function
 * exportFunction derives from it has the native `.length`. A method definition,
 * so it is not a constructor.
 */
const arityForwarderCache: Record<
  number,
  (impl: unknown, apply: typeof Reflect.apply) => unknown
> = {};
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
    /* eslint-disable no-new-func -- a fixed template over an integer arity. */
    factory = new Function(
      "__impl",
      "__apply",
      "return ({ f(" +
        params.join(", ") +
        ") { return __apply(__impl, this, arguments); } }).f;",
    ) as (impl: unknown, apply: typeof Reflect.apply) => unknown;
    /* eslint-enable no-new-func */
    arityForwarderCache[arity] = factory;
  }
  return factory(impl, reflectApply);
}

/* Replaces a method with its instrumented forwarder, named after the native. */
function instrumentFunction(
  context: any,
  descriptor: any,
  identifier: string,
  pageObject: any,
  propertyName: any,
  logCallStack = false,
  logFunctionsAsStrings = false,
  receiverInterfaces: string[] | undefined = undefined,
) {
  const original = descriptor.value;
  const tempFunction = functionGenerator(
    identifier,
    original,
    logCallStack,
    logFunctionsAsStrings,
    receiverInterfaces,
  );
  const exportedFunction = exportCustomFunction(
    tempFunction,
    context,
    original.name,
  );
  descriptor.value = exportedFunction;
  Object.defineProperty(pageObject, propertyName, descriptor);
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
  const descriptor: PropertyDescriptor = {
    get() {
      return backingValue;
    },
    set(value) {
      backingValue = value;
    },
    enumerable: false,
    configurable: true,
  };
  ownAccessors.add(descriptor.get!);
  ownAccessors.add(descriptor.set!);
  return descriptor;
}

/*
 * Helper class to perform all needed functionality
 *
 * @param context: the window object that is currently instrumented
 * @param object: child object that shall be instumented
 */
function instrument(
  context: any,
  item: SettingsObjects,
  pageObjectAt: (depth: number) => any,
  depth: any,
  propertyName: any,
  newValue: any = undefined,
): boolean {
  // Replacing a prototype's `constructor` breaks `x.constructor === X`.
  if (propertyName === "constructor") {
    return false;
  }
  try {
    const identifier = item.instrumentedName + "." + propertyName;
    const pageObject = pageObjectAt(depth);
    const ownDescriptor = Object.getOwnPropertyDescriptor(
      pageObject,
      propertyName,
    );
    let descriptor =
      ownDescriptor ?? getPropertyDescriptor(pageObject, propertyName);
    const logSettings: LogSettings = item.logSettings;
    if (descriptor !== undefined && ownDescriptor === undefined) {
      // Installing an inherited property as own would change
      // hasOwnProperty/ownKeys on `pageObject`: a custom entry's `depth` must
      // land on the object that owns it.
      console.error(
        "OpenWPM stealth: refusing to instrument inherited property '" +
          propertyName +
          "' as an own property — the configured `depth` resolved to an " +
          "object that does not natively own it, which would be " +
          "page-detectable. Fix the entry's `depth` to land on the owning " +
          "object.",
      );
      return false;
    }
    if (descriptor === undefined) {
      // The property does not exist on the target. Only instrument it when the
      // study explicitly opted this name in via nonExistingPropertiesToInstrument
      // (a non-existing property); otherwise there is nothing to instrument and adding
      // an accessor would be a gratuitous, page-observable artifact.
      const nonExisting = logSettings.nonExistingPropertiesToInstrument || [];
      if (!nonExisting.includes(propertyName)) {
        return false;
      }
      descriptor = makeNonExistingPropertyDescriptor();
    }
    if (typeof descriptor.value === "function") {
      if (newValue !== undefined) {
        console.error(
          "OpenWPM stealth: refusing to overwrite method '" +
            identifier +
            "' — overwrittenProperties replaces a property's value on read " +
            "and applies to accessors only.",
        );
        return false;
      }
      if (isConstructor(descriptor.value)) {
        // The forwarder cannot be constructed and has no `prototype`.
        console.error(
          "OpenWPM stealth: refusing to instrument constructor '" +
            identifier +
            "' — the instrumented replacement could not be called with " +
            "`new`, which would break the page. Instrument its prototype's " +
            "members instead.",
        );
        return false;
      }
      instrumentFunction(
        context,
        descriptor,
        identifier,
        pageObject,
        propertyName,
        Boolean(logSettings.logCallStack),
        Boolean(logSettings.logFunctionsAsStrings),
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
    return true;
  } catch (error) {
    console.error(error);
    console.error((error as Error).stack);
    return false;
  }
}

/*
 * Records which properties of which page objects are already instrumented, so
 * a property is wrapped once even when several settings entries (or repeated
 * frame interception) resolve to the same prototype. The first entry claiming a
 * property supplies its label and log settings; other entries still instrument
 * the remaining properties of that prototype.
 */
const instrumentedProperties = new WeakMap<object, Set<string>>();
function claimProperty(object: any, propertyName: string) {
  let claimed = instrumentedProperties.get(object);
  if (!claimed) {
    claimed = new Set();
    instrumentedProperties.set(object, claimed);
  }
  if (claimed.has(propertyName)) {
    return false;
  }
  claimed.add(propertyName);
  return true;
}

/** The page object an entry installs on at each depth, resolved once. */
function pageObjectsOf(
  context: any,
  item: SettingsObjects,
): (depth: number) => any {
  const byDepth = new Map<number, any>();
  let root: any;
  return (depth) => {
    if (!byDepth.has(depth)) {
      root ??= getPageObjectInContext(context.wrappedJSObject, item.object);
      byDepth.set(depth, getPrototypeByDepth(root, depth));
    }
    return byDepth.get(depth);
  };
}

function startInstrument(context: any) {
  pageGlobal = context.wrappedJSObject;
  for (const item of resolveInstrumentationSettings()) {
    const pageObjectAt = pageObjectsOf(context, item);
    // retrieve Object properties along the chain
    let propertyCollection;
    try {
      propertyCollection = getObjectProperties(context, item, pageObjectAt);
    } catch (err) {
      console.error(err);
      continue;
    }
    let covered = 0;
    // Instrument each Property per object/prototype
    if (propertyCollection.length > 0) {
      propertyCollection.forEach(
        ({
          depth,
          propertyNames,
          object,
        }: {
          depth: any;
          propertyNames: any;
          object: any;
        }) => {
          propertyNames.forEach((propertyName: any) => {
            if (
              !claimProperty(object, propertyName) ||
              instrument(context, item, pageObjectAt, depth, propertyName)
            ) {
              covered++;
            }
          });
        },
      );
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
        if (
          instrument(context, item, pageObjectAt, item.depth || 0, propertyName)
        ) {
          covered++;
        }
      });
    }
    // Instrument properties and overwrite their return value
    if (item.logSettings.overwrittenProperties) {
      item.logSettings.overwrittenProperties.forEach(({ key: name, value }) => {
        const root = getPageObjectInContext(context, item.object);
        if (root) {
          let found;
          try {
            found = findPropertyInChain(root, name);
          } catch (error) {
            console.error(error);
            return;
          }
          if (
            instrument(
              context,
              item,
              pageObjectAt,
              found.depth,
              found.propertyName,
              value,
            )
          ) {
            covered++;
          }
        } else {
          console.error(
            "Could not instrument " +
              item.object +
              ". Encountered undefined object.",
          );
        }
      });
    }
    if (covered === 0) {
      console.error(
        "OpenWPM stealth: settings entry '" +
          item.instrumentedName +
          "' (object '" +
          item.object +
          "', depth " +
          item.depth +
          ") instruments no member; check its object and depth.",
      );
    }
  }
}

export { startInstrument };
