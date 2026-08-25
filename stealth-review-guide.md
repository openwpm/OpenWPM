---
title: "Reviewer's guide: stealth instrument PR #1154"
tags: ["review", "stealth", "design-doc"]
sources: []
contributors: ["claude"]
created: 2026-06-16
updated: 2026-08-25
---

## Design Specification

### Standard of evidence for this page

Every statement below about the **legacy** instrument names an experiment a reviewer can re-run — a
test id, a `file:line`, or a PR number. Anything that could not be backed that way was **deleted**,
not softened. Removed in this revision, and not to be reintroduced without an artifact:

- A "FingerprintJS oracle, 27/28 components byte-identical, Strong" result. **No FingerprintJS
  harness, page, fixture, dependency, or test exists** on this branch, on master, or anywhere in git
  history (`grep -rli fingerprintjs --exclude-dir=node_modules --exclude-dir=.git .` is empty;
  `git log --all -S fingerprintjs -i` matches only the commit that added the previous revision of
  this page). The same claim is still live in the PR #1154 body and should be struck there too.
- A "50+ introspection probes clean" count. Unattributable. The checkable number is **30**
  detection vectors; see the evidence index.
- The "Xray forbids accessor-defines on `[Object]`/`[Array]` instances — the one true coverage
  ceiling, re-verified real" claim. **Retracted by the branch itself** — see "Recursion" below.
- The "collapsed frontier" framing. The phrase does not appear anywhere in the PR, and ADR-0001 now
  frames detectability and tamper-resilience as **independent axes**
  (`adr/0001-retain-legacy-js-instrument.rst:113-144`, `:259-289`), which is the opposite claim.

### ⚠️ Read this before trusting any D/X number

The `legacy_detectable` ratchet was **measured on Firefox 150** (`test/test_stealth.py:391-399`,
unbranded add-on-devel run). Master is now **Firefox 154** (`scripts/install-firefox.sh` →
`FIREFOX_154_0_RELEASE`; `VERSION` = 0.36.0). A Firefox 152 spot-check was recorded in an earlier
session; **no Firefox 154 run is recorded anywhere.**

Consequence: the D/X ratchet is **unverified on the browser this branch now targets**. Re-run and
re-ratchet before treating any of the numbers below as current, and before concluding that any area
needs less scrutiny:

```
scripts/build-extension.sh        # need a built openwpm.xpi + firefox-bin/
pytest test/test_stealth.py::TestStealthDetectability -v
pytest test/test_stealth.py::TestStealthDisruption -v
```

These are browser tests (no `pyonly` marker). The `server` fixture is session-scoped, so run one
test file at a time.

### Map of the branch

**7 commits** on top of master `61d285fc` (*release: v0.36.0 (Firefox 154)*), **11,732 insertions /
16 deletions across 55 files**. Bottom to top:

| # | Commit | Insertions | What it is |
|---|---|---|---|
| 1 | `feat(stealth): add the stealth JavaScript instrument` | +4,646 | The wrapping engine: `Extension/src/stealth/*`, the `stealth_js_instrument` flag and its mutual exclusion with `js_instrument`, the `recursive` → `ConfigError`, **and** the `receiver` column (`openwpm/storage/schema.sql:153`, `openwpm/storage/parquet_schema.py:155`). There is no separate storage commit. |
| 2 | `feat(stealth): make the stealth instrumentation surface configurable` | +1,593 | `stealth_js_instrument_settings` (`openwpm/config.py:87`) — the stealth surface is runtime-configurable, not hardcoded. |
| 3 | `feat(stealth): add the legacy-to-stealth settings migrator` | +2,887 | `openwpm/utilities/js_settings_migrator.py` (1,093) + the extracted `openwpm/utilities/walker.js` (346, shipped as package data) + the settings schema. |
| 4 | `feat(stealth): add the --capture-universal-members migrator flag` | +503 | The opt-in flag and its page-wide-`toString` warning. |
| 5 | `docs(stealth): document the stealth JavaScript instrument` | +1,747 | All four docs, in reStructuredText. |
| 6 | `fix(stealth): migrator empty-leaf over-capture guard + iframe comment + recursive-toString test` | +123 | |
| 7 | `fix(stealth): resolve window.fetch and similar [Global] members in the migrator walk` | +347 | |

Two things a reviewer should know going in:

