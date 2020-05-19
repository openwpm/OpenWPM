import { getInstrumentJS } from "../lib/js-instruments";
import { pageScript } from "./javascript-instrument-page-scope";

function getPageScriptAsString(jsInstrumentationRequestsString: string): string {
  // The JS Instrument Requests are setup and validated python side
  // including setting defaults for logSettings. See JSInstrumentation.py

  // The string jsInstrumentationRequestsString should be a string of a JS list.
  // If testing, use this carefully as no validation happens JS side.
  // You can use the JSInstrumentation.py as a standalone module to validate input.
  // We do this to help the JS instrumentation code load as fast as possible.
  const pageScriptString = `
// Start of js-instruments.
${getInstrumentJS}
// End of js-instruments.

// Start of custom instrumentRequests.
const instrumentationRequests = ${jsInstrumentationRequestsString};
// End of custom instrumentRequests.

// Start of anonymous function from javascript-instrument-page-scope.ts
(${pageScript}(getInstrumentJS, instrumentationRequests));
// End.
  `;

  return pageScriptString;
}

function insertScript(pageScript: string, event_id: string, testing: boolean = false) {
  const parent = document.documentElement,
    script = document.createElement("script");
  script.text = pageScript;
  script.async = false;
  script.setAttribute("data-event-id", event_id);
  script.setAttribute("data-testing", `${testing}`);
  parent.insertBefore(script, parent.firstChild);
  parent.removeChild(script);
}

function emitMsg(type, msg) {
  msg.timeStamp = new Date().toISOString();
  browser.runtime.sendMessage({
    namespace: "javascript-instrumentation",
    type,
    data: msg,
  });
}

const event_id = Math.random().toString();

// listen for messages from the script we are about to insert
document.addEventListener(event_id, function(e: CustomEvent) {
  // pass these on to the background page
  const msgs = e.detail;
  if (Array.isArray(msgs)) {
    msgs.forEach(function(msg) {
      emitMsg(msg.type, msg.content);
    });
  } else {
    emitMsg(msgs.type, msgs.content);
  }
});

export function injectJavascriptInstrumentPageScript(contentScriptConfig) {
  insertScript(
    getPageScriptAsString(contentScriptConfig.jsInstrumentationRequestsString),
    event_id,
    contentScriptConfig.testing,
  );
}
