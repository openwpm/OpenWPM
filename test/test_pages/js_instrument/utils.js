function getLogSettings(
    propertiesToInstrument=[],
    nonExistingPropertiesToInstrument=[],
    excludedProperties=[],
    logCallStack=false,
    logFunctionsAsStrings= false,
    logFunctionGets=false,
    preventSets=false,
    recursive=false,
    depth=5) {
       return {
        propertiesToInstrument: propertiesToInstrument,
        nonExistingPropertiesToInstrument: nonExistingPropertiesToInstrument,
        excludedProperties: excludedProperties,
        logCallStack: logCallStack,
        logFunctionsAsStrings: logFunctionsAsStrings,
        logFunctionGets: logFunctionGets,
        preventSets: preventSets,
        recursive: recursive,
        depth: depth,
    };
};