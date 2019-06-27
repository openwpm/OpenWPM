import { injectJavascriptInstrumentPageScript } from "openwpm-webext-instrumentation";

const testing = window.openWpmTesting || false;
injectJavascriptInstrumentPageScript(testing);
