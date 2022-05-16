import { jsInstrumentationSettings } from "./settings";
import { generateErrorObject, getBeginOfScriptCalls, getStackTrace } from "./error";
/**************************************
* OpenWPM legacy code
***************************************/
// Counter to cap # of calls logged for each script/api combination
const maxLogCount = 500;
// logCounter
const logCounter = new Object();
// Prevent logging of gets arising from logging
let inLog = false;
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
function rsplit(source, sep, maxsplit){
  const split = source.split(sep);
  return maxsplit
    ? [split.slice(0, -maxsplit).join(sep)].concat(split.slice(-maxsplit))
    : split;
}

// Helper for JSONifying objects
function serializeObject(
  object,
  //stringifyFunctions: boolean = false,
  stringifyFunctions,
//): string {
){
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

// Rough implementations of Object.getPropertyDescriptor and Object.getPropertyNames
// See http://wiki.ecmascript.org/doku.php?id=harmony:extended_object_api
Object.getPropertyDescriptor = function (subject, name) {
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

function updateCounterAndCheckIfOver(scriptUrl, symbol){
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
function getPathToDomElement(element, visibilityAttr) {
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

function getOriginatingScriptContext(getCallStack = false, isCall = false){
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

  let traceStart = getBeginOfScriptCalls(trace);
  if (traceStart == -1){
    // If not included, use heuristic, 0-3 or 0-2 are OpenWPMs functions
    traceStart = isCall ? 3 : 4;
  }
  const callSite = trace[traceStart];
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
      callStack: getCallStack ? trace.slice(3).join("\n").trim() : "",
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

function logErrorToConsole(error, context = false) {
    console.error("OpenWPM: Error name: " + error.name);
    console.error("OpenWPM: Error message: " + error.message);
    console.error("OpenWPM: Error filename: " + error.fileName);
    console.error("OpenWPM: Error line number: " + error.lineNumber);
    console.error("OpenWPM: Error stack: " + error.stack);
    if (context) {
        console.error("OpenWPM: Error context: " + JSON.stringify(context));
    }
}

// For gets, sets, etc. on a single value
function logValue(
  instrumentedVariableName,//: string,
  value,//: any,
  operation,//: string, // from JSOperation object please
  callContext,//: any,
  logSettings = false,//: LogSettings,
){
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
    const overLimit = updateCounterAndCheckIfOver(callContext.scriptUrl, instrumentedFunctionName);
    if (overLimit) {
        inLog = false;
        return;
    }
    try {
        // Convert special arguments array to a standard array for JSONifying
        const serialArgs = [];
        for (const arg of args) {
            serialArgs.push(serializeObject(arg, false));//TODO: Get back to logSettings.logFunctionsAsStrings));
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
    }
    catch (error) {
        console.log("OpenWPM: Unsuccessful call log: " + instrumentedFunctionName);
        console.log(error);
        logErrorToConsole(error);
    }
    inLog = false;
}

/*********************************************************************************
* New functionality
**********************************************************************************/

/**
 * Provides the properties per prototype object
 */
Object.getPrototypeByDepth = function (subject, depth) {
  if (subject === undefined) {
    throw new Error("Can't get property names for undefined");
  }
  if (depth === undefined || typeof(depth) !== "number" ) {
    throw new Error("Depth "+ depth +" is invalid");
  }
  let proto = subject;
  for(let i=1; i<=depth; i++) {
    proto = Object.getPrototypeOf(proto);
  }
  if (proto === undefined){
    throw new Error("Prototype was undefined. Too deep iteration?");
  }
  return proto;
}

/**
 * Traverses the prototype chain to collect properties. Returns an array containing
 * an object with the depth, propertyNames and scanned subject
 */
Object.getPropertyNamesPerDepth = function (subject, maxDepth=0) {
  if (subject === undefined) {
    throw new Error("Can't get property names for undefined");
  }
  let res = [];
  let depth = 0;
  let properties = Object.getOwnPropertyNames(subject);
  res.push({"depth": depth, "propertyNames":properties, "object":subject});
  let proto = Object.getPrototypeOf(subject);

  while (proto !== null, depth < maxDepth) {
    depth++;
    properties = Object.getOwnPropertyNames(proto);
    res.push({"depth": depth, "propertyNames":properties, "object":proto});
    proto = Object.getPrototypeOf(proto);
  }
  return res;
}

/**
 * Finds a property along the prototype chain
 */
Object.findPropertyInChain = function (subject, propertyName) {
  if (subject === undefined || propertyName === undefined) {
    throw new Error("Object and property name must be defined");
  }
  let properties = [];
  let depth = 0;
  while (subject !== null) {
    properties = Object.getOwnPropertyNames(subject);
    if (properties.includes(propertyName)){
      return {"depth": depth, "propertyName":propertyName};
    }
    depth++;
    subject = Object.getPrototypeOf(subject);
  }
  throw Error("Property not found. Check whether configuration is correct!");
}


/*
 * Get all keys for properties that shall be overwritten
 */
function getPropertyKeysToOverwrite(item){
  let res = [];
  item.logSettings.overwrittenProperties.forEach(obj =>{
    res.push(obj.key);
  })
  return res;
}

function getContextualPrototypeFromString(context, objectAsString) {
  const obj = context[objectAsString];
  if (obj) {
    return (obj.prototype) ? obj.prototype : Object.getPrototypeOf(obj);
  } else {
    return undefined;
  }
}


/**
 * Prepares a list of properties that need to be instrumented
 * Here, this can be a previous created list (settings.js: propertiesToInstrument)
 * or all properties of a given object (settings.js: propertiesToInstrument is empty)
 */
function getObjectProperties(context, item){
  let propertiesToInstrument = item.logSettings.propertiesToInstrument;
  const proto = getContextualPrototypeFromString(context, item["object"]);
  if (!proto) {
    throw Error("Object " + item['object'] + "was undefined.");
  }

  if (propertiesToInstrument === undefined || !propertiesToInstrument.length) {
    propertiesToInstrument = Object.getPropertyNamesPerDepth(proto, item['depth']);
    // filter excluded and overwritten properties
    const excluded = getPropertyKeysToOverwrite(item).concat(item.logSettings.excludedProperties);
    propertiesToInstrument = filterPropertiesPerDepth(propertiesToInstrument, excluded);
  }else{
    // include the object to each item
    propertiesToInstrument.forEach(propertyList => {
      propertyList["object"] = Object.getPrototypeByDepth(proto, propertyList["depth"]);
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
function notify(type, content){
  content.timeStamp = new Date().toISOString();
  browser.runtime.sendMessage({
    namespace: "javascript-instrumentation",
    type,
    data: content
  });
}

function filterPropertiesPerDepth(collection, excluded){
  for (let i=0; i<collection.length; i++){
    collection[i]["propertyNames"] = collection[i]["propertyNames"].filter(p => !excluded.includes(p));
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
function exportCustomFunction(func, context, name){
	const targetObject = context.wrappedJSObject.Object.create(null);
	const exportedTry = exportFunction(func, targetObject, {allowCrossOriginArguments: true, defineAs: name});
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
  propertyName){
    const exportedFunction = exportCustomFunction(instrumentedFunction, window, propertyName);
    changeProperty(descriptor, pageObject, propertyName, functionType,	exportedFunction);
}


/*
  * Add notifications when a property is requested
 * TODO: Bring everything together at this point
 *
 * @param original: the original getter/setter function
 * @param object:
 * @param args:
 */
function instrumentGetObjectProperty(identifier, original, newValue, object, args){
  const originalValue = original.call(object, ...args);
  const callContext = getOriginatingScriptContext(true);
  const returnValue = (newValue !== undefined) ? newValue : originalValue;
  logValue(
    identifier,
    returnValue,
    JSOperation.get,
    callContext,
    //logSettings
   );
  return returnValue;
}
 /*
  * Add notifications when a property is set
  *
  * @param original: the original getter/setter function
  * @param object:
  * @param args:
  */
function instrumentSetObjectProperty(identifier, original, newValue, object, args){
  const callContext = getOriginatingScriptContext(true);
  logValue(
     identifier,
     newValue,
     (!!original) ? JSOperation.set : JSOperation.set_failed,
     callContext,
     //logSettings
    );
    if (!original){
      return newValue;
    }
    else{
      return original.call(object, newValue);
    }
}

/*
* Creates a getter function
*
* @param descriptor: the descriptor of the original function
* @param funcName: Name of property/function that shall be overwritten
* @param newValue: in Case the value shall be changed
*/
function generateGetter(identifier, descriptor, propertyName, newValue = undefined){
  const original = descriptor.get;
  return Object.getOwnPropertyDescriptor(
  {
   get [propertyName](){
     return instrumentGetObjectProperty(identifier, original, newValue, this, arguments);
   }
  },
  propertyName).get;
}

/*
* Creates a setter function
*
* @param descriptor: the descriptor of the original function
* @param funcName: Name of property/function that shall be overwritten
* @param newValue: in Case the value shall be changed
*/
function generateSetter(identifier, descriptor, propertyName, newValue){
  const original = descriptor.set;
  return Object.getOwnPropertyDescriptor(
  {
   set [propertyName](newValue){
     return instrumentSetObjectProperty(identifier, original, newValue, this, arguments);
   }
  },
  propertyName).set;
}

/*
 * Overwrites the prototype to access a property
 * @param
 */
function changeProperty(
  descriptor,
  pageObject,
  name,
  method,
  changed){
  	descriptor[method] = changed;
    Object.defineProperty(pageObject, name, descriptor);
}


/*
 * Retrieves an object in a context
 *
 * @param context: the window object that is currently instrumented
 * @param object: the subobject needed
 */
function getPageObjectInContext(context, context_object){
  if (context === undefined || context_object === undefined){
    return ;
  }
  return context[context_object].prototype || context[context_object];
}

/*
 * TODO: Add description
 */
const getPropertyType = (object, property) => typeof(object[property]);


/*
 * Entry point to creates (g/s)etter functions,
 * instrument them and inject them to the page
 * context
 */
function instrumentGetterSetter(
  descriptor,
  identifier,
  pageObject,
  propertyName,
  newValue = undefined)
  {
    let instrumentedFunction;
    const getFuncType = "get";
    const setFuncType = "set";

    if (descriptor.hasOwnProperty(getFuncType)){
      instrumentedFunction = generateGetter(identifier, descriptor, propertyName, newValue);
      injectFunction(instrumentedFunction, descriptor, getFuncType, pageObject, propertyName);
    }
    if (descriptor.hasOwnProperty(setFuncType)){
      instrumentedFunction = generateSetter(identifier, descriptor, propertyName);
      injectFunction(instrumentedFunction, descriptor, setFuncType, pageObject, propertyName);
    }
}

/*
 * TODO: Add description
 */
function functionGenerator(context, identifier, original, funcName) {
  function temp(){
    let result;
    const callContext = getOriginatingScriptContext(true, true);
    logCall(identifier,
      arguments,
      callContext
    );
    try{
      result = (arguments.length > 0) ? original.call(this, ...arguments) : original.call(this);
    }catch(err){
      let fakeError = generateErrorObject(err);
      throw fakeError;
    }
    return result;
  }
  return temp
}


/*
 * TODO: Add description
 */
function instrumentFunction(context, descriptor, identifier, pageObject, propertyName) {
  const original = descriptor.value;
  const tempFunction = functionGenerator(context, identifier, original, propertyName);
  const exportedFunction = exportCustomFunction(tempFunction, context, original.name);
  changeProperty(descriptor, pageObject, propertyName, "value",	exportedFunction);
}


/*
 * Helper class to perform all needed functionality
 *
 * @param context: the window object that is currently instrumented
 * @param object: child object that shall be instumented
 */
function instrument(context, item, depth, propertyName, newValue = undefined){
  try{
    const identifier = item["instrumentedName"] + "." + propertyName;
    const initialPageObject = getPageObjectInContext(context.wrappedJSObject, item["object"]);
    const pageObject = Object.getPrototypeByDepth(initialPageObject, depth);
    const descriptor = Object.getPropertyDescriptor(pageObject, propertyName);
    if (descriptor === undefined){
      // Do not do undefined descriptor. We can safely skip them
      return;
    }
    if (typeof(descriptor.value) === "function"){
      instrumentFunction(context, descriptor, identifier, pageObject, propertyName);
    } else {
      instrumentGetterSetter(descriptor, identifier, pageObject, propertyName, newValue);
    }
  } catch (error){
    console.log(error);
    console.log(error.stack);
    return;
  }
}


/*
 * Checks if an object was already wrapped
 * Unwrapped objects should be wrapped immediately
 */
let wrappedObjects = [];
function needsWrapper(object) {
  if (wrappedObjects.some(obj => object === obj)){
    //console.log("is already wrapped:" + object);
    return false;
  }
  wrappedObjects.push(object);
  //console.log("Will be wrapped:" + object);
  return true;
}

function startInstrument(context){
  jsInstrumentationSettings.forEach(item => {

    // retrieve Object properties alont the chain
    let propertyCollection;
    try {
      propertyCollection = getObjectProperties(context, item);
    } catch (err){
      console.log(err);
      return;
    }
    // Instrument each Property per object/prototype
    if (propertyCollection[0] !== ""){
      // console.log(item["instrumentedName"]);
      // console.log(propertyCollection);
      propertyCollection.forEach(({depth, propertyNames, object}) => {
        if (needsWrapper(object)){
          propertyNames.forEach(propertyName => instrument(context, item, depth, propertyName));
        }
      });
    }
    // Instrument properties and overwrite their return value
    if (item.logSettings.overwrittenProperties){
      item.logSettings.overwrittenProperties.forEach(({key: name, value}) => {
        const proto = getContextualPrototypeFromString(context, item["object"]);
        if (proto){
          let {depth, propertyName} = Object.findPropertyInChain(proto, name);
          instrument(context, item, depth, propertyName, value);
        } else {
          console.log("Could not instrument " + item["object"] + ". Encountered undefined object.");
        }
      });
    }
  });
  //console.log(wrappedObjects);
}

export {
  startInstrument,
  exportCustomFunction
};