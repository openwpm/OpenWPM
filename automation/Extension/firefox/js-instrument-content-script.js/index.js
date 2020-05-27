import { injectJavascriptInstrumentPageScript } from "openwpm-webext-instrumentation";

injectJavascriptInstrumentPageScript(window.openWpmJsInstrumentContentScriptConfig || {});
delete window.openWpmJsInstrumentContentScriptConfig;
