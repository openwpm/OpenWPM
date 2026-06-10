# Stealth Instrumentation — Requirements & Test Matrix

This is a lightweight requirements specification for the stealth JavaScript
instrumentation. Each requirement is derived from a concrete concern in Krumnow,
Jonker & Karsch, *"Analysing and strengthening OpenWPM's reliability"*
(arXiv:2205.08890, 2022), and maps to a test that demonstrates the **legacy**
instrument exhibits the problem while the **stealth** instrument does not.

Concerns fall into two families:

- **Detectability (D)** — a page can *tell* OpenWPM's instrumentation is present
  and refuse to behave normally.
- **Disruptability (X)** — a page can *corrupt or evade* the data collection,
  silently degrading the dataset.

Tests live in `test/test_stealth.py`; detection vectors are exercised by
`test/test_pages/stealth_detection.html`, disruption attacks by
`test/test_pages/stealth_disruption_*.html`.

## Detectability requirements

| ID | Requirement | Attack mechanism (how a page detects) | Legacy outcome | Stealth defense | Test (result key) |
|----|-------------|----------------------------------------|----------------|------------------|-------------------|
| **D1** | `navigator.webdriver` is not exposed as `true` | read `navigator.webdriver` | env-dependent | `overwrittenProperties: webdriver→false` in `settings.ts` | `webdriver_flag` |
| **D2** | Instrumented **functions** report `[native code]` | `Function.prototype.toString.call(fn)` on canvas / storage / WebRTC methods | wrapper body leaks ❌ | `exportFunction` + `toString` proxy | `canvas_functions_native`, `storage_functions_native`, `rtc_native` |
| **D3** | Instrumented **getters** report `[native code]` | `toString` of `Navigator.prototype.userAgent` getter | wrapper leaks ❌ | native-looking getter via `exportFunction` | `navigator_native` |
| **D4** | No OpenWPM globals are leaked | `typeof window.getInstrumentJS / jsInstruments / instrumentFingerprintingApis` | legacy injects `window.getInstrumentJS` ❌ | nothing added to page global scope | `no_global_leaks` |
| **D5** | Constructors preserved on instrumented objects | `obj.constructor`, `obj.__proto__.constructor` | sometimes stripped | per-prototype overwrite leaves chain intact | `constructors_present` |
| **D6** | `Function.prototype.bind` integrity | compare `bind.toString()` shape | tamper check | `bind` untouched | `bind_integrity` |
| **D7** | Error stacks free of `moz-extension://` | force an error, inspect `e.stack` | depends on injection path | `error.ts` rebuilds errors, strips extension frames | `clean_error_stacks` |
| **D8** | No prototype pollution / no extra props | `Object.getOwnPropertyNames(Object.prototype)` members must NOT be **own** properties of an instrumented prototype (e.g. `CanvasRenderingContext2D.prototype`) | legacy flattens ancestor prototypes ❌ — `Object.getPropertyNames` concatenates the whole chain and each name is `defineProperty`'d back onto the first object, so `hasOwnProperty`/`valueOf`/`isPrototypeOf`/… leak down as own properties | per-prototype overwrite leaves the chain shape intact | `no_extra_prototype_properties` |

> **Confidence note (ratcheted from an empirical Firefox 150 run).** A real
> headless run recorded the legacy detection-page results, so the
> `legacy_detectable` flags now reflect observed behaviour rather than a guess:
>
> - **Legacy provably DETECTED (control asserted):** D1 `webdriver_flag`
>   (Selenium sets `navigator.webdriver=true`; legacy never overrides it),
>   D2 `canvas/storage/rtc` (wrapper bodies leak via `toString`),
>   D4 `no_global_leaks` (legacy injects `window.getInstrumentJS`),
>   D5 `constructors_present` (legacy's chain manipulation triggers
>   `too much recursion` when reading `constructor`), and D8
>   `no_extra_prototype_properties` (ancestor-prototype flattening — see the D8
>   row above).
> - **Legacy NOT reliably detected in this build (stealth-only, `None`):** D3
>   `navigator_native` (the legacy fingerprinting collection instruments the
>   `window.navigator` *instance*, not the `Navigator.prototype.userAgent`
>   getter the page probes, so that getter stays native), D6 `bind_integrity`,
>   and D7 `clean_error_stacks`.
>
> The **stealth** direction is asserted unconditionally for all ten vectors and
> passed every one in the same run.

## Disruptability requirements

