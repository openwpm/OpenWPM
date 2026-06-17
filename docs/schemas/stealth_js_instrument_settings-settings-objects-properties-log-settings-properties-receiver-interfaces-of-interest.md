# Receiver interfaces of interest Schema

```txt
http://example.com/stealth-js-instrument-settings.schema#/items/properties/logSettings/properties/receiverInterfaces
```

For a method hooked once on a shared prototype (e.g. `addEventListener` on `EventTarget`): the receiver interfaces whose calls are recorded; when absent, every call is. `symbol` stays `<owner>.<method>`. The `receiver` column holds the receiver's interface for every record either way, read from its `constructor.name` through the Xray, so the page cannot spoof it.

| Abstract            | Extensible | Status         | Identifiable            | Custom Properties | Additional Properties | Access Restrictions | Defined In                                                                                                                         |
| :------------------ | :--------- | :------------- | :---------------------- | :---------------- | :-------------------- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| Can be instantiated | No         | Unknown status | Unknown identifiability | Forbidden         | Allowed               | none                | [stealth\_js\_instrument\_settings.schema.json\*](../../schemas/stealth_js_instrument_settings.schema.json "open original schema") |

## receiverInterfaces Type

`string[]`

## receiverInterfaces Constraints

**minimum number of items**: the minimum number of items for this array is: `1`
