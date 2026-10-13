# Prototype depth Schema

```txt
http://example.com/stealth-js-instrument-settings.schema#/items/properties/depth
```

Prototype-chain offset from the resolved `object`. With an empty `propertiesToInstrument`, the own members of every prototype from offset 0 to this one are instrumented; `nonExistingPropertiesToInstrument` names are added at this offset.

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                                         |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [stealth\_js\_instrument\_settings.schema.json\*](../../schemas/stealth_js_instrument_settings.schema.json "open original schema") |

## depth Type

`integer` ([Prototype depth](stealth_js_instrument_settings-settings-objects-properties-prototype-depth.md))

## depth Constraints

**minimum**: the value of this number must greater than or equal to: `0`

## depth Default Value

The default value is:

```json
0
```
