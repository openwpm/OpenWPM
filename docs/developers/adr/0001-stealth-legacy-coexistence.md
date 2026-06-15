# ADR: Stealth and legacy JS instrumentation are complementary, composable tools

- **Status:** Proposed
- **Date:** 2026-06-15
- **Context PR:** stealth JS instrument (`feat/stealth-js-instrument-v2`)

## Context

OpenWPM has two JavaScript instruments: the **legacy** instrument (`js_instrument`) and the **stealth** instrument (`stealth_js_instrument`). They are currently **mutually exclusive** (a `ConfigError` is raised if both are enabled).

The stealth instrument intercepts APIs with `Proxy`/`exportFunction` across Firefox's **Xray boundary**. That boundary fundamentally prevents a privileged-side wrapper from perfectly impersonating a *native* accessor for certain built-ins — function `.length`/arity, `toString()` returning `[native code]`, and getters that live on `Window.prototype`. For any API a page can cheaply fingerprint that way, **capture and undetectability are mutually exclusive**: you can record the access (and be detectable) or look native (and not record it), but not both.

Therefore stealth **cannot fully subsume legacy**. Some basic APIs (e.g. `window.name`) sit on the capture-XOR-native frontier. Concluding that the two instruments must coexist long-term is the correct architecture, not a concession.

## Prior work

The reliability paper that motivates the stealth instrument — Krumnow, Jonker & Karsch, *Analysing and strengthening OpenWPM's reliability* (arXiv:2205.08890, 2022) — directly supports the framing above, and its own stealth proof-of-concept (`WPMhide`) hit the same frontier.

- **Detection vectors named for the JavaScript instrument** (Sec. 4.1, "Detecting instrumentation"): overwritten functions are caught via `toString` returning the wrapper body instead of `[native code]` (their Listing 1), extra DOM properties (`window.getInstrumentJS`), wrapper frames visible in stack traces, and **prototype pollution** along the prototype chain. These are exactly the tells the ADR treats as the shared-base / XOR-frontier concern.

- **Capture-vs-stealth tradeoff is acknowledged as a hard limit, not just an engineering gap.** Their prototype-pollution fix (Sec. 7.1, "Avoid prototype pollution") overwrites properties per-prototype, but they note: *"this approach has its own limitation, as it is not possible to determine the caller of a function, when a prototype has multiple children … raising the potential to capture unwanted API calls on other children objects."* They could only cover the APIs whose prototypes sit low on the chain: *"most of our these APIs are provided by prototypes close to the bottom, which allows us to cover a wide set of OpenWPM's instrumented APIs"* — i.e. **stealth coverage is a strict subset of what legacy captures**, which is precisely this ADR's "stealth cannot fully subsume legacy."

- **They foresee that some recording is unattainable without becoming detectable / assuming a weaker adversary.** On the HTTP file recorder (Sec. 7.2): *"there is no known way to distinguish JavaScript code from text that is robust against a dedicated obfuscator … an active adversary should be assumed to be capable of hiding JavaScript in a way that would accidentally be filtered out … we recommend in such a case not to use any filtering."* This is the same "per-API / per-configuration, not global" undetectability the ADR records under Consequences.

- **They quantify the capture cost of stealth.** In their open-world evaluation (Sec. 7.3), `WPMhide` received *16.32% fewer cookies* (and 57% fewer trackable cookies) than vanilla OpenWPM. Stealth changes *what gets measured*, reinforcing that the two instruments serve different threat models rather than one replacing the other.

The paper does **not** propose keeping a detectable legacy instrument alongside stealth, nor does it frame the two as a composable partition with an overlap check — that architectural decision is original to this ADR. The paper establishes the *constraint* (a single PoC cannot be both complete and undetectable); this ADR draws the *organisational* conclusion (run two cooperating instruments split along the capture↔detectability frontier).

## Decision

**1. Each instrument holds exactly one invariant absolute, and pushes the other axis as far as it will go under that constraint.**
- **Legacy — capture is absolute.** Move it toward stealth/resilience *only* where doing so never drops a recorded call.
- **Stealth — undetectability is absolute** (practically: passes the realistic detection suite, not "provably undetectable against exhaustive timing/probing"). Move it toward coverage *only* where capturing introduces no detectable tell.

They converge on the same capture↔detectability frontier from opposite ends.

**2. Three layers.**
- **Shared base (capture-safe, used by both):** `navigator.webdriver` hiding, native `toString`/arity, anti-tamper resilience. These don't touch the capture path, so legacy can adopt them and stop failing the *easy* detection checks at zero capture cost. Note: **legacy can exceed stealth on resilience** — making a wrapper non-configurable/non-removable protects capture but is itself a tell, so stealth is capped at "as fragile as the real API" while legacy is not. Most of this code already exists inside stealth (arity/toString machinery); extracting it into a shared base is a refactor, not new invention.
- **Capture wrappers:** legacy (complete, possibly detectable) vs stealth (native-looking, possibly gapped), **partitioned by API** (disjoint sets — no property instrumented by both).
- **XOR frontier:** capture-XOR-native APIs → legacy captures them (detectably), stealth skips them.

**3. Replace blanket mutual-exclusion with an overlap check.** Enabling both is allowed; error *only* if a single property is claimed by both instruments. The instruments' default settings become the recommended partition, so "instrument as much as possible through stealth, hand the rest to legacy" is just "run both with sensible defaults."

## Open question (gates compose viability — resolve before building partition/compose)

Is legacy detectable **only via the APIs it wraps**, or does its injection **footprint** (added globals, content-script artifacts, timing signatures) leak independently? Composing stealth + legacy only yields a stealthy browser if legacy's detectability is **confined to its wrapped properties**. If the footprint itself leaks, the work is not "partition the APIs" but "make legacy's footprint invisible even where its wrappers are detectable" — a different, bigger job. **This must be verified first.**

## Consequences

- "Undetectable" becomes **per-API / per-configuration**, not global. Guidance must state the residual detection surface explicitly and not over-promise.
- **Long-term maintenance of both instruments is expected.** Stealth is not a replacement for legacy; they serve different threat models (legacy: sites that don't adapt or need every API; stealth: measuring the cloaking/anti-bot behavior that detection itself would perturb).
- Enables incremental, independently-valuable wins — e.g. `navigator.webdriver=false` (there is an existing PR) as a *shared-base* feature usable even by detectable legacy, decoupling the automation fingerprint from the instrumentation fingerprint.
- The window.name capture investigation seeds the concrete XOR-frontier list.
- **Confirmed coverage ceiling: `recursive`.** Empirically, `window.name` and native function arity turned out **not** to be ceilings (stealth captures both natively). `recursive` instrumentation **is** the concrete ceiling this ADR anticipated: it requires mutating the page's in-page object graph, which is incompatible with stealth's isolated compartment (Firefox Xray forbids accessor-defines on `Object`/`Array` instances; `wrappedJSObject` waiving gives a different object identity). It is rejected at config time and stays on legacy `js_instrument`. See `docs/developers/Stealth-Instrumentation.md` ("Limitations: `recursive` is unsupported").

## Precursors / follow-ups

1. Verify legacy's footprint-vs-wrapped-API detectability (the open question above).
2. Resolve window.name capture-vs-detectability (does a native-looking capture exist, or is it XOR → legacy?).
3. Relax the config from mutual-exclusion to overlap-validation.
4. Extract the shared base layer (webdriver/toString/arity/resilience) from stealth so legacy can use it.
