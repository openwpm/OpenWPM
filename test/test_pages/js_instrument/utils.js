function getLogSettings(requestedLogSettings={}) {
    const {
        propertiesToInstrument=[],
        nonExistingPropertiesToInstrument=[],
        excludedProperties=[],
        logCallStack=false,
        logFunctionsAsStrings= false,
        logFunctionGets=false,
        preventSets=false,
        recursive=false,
        depth=5
    } = requestedLogSettings;
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