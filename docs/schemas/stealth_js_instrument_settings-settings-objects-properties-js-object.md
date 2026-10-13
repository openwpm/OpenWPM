# JS object Schema

```txt
http://example.com/stealth-js-instrument-settings.schema#/items/properties/object
```

The bare global name to instrument, e.g. `Navigator` or `document`. A constructor resolves to its prototype, any other global to the object itself.

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                                         |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [stealth\_js\_instrument\_settings.schema.json\*](../../schemas/stealth_js_instrument_settings.schema.json "open original schema") |

## object Type

`string` ([JS object](stealth_js_instrument_settings-settings-objects-properties-js-object.md))

## object Constraints

**pattern**: the string must match the following regular expression:&#x20;

```regexp
^[A-Za-z_$][A-Za-z0-9_$]*$
```

[try pattern](https://regexr.com/?expression=%5E%5BA-Za-z_%24%5D%5BA-Za-z0-9_%24%5D*%24 "try regular expression with regexr.com")