- **Tests are folded into the commit they test.** There is no `test(stealth):` commit. (The previous
  revision of this page asked the reviewer to decide this; it was decided the other way and is
  settled — don't re-open it.)
- **Commits 6 and 7 sit above the docs commit**, so the PR body's "each commit is the final state of
  its area, no later fixups" is **no longer true of the branch**. Either squash them into commits 3/4,
  or review knowing they are there. Flag the PR body either way.

### Review surface

The engine is **six** files, **3,858 lines** — not two. The rest is tests (~3,900 lines of
`test/test_stealth.py`), docs, test pages, and generated `.d.ts` (skip).

| File | Lines | Role |
|---|---|---|
| `Extension/src/stealth/instrument.ts` | 1,349 | The wrapping engine |
| `Extension/src/stealth/index.ts` | 533 | **Frame protection** — the subsystem the previous revision of this page never mentioned |
| `Extension/src/stealth/settings.ts` | 348 | The bundled *default* surface (17 objects) |
| `Extension/src/stealth/error.ts` | 189 | Error/stack handling |
| `openwpm/utilities/js_settings_migrator.py` | 1,093 | Legacy → stealth settings translation |
| `openwpm/utilities/walker.js` | 346 | The injected walker, extracted from the Python |

**Read order:** `docs/developers/Stealth-Instrumentation.rst` →
`docs/developers/adr/0001-retain-legacy-js-instrument.rst` →
`docs/developers/Stealth-Requirements.rst` (the D*/X* requirement rows, `literalinclude`-linked to
the tests) → then `instrument.ts` → `index.ts` → `js_settings_migrator.py` + `walker.js`.
`docs/Stealth-Instrument.rst` is the user-facing page.

### Architecture in one screen

- The stealth instrument runs in the extension's **privileged content-script compartment**; the page
  runs in its own, with Firefox's **Xray membrane** between them. Wrappers are handed to the page via
  `exportFunction` so they read as native (`[native code]` `toString`, native `.name`/`.length`).
  `wrappedJSObject` is undefined to the page.
- It hooks **interface prototypes**. See "Recursion" for why it stops there — it is a **choice with a
  stated reason**, not a platform limit.
- It records to the same `javascript` table/schema as legacy. For **shared-prototype (inherited)**
  methods it records a static `symbol` (e.g. `EventTarget.addEventListener`) plus the runtime receiver
  interface in the nullable **`receiver`** column (`schema.sql:153`).
- The **bundled default surface** (`Extension/src/stealth/settings.ts`, 17 objects — the audio
  interfaces, `RTCPeerConnection`, `HTMLCanvasElement`, `CanvasRenderingContext2D`, `Storage`,
  `Navigator`, `Screen`, **plus `document` and `window`**) is a default, **not** a hardcoding: it is
  overridable at runtime via `stealth_js_instrument_settings` (`openwpm/config.py:87`).
- **Frame protection** (`index.ts`) installs into child frames synchronously on creation and covers
  `srcdoc` / `about:blank`, named access, `document.write`, `window.open`, and MutationObserver-driven
  insertion. This is 16 of the 30 detection vectors (the D10 rows) and deserves proportionate review
  time.
- The **migrator** (`python -m openwpm.utilities.js_settings_migrator`, formerly called "the sweep")
  is a browser-based translator from legacy `js_instrument_settings` to a stealth-shaped config. It
  expands `recursive` offline by walking the live object graph, captures own members narrowly and
  real-interface inherited methods via interface-filtered shared-prototype entries, and reports what
  it cannot translate as `UntranslatedEntry` rows (the old `residue`/`ResidueEntry` vocabulary is
  gone — zero occurrences).

**Recursion.** A stealth surface asking for `logSettings.recursive` is rejected at config-validation
time. The reason, verbatim from `openwpm/config.py:336-344`: recursion descends into plain
`Object`/`Array` instances that have **no global interface prototype to hook**, so capturing them
"would require defining accessors directly on those page instances — a page-observable own-property
mutation that any script can detect. Stealth **deliberately refuses** to do this rather than give
itself away." The `wrappedJSObject` waiver *was* prototyped and disproved (the page holds a different
object identity, so it reads `undefined`) — that half is experimentally grounded and survives. The
migrator expands the recursion offline instead. Tests:
`TestStealthRecursiveRejected` (`test_stealth.py:1693`, `pyonly`) and
`TestStealthRecursiveSweepParity` (`:2064`).

### Evidence index

Claim → test → invocation → last-observed browser. Every row runs from a clean checkout of the PR.
Browser rows need `scripts/build-extension.sh` and `firefox-bin/`.

