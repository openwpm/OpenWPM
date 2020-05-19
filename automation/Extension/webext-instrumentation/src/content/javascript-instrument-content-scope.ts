//import { instrumentFingerprintingApis } from "../lib/instrument-fingerprinting-apis";
import { getInstrumentJS, LogSettings } from "../lib/js-instruments";
import { api } from "../lib/mdn-browser-compat-data";
import { pageScript } from "./javascript-instrument-page-scope";
import { JSInstrumentRequest } from "../types/js-instrumentation";

const presetMap = {
  'fingerprinting': '../js-instrumentation-presets/fingerprinting.json',
};

function validateJsModuleRequest(jsModuleRequest: any) {
  if (typeof jsModuleRequest === 'string') {
    const isPreset = Object.keys(presetMap).includes(jsModuleRequest);
    const isAPI = api.includes(jsModuleRequest);
    if (!isPreset && !isAPI) {
      throw new Error(`String jsModuleRequest ${jsModuleRequest} is not a preset or a recognized API.`);
    }
  } else if (typeof jsModuleRequest === 'object') {
    const properties = Object.keys(jsModuleRequest);
    if (properties.length !== 1) {
      throw new Error(`Object jsModuleRequest must only have one property.`);
    }


  } else {
    throw new Error(`Invalid jsModuleRequest: ${jsModuleRequest}. Must be string or object.`)
  }
  console.debug(`Validation successful for`, jsModuleRequest);
}

function getPageScriptAsString(jsModuleRequests: any[]): string {
  // The new goal of this function is to collect together a de-duped
  // list of JSInstrumentRequests from the input request (which allows
  // shorthand for various things).

  /*
  We accept a list. From the list we need to parse each item.
  The item may be a string or an object with one key.
  If the item is a string:
    - Is it a shortcut e.g. "fingerprinting"
    - Is it an object (verified by mdn-browser-compat)
    - If neither, reject
  If the item is an object:
    - Must only have one property
    - The value may be a list or a LogSettings object
    - If the value is a list, it is transformed into the propertiesToInstrument
      property of a new LogSettings object.

  We must also create the instrumentedName value.
  */


  const instrumentationRequests: JSInstrumentRequest[] = [];

  if (!Array.isArray(jsModuleRequests)) {
    throw new Error(`jsModuleRequests, must be an Array. Received: ${jsModuleRequests}`);
  }

  for (let jsModuleRequest of jsModuleRequests) {

    validateJsModuleRequest(jsModuleRequest);

    console.log(presetMap);
    let logSettings = new LogSettings();
    let requestedModule = jsModuleRequest.object;
    console.log(logSettings);
    console.log(requestedModule);
    instrumentationRequests.push({
      object: requestedModule,
      instrumentedName: 'name',
      logSettings: logSettings,
    });
  }

  /*
  const instrumentedApiFuncs: string[] = [];

  jsModuleRequests.forEach(requestedModule => {
    if (requestedModule == "fingerprinting") {
      // Special case collection of fingerprinting
      instrumentedApiFuncs.push(String(instrumentFingerprintingApis));
    } else {
      // Note: We only do whole modules for now
      // Check requestedModule is a member of api
      if (api.includes(requestedModule)) {
        // Then add functions that do the instrumentation
        instrumentedApiFuncs.push(`
        function instrument${requestedModule}({
          instrumentObjectProperty,
          instrumentObject,
        }) {
          instrumentObject(window.${requestedModule}.prototype, "${requestedModule}");
        }
        `);
      } else {
        console.error(
          `The requested module ${requestedModule} does not appear to be part of browser api.`,
        );
      }
    }
  });
  */
  // Build script as string
  const pageScriptString = `
    ${getInstrumentJS}
    const instrumentationRequests = [${instrumentationRequests.join(",\n")}];
    (${String(pageScript)}({getInstrumentJS, instrumentationRequests}));
  `;
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
