"""
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
"""