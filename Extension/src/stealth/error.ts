/*
 * Functionality to generate error objects
 */
function generateErrorObject(
  err: { stack: any; name: string | number; message: any },
  context = undefined,
) {
  context = context !== undefined ? context : window;
  const cleaned = cleanErrorStack(err.stack);
  const stack = splitStack(cleaned);
  const lineInfo = getLineInfo(stack);
  const fileName = getFileName(stack);
  let fakeError: { lineNumber: any; columnNumber: any };
  try {
    const wrappedJS = context.wrappedJSObject;
    const ErrorConstructor =
      typeof err.name === "string" && wrappedJS[err.name]
        ? wrappedJS[err.name]
        : null;

    if (
      err instanceof DOMException ||
      (typeof err.name === "string" && err.name === "DOMException")
    ) {
      // DOMException constructor takes (message, name) not (message, fileName)
      fakeError = new wrappedJS.DOMException(err.message, err.name);
    } else if (
      ErrorConstructor &&
      typeof ErrorConstructor === "function" &&
      (ErrorConstructor === wrappedJS.Error ||
        ErrorConstructor.prototype instanceof wrappedJS.Error)
    ) {
      fakeError = new ErrorConstructor(err.message, fileName);
    } else {
      // Fallback for custom errors or unknown error types
      fakeError = new wrappedJS.Error(err.message, fileName);
    }

    if (lineInfo) {
      fakeError.lineNumber = lineInfo.lineNumber;
      fakeError.columnNumber = lineInfo.columnNumber;
    }
  } catch (error) {
    console.log("ERROR creation failed. Error was:" + error);
  }
  return fakeError || err;
}

/*
 * Trims traces from the stack, which contain the extionsion ID
 */
function cleanErrorStack(stack) {
  const extensionID = browser.runtime.getURL("");
  const lines = typeof stack !== "string" ? stack : splitStack(stack);
  lines.forEach((line) => {
    if (line.includes(extensionID)) {
      stack = stack.replace(line + "\n", "");
    }
  });
  return stack;
}

/*
 * Provides the index the first call outside of the extension
 */
function getBeginOfScriptCalls(stack) {
  const extensionID = browser.runtime.getURL("");
  const lines = typeof stack !== "string" ? stack : splitStack(stack);
  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].includes(extensionID)) {
      return i;
    }
  }
  return -1;
}

/*
 * Get the stack as array
 */
function splitStack(stack) {
  return stack.split("\n").map(function (line) {
    return line.trim();
  });
}

/*
 * Retrieves line and column information of the function
 * calling before the extension was involved
 */
function getLineInfo(stack) {
  if (!stack || !stack.length || !stack[0]) {
    return null;
  }
  const firstLine = stack[0];
  const matches = [...firstLine.matchAll(/:/g)];
  if (matches.length < 2) {
    return null;
  }
  const column = firstLine.slice(
    matches[matches.length - 1].index + 1,
    firstLine.length,
  );
  const line = firstLine.slice(
    matches[matches.length - 2].index + 1,
    matches[matches.length - 1].index,
  );
  return {
    lineNumber: line,
    columnNumber: column,
  };
}

/*
 * Retrieves file name of the function
 * that called before the extension got involved
 */
function getFileName(stack) {
  if (!stack || !stack.length || !stack[0]) {
    return "";
  }
  const firstLine = stack[0];
  const matches_at = [...firstLine.matchAll(/@/g)];
  const matches_colon = [...firstLine.matchAll(/:/g)];
  if (!matches_at.length || matches_colon.length < 2) {
    return "";
  }
  return firstLine.slice(
    matches_at[matches_at.length - 1].index + 1,
    matches_colon[matches_colon.length - 2].index,
  );
}

// function getOriginFromStackTrace(err, includeStack){
//   console.log(err.stack);

//   const stack = splitStack(err.stack);
//   const lineInfo = getLineInfo(stack);
//   const fileName = getFileName(stack);

//   const callSite = stack[1];
//   const callSiteParts = callSite.split("@");
//   const funcName = callSiteParts[0] || "";
//   const items = rsplit(callSiteParts[1], ":", 2);
//   const scriptFileName = items[items.length - 3] || "";

//   const callContext = {
//     scriptUrl,
//     scriptLine: lineInfo.lineNumber,
//     scriptCol: lineInfo.columnNumber,
//     funcName,
//     scriptLocEval,
//     callStack: includeStack ? trace.slice(3).join("\n").trim() : "",
//   };

// }

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
