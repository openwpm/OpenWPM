import { JSInstrumentRequest } from "../lib/js-instruments";

export interface openWpmContentScriptConfig {
  testing: boolean;
  jsInstrumentationSettings: JSInstrumentRequest[];
}
declare global {
  interface Window {
    // Optional: the content script deletes it after reading it.
    openWpmContentScriptConfig?: openWpmContentScriptConfig;
  }
}
