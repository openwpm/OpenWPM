# Stealth JavaScript Instrumentation

This document describes the *stealth* JavaScript instrumentation mode added by
`stealth_js_instrument`, the threat model it addresses, and exactly how its
data capture differs from the legacy `js_instrument` mode. It is intended both
as user-facing documentation and as a reviewer's reference for the trade-offs
involved.

## Background: why stealth instrumentation exists

The design follows Krumnow, Jonker & Karsch, *"Analysing and strengthening
OpenWPM's reliability"* (arXiv:2205.08890, 2022). That paper shows OpenWPM is
both **easily detectable** and **vulnerable to data-integrity attacks**, and
proposes the mitigations implemented here.

The paper splits the problem into two families.

### Detectability (the fingerprint surface)

A page can recognise OpenWPM's *legacy* instrument from artifacts it leaks:

- **`toString()` leak** — wrapped functions return their JS body instead of
  `[native code]`. The single most reliable tell.
- **Prototype pollution** — properties from ancestor prototypes are flattened
  onto the first prototype, producing a structurally anomalous chain.
- **Leaked globals** — `window.jsInstruments`, `instrumentFingerprintingApis`,
  and `getInstrumentJS` exist in no real browser. These are the OpenWPM-specific
  signature; the paper found 356 sites keying on exactly these (CHEQ, reCAPTCHA,
  AdZouk).
- **`navigator.webdriver === true`** — the Selenium tell.
- **Error stack traces** leaking `moz-extension://…` frames.

The paper measured **~14% of Tranco Top 100K front pages** running Selenium
detection, rising ~37% on subpages.

### Data-integrity attacks

These silently corrupt a dataset rather than merely blocking the crawler:

- **Event-dispatcher hijacking** — legacy OpenWPM ships instrumentation data
  page→extension via DOM `CustomEvent`. A page can read the random event ID,
  overwrite `document.dispatchEvent`, and drop all instrumentation messages.
- **Fake-data injection** — the same hole lets a page emit events with
  OpenWPM's ID and write arbitrary rows into the dataset.
- **Unobserved iframes** — dynamically-created iframes can execute before
  instrumentation is injected.

## What stealth mode implements

