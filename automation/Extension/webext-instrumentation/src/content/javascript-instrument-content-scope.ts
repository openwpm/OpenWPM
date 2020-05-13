import { instrumentFingerprintingApis } from "../lib/instrument-fingerprinting-apis";
import { jsInstruments } from "../lib/js-instruments";
import { pageScript } from "./javascript-instrument-page-scope";

const getPageScriptAsString = () => {
  return (
    jsInstruments +
    "\n" +
    instrumentFingerprintingApis +
    "\n" +
    "(" +
    pageScript +
    "({jsInstruments, instrumentFingerprintingApis}));"
  );
};

const insertScript = (text, data) => {
  const parent = document.documentElement;
  const script = document.createElement("script");
  script.text = text;
  script.async = false;

  for (const key in data) {
    if (data.hasOwnProperty(key)) {
      script.setAttribute("data-" + key.replace("_", "-"), data[key]);
    }
  }

  parent.insertBefore(script, parent.firstChild);
  parent.removeChild(script);
};

const emitMsg = (type, msg) => {
  msg.timeStamp = new Date().toISOString();
  browser.runtime.sendMessage({
    data: msg,
    namespace: "javascript-instrumentation",
    type,
  });
};

const eventId = Math.random();

// listen for messages from the script we are about to insert
document.addEventListener(eventId.toString(), (e: CustomEvent) => {
  // pass these on to the background page
  const msgs = e.detail;
  if (Array.isArray(msgs)) {
    msgs.forEach(msg => {
      emitMsg(msg.type, msg.content);
    });
  } else {
    emitMsg(msgs.type, msgs.content);
  }
});

export const injectJavascriptInstrumentPageScript = contentScriptConfig => {
  insertScript(getPageScriptAsString(), {
    event_id: eventId,
    ...contentScriptConfig,
  });
};
