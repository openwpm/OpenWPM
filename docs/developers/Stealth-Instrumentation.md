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
Navigator, `document.cookie`, `document.referrer`.

**Captured additionally by stealth:** `AudioWorkletNode` (the modern
replacement legacy lacks); all `Screen` properties (legacy records only
`colorDepth`/`pixelDepth`).

**Not captured by stealth (regressions vs legacy fingerprinting preset):**

| Lost signal | Legacy | Stealth | Notes |
|---|---|---|---|
| `window.name` | instrumented | not instrumented | Loses a cross-origin tracking vector. |
| `window.localStorage` / `window.sessionStorage` property access | instrumented at `window` level | only the `Storage` prototype methods | The actual `getItem`/`setItem` calls are still recorded; only the property *access* logging is lost. |
| `nonExistingPropertiesToInstrument` (honey properties) | supported | unused | Cannot instrument access to non-existent properties. |

These are properties of the **bundled default** surface, not hard limits of
stealth mode: a study can capture any of these by supplying a custom
`stealth_js_instrument_settings` (see "Configuring the instrumented surface").

## Test coverage

`test/test_stealth.py` is requirement-driven: each test maps to a numbered
requirement in `docs/developers/Stealth-Requirements.md`. See that document for
the full detectability (D1–D8), disruptability (X1–X3), attribution (A1) and
configurability (C1) matrices and the per-requirement test names. In summary:

- **Detectability** — `stealth_detection.html` exercises the D1–D8 vectors;
  `TestStealthDetectability` asserts stealth passes every vector and that legacy
  trips the reliable subset (D2/D3/D4) as a control.
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