Stealth mode is a direct implementation of the paper's §7 mitigations
(adapted from CanvasBlocker's approach):

1. **Native `toString()`** is preserved via Firefox's privileged
   `exportFunction`, with a `toString` proxy so wrappers report `[native code]`.
2. **Per-prototype overwrites** (no flattening) eliminate prototype pollution.
3. **No leaked globals**; the page context stays clean.
4. **Faked error stacks** — thrown errors are rebuilt with extension frames
   stripped while preserving name/message/fileName (see `stealth/error.ts`).
5. **Off-DOM messaging** — instrumentation data is sent via the privileged
   `browser.runtime` channel rather than DOM events, so `dispatchEvent`
   hijacking cannot drop or forge records.
6. **Frame protection** — `contentWindow`/`contentDocument`/`document.write`/
   `window.open` are hooked, plus a `MutationObserver`, so every new frame is
   instrumented (see `stealth/stealth.ts`).

Key files: `Extension/src/stealth/{stealth,instrument,settings,error}.ts`.

## Enabling stealth mode

```python
browser_params.stealth_js_instrument = True
browser_params.js_instrument = False  # mutually exclusive — see below
```

`stealth_js_instrument` and `js_instrument` **cannot both be enabled** on the
same browser; doing so raises `ConfigError`. Both instruments are
runtime-configurable — legacy via `js_instrument_settings`, stealth via
`stealth_js_instrument_settings` (see "Configuring the instrumented surface"
below). The reason to choose between them is **detectability**: stealth is
undetectable by the page (at the cost of a handful of capture trade-offs
documented below), whereas legacy leaks the artifacts described above and can be
fingerprinted and disrupted.

## Configuring the instrumented surface

The stealth surface is **runtime-configurable** via
`browser_params.stealth_js_instrument_settings`:

```python
browser_params.stealth_js_instrument = True
browser_params.js_instrument = False
# Leave unset to use the bundled fingerprinting default, or override:
browser_params.stealth_js_instrument_settings = [
    {
        "object": "CanvasRenderingContext2D",   # bare global name (see below)
        "instrumentedName": "CanvasRenderingContext2D",
        "depth": 0,
        "logSettings": { ... },
    },
    ...
]
```

When the field is `None` (the default), the instrument uses the bundled set in
`Extension/src/stealth/settings.ts`, so the out-of-the-box behaviour is
unchanged. When set, the list is validated against
`schemas/js_instrument_settings.schema.json` (by
`clean_stealth_js_instrumentation_settings` in `openwpm/js_instrumentation.py`),
written into `browser_params.json`, and injected into the content script as
`window.openWpmStealthInstrumentSettings`. `startInstrument`
(`stealth/instrument.ts`) reads that global when present and otherwise falls
back to the bundled default. The `Navigator.webdriver → false` override lives in
the default; a custom surface that needs it must include it explicitly.

### The `object` naming convention (differs from legacy)

Stealth resolves `object` as a **bare global name** — the property is looked up
directly on the page's global scope (`context.wrappedJSObject[object]`). Use
`"CanvasRenderingContext2D"`, `"Navigator"`, `"Storage"`, `"document"`, etc.

This is **not** the legacy convention. Legacy `js_instrument_settings` express
`object` as a dotted/bracketed `window` path
(`"window['CanvasRenderingContext2D'].prototype"`,
`"window.document"`) produced by `clean_js_instrumentation_settings`. The two
formats are intentionally separate: the legacy path is untouched, and stealth
settings are supplied in the stealth shape directly.

**Instance vs. prototype properties.** For most objects the named global is a
constructor and stealth instruments its `.prototype` (where the native accessors
live). Some globals are *instances*, though — `document` and `window` — and a
few of their attributes (e.g. `document.cookie`, `window.name`) are accessor
properties defined on the corresponding *interface* prototype
(`Document.prototype`, `Window.prototype`), not on the instance. The `depth`
field in a `propertiesToInstrument` entry walks that many steps up the prototype
chain from the resolved instance to reach the prototype carrying the accessor,
and stealth redefines the property **there**. For example,
`{ object: "window", propertiesToInstrument: [{ depth: 1, propertyNames:
["name", "localStorage", "sessionStorage"] }] }` resolves the `window` instance,
walks one step to `Window.prototype`, and instruments the native accessors in
place. Because the descriptor is replaced on the prototype where the browser
natively defines it — with `exportFunction`-backed getters/setters that report
`[native code]` — no own property is added to the `window` instance and the
masquerade is preserved (this is why instrumenting `window.name` is
undetectable). The default surface deliberately restricts the `window` list to
exactly `name`, `localStorage`, and `sessionStorage`; it does **not** instrument
layout/dimension properties (`innerWidth`, `innerHeight`, `screenX`, …), which
fire constantly and would inflate capture volume without adding tracking signal.

## Data capture: differences from legacy `js_instrument`

The bundled default surface (`Extension/src/stealth/settings.ts`) is a curated,
stealth-shaped configuration rather than a 1:1 copy of the legacy
`collection_fingerprinting` preset.

The records it produces are written to the same `javascript` table with the
same schema (`operation`, `symbol`, `arguments`, `value`, `script_url`,
`func_name`, `call_stack`, …) as legacy mode. For a given captured call the row
shape matches what legacy emits.

> **Fidelity caveat (inherited from legacy).** Like the legacy instrument,
> stealth uses a module-global `inLog` re-entrancy guard
> (`stealth/instrument.ts`): while one instrumented call is being serialized,
> any *further* instrumented get/call triggered during that window — including
> ones the page legitimately makes — is dropped to avoid logging recursion.
> Nested instrumented accesses that occur mid-serialization are therefore not
> guaranteed to be captured. This is pre-existing legacy behaviour, not specific
> to stealth; it is noted here so "same schema, same per-row shape" is not read
> as "every nested access is recorded".

Compared to the legacy `collection_fingerprinting` preset (the default):

**Captured identically:** ScriptProcessorNode, GainNode, AnalyserNode,
OscillatorNode, AudioContext, OfflineAudioContext, RTCPeerConnection,
HTMLCanvasElement, CanvasRenderingContext2D, Storage (`getItem`/`setItem`/…),
Navigator, `document.cookie`, `document.referrer`, `window.name` (get/set),
`window.localStorage` / `window.sessionStorage` (property get).

**Captured additionally by stealth:** `AudioWorkletNode` (the modern
replacement legacy lacks); all `Screen` properties (legacy records only
`colorDepth`/`pixelDepth`).

There are no `logSettings`-level capture regressions versus legacy: every
`logSettings` field is now honoured by the stealth instrument (see
"`logSettings` semantics" below). The bundled default leaves the optional
fields (`recursive`, `preventSets`, `logFunctionGets`,
`nonExistingPropertiesToInstrument`) off, exactly like legacy's
`collection_fingerprinting` preset; a study can enable any of them via a custom
`stealth_js_instrument_settings` (see "Configuring the instrumented surface").

### `logSettings` semantics

All `logSettings` fields are read by the stealth instrument
(`Extension/src/stealth/instrument.ts`) and match the legacy semantics defined
in `Extension/src/lib/js-instruments.ts`:

| Field | Stealth behaviour |
|---|---|
| `propertiesToInstrument` | Named list (with `{depth, propertyNames}`) or, when empty, every own property to `depth`. `excludedProperties`/`overwrittenProperties` are filtered out on **both** paths. |
| `excludedProperties` | Skipped on the named-list path and the instrument-everything path. |
| `overwrittenProperties` | Property value overwritten on read (e.g. `Navigator.webdriver → false`). |
| `logCallStack` | Per-object call-stack capture (page frames only; never `moz-extension://`). |
| `logFunctionsAsStrings` | Function values serialised as their source instead of `"FUNCTION"`. |
| `logFunctionGets` | When an instrumented getter returns a **function**, a `get(function)` row is emitted (and no plain `get`), matching legacy. |
| `preventSets` | When the property currently holds a **function/object**, an assignment is logged as `set(prevented)` and the original setter is **not** called, blocking the write. Plain (string/number) values still pass through. |
| `recursive` + `depth` | The object **returned by an instrumented getter** is instrumented one level down, decrementing `depth`, done lazily at access time so page-built nested objects are reachable. Captures e.g. `obj.nested.leaf` accesses. |
| `nonExistingPropertiesToInstrument` | Names absent from the target get a synthesized, `[native code]`-reporting accessor (backed by a closure variable), so a study can capture access to decoy "honey" property names. |

**Native-arity preservation.** Instrumented functions report the **same
`.length` (arity)** as the native function they replace (e.g.
`canvas.getContext.length === 1`). A naive wrapper forwards via `arguments` and
would expose `.length === 0` — a fingerprint. `copyFunctionArity` redefines
`.length` on the exported, page-visible wrapper using the native descriptor
shape (`{ writable: false, enumerable: false, configurable: true }`). The
frame-protection replacements in `stealth.ts` are wrapped in a `Proxy` over the
native original, so their `.length` is forwarded from that target. The
`function_arity_native` detection vector (`stealth_detection.html`,
`D8b-native-fn-arity`) locks this in; legacy trips it.

**Detectability of `nonExistingPropertiesToInstrument`.** Honey properties are
*intentionally* page-observable — they are bait a tracker is meant to probe.
Stealth makes them native-looking (the synthesized accessor reports
`[native code]`), so they are not identifiable as OpenWPM specifically, but a
page that *knows* a given name should not exist on a real Firefox object could
still notice the decoy. This is inherent to the technique (legacy is identical),
the names are study-chosen rather than an OpenWPM signature, and the field is
empty in the default surface — so the out-of-the-box instrument adds no such
artifact.

## Test coverage

`test/test_stealth.py` is requirement-driven: each test maps to a numbered
requirement in `docs/developers/Stealth-Requirements.md`. See that document for
the full detectability (D1–D8), disruptability (X1–X3), attribution (A1) and
configurability (C1) matrices and the per-requirement test names. In summary:

- **Detectability** — `stealth_detection.html` exercises the D1–D8 vectors plus
  `D8b-native-fn-arity` (instrumented `.length` matches native);
  `TestStealthDetectability` asserts stealth passes every vector and that legacy
  trips the reliable subset (D2/D3/D4/D8b) as a control.
- **`logSettings` fidelity** — `TestStealthLogSettings` proves the stealth
  instrument honours `preventSets` (logs `set(prevented)` and blocks the write),
  `logFunctionGets` (emits `get(function)`), `recursive`/`depth` (captures
  nested-object access), and `nonExistingPropertiesToInstrument` (synthesized
  honey accessor), each with a native-looking / undetectability check where the
  target is a native object (pages `stealth_prevent_sets.html`,
  `stealth_honey_props.html`, `stealth_recursive.html`).
- **Disruptability** — `TestStealthDisruption` runs the X1 (suppression), X2
  (forgery) and X3 (dynamic iframe) attack pages both ways: legacy is shown to
  lose/accept records or miss the parent-context attribution, stealth to resist
  and instrument the dynamic frame.
- **Attribution** — the A1 test asserts stealth records name the page script and
  carry a `call_stack` free of `moz-extension://` frames.
- **Configurability** — `TestStealthConfigurability` proves a custom surface
  replaces the default (via a distinctive `instrumentedName`) and stays
  undetectable.

## Known limitations / future work

- **X3 (dynamic iframes).** Stealth's frame protection (`stealth.ts`
  contentWindow/contentDocument hooks + `MutationObserver`) instruments
  dynamically-created iframes; a paired regression test ships
  (`test_x3_*` in `test/test_stealth.py`, page
  `stealth_disruption_iframe.html`). Empirically both modes record an in-iframe
  `toDataURL`, but only stealth additionally attributes it to the **parent
  page** `document_url` (frame protection runs in the parent's instrumented
  context); legacy records it solely under the frame's own `about:blank`. See
  `Stealth-Requirements.md` for the full empirical finding.
- Out of scope (environment fingerprints, not instrumentation artifacts):
  screen/window position, font enumeration, WebGL deviations, timezone. Also
  out of scope: silent JS delivery via non-`.js` MIME/extension, which concerns
  the HTTP instrument rather than the JS instrument.

## Design decisions

- [ADR 0001: Stealth and legacy JS instrumentation are complementary,
  composable tools](adr/0001-stealth-legacy-coexistence.md) — why stealth
  cannot fully subsume legacy, and the proposed shared-base / partition / XOR-frontier
  architecture for letting the two instruments coexist.
