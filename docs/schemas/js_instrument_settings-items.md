# Untitled object in JS Instrument Settings Schema

```txt
http://example.com/js-instrument-settings.schema#/items
```




| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                      |
| :------------------ | ---------- | -------------- | ------------ | :---------------- | --------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [js_instrument_settings.schema.json\*](../../schemas/js_instrument_settings.schema.json "open original schema") |

## items Type

`object` ([Details](js_instrument_settings-items.md))

# undefined Properties

| Property                              | Type     | Required | Nullable       | Defined by                                                                                                                                                                       |
| :------------------------------------ | -------- | -------- | -------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [object](#object)                     | `string` | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-object.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/object")                     |
| [instrumentedName](#instrumentedName) | `string` | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-instrumentedname.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/instrumentedName") |
| [logSettings](#logSettings)           | `object` | Required | cannot be null | [JS Instrument Settings](js_instrument_settings-items-properties-logsettings.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings")           |

## object

The JS object to be instrumented.


`object`

-   is required
-   Type: `string`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-object.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/object")

### object Type

`string`

## instrumentedName

The name recorded by the instrumentation for this object.


`instrumentedName`

-   is required
-   Type: `string`
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-instrumentedname.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/instrumentedName")

### instrumentedName Type

`string`

## logSettings

The log settings object.


`logSettings`

-   is required
-   Type: `object` ([Details](js_instrument_settings-items-properties-logsettings.md))
-   cannot be null
-   defined in: [JS Instrument Settings](js_instrument_settings-items-properties-logsettings.md "http&#x3A;//example.com/js-instrument-settings.schema#/items/properties/logSettings")

### logSettings Type

`object` ([Details](js_instrument_settings-items-properties-logsettings.md))
