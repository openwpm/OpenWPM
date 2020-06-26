# Prevent sets? Schema

```txt
http://example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/preventSets
```

Set to true to prevent nested objects and functions from being overwritten (and thus having their instrumentation removed). Other properties (static values) can still be set with this is enabled.


| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                      |
| :------------------ | ---------- | -------------- | ----------------------- | :---------------- | --------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [js_instrument_settings.schema.json\*](../../schemas/js_instrument_settings.schema.json "open original schema") |

## preventSets Type

`boolean` ([Prevent sets?](js_instrument_settings-settings-objects-properties-log-settings-properties-prevent-sets.md))