These are the paper's data-integrity attacks (RQ5–RQ8). The legacy instrument
ships records page→extension via `document.dispatchEvent(new CustomEvent(eventId,
…))` (see `content/javascript-instrument-page-scope.ts:8`), relayed by a
`document.addEventListener(eventId, …)` listener
(`content/javascript-instrument-content-scope.ts:53`). Both the dispatcher and
the event id are reachable from page script, so a hostile page can suppress or
forge records. The stealth instrument calls the privileged
`browser.runtime.sendMessage` directly from an exported function
(`stealth/instrument.ts:notify`), which page script cannot reach.

| ID | Requirement | Attack mechanism | Legacy outcome | Stealth defense | Test |
|----|-------------|------------------|----------------|------------------|------|
| **X1** | A page cannot **suppress** record delivery | override `document.dispatchEvent` to swallow events, then call instrumented APIs | post-hijack calls dropped ❌ | privileged messaging bypasses the DOM | `stealth_disruption_suppress.html` |
| **X2** | A page cannot **forge** records | grab `eventId` (via an intercepted dispatch), emit `CustomEvent(eventId, {detail:[forged]})` | forged rows enter the DB ❌ | no page-reachable channel to inject into | `stealth_disruption_forge.html` |
| **X3** | Dynamically-created **iframes** are instrumented | JS-create an iframe that runs an API call before injection | timing gap can miss frames | `stealth.ts` frame protection + `MutationObserver` | *(spec'd; differential is timing-sensitive — investigate before implementing)* |

## Attribution requirement

| ID | Requirement | Why it matters | Stealth defense | Test |
|----|-------------|----------------|------------------|------|
| **A1** | Records attribute to the **page script** with a stack free of extension frames | a polluted `call_stack` (or wrong `script_url`) corrupts provenance analysis and re-leaks `moz-extension://` | `instrument.ts` parses `script_url` from the first non-extension frame; the recorded `call_stack` then has **every** extension frame filtered out (not just the leading prefix), so an API invoked purely from instrumentation, or a page that calls back into instrumented APIs, can never leak `moz-extension://`. When no page frame remains the context is blank. | `stealth_attribution.html` |

## Configurability requirement

| ID | Requirement | Why it matters | Mechanism | Test |
|----|-------------|----------------|-----------|------|
| **C1** | The instrumented surface is **runtime-configurable** | studies must instrument arbitrary APIs without forking the extension | `browser_params.stealth_js_instrument_settings` (defaults to `None` → bundled `settings.ts`) is validated against `schemas/js_instrument_settings.schema.json` and injected as `window.openWpmStealthInstrumentSettings` | `TestStealthConfigurability` |

> **Configurability is RESTORED.** A custom surface uses bare global names for
> `object` (e.g. `"CanvasRenderingContext2D"`, `"Navigator"`, `"document"`),
> the full stealth shape (top-level `depth`, nested `propertiesToInstrument`
> `{depth, propertyNames}`, and `overwrittenProperties`). When unset, the
> bundled default is used, so existing behaviour is unchanged.

## Test matrix summary

Each requirement is a separate, named test so failures are traceable to a
specific concern. To keep browser launches bounded, the detection page is run
**once per mode** (class-scoped fixtures) and every D* test asserts against the
shared results; X* tests each run their own attack page per mode.

- **D1–D8** → `TestStealthDetectability` — `test_stealth_undetectable[D*]`
  (asserts stealth clean, all ten vectors) and `test_legacy_detectable`
  (asserts legacy trips the empirically-confirmed vectors:
  D1, D2×3, D4, D5, D8).
- **X1** → `TestStealthDisruption` — `test_x1_legacy_channel_can_be_suppressed`
  (control: legacy loses records) and
  `test_x1_stealth_channel_resists_suppression` (stealth keeps them).
- **X2** → `TestStealthDisruption` — `test_x2_legacy_channel_can_be_forged`
  (control: legacy accepts the forged `FORGED.injectedByPage` row) and
  `test_x2_stealth_channel_rejects_forgery` (stealth rejects it).
- **A1** → `TestStealthDisruption` —
  `test_attribution_stealth_records_page_script_and_clean_stack` (stealth
  `script_url` names the page and `call_stack` has no `moz-extension://`) with
  `test_attribution_legacy_records_page_script` as reference.
- **C1** → `TestStealthConfigurability` — `test_custom_settings_take_effect`
  (a custom `instrumentedName` proves the configured surface replaced the
  default) and `test_custom_settings_stay_undetectable` (a custom surface still
  passes every D* vector).
- **X3** → specified above; same paired pattern, pending investigation (the
  differential is timing-sensitive, so no test is shipped to avoid flakiness).

> The new browser-driven tests require a Firefox + xpi run to validate; they are
> written from the code paths above but have not been executed in CI yet.
