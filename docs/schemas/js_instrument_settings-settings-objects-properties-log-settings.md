# Log settings Schema

```txt
http://example.com/js-instrument-settings.schema#/items/properties/logSettings
```

The log settings object.


| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                      |
| :------------------ | ---------- | -------------- | ------------ | :---------------- | --------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [js_instrument_settings.schema.json\*](../../schemas/js_instrument_settings.schema.json "open original schema") |

## logSettings Type

`object` ([Log settings](js_instrument_settings-settings-objects-properties-log-settings.md))

# Log settings Properties

| Property                                                                | Type         | Required | Nullable       | Defined by                                                                                                                                                                                                                                                                       |
| :---------------------------------------------------------------------- | ------------ | -------- | -------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [propertiesToInstrument](#propertiesToInstrument)                       | Unknown Type | Required | can be null    | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument")                         |
| [nonExistingPropertiesToInstrument](#nonExistingPropertiesToInstrument) | `array`      | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-non-existing-properties-to-instrument.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/nonExistingPropertiesToInstrument") |
| [excludedProperties](#excludedProperties)                               | `array`      | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-excluded-properties.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/excludedProperties")                                  |
| [logCallStack](#logCallStack)                                           | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-log-call-stack.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logCallStack")                                             |
| [logFunctionsAsStrings](#logFunctionsAsStrings)                         | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-log-functions-as-strings.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionsAsStrings")                          |
| [logFunctionGets](#logFunctionGets)                                     | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-log-function-gets.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionGets")                                       |
| [preventSets](#preventSets)                                             | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-prevent-sets.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/preventSets")                                                |
| [recursive](#recursive)                                                 | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-recursive.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/recursive")                                                     |
| [depth](#depth)                                                         | `number`     | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-recursion-depth.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/depth")                                                   |

## propertiesToInstrument

An array of properties to instrument on this object. If array is empty, then all properties are instrumented.


`propertiesToInstrument`

-   is required
-   Type: `string[]`
-   can be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument")

### propertiesToInstrument Type

`string[]`

### propertiesToInstrument Default Value

The default value is:

```json
[]
```

## nonExistingPropertiesToInstrument

An array of non-existing properties to instrument on this object.


`nonExistingPropertiesToInstrument`

-   is required
-   Type: `string[]`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-non-existing-properties-to-instrument.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/nonExistingPropertiesToInstrument")

### nonExistingPropertiesToInstrument Type

`string[]`

### nonExistingPropertiesToInstrument Default Value

The default value is:

```json
[]
```

## excludedProperties

Properties excluded from instrumentation.


`excludedProperties`

-   is required
-   Type: `string[]`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-excluded-properties.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/excludedProperties")

### excludedProperties Type

`string[]`

### excludedProperties Default Value

The default value is:

```json
[]
```

## logCallStack

Set to true save the call stack info with each property call.


`logCallStack`

-   is required
-   Type: `boolean` ([Log call stack?](js_instrument_settings-settings-objects-properties-log-settings-properties-log-call-stack.md))
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-log-call-stack.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logCallStack")

### logCallStack Type

`boolean` ([Log call stack?](js_instrument_settings-settings-objects-properties-log-settings-properties-log-call-stack.md))

## logFunctionsAsStrings

Set to true to save args that are functions as strings during argument serialization. If false `FUNCTION` is recorded.


`logFunctionsAsStrings`

-   is required
-   Type: `boolean` ([Log functions as strings?](js_instrument_settings-settings-objects-properties-log-settings-properties-log-functions-as-strings.md))
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-log-functions-as-strings.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionsAsStrings")

### logFunctionsAsStrings Type

`boolean` ([Log functions as strings?](js_instrument_settings-settings-objects-properties-log-settings-properties-log-functions-as-strings.md))

## logFunctionGets

Set true to log get requests to properties that are functions. If true when a call is made, the log will contain both the call and a get log.


`logFunctionGets`

-   is required
-   Type: `boolean` ([Log function gets?](js_instrument_settings-settings-objects-properties-log-settings-properties-log-function-gets.md))
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-log-function-gets.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionGets")

### logFunctionGets Type

`boolean` ([Log function gets?](js_instrument_settings-settings-objects-properties-log-settings-properties-log-function-gets.md))

## preventSets

Set to true to prevent nested objects and functions from being overwritten (and thus having their instrumentation removed). Other properties (static values) can still be set with this is enabled.


`preventSets`

-   is required
-   Type: `boolean` ([Prevent sets?](js_instrument_settings-settings-objects-properties-log-settings-properties-prevent-sets.md))
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-prevent-sets.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/preventSets")

### preventSets Type

`boolean` ([Prevent sets?](js_instrument_settings-settings-objects-properties-log-settings-properties-prevent-sets.md))

## recursive

Set to `true` to recursively instrument all object properties of the given `object`. NOTE: (1) `propertiesToInstrument` does not propagate to sub-objects. (2) Sub-objects of prototypes can not be instrumented recursively as these properties can not be accessed until an instance of the prototype is created.


`recursive`

-   is required
-   Type: `boolean` ([Recursive?](js_instrument_settings-settings-objects-properties-log-settings-properties-recursive.md))
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-recursive.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/recursive")

### recursive Type

`boolean` ([Recursive?](js_instrument_settings-settings-objects-properties-log-settings-properties-recursive.md))

## depth

Recursion limit when instrumenting object recursively


`depth`

-   is required
-   Type: `number` ([Recursion depth](js_instrument_settings-settings-objects-properties-log-settings-properties-recursion-depth.md))
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-settings-objects-properties-log-settings-properties-recursion-depth.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/depth")

### depth Type

`number` ([Recursion depth](js_instrument_settings-settings-objects-properties-log-settings-properties-recursion-depth.md))

### depth Default Value

The default value is:

```json
5
```
