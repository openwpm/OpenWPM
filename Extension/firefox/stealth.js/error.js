/*
 * Functionality to generate error objects
 */
function generateErrorObject(err, context){
  // TODO: Pass context
  context = (context !== undefined) ? context : window;
  const cleaned = cleanErrorStack(err.stack)
  const stack = splitStack(cleaned);
  const lineInfo = getLineInfo(stack);
  const fileName = getFileName(stack);
  let fakeError;
  try{
    // fake type, message, filename, column and line
    const propertyName = "stack";
    fakeError = new context.wrappedJSObject[err.name](err.message, fileName);
    fakeError.lineNumber = lineInfo.lineNumber;
    fakeError.columnNumber = lineInfo.columnNumber;
  }catch(error){
    console.log("ERROR creation failed. Error was:" + error);
  }
  return fakeError;
}

/*
 * Trims traces from the stack, which contain the extionsion ID
 */
function cleanErrorStack(stack) {
  const extensionID = browser.runtime.getURL("");
  const lines = (typeof(stack) !== "string") ? stack : splitStack(stack);
  lines.forEach(line =>{
    if (line.includes(extensionID)){
      stack = stack.replace(line+"\n","");
    }
  });
  return stack;
}

/*
 * Provides the index the first call outside of the extension
 */
function getBeginOfScriptCalls(stack) {
  const extensionID = browser.runtime.getURL("");
  const lines = (typeof(stack) !== "string") ? stack : splitStack(stack);
  for (let i=0; i<lines.length; i++){
    if (!lines[i].includes(extensionID)){
      return i;
    }
  }
  return -1;
}

/*
 * Get the stack as array
 */
function splitStack(stack){
  return stack.split('\n').map(function (line) { return line.trim(); });
}

/*
 * Retrieves line and column information of the function
 * calling before the extension was involved
 */
function getLineInfo(stack) {
  const firstLine = stack[0];
  const matches = [...firstLine.matchAll(":")];
  const column = firstLine.slice(
    matches[matches.length-1].index + 1,
    firstLine.length);
  const line = firstLine.slice(
    matches[matches.length-2].index + 1,
    matches[matches.length-1].index);
  return {
    "lineNumber": line,
    "columnNumber": column
  }
}

/*
 * Retrieves file name of the function
 * that called before the extension got involved
 */
function getFileName(stack) {
  const firstLine = stack[0];
  const matches_at = [...firstLine.matchAll("@")];
  const matches_colon = [...firstLine.matchAll(":")];
  return firstLine.slice(
    matches_at[matches_at.length-1].index + 1,
    matches_colon[matches_colon.length-2].index
  );
}

function getOriginFromStackTrace(err, includeStack){
  console.log(err.stack);

  const stack = splitStack(err.stack);
  const lineInfo = getLineInfo(stack);
  const fileName = getFileName(stack);

  const callSite = stack[1];
  const callSiteParts = callSite.split("@");
  const funcName = callSiteParts[0] || "";
  const items = rsplit(callSiteParts[1], ":", 2);
  const scriptFileName = items[items.length - 3] || "";

  const callContext = {
    scriptUrl,
    scriptLine: lineInfo.lineNumber,
    scriptCol: lineInfo.columnNumber,
    funcName,
    scriptLocEval,
    callStack: includeStack ? trace.slice(3).join("\n").trim() : "",
  };

}


// Helper to get originating script urls
// Legacy code
function getStackTrace() {
  let stack;

  try {
    throw new Error();
  } catch (err) {
    stack = err.stack;
  }

  return stack;
}


export { generateErrorObject, getBeginOfScriptCalls, getStackTrace };