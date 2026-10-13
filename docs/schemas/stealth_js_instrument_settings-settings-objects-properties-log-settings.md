# Log settings Schema

```txt
http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings
```

The log settings object.

| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                                         |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [stealth\_js\_instrument\_settings.schema.json\*](../../schemas/stealth_js_instrument_settings.schema.json "open original schema") |

## logSettings Type

`object` ([Log settings](stealth_js_instrument_settings-settings-objects-properties-log-settings.md))

# logSettings Properties

| Property                                                                | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                                                                                                          |
| :---------------------------------------------------------------------- | :-------- | :------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [propertiesToInstrument](#propertiestoinstrument)                       | `array`   | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument")                         |
| [nonExistingPropertiesToInstrument](#nonexistingpropertiestoinstrument) | `array`   | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-non-existing-properties-to-instrument.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/nonExistingPropertiesToInstrument") |
| [excludedProperties](#excludedproperties)                               | `array`   | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-excluded-properties.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/excludedProperties")                                  |
| [overwrittenProperties](#overwrittenproperties)                         | `array`   | Optional | can be null    | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-overwritten-property.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/overwrittenProperties")                              |
| [logCallStack](#logcallstack)                                           | `boolean` | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-call-stack.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/logCallStack")                                             |
| [logFunctionsAsStrings](#logfunctionsasstrings)                         | `boolean` | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-functions-as-strings.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionsAsStrings")                          |
| [logFunctionGets](#logfunctiongets)                                     | `boolean` | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-function-gets.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionGets")                                       |
| [receiverInterfaces](#receiverinterfaces)                               | `array`   | Optional | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-receiver-interfaces-of-interest.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/receiverInterfaces")                      |

## propertiesToInstrument

Members to instrument. A name is an own member of the resolved `object`; `{depth, propertyNames}` lists own members of the prototype `depth` steps up its chain. If empty, every own member up to the entry's `depth` is instrumented.

`propertiesToInstrument`

* is required

* Type: an array of merged types ([Details](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument-items.md))

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument")

### propertiesToInstrument Type

an array of merged types ([Details](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument-items.md))

### propertiesToInstrument Default Value

The default value is:

```json
[]
```

## nonExistingPropertiesToInstrument

An array of non-existing properties to instrument on this object.

`nonExistingPropertiesToInstrument`

* is required

* Type: `string[]`

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-non-existing-properties-to-instrument.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/nonExistingPropertiesToInstrument")

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

* is required

* Type: `string[]`

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-excluded-properties.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/excludedProperties")

### excludedProperties Type

`string[]`

### excludedProperties Default Value

The default value is:

```json
[]
```

## overwrittenProperties

A property whose value will be overwritten during instrumentation

`overwrittenProperties`

* is optional

* Type: `object[]` ([Details](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-overwritten-property-items.md))

* can be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-overwritten-property.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/overwrittenProperties")

### overwrittenProperties Type

`object[]` ([Details](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-overwritten-property-items.md))

### overwrittenProperties Default Value

The default value is:

```json
[]
```

## logCallStack

Set to true save the call stack info with each property call.

`logCallStack`

* is required

* Type: `boolean` ([Log call stack?](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-call-stack.md))

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-call-stack.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/logCallStack")

### logCallStack Type

`boolean` ([Log call stack?](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-call-stack.md))

### logCallStack Default Value

The default value is:

```json
false
```

## logFunctionsAsStrings

Set to true to save args that are functions as strings during argument serialization. If false `FUNCTION` is recorded.

`logFunctionsAsStrings`

* is required

* Type: `boolean` ([Log functions as strings?](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-functions-as-strings.md))

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-functions-as-strings.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionsAsStrings")

### logFunctionsAsStrings Type

`boolean` ([Log functions as strings?](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-functions-as-strings.md))

### logFunctionsAsStrings Default Value

The default value is:

```json
false
```

## logFunctionGets

Set true to log get requests to properties that are functions. If true when a call is made, the log will contain both the call and a get log.

`logFunctionGets`

* is required

* Type: `boolean` ([Log function gets?](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-function-gets.md))

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-function-gets.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/logFunctionGets")

### logFunctionGets Type

`boolean` ([Log function gets?](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-log-function-gets.md))

### logFunctionGets Default Value

The default value is:

```json
false
```

## receiverInterfaces

For a method hooked once on a shared prototype (e.g. `addEventListener` on `EventTarget`): the receiver interfaces whose calls are recorded; when absent, every call is. `symbol` stays `<owner>.<method>`. The `receiver` column holds the receiver's interface for every record either way, read from its `constructor.name` through the Xray, so the page cannot spoof it.

`receiverInterfaces`

* is optional

* Type: `string[]`

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-receiver-interfaces-of-interest.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/receiverInterfaces")

### receiverInterfaces Type

`string[]`

### receiverInterfaces Constraints

**minimum number of items**: the minimum number of items for this array is: `1`
