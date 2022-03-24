import { injectJavascriptInstrumentPageScript } from "./content/javascript-instrument-content-scope";

injectJavascriptInstrumentPageScript(
  window.openWpmContentScriptConfig || {
    testing: false,
    jsInstrumentationSettings: [],
  },
);
delete window.openWpmContentScriptConfig;
