# Untitled object in JS Instrument Settings Schema

```txt
http://example.com/js-instrument-settings.schema#/items/properties/logSettings
```

The log settings object.


| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                      |
| :------------------ | ---------- | -------------- | ------------ | :---------------- | --------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [js_instrument_settings.schema.json\*](../../schemas/js_instrument_settings.schema.json "open original schema") |

## logSettings Type

`object` ([Details](js_instrument_settings-items-properties-logsettings.md))

# undefined Properties

| Property                                                                | Type         | Required | Nullable       | Defined by                                                                                                                                                                                                                                                       |
| :---------------------------------------------------------------------- | ------------ | -------- | -------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [propertiesToInstrument](#propertiesToInstrument)                       | Unknown Type | Required | can be null    | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-propertiestoinstrument.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument")                       |
| [nonExistingPropertiesToInstrument](#nonExistingPropertiesToInstrument) | `array`      | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-nonexistingpropertiestoinstrument.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/nonExistingPropertiesToInstrument") |
| [excludedProperties](#excludedProperties)                               | `array`      | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-excludedproperties.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/excludedProperties")                               |
| [logCallStack](#logCallStack)                                           | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-logcallstack.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logCallStack")                                           |
| [logFunctionsAsStrings](#logFunctionsAsStrings)                         | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-logfunctionsasstrings.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionsAsStrings")                         |
| [logFunctionGets](#logFunctionGets)                                     | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-logfunctiongets.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionGets")                                     |
| [preventSets](#preventSets)                                             | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-preventsets.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/preventSets")                                             |
| [recursive](#recursive)                                                 | `boolean`    | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-recursive.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/recursive")                                                 |
| [depth](#depth)                                                         | `number`     | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-depth.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/depth")                                                         |

## propertiesToInstrument

An array of properties to instrument on this object. If array is empty, then all properties are instrumented.


`propertiesToInstrument`

-   is required
-   Type: `string[]`
-   can be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-propertiestoinstrument.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument")

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
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-nonexistingpropertiestoinstrument.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/nonExistingPropertiesToInstrument")

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
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-excludedproperties.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/excludedProperties")

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
-   Type: `boolean`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-logcallstack.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logCallStack")

### logCallStack Type

`boolean`

## logFunctionsAsStrings

Set to true to save args that are functions as strings during argument serialization. If false `FUNCTION` is recorded.


`logFunctionsAsStrings`

-   is required
-   Type: `boolean`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-logfunctionsasstrings.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionsAsStrings")

### logFunctionsAsStrings Type

`boolean`

## logFunctionGets

Set true to log get requests to properties that are functions. If true when a call is made, the log will contain both the call and a get log.


`logFunctionGets`

-   is required
-   Type: `boolean`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-logfunctiongets.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionGets")

### logFunctionGets Type

`boolean`

## preventSets

Set to true to prevent nested objects and functions from being overwritten (and thus having their instrumentation removed). Other properties (static values) can still be set with this is enabled.


`preventSets`

-   is required
-   Type: `boolean`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-preventsets.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/preventSets")

### preventSets Type

`boolean`

## recursive

Set to `true` to recursively instrument all object properties of the given `object`. NOTE: (1) `propertiesToInstrument` does not propagate to sub-objects. (2) Sub-objects of prototypes can not be instrumented recursively as these properties can not be accessed until an instance of the prototype is created.


`recursive`

-   is required
-   Type: `boolean`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-recursive.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/recursive")

### recursive Type

`boolean`

## depth

Recursion limit when instrumenting object recursively


`depth`

-   is required
-   Type: `number`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings-properties-depth.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/depth")

### depth Type

`number`

### depth Default Value

The default value is:

```json
5
```
