# Properties to instrument Schema

```txt
http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/propertiesToInstrument
```

Members to instrument. A name is an own member of the resolved `object`; `{depth, propertyNames}` lists own members of the prototype `depth` steps up its chain. If empty, every own member up to the entry's `depth` is instrumented.

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                                         |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [stealth\_js\_instrument\_settings.schema.json\*](../../schemas/stealth_js_instrument_settings.schema.json "open original schema") |

## propertiesToInstrument Type

an array of merged types ([Details](stealth_js_instrument_settings-settings-objects-properties-log-settings-properties-properties-to-instrument-items.md))

## propertiesToInstrument Default Value

The default value is:

```json
[]
```
