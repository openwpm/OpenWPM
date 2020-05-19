"""

const presetMap = {
  'fingerprinting': '../js-instrumentation-presets/fingerprinting.json',
};


function validateJsModuleRequest(jsModuleRequest: any) {
  if (typeof jsModuleRequest === 'string') {
    const isPreset = Object.keys(presetMap).includes(jsModuleRequest);
    const isAPI = api.includes(jsModuleRequest);
    if (!isPreset && !isAPI) {
      throw new Error(`String jsModuleRequest ${jsModuleRequest} is not a preset or a recognized API.`);
    }
  } else if (typeof jsModuleRequest === 'object') {
    const properties = Object.keys(jsModuleRequest);
    if (properties.length !== 1) {
      throw new Error(`Object jsModuleRequest must only have one property.`);
    }


  } else {
    throw new Error(`Invalid jsModuleRequest: ${jsModuleRequest}. Must be string or object.`)
  }
  console.debug(`Validation successful for`, jsModuleRequest);
}



  const instrumentationRequests: JSInstrumentRequest[] = [];

  if (!Array.isArray(jsModuleRequests)) {
    throw new Error(`jsModuleRequests, must be an Array. Received: ${jsModuleRequests}`);
  }

  for (let jsModuleRequest of jsModuleRequests) {

    validateJsModuleRequest(jsModuleRequest);

    console.log(presetMap);
    let logSettings = new LogSettings();
    let requestedModule = jsModuleRequest.object;
    console.log(logSettings);
    console.log(requestedModule);
    instrumentationRequests.push({
      object: requestedModule,
      instrumentedName: 'name',
      logSettings: logSettings,
    });
  }

  /*
  const instrumentedApiFuncs: string[] = [];

  jsModuleRequests.forEach(requestedModule => {
    if (requestedModule == "fingerprinting") {
      // Special case collection of fingerprinting
      instrumentedApiFuncs.push(String(instrumentFingerprintingApis));
    } else {
      // Note: We only do whole modules for now
      // Check requestedModule is a member of api
      if (api.includes(requestedModule)) {
        // Then add functions that do the instrumentation
        instrumentedApiFuncs.push(`
        function instrument${requestedModule}({
          instrumentObjectProperty,
          instrumentObject,
        }) {
          instrumentObject(window.${requestedModule}.prototype, "${requestedModule}");
        }
        `);
      } else {
        console.error(
          `The requested module ${requestedModule} does not appear to be part of browser api.`,
        );
      }
    }
  });
  */


  // The new goal of this function is to collect together a de-duped
  // list of JSInstrumentRequests from the input request (which allows
  // shorthand for various things).

  /*
  We accept a list. From the list we need to parse each item.
  The item may be a string or an object with one key.
  If the item is a string:
    - Is it a shortcut e.g. "fingerprinting"
    - Is it an object (verified by mdn-browser-compat)
    - If neither, reject
  If the item is an object:
    - Must only have one property
    - The value may be a list or a LogSettings object
    - If the value is a list, it is transformed into the propertiesToInstrument
      property of a new LogSettings object.

  We must also create the instrumentedName value.
  */

// Implements ILogSettings and sets defaults
export class LogSettings implements ILogSettings {
    //   propertiesToInstrument : Array
    //     An array of properties to instrument on this object.
    //     If array is empty, then all properties are instrumented.
    //   nonExistingPropertiesToInstrument : Array
    //     An array of non-existing properties to instrument on this object.
    //   excludedProperties : Array
    //     Properties excluded from instrumentation.
    //   logCallStack : boolean
    //     Set to true save the call stack info with each property call.
    //   logFunctionsAsStrings : boolean
    //     Set to true to save functional arguments as strings during
    //     argument serialization.
    //   logFunctionGets: boolean
    //     ....
    //   preventSets : boolean
    //     Set to true to prevent nested objects and functions from being
    //     overwritten (and thus having their instrumentation removed).
    //     Other properties (static values) can still be set with this is
    //     enabled.
    //   recursive : boolean
    //     Set to `true` to recursively instrument all object properties of
    //     the given `object`.
    //     NOTE:
    //       (1)`logSettings['propertiesToInstrument']` does not propagate
    //           to sub-objects.
    //       (2) Sub-objects of prototypes can not be instrumented
    //           recursively as these properties can not be accessed
    //           until an instance of the prototype is created.
    //   depth : integer
    //     Recursion limit when instrumenting object recursively.
  propertiesToInstrument: string[] = [];
  nonExistingPropertiesToInstrument: string[] = [];
  excludedProperties: string[] = [];
  logCallStack: boolean = false;
  logFunctionsAsStrings: boolean = false;
  logFunctionGets: boolean = false;
  preventSets: boolean = false;
  recursive: boolean = false;
  depth: number = 5;
}


        // Shortcut
        //"fingerprinting",
        // APIs
        {"XMLHttpRequest": {"badSetting": 1}},
        {"XMLHttpRequest": {"excludedProperties": ["send"]}},
        {"Prop1": ["hi"], "Prop2": ["hi2"]},
        {"XMLHttpRequest": ["send"]},
        "Storage",
        // Specific instances on window
        //{"window.document": ["cookie", "referrer"]},
        //{"window": ["name", "localStorage", "sessionStorage"]}


"""  # noqa
