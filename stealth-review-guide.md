---
title: "Reviewer's guide: stealth instrument PR #1154"
tags: ["review", "stealth", "design-doc"]
sources: []
contributors: ["claude"]
created: 2026-06-16
updated: 2026-06-16
---


## Design Specification

### how to use this

The PR is ~9000 added lines, but the *review surface* is ~2 files / ~4600 lines; the rest is tests (skim, trust-calibrated), docs (read first as the map), and generated `.d.ts` (skip). Read the design (Stealth-Instrumentation.md + ADR-0001) first, then the two core files, then skim tests. Per-commit haters get this page as shared context so they don't have to re-derive the architecture or carry "fixed-later" state.

### architecture in one screen

- The stealth instrument runs in the extension's **privileged content-script compartment**; the page runs in its own. Firefox's **Xray membrane** sits between them. The instrument exposes wrappers to the page via `exportFunction` so they look native (`[native code]` toString, native `.name`/`.length`/arity), and the page can't see privileged artifacts (`wrappedJSObject` is undefined to it; no `moz-extension://` stack frames).
- It hooks **prototypes**, never instances (Xray forbids accessor-defines on `[Object]`/`[Array]` instances — this is the one true coverage ceiling).
- Records to the same `javascript` table/schema as legacy, with `symbol` byte-identical for directly-instrumented members. For **shared-prototype (inherited) methods** it records a static `symbol` (`EventTarget.addEventListener`) plus the runtime receiver interface in a new nullable **`receiver`** column.
- The **sweep** (`openwpm/utilities/stealth_settings.py`) is a browser-based translator: legacy `js_instrument_settings` → stealth-shaped config. It expands `recursive` (rejected at runtime) by walking the live object graph; captures own members narrowly and real-interface inherited methods via interface-filtered shared-prototype entries; surfaces what it can't translate as honest residue.

### proposed clean commit stack (the reshape target — confirm before i rewrite history)

Each commit is the *final* state of its area, self-contained, no later fixups. Deps-ordered. Tip stays identical (CI-green preserved).

1. **feat(stealth): core stealth JS instrument** — `Extension/src/stealth/*` + `Extension/src/schema.ts` + `openwpm/config.py` (the `stealth_js_instrument` flag, mutual-exclusion with `js_instrument`, recursive→ConfigError). The wrapping engine.
   - Scrutinize: the `exportFunction`/Proxy Xray crossing; arity/`name`/`toString` native-faking (`functionGenerator`/`makeArityForwarder`); `getReceiverInterfaceName` (the B' receiver read); `needsWrapper` + `getObjectProperties` coalescing; the `inLog` reentrancy guard; the bundled fingerprinting `settings.ts`.
   - Verified: FingerprintJS byte-identical to vanilla (27/28 components; only the deliberate `webdriver→false`); 50+ introspection probes clean; multiple the-hater passes on the Xray reads (robust against `constructor` tampering, null proto, primitives).
2. **feat(storage): `receiver` column for interface-attributed capture** — `schema.sql` + `parquet_schema.py` (kept in sync) + `javascript-instrument.ts` (ingestion) + `test/storage/test_values.py`.
   - Scrutinize: SQLite/Parquet column sync; NULL for all non-shared rows.
   - Verified: storage round-trip test; hater confirmed NULL-safe end-to-end.
3. **feat(stealth): legacy→stealth settings sweep** — `openwpm/utilities/stealth_settings.py` + settings schema JSON (+ generated d.ts) + legacy-shape `ConfigError` hint in config.py.
   - Scrutinize: walker fidelity to legacy's `instrumentObject` descent; real-interface-vs-universal-vs-residue classification (name-based across the Xray realm); needsWrapper consolidation (one entry per owner, all members); narrow own-name capture (`stealthOwnNames ∩ requested`); residue honesty (nothing silently dropped).
   - Verified: symbol-parity, over-capture (narrow→wide), multi-member silent-drop, honey-prop residue lie — each found+fixed by the-hater with FAIL-before/PASS-after.
4. **feat(stealth): opt-in `--capture-universal-members` flag** — the flag in `stealth_settings.py`.
   - Scrutinize: the flag gates Object/Function/Array consistently; the page-wide-`toString` warning is honest; default OFF = unchanged (universal→residue).
   - Verified: runtime crawl test (navigator.toString captured w/ receiver=Navigator, div.toString dropped, no reentrancy); Function gating FAIL-before/PASS-after.
5. **test(stealth): detection-vector + capture + sweep suite** — `test/test_stealth.py` + `test/test_pages/*`. (OPEN QUESTION: keep tests in one commit, or fold each test group into the commit it tests? Tests-with-code is more coherent per-commit but more reshape surgery — your call.)
   - Scrutinize: are the tests non-vacuous + non-masking? (The session's haters specifically hunted these for prefix-blind `LIKE` masking and vacuity; the guide flags which classes were stress-tested.)
6. **docs(stealth): instrumentation guide + ADR-0001** — `Stealth-Instrumentation.md`, `adr/0001-stealth-legacy-coexistence.md`.
   - Scrutinize: accuracy vs the code; the "collapsed frontier" + "stealth more tamper-resilient" framing. (Hater-verified accurate.)

### the two core files (deep-dive pointers)

**`Extension/src/stealth/instrument.ts`** — `instrument`→`instrumentFunction`→`functionGenerator`→`temp` forwarder (has `this`=receiver); `logCall` (sets `inLog`, builds the record, the `receiverInterfaces` filter + `receiver` field); `makeArityForwarder` (per-arity codegen so Xray reads native `.length`); `getReceiverInterfaceName` (`Object.getPrototypeOf(this).constructor.name`); `getObjectProperties` (+ the same-prototype coalescing that makes multi-member work); `needsWrapper`.
**`openwpm/utilities/stealth_settings.py`** — the injected walker JS (replays legacy `getPropertyNames` own+chain + `instrumentObject` descent); `inheritedOwners`/`_inherited_members_of_node` (classification); `_shared_prototype_entries` (consolidation + receiverInterfaces union); `_stealth_entry_from_node` (narrow own-name capture); residue assembly; the flag.

### verification record (review these areas lighter)

- Detectability: real-world FingerprintJS oracle = indistinguishable; introspection sweep clean. Strong.
- Sweep correctness: every gap found this session (symbol parity, over-capture, multi-member, honey-prop, universal-flag) was caught by the-hater and fixed with FAIL-before/PASS-after, then re-verified.
- Recursive ceiling: re-verified real (Xray forbids instance accessor-defines; wrappedJSObject/Proxy substitution diverges identity).
- The one inherent gap: per-instance (vs per-interface) attribution for shared methods; recursion into non-interface plain Object/Array.

