"""
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
"""
