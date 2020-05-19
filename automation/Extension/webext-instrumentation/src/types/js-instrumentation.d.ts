export interface LogSettings {
  propertiesToInstrument: string[];
  nonExistingPropertiesToInstrument: string[];
  excludedProperties: string[];
  logCallStack: boolean;
  logFunctionsAsStrings: boolean;
  logFunctionGets: boolean;
  preventSets: boolean;
  recursive: boolean;
  depth: number;
}

export interface JSInstrumentRequest {
  object: string,
  instrumentedName: string,
  logSettings: LogSettings,
}