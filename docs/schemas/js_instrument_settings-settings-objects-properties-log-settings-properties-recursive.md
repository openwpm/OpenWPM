# Recursive? Schema

```txt
http://example.com/js-instrument-settings.schema#/items/properties/logSettings/properties/recursive
```

Set to `true` to recursively instrument all object properties of the given `object`. NOTE: (1) `propertiesToInstrument` does not propagate to sub-objects. (2) Sub-objects of prototypes can not be instrumented recursively as these properties can not be accessed until an instance of the prototype is created.


| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                      |
| :------------------ | ---------- | -------------- | ----------------------- | :---------------- | --------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [js_instrument_settings.schema.json\*](../../schemas/js_instrument_settings.schema.json "open original schema") |

## recursive Type

`boolean` ([Recursive?](js_instrument_settings-settings-objects-properties-log-settings-properties-recursive.md))
