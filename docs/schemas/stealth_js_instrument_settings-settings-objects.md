# Settings objects Schema

```txt
http://example.com/stealth-js-instrument-settings.schema#/items
```



| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                                         |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [stealth\_js\_instrument\_settings.schema.json\*](../../schemas/stealth_js_instrument_settings.schema.json "open original schema") |

## items Type

`object` ([Settings objects](stealth_js_instrument_settings-settings-objects.md))

# items Properties

| Property                              | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                      |
| :------------------------------------ | :-------- | :------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [object](#object)                     | `string`  | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-js-object.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/object")                   |
| [instrumentedName](#instrumentedname) | `string`  | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-instrumented-name.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/instrumentedName") |
| [depth](#depth)                       | `integer` | Optional | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-prototype-depth.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/depth")              |
| [logSettings](#logsettings)           | `object`  | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings")           |

## object

The bare global name to instrument, e.g. `Navigator` or `document`. A constructor resolves to its prototype, any other global to the object itself.

`object`

* is required

* Type: `string` ([JS object](stealth_js_instrument_settings-settings-objects-properties-js-object.md))

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-js-object.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/object")

### object Type

`string` ([JS object](stealth_js_instrument_settings-settings-objects-properties-js-object.md))

### object Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[A-Za-z_$][A-Za-z0-9_$]*$
```

[try pattern](https://regexr.com/?expression=%5E%5BA-Za-z_%24%5D%5BA-Za-z0-9_%24%5D*%24 "try regular expression with regexr.com")

## instrumentedName

The name recorded by the instrumentation for this object.

`instrumentedName`

* is required

* Type: `string` ([Instrumented name](stealth_js_instrument_settings-settings-objects-properties-instrumented-name.md))

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-instrumented-name.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/instrumentedName")

### instrumentedName Type

`string` ([Instrumented name](stealth_js_instrument_settings-settings-objects-properties-instrumented-name.md))

## depth

Prototype-chain offset from the resolved `object`. With an empty `propertiesToInstrument`, the own members of every prototype from offset 0 to this one are instrumented; `nonExistingPropertiesToInstrument` names are added at this offset.

`depth`

* is optional

* Type: `integer` ([Prototype depth](stealth_js_instrument_settings-settings-objects-properties-prototype-depth.md))

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-prototype-depth.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/depth")

### depth Type

`integer` ([Prototype depth](stealth_js_instrument_settings-settings-objects-properties-prototype-depth.md))

### depth Constraints

**minimum**: the value of this number must greater than or equal to: `0`

### depth Default Value

The default value is:

```json
0
```

## logSettings

The log settings object.

`logSettings`

* is required

* Type: `object` ([Log settings](stealth_js_instrument_settings-settings-objects-properties-log-settings.md))

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings")

### logSettings Type

`object` ([Log settings](stealth_js_instrument_settings-settings-objects-properties-log-settings.md))
