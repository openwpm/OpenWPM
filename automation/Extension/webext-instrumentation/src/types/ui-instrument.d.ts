export {}; // this file needs to be a module
declare global {
  interface Window {
    openWpmUiInstrumentContentScriptConfig: any;
    openWpmUiInstrumentClickListenerAdded: boolean;
    openWpmUiInstrumentUiStateCheckIntervalSet: boolean;
  }
}
