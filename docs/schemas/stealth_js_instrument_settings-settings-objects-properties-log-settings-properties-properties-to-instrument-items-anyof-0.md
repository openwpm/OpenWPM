# Untitled object in Stealth JS Instrument Settings Schema

```txt
http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument/items/anyOf/0
```



| Abstract            | Extensible | Status         | Identifiable | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                                         |
| :------------------ | :--------- | :------------- | :----------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | No           | Forbidden         | Forbidden             | none                | [stealth\_js\_instrument\_settings.schema.json\*](../../schemas/stealth_js_instrument_settings.schema.json "open original schema") |

## 0 Type

`object` ([Details](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument-items-anyof-0.md))

# 0 Properties

| Property                        | Type      | Required | Nullable       | Defined by                                                                                                                                                                                                                                                                                                                                                |
| :------------------------------ | :-------- | :------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [depth](#depth)                 | `integer` | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument-items-anyof-0-properties-depth.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument/items/anyOf/0/properties/depth")                 |
| [propertyNames](#propertynames) | `array`   | Required | cannot be null | [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument-items-anyof-0-properties-propertynames.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument/items/anyOf/0/properties/propertyNames") |

## depth

Prototype-chain offset from the resolved `object` of the prototype owning `propertyNames`.

`depth`

* is required

* Type: `integer`

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument-items-anyof-0-properties-depth.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument/items/anyOf/0/properties/depth")

### depth Type

`integer`

### depth Constraints

**minimum**: the value of this number must greater than or equal to: `0`

## propertyNames



`propertyNames`

* is required

* Type: `string[]`

* cannot be null

* defined in: [Stealth JS Instrument Settings](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument-items-anyof-0-properties-propertynames.md "http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument/items/anyOf/0/properties/propertyNames")

### propertyNames Type

`string[]`
