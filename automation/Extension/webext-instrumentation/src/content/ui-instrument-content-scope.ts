import { xpath } from "../lib/xpath";
import { pageScript } from "./ui-instrument-page-scope";

export interface UiInstrumentTimeStampedMessage {
  timeStamp: string;
}

function getPageScriptAsString() {
  return `const xpath = ${xpath};\n(${pageScript}({xpath}));`;
}

function insertScript(text, data) {
  const parent = document.documentElement,
    script = document.createElement("script");
  script.text = text;
  script.async = false;

  for (const key of Object.keys(data)) {
    const qualifiedName = "data-" + key.split("_").join("-");
    script.setAttribute(qualifiedName, data[key]);
  }

  parent.insertBefore(script, parent.firstChild);
  parent.removeChild(script);
}

function emitMsg(type, msg) {
  msg.timeStamp = new Date().toISOString();
  browser.runtime.sendMessage({
    namespace: "ui-instrument",
    type,
    data: msg,
  });
}

const injection_uuid = Math.random();

// listen for messages from the script we are about to insert
document.addEventListener(injection_uuid.toString(), function(e: CustomEvent) {
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

export function injectUiInstrumentPageScript(contentScriptConfig) {
  insertScript(getPageScriptAsString(), {
    injection_uuid,
    ...contentScriptConfig,
  });
}