| Claim | Test | Invocation | Last observed |
|---|---|---|---|
| Stealth is not detected on 30 vectors D1–D11 | `TestStealthDetectability` (`test_stealth.py:524`; rows at `:413-518`) | `pytest test/test_stealth.py::TestStealthDetectability -v` | **FF150** ratchet ⚠️ |
| Stealth's record channel resists suppression, forgery, and dynamic-iframe evasion | `TestStealthDisruption` X1/X2/X3 (`:623`; paired tests `:635-800`) | `pytest test/test_stealth.py::TestStealthDisruption -v` | **FF150** ⚠️ (X3 docstring records the FF150 3-run observation at `:758`) |
| `symbol` is byte-identical to legacy | `TestStealthSymbolParity::test_symbols_match_legacy` (`:1838`) | `pytest test/test_stealth.py::TestStealthSymbolParity -v` | — |
| The surface is runtime-configurable | `TestStealthConfigurability` (`:858`) | `pytest test/test_stealth.py::TestStealthConfigurability -v` | — |
| Shared-prototype calls carry the receiving interface | `TestStealthSharedPrototypeCapture::test_targeted_interface_is_captured_in_receiver_column` (`:2580`) | `pytest test/test_stealth.py::TestStealthSharedPrototypeCapture -v` | — |
| Stealth's thrown-error stacks carry no `moz-extension://` frames | `TestStealthErrorDrift::test_instrumented_throw_stack_has_no_extension_frames` (`:1160`) | `pytest test/test_stealth.py::TestStealthErrorDrift -v` | — |
| The migrator reproduces legacy's descent | `TestStealthRecursiveSweepParity` (`:2064`) + golden-output tests | `pytest test/test_stealth.py::TestStealthRecursiveSweepParity -v` | — |
| `recursive` is rejected with an actionable message | `TestStealthRecursiveRejected` (`:1693`) | `pytest -m pyonly test/test_stealth.py::TestStealthRecursiveRejected -v` | — |
| `--capture-universal-members` is default-OFF and its warning is honest | `TestStealthSweepUniversalPrototypeCapture` (`:2886`), `TestStealthSweepFunctionUniversalDefault` (`:3375`) | `pytest test/test_stealth.py::TestStealthSweepUniversalPrototypeCapture -v` | — |

**Symbol parity, stated precisely.** Set equality holds **modulo one documented audio
shared-prototype granularity delta** — the test subtracts `LEGACY_ONLY_AUDIO_SYMBOLS` /
`STEALTH_ONLY_AUDIO_SYMBOLS`. `adr/0001-retain-legacy-js-instrument.rst` states it this way
("modulo one documented audio shared-prototype granularity delta"); the previous revision of this
page dropped the caveat. Do not repeat the unqualified version.

**Tamper-resilience, scoped.** The win is on the **record channel**, not the wrapper: X1 and X2 pair a
legacy-RED test with a stealth-GREEN test, and each legacy control asserts the attack *works* on
legacy before the stealth assertion is made (`test_x1_legacy_channel_can_be_suppressed` `:635` /
`test_x1_stealth_channel_resists_suppression` `:649`; `test_x2_legacy_channel_can_be_forged` `:660` /
`test_x2_stealth_channel_rejects_forgery` `:675`). X3 is coverage rather than tampering
(`test_x3_stealth_instruments_dynamic_iframe` `:746` / `test_x3_legacy_misses_dynamic_iframe_parent_attribution`
`:777`). On raw wrapper *deletability* the two modes are equal — see
`adr/0001-retain-legacy-js-instrument.rst:113-144`. Cite these tests, not a review pass.

### Claims about legacy that this page will make (and only these)

Four, each with an in-repo test:

1. **Legacy is detected on 8 of the 30 vectors** — D1-webdriver-flag, D2-native-fn-{canvas,storage,rtc},
   D4-no-global-leaks, D5-constructors-present, D8-no-prototype-pollution, D8b-native-fn-arity.
   `TestStealthDetectability::test_legacy_detectable` (`test_stealth.py:575`) is parametrized over
   exactly those rows. Provenance and the FF150 caveat: `test_stealth.py:391-399`.
2. **Legacy's record channel is suppressible and forgeable** — X1/X2 legacy controls above.
3. **Legacy misses dynamically-created iframes** for parent attribution — X3 legacy control
   (`test_stealth.py:777`).
4. **Legacy's `window.name` handling is a tell** —
   `TestStealthWindowName::test_legacy_window_name_is_detectable` (`test_stealth.py:1363`).

