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


"""