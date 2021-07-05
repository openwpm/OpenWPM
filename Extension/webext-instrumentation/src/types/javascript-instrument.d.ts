import { JSInstrumentRequest } from "../lib/js-instruments";

export interface openWpmContentScriptConfig {
  testing: boolean;
  jsInstrumentationSettings: JSInstrumentRequest[];
}
declare global {
  interface Window {
    openWpmContentScriptConfig: JSInstrumentRequest[];
  }
}
