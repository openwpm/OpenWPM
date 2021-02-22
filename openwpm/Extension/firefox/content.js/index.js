import {injectJavascriptInstrumentPageScript} from "openwpm-webext-instrumentation";

injectJavascriptInstrumentPageScript(window.openWpmContentScriptConfig || {});
delete window.openWpmContentScriptConfig;
