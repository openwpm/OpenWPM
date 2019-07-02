import { injectJavascriptInstrumentPageScript } from "openwpm-webext-instrumentation";

const testing = openWpmTesting || false;
injectJavascriptInstrumentPageScript(testing);
