import { getInstrumentJS } from "../lib/js-instruments";
import { pageScript } from "./javascript-instrument-page-scope";

function getPageScriptAsString(
  jsInstrumentationSettingsString: string,
): string {
  // The JS Instrument Requests are setup and validated python side
  // including setting defaults for logSettings. See JSInstrumentation.py
  const pageScriptString = `
// Start of js-instruments.
${getInstrumentJS}
// End of js-instruments.

// Start of custom instrumentRequests.
const jsInstrumentationSettings = ${jsInstrumentationSettingsString};
// End of custom instrumentRequests.

// Start of anonymous function from javascript-instrument-page-scope.ts
(${pageScript}(getInstrumentJS, jsInstrumentationSettings));
// End.
  `;
  return pageScriptString;
}

function insertScript(
  pageScriptString: string,
  eventId: string,
  testing: boolean = false,
) {
  const parent = document.documentElement,
    script = document.createElement("script");
  script.text = pageScriptString;
  script.async = false;
  script.setAttribute("data-event-id", eventId);
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

const eventId = Math.random().toString();

// listen for messages from the script we are about to insert
document.addEventListener(eventId, function(e: CustomEvent) {
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
    getPageScriptAsString(contentScriptConfig.jsInstrumentationSettingsString),
    eventId,
    contentScriptConfig.testing,
  );
}