Two more are earned but live in **unmerged** PRs, so phrase them with their state. Master
`61d285fc` still ships the unfixed `Extension/src/lib/js-instruments.ts`, so both are **true on
master today**:

- **Legacy assigns `Object.getPropertyDescriptor` / `Object.getPropertyNames` onto the page-world
  `Object`** (`js-instruments.ts:111`, `:124`). RED proof: PR **#1191**, test-only commit `f88705a0`.
- **Legacy wrappers report `.length === 0` and `.name === ""`** (`js-instruments.ts:516`). RED proof:
  PR **#1213**; the one-line fix is PR **#1210**.

### Anti-claims — do not infer these

- **Legacy does *not* leak `moz-extension://` stack frames.** It runs in the page compartment, so its
  extra frame is attributed to the **document's own URL**; the tell is the page-foreign function name
  `getInstrumentJS/instrumentFunction/<`, not the URL scheme. PR #1207's own test docstring says its
  assertion "holds by construction" and is not a leak reproduction; PR #1212 prints the actual trace.
  `docs/developers/Stealth-Instrumentation.rst:63-67` states this correctly. Crosslink #54 was closed
  as not-reproducible. Do not turn stealth's clean-stack property into a legacy accusation.
- **Legacy is not detectable on every vector.** In the ratchet run D3 (native navigator getter), D6
  (bind integrity) and D7 (clean error stacks) came out **not detected** for legacy, which is why
  they carry `legacy_detectable=None`.
- **Legacy does not wrap methods on the instance.** It resolves `window['X'].prototype`
  (`openwpm/js_instrumentation.py:119`) and defines there (`Extension/src/lib/js-instruments.ts:587`)
  — the same object stealth hooks. Its only instance mutation is value shadowing on the *set* path
  (`js-instruments.ts:700`). And `logCall` (`js-instruments.ts:332`) never serializes `this`, so
  legacy's per-instance granularity is latent and **never recorded**. (ADR-0001 asserted the instance
  version; that has been corrected on this branch.)
- **Prototype pollution is not "inherent".** It is **removable but costly** — an implementation
  choice, not a second structural wall
  (`adr/0001-retain-legacy-js-instrument.rst:270-274`). The flatten is load-bearing: hooking the
  owning prototype instead collapses sibling attribution (`AnalyserNode` vs `GainNode` `connect`) and
  `collection_fingerprinting` depends on the flatten path for 11 of its 14 entries. Measured in
  `datadir/r56-repro/run_attrib.py`, verdict in `datadir/r56-protochain-flattening-verdict.md`.
- **"Frame coverage is fixable in legacy" is unsubstantiated.** X3 proves only that legacy *misses*
  dynamic iframes. All 16 D10 rows carry `legacy_detectable=None` with no paired legacy control
  (`test_stealth.py:467` onward). Nothing measures a legacy fix.
- **`navigator.webdriver === true` is a Selenium tell, not an instrument tell.** Stealth also sets it
  to `false`. The "one line would fix it for legacy" half has never been built or measured; ADR-0001
  proposes it as follow-up #3.

### Durability of the evidence

The strongest legacy experiments — `datadir/issue57-repro/` (cross-realm `toString`),
`datadir/r56-repro/` (prototype flattening and sibling attribution), `datadir/stack-leak/` (the
wrapper stack frame) — live in **`datadir/`, which is gitignored scratch space**. A reviewer working
from PR #1154 alone **cannot re-run them**; only their recorded verdicts survive. The in-repo,
re-runnable legacy evidence is exactly the four numbered claims above plus PRs #1191 / #1213. Any new
legacy claim should cite from that list, or say plainly that its evidence is an unshipped scratch
experiment.

### What is genuinely open

- **Re-ratchet D/X on Firefox 154.** Highest-priority open item; see the caveat at the top.
- **One capability gap** justifies keeping legacy: per-interface attribution naming for
  shared-prototype (inherited) members. The `receiver` column
  (`schema.sql:153`, `TestStealthSharedPrototypeCapture` `:2580`) narrows it considerably; judge for
  yourself whether what remains carries ADR-0001's decision. Recursion belongs under "deliberately
  refused", not under "gap".
- **`generateErrorObject`'s stack *reconstruction*** (as opposed to filtering) has not been shown
  load-bearing on the function path; filtering was proven defence-in-depth by a neutering experiment
  (Xray already strips extension frames). Non-blocking; needs a content-script probe of raw
  `err.stack`.
- **PR-body hygiene** (not code): the #1154 body still carries the FingerprintJS claim and the "no
  later fixups" promise. Both should be struck or made true before merge.
