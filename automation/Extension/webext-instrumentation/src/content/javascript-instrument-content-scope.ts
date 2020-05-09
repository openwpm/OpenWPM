import { instrumentFingerprintingApis } from "../lib/instrument-fingerprinting-apis";
import { jsInstruments } from "../lib/js-instruments";
import { pageScript } from "./javascript-instrument-page-scope";

function getPageScriptAsString(jsModuleRequests: string[]): string {
  const instrumentedApis: string[] = [];

  jsModuleRequests.forEach(requestedModule => {
    if (requestedModule == "fingerprinting") {
      instrumentedApis.push(String(instrumentFingerprintingApis));
    }
  });

  const pageScriptString = `
    ${jsInstruments}
    const instrumentedApis = [${instrumentedApis.join("\n")}];
    (${String(pageScript)}({jsInstruments, instrumentedApis}));
  `;

  console.log(pageScriptString);
  return pageScriptString;
}

function insertScript(text, data) {
  const parent = document.documentElement,
    script = document.createElement("script");
  script.text = text;
  script.async = false;

  for (const key in data) {
    script.setAttribute("data-" + key.replace("_", "-"), data[key]);
  }

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

const event_id = Math.random();

// listen for messages from the script we are about to insert
document.addEventListener(event_id.toString(), function(e: CustomEvent) {
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
  const jsModules: string[] = contentScriptConfig.modules;
  insertScript(getPageScriptAsString(jsModules), {
    event_id,
    ...contentScriptConfig,
  });
}
