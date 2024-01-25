import { JSInstrumentRequest } from "../lib/js-instruments";

export interface openWpmContentScriptConfig {
  testing: boolean;
  jsInstrumentationSettings: JSInstrumentRequest[];
}
declare global {
  interface Window {
    openWpmContentScriptConfig: openWpmContentScriptConfig;
  }
  // https://searchfox.org/mozilla-central/source/js/xpconnect/idl/xpccomponents.idl#519-534
  // https://searchfox.org/mozilla-central/rev/1e726a0e49225dc174ab55d1d0b21e86208d7251/js/xpconnect/src/xpcprivate.h#2332-2348
  function exportFunction(vfunction: any, scope: any, options: {defineAs: string, allowCrossOriginArguments: boolean}):any
}
