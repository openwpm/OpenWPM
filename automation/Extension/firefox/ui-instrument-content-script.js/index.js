import { injectUiInstrumentPageScript } from "openwpm-webext-instrumentation";

injectUiInstrumentPageScript(window.openWpmUiInstrumentContentScriptConfig || {});
delete window.openWpmUiInstrumentContentScriptConfig;
