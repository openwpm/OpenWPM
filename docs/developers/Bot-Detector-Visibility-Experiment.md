# Objective: does off-the-shelf bot detection see OpenWPM's instrumentation?

Measurement for crosslink #75 / OpenWPM PR #1154 (`feat/stealth-js-instrument-v2`).

**The claim under test**, in the PR owner's words:

> off-the-shelf bot detection triggers on the legacy instrument but cannot
> distinguish stealth from an uninstrumented browser.

This is the companion to
[FingerprintJS-Visibility-Experiment.md](FingerprintJS-Visibility-Experiment.md),
which established that a commodity *fingerprinter* cannot distinguish any arm,
because FingerprintJS OSS reads values and OpenWPM's legacy wrappers are
value-transparent. Bot detectors are different: they run **integrity** checks.
That is the gap this experiment fills.

## Verdict

| half of the claim | verdict |
| --- | --- |
| off-the-shelf bot detection triggers on legacy | **REFUTED** — BotD and fpscanner read legacy *identically* to an uninstrumented OpenWPM browser on all 185 oracle signals |
| bot detection cannot distinguish stealth from an uninstrumented browser | **REFUTED, in stealth's favour** — it distinguishes them easily, on 10 oracle signals, and stealth is the one that looks *less* like a bot |

Neither half survives. The claim should be replaced with what was actually
measured, which is still a good story for the PR but a different one:

> Two off-the-shelf OSS bot detectors — BotD 2.0.0 and fpscanner 1.0.8 — cannot
> see the legacy JS instrument *at all*: 18 BotD detectors, 21 fpscanner rules
> and ~140 underlying readings are identical between legacy and an
> uninstrumented OpenWPM browser. Legacy is nevertheless plainly detectable —
> all four instrumentation tells named by Krumnow, Jonker & Karsch fire on it in
> the same page load, including a `Function.prototype.toString` leak on every
> wrapped native and a prototype-pollution blowup from 10 to 351 own properties
> on `HTMLCanvasElement.prototype`. Stealth fires none of them. What these two
> commodity libraries *do* see is `navigator.webdriver`, which stealth
> suppresses and baseline does not — so stealth reads as **less** automated than
> an uninstrumented OpenWPM browser, not the same.

And the caveat that must travel with it: **stealth does not make OpenWPM
undetectable as a bot.** fpscanner's aggregate verdict is `true` in all four
arms, stealth included.

## What was built

| artifact | purpose |
| --- | --- |
| `test/test_pages/vendor/botd-2.0.0.esm.js` | vendored oracle 1 (hermetic, no CDN) |
| `test/test_pages/vendor/botd-2.0.0.LICENSE.txt` | MIT license text |
| `test/test_pages/vendor/fpscanner-1.0.8.es.js` | vendored oracle 2 |
| `test/test_pages/vendor/fpscanner-1.0.8.LICENSE.txt` | MIT license text |
| `test/test_pages/vendor/README.md` | provenance + hermeticity notes (extended) |
| `test/test_pages/bot_detection.html` | probe page; publishes every check verdict on `#results/@data-results` |
| `test/test_bot_detection.py` | 4-arm harness, validity gate, activity control, assertions |

### Vendored oracles

| field | BotD | fpscanner |
| --- | --- | --- |
| package | `@fingerprintjs/botd` | `fpscanner` |
| version | `2.0.0` (exact, pinned) | `1.0.8` (exact, pinned) |
| license | MIT | MIT |
| author | FingerprintJS, Inc. | Antoine Vastel |
| file | `package/dist/botd.esm.js` | `package/dist/fpScanner.es.js` |
| SHA-256 | `f438ed251dc7414ece9d4a2b6941441ad9ffae1a1905817f5f0c7366e701dd86` | `75abba497a00625ed053ce7a0bc9353fa5d5c9859cc67438141fe83d8d0946b2` |
| surface | 23 sources → 18 named detectors → 1 aggregate | ~116 leaf signals → 21 named rules → 1 aggregate |

Both files are **byte-identical to the published npm artifact**, so the hashes
reproduce against upstream with no local edits to account for. Both are pinned
and asserted in
`test_bot_detection.py::test_vendored_bundles_are_the_pinned_artifacts` before
any measurement runs.

Neither project publishes a UMD/IIFE build — npm ships CommonJS and ESM only —
so the probe page imports them from a `<script type="module">` rather than
loading them with a classic `<script src>`. That is what preserves
byte-identity; it is a deliberate choice, recorded in `vendor/README.md`.

**Hermeticity.** BotD carries the same install-statistics beacon as
FingerprintJS: `load()` fires an XHR to `m1.openfpcdn.io` with probability 0.001
unless disabled, so the page calls `botd.load({ monitoring: false })`. fpscanner
makes no network request of any kind — the bundle contains no `fetch`,
`XMLHttpRequest`, `sendBeacon` or `WebSocket` call site, and its one
`new Image()` loads an inline 1×1 `data:image/png` for the canvas-tamper check.
The page passes `collectFingerprint({ encrypt: false })` so the scanner returns
the plain object instead of an encrypted string; nothing is transmitted either
way.

### A note on `fpscanner`

The task brief described `fpscanner@1.0.8` as exposing per-test
`CONSISTENT`/`UNSURE`/`INCONSISTENT` verdicts. That was true of Vastel's
original *fp-scanner*; `fp-scanner` is **no longer published on npm** (404), and
`fpscanner@1.0.8` is a 2025-era TypeScript rewrite by the same author with a
different output shape. It is still the right oracle — it exposes 21
individually-named `{detected, severity}` rules, which is the per-signal
granularity that was wanted — but the verdict vocabulary in this report is
`detected: true/false`, not the three-valued one.

## Method

Four arms, one probe page, one page load per run:

| arm | configuration |
| --- | --- |
| `plain` | stock Firefox 154 driven by **bare Selenium**. No OpenWPM, no extension, no OpenWPM preference set |
| `baseline` | OpenWPM, `js_instrument=False`, `stealth_js_instrument=False` |
| `legacy` | OpenWPM, `js_instrument=True`, `js_instrument_settings=["collection_fingerprinting"]` |
| `stealth` | OpenWPM, `stealth_js_instrument=True`, bundled default surface |

The fourth arm is the point. "OpenWPM with no instrument" and "a browser that is
not OpenWPM" are different references, and only having both lets a firing signal
be attributed to *Selenium*, to *OpenWPM*, or to *the instrument*. `plain` is
still WebDriver-driven, so `navigator.webdriver` is true there too — which is
exactly what makes it the right control.

The legacy arm uses **the project's own standard preset**
(`openwpm/js_instrumentation_collections/fingerprinting.json`), which is also
the `BrowserParams` default, spelled out explicitly in the test so it is evident
on inspection that it was not hand-tuned.

`manager_params.testing` is deliberately **`False`**, unlike the FingerprintJS
harness. With `testing=True` the legacy page script additionally publishes
`window.instrumentJS`; that is a harness artifact, and including it would have
inflated legacy's measured detectability above what a real crawl has.

Environment: Firefox 154.0 (unbranded add-on-devel, `firefox-bin/`), headless,
fresh temporary profile per launch, `claude-sandbox` (no `/dev/snd`, no GPU).

220 signals are compared per run: 185 from the two oracles and 35 from a
separate `paper.*` namespace described below.

| namespace | count | what it is |
| --- | --- | --- |
| `botd.verdict.*` | 2 | BotD's aggregate `{bot, botKind}` |
| `botd.detection.*` | 18 | one verdict per BotD detector |
| `botd.component.*` | 23 | BotD's raw source readings |
| `fpscanner.fastBotDetection` | 1 | fpscanner's aggregate |
| `fpscanner.rule.*` | 21 | one `detected` flag per named rule |
| `fpscanner.signal.*` | 116 | fpscanner's raw leaf readings |
| `fpscanner.{fsid,nonce,time,url}` | 4 | fpscanner metadata |
| `paper.*` | 35 | **not an oracle** — see below |

## The `paper.*` probes are not an oracle

Krumnow, Jonker & Karsch (arXiv:2205.08890) predate both libraries and mention
neither. Their tells are measured in the same page load, in a clearly separate
namespace, for one reason: so this report can say *where the two off-the-shelf
oracles sit relative to a detector that knows what to look for*. Every verdict
about "what off-the-shelf detection can see" in this document is computed over
the 185 oracle signals only.

The paper separates two classes of tell, and this report preserves that
separation because stealth can only address one of them.

**Automation tells — apply to every mode of running OpenWPM** (their Sec. 4.1):
`navigator.webdriver`; screen dimension and position properties that use
standard values and "cannot be changed from OpenWPM" (their Table 3, where the
browser window is 1366 × 683 in *every* configuration they tested); and WebGL
vendor/renderer strings that give away display-less or virtualised hosts (their
Table 4). Their conclusion: *"every mode of running OpenWPM is identifiable as a
web bot."*

**Instrumentation tells — specific to the JS instrument** (their Sec. 4.1,
"Detecting instrumentation", and Listing 1): `toString` on overwritten
functions; the `window.getInstrumentJS` global, "which is not present in any
common desktop browser (Firefox, Safari, Chrome, Edge, Opera)"; OpenWPM wrapper
functions appearing in stack traces; and prototype-chain pollution, where the
properties of later ancestor prototypes are all flattened onto the first
ancestor (their Fig. 2).

Stealth can fix the second class, plus `navigator.webdriver`. It cannot fix
screen geometry or WebGL. **Any claim that stealth makes OpenWPM undetectable as
a bot is false and does not appear in this report.**

## Validity gate: every arm run twice

Each of the four arms was run twice *before* any cross-arm comparison, and only
signals that reproduce in **all four** arms are compared. The exclusion set is
derived from the data, never hardcoded.

- **Stable: 216 of 220 signals**, including every one of BotD's 18 detector
  verdicts, all 21 fpscanner rules, and both aggregates. No detection verdict
  drifts.
- **Excluded: 4 signals.**

  | excluded signal | plain A → B | why |
  | --- | --- | --- |
  | `fpscanner.nonce` | `gnx9qbs16zm` → `45sxxb71v2z` | `Math.random()` by construction |
  | `fpscanner.time` | `1787652659585` → `1787652663290` | wall-clock stamp |
  | `fpscanner.signal.graphics.canvas.canvasFingerprint` | `316a425d` → `12d831aa` | Firefox re-seeds canvas readback noise **per profile**, and every launch gets a fresh profile |
  | `fpscanner.fsid` | differs in the canvas sub-hash only | rolled-up id that mixes the canvas hash in, so it inherits its instability |

  The canvas instability is a **browser property, not an instrumentation
  artifact** — established by the out-of-OpenWPM control in the FingerprintJS
  experiment (plain Firefox 154, bare Selenium, no extension: byte-identical
  across three loads in one profile, different across fresh profiles under every
  pref combination tried). It reproduces here in all four arms, `plain`
  included.

  Note what this costs: fpscanner's `hasModifiedCanvas` check reads the
  *tamper* flag, which is stable and **is** compared; only the rendered-bytes
  hash is excluded.

## Activity control: were the instruments actually running?

Without this, "no detector could tell the arms apart" has a trivial and wrong
explanation. Rows in the crawl DB's `javascript` table for the single probe-page
visit:

| arm | rows captured | distinct symbols |
| --- | --- | --- |
| `plain_a` / `plain_b` | *n/a* — no OpenWPM, no crawl DB | — |
| `baseline_a` / `baseline_b` | **0** | 0 |
| `legacy_a` / `legacy_b` | **103** | 32 |
| `stealth_a` / `stealth_b` | **124** | 39 |

Both instrumented arms captured exactly the surfaces the probe page drives:

- `HTMLCanvasElement.{getContext, toDataURL, width, height}` and
  `CanvasRenderingContext2D.{fillText, fillRect, fillStyle, font, textBaseline, arc, fill, rect, globalCompositeOperation, getImageData}`
  — fpscanner's canvas-tamper and canvas-fingerprint probes
- `window.navigator.{userAgent, appVersion, platform, productSub, languages, language, vendor, plugins, mimeTypes, hardwareConcurrency, permissions, mediaDevices, serial, buildID, webdriver}`
  — the bulk of both oracles' sources
- `window.screen.{colorDepth, pixelDepth}` (legacy); stealth additionally
  `{width, height, avail{Width,Height,Left,Top}}`

Note the last line: **both instruments watched the detectors read
`navigator.webdriver`, call by call**, and BotD and fpscanner still could not
tell legacy from baseline.

## Results: the differences

### `plain` vs `baseline` — **zero differing signals**

On all 216 reproducible signals, stock Firefox driven by bare Selenium and
OpenWPM's own uninstrumented baseline read *identically*. OpenWPM's whole
preference set and the presence of the (uninstrumented) extension add no
bot-detectable surface here.

This is what licenses calling everything that fires on `baseline` an
**automation** tell rather than an OpenWPM tell.

### `legacy` vs `baseline` — **zero oracle differences, 12 paper-probe differences**

| signal | baseline | legacy | class |
| --- | --- | --- | --- |
| *all 185 oracle signals* | — | **identical** | — |
| `paper.globalsOnWindow` | `[]` | `["getInstrumentJS"]` | INSTRUMENTATION |
| `paper.globalsInScope` | `[]` | `["getInstrumentJS", "jsInstrumentationSettings"]` | INSTRUMENTATION |
| `paper.nativeToString.HTMLCanvasElement.prototype.getContext` | `true` | `false` | INSTRUMENTATION |
| `paper.nativeToString.HTMLCanvasElement.prototype.toDataURL` | `true` | `false` | INSTRUMENTATION |
| `paper.nativeToString.CanvasRenderingContext2D.prototype.fillText` | `true` | `false` | INSTRUMENTATION |
| `paper.nativeToString.Storage.prototype.setItem` | `true` | `false` | INSTRUMENTATION |
| `paper.errorStack.frameCount` | `4` | `5` | INSTRUMENTATION |
| `paper.errorStack.frameFunctions` | `["collectPaperProbes/<", "record", "collectPaperProbes", ""]` | `["getInstrumentJS/instrumentFunction/<", "collectPaperProbes/<", "record", "collectPaperProbes", ""]` | INSTRUMENTATION |
| `paper.errorStack.raw` | *(no wrapper frame)* | leading frame `getInstrumentJS/instrumentFunction/<@…` | INSTRUMENTATION |
| `paper.prototypeOwnPropertyCounts.HTMLCanvasElement.prototype` | `10` | **`351`** | INSTRUMENTATION |
| `paper.prototypeOwnPropertyCounts.CanvasRenderingContext2D.prototype` | `73` | `84` | INSTRUMENTATION |
| `paper.prototypeOwnPropertyCounts.Storage.prototype` | `7` | `18` | INSTRUMENTATION |

All four of the paper's instrumentation tells reproduce, exactly as described,
on current `master` + PR #1154's legacy path. The prototype-pollution figure is
the paper's Fig. 2 effect made concrete: `HTMLCanvasElement.prototype` grows
from 10 own properties to 351, because the ancestor chain
(`Element`, `Node`, `EventTarget`, …) is flattened onto it.

`Navigator.prototype` (47), `Screen.prototype` (16) and `Document.prototype`
(232) are **unchanged** by legacy — the preset instruments the `navigator` and
`screen` *instances* at depth 0, so no prototype work happens there. Only the
class-level objects (`HTMLCanvasElement`, `CanvasRenderingContext2D`, `Storage`)
pollute.

### `stealth` vs `baseline` — **10 oracle differences, 1 paper-probe difference, all `navigator.webdriver`**

| signal | baseline | stealth | class |
| --- | --- | --- | --- |
| `botd.component.webDriver` | `{"state":0,"value":true}` | `{"state":0,"value":false}` | STEALTH-ONLY |
| `botd.detection.detectWebDriver` | `{"bot":true,"botKind":"headless_chrome"}` | `{"bot":false}` | STEALTH-ONLY |
| `botd.verdict.bot` | `true` | **`false`** | STEALTH-ONLY |
| `botd.verdict.botKind` | `"headless_chrome"` | `null` | STEALTH-ONLY |
| `fpscanner.rule.hasWebdriver` | `true` | `false` | STEALTH-ONLY |
| `fpscanner.rule.hasWebdriverWritable` | `true` | `false` | STEALTH-ONLY |
| `fpscanner.rule.hasWebdriverIframe` | `true` | `false` | STEALTH-ONLY |
| `fpscanner.signal.automation.webdriver` | `true` | `false` | STEALTH-ONLY |
| `fpscanner.signal.automation.webdriverWritable` | `true` | `false` | STEALTH-ONLY |
| `fpscanner.signal.contexts.iframe.webdriver` | `true` | `false` | STEALTH-ONLY |
| `paper.navigatorWebdriver` | `true` | `false` | STEALTH-ONLY |

Every one of these is the same property viewed from a different angle, and every
one makes stealth look *more* human, never less. The cause is explicit and
deliberate: `Extension/src/stealth/settings.ts` sets
`overwrittenProperties: [{ key: "webdriver", value: false, level: 0 }]` on
`Navigator`.

Two of these deserve a callout:

- `fpscanner.signal.contexts.iframe.webdriver` — fpscanner reads
  `navigator.webdriver` from inside a freshly created **iframe**, a classic way
  to defeat main-realm patching. Stealth's frame protection holds: the iframe
  reads `false` too.
- `botd.verdict.bot` — stealth flips BotD's *aggregate* verdict from `true` to
  `false`. BotD has no timezone, screen-geometry or WebGL check, so once
  `webdriver` is gone it has nothing left to fire on in this environment.

Stealth is **identical to baseline on all 34 remaining paper probes**: no
`toString` leak, no globals, no extra stack frame, no prototype pollution.

## Signal × arm matrix: every detection verdict

`FIRE` = the check reported automation. All 41 verdict signals; none of them
drifted run-to-run.

| signal | plain | baseline | legacy | stealth | class |
| --- | --- | --- | --- | --- | --- |
| `botd.verdict.bot` | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by stealth) |
| `botd.detection.detectWebDriver` | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by stealth) |
| `botd.detection.detectAppVersion` | — | — | — | — | |
| `botd.detection.detectDistinctiveProperties` | — | — | — | — | |
| `botd.detection.detectDocumentAttributes` | — | — | — | — | |
| `botd.detection.detectErrorTrace` | — | — | — | — | |
| `botd.detection.detectEvalLengthInconsistency` | — | — | — | — | |
| `botd.detection.detectFunctionBind` | — | — | — | — | |
| `botd.detection.detectLanguagesLengthInconsistency` | — | — | — | — | |
| `botd.detection.detectMimeTypesConsistent` | — | — | — | — | |
| `botd.detection.detectNotificationPermissions` | — | — | — | — | |
| `botd.detection.detectPluginsArray` | — | — | — | — | |
| `botd.detection.detectPluginsLengthInconsistency` | — | — | — | — | |
| `botd.detection.detectProcess` | — | — | — | — | |
| `botd.detection.detectProductSub` | — | — | — | — | |
| `botd.detection.detectUserAgent` | — | — | — | — | |
| `botd.detection.detectWebGL` | — | — | — | — | |
| `botd.detection.detectWindowExternal` | — | — | — | — | |
| `botd.detection.detectWindowSize` | — | — | — | — | |
| `fpscanner.fastBotDetection` | FIRE | FIRE | FIRE | **FIRE** | AUTOMATION |
| `fpscanner.rule.hasUTCTimezone` | FIRE | FIRE | FIRE | **FIRE** | ENVIRONMENT — fires on plain Firefox too; the sandbox's TZ is UTC |
| `fpscanner.rule.hasWebdriver` | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by stealth) |
| `fpscanner.rule.hasWebdriverIframe` | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by stealth) |
| `fpscanner.rule.hasWebdriverWritable` | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by stealth) |
| `fpscanner.rule.hasBotUserAgent` | — | — | — | — | |
| `fpscanner.rule.hasCDP` | — | — | — | — | |
| `fpscanner.rule.hasGPUMismatch` | — | — | — | — | |
| `fpscanner.rule.hasHighCPUCount` | — | — | — | — | |
| `fpscanner.rule.hasImpossibleDeviceMemory` | — | — | — | — | |
| `fpscanner.rule.hasInconsistentEtsl` | — | — | — | — | |
| `fpscanner.rule.hasMismatchLanguages` | — | — | — | — | |
| `fpscanner.rule.hasMismatchPlatformIframe` | — | — | — | — | |
| `fpscanner.rule.hasMismatchPlatformWorker` | — | — | — | — | |
| `fpscanner.rule.hasMismatchWebGLInWorker` | — | — | — | — | |
| `fpscanner.rule.hasMissingChromeObject` | — | — | — | — | |
| `fpscanner.rule.hasPlatformMismatch` | — | — | — | — | |
| `fpscanner.rule.hasPlaywright` | — | — | — | — | |
| `fpscanner.rule.hasSeleniumProperty` | — | — | — | — | |
| `fpscanner.rule.hasSwiftshaderRenderer` | — | — | — | — | |
| `fpscanner.rule.hasWebdriverWorker` | — | — | — | — | |
| `fpscanner.rule.headlessChromeScreenResolution` | — | — | — | — | |

**No signal fires on `legacy` that does not also fire on `plain`.** There is not
a single INSTRUMENTATION tell in the entire off-the-shelf oracle set.

`fpscanner.rule.hasWebdriverWorker` does not fire in any arm because
`navigator.webdriver` does not exist in a Web Worker at all — fpscanner's worker
signal has no `webdriver` key on Firefox 154. That is a browser property, not a
stealth effect.

## Why the oracles miss legacy

This is coverage, not innocence. Reading the bundles:

- **BotD's only integrity checks are on `eval`, `Function.prototype.bind` and
  its own stack trace, and two of the three are weaker than they look.**
  `detectEvalLengthInconsistency` compares `eval.toString().length` against a
  per-engine constant (37 on Gecko — measured, unchanged in every arm).
  `getFunctionBind` reads `Function.prototype.bind.toString()`
  (`"function bind() {\n    [native code]\n}"` in every arm) but
  `detectFunctionBind` never compares the string — it fires only when `bind` is
  *undefined*, so the one `toString()` call BotD makes on a native is collected
  and then discarded. `getErrorTrace` provokes `null[0]()` inside BotD's **own**
  code and `detectErrorTrace` regex-matches the result for `/PhantomJS/i`;
  legacy's wrapper frames never enter that stack, because BotD never provokes an
  error inside a wrapped function. No OpenWPM preset wraps `eval` or `bind`.
- **BotD's global-name probe is the closest analogue to the paper's
  `getInstrumentJS` tell, and OpenWPM is simply not on its list.**
  `checkDistinctiveProperties` tests a fixed roster of window globals
  (`awesomium`, `RunPerfTest`, `CefSharp`, `fmget_targets`, `geb`,
  `__nightmare`, `_selenium`, `callPhantom`, …). `getInstrumentJS` is present on
  `window` in the legacy arm and BotD walks straight past it.
- **fpscanner has exactly one prototype-shape check, and it looks in the wrong
  place.** `navigatorPropertyDescriptors` tests whether
  `Object.getOwnPropertyDescriptor(Object.getPrototypeOf(navigator), p)` is a
  data property, for `p` in `deviceMemory, hardwareConcurrency, language,
  languages, platform`. It reads `"00000"` in all four arms — legacy defines its
  wrappers on the `navigator` *instance*, leaving `Navigator.prototype`
  untouched. Its `toSourceError` and `etsl` signals are Gecko-vs-V8
  discriminators, not tamper checks.
- **Neither library ever calls `Function.prototype.toString` on a DOM method**,
  which is the single check that would have caught legacy on four surfaces at
  once.

So the honest framing for the PR is: *off-the-shelf commodity bot detection does
not catch legacy either — but legacy is trivially catchable, and the vendors
whose products the paper found in the wild (Akamai, Incapsula, Cloudflare,
PerimeterX, and CHEQ, which the paper observed reading `jsInstruments` on 331
sites) are not shipping BotD OSS.*

## Automation tells that survive every arm

Present identically in `plain`, `baseline`, `legacy` **and** `stealth`, and
outside what any JS instrument could fix:

| tell | value | paper reference |
| --- | --- | --- |
| `screen.availTop` / `availLeft` | `0` / `0` | Table 4 — the display-less signature |
| `screen` / window geometry | `1366×768`, inner `1366×682`, `screenX/Y = 0` | Table 3 — "standard values … cannot be changed from OpenWPM" |
| WebGL | **absent entirely** (`getContext("webgl")` returns null; fpscanner reports vendor/renderer `"NA"`) | Table 4 — headless mode, "the lack of a WebGL implementation" |
| timezone | `UTC` → `fpscanner.rule.hasUTCTimezone` fires | — (sandbox property; fpscanner's own rule) |
| `navigator.webdriver` | `true` in three of four arms | Table 2, row 1 |

`hasUTCTimezone` alone keeps `fpscanner.fastBotDetection` at `true` for stealth.
The paper's conclusion holds unchanged: every mode of running OpenWPM measured
here is identifiable as a web bot.

## Arms run, including discarded ones

Every arm-set executed is listed; nothing was retried-until-green.

| # | arm set | outcome | kept? |
| --- | --- | --- | --- |
| 1 | plain Firefox ×1, bare Selenium, oracles only | both bundles loaded and reported; BotD verdict `{bot:true, botKind:"headless_chrome"}` | superseded by #3 — the page had no `paper.*` probes yet, so instrumentation tells could not be classified |
| 2 | all 4 arms ×2, oracles + first `paper.*` draft | same conclusions as the final run | **discarded as a measurement.** Two defects: (a) it was assembled from two batches started against *different* test-server ports, so the port-bearing signals (`fpscanner.url`, `botd.component.errorTrace`, `paper.errorStack.raw`) were falsely unstable; (b) `botd.verdict.botKind` vanishes from stealth's report rather than changing value, so the validity gate mislabelled the headline result as "irreproducible" |
| 3 | all 4 arms ×2, one server, normalised `botd.verdict` keys, stack probe reporting frame *names* rather than origin-filtered frames | the tables above | **kept — the reported measurement** |

Two probe defects found and fixed between #2 and #3, both recorded because they
would each have produced a subtly wrong report:

- `botd.verdict.botKind` is *absent* from BotD's result when nothing is
  detected, rather than being `null`. Flattened naively, the signal disappears
  from stealth's key set, the cross-arm intersection drops it, and the single
  most important difference in the experiment gets filed under "unstable". The
  harness now normalises the verdict to a fixed key set.
- The first stack probe classified frames by **origin**, on the assumption that
  instrument frames would come from `moz-extension://`. They do not: legacy's
  page script is injected *inline into the visited document*, so its wrapper
  frames carry the page's own URL and an origin filter reports zero foreign
  frames while `getInstrumentJS/instrumentFunction/<` sits at the top of the
  trace. The probe now reports frame function names and a frame count.

## Caveats

1. **This measures two specific OSS libraries, not "bot detection".** The
   result "off-the-shelf detection cannot see legacy" is a statement about BotD
   2.0.0 and fpscanner 1.0.8 and generalises no further. The paper found
   OpenWPM-specific detection deployed in the wild (CHEQ reading `jsInstruments`
   on 331 sites, plus Akamai/Incapsula/Cloudflare/PerimeterX on ~2,600 more);
   none of those are open source and none could be run here.
2. **The `paper.*` probes are not exhaustive.** They are the four tells the
   paper names, nothing more. The full detection-vector suite is
   `test/test_stealth.py::TestStealthDetectability`; this experiment
   deliberately does not duplicate it.
3. **Headless, no GPU, no audio device, UTC.** WebGL is absent entirely, so
   every WebGL-based check (`detectWebGL`, `hasGPUMismatch`,
   `hasSwiftshaderRenderer`, `hasMismatchWebGLInWorker`) is vacuous here — they
   report "no data", not "consistent". A GPU-backed host would exercise them,
   and the paper's Table 4 shows they are exactly where Docker and Xvfb modes
   get caught. `hasUTCTimezone` fires because the sandbox is UTC, which is a
   property of this host, not of OpenWPM.
4. **Canvas image bytes are unmeasurable here**, as in the FingerprintJS
   experiment: Firefox re-seeds canvas readback noise per profile and OpenWPM
   uses a fresh profile per launch. fpscanner's `hasModifiedCanvas` *flag* is
   stable and was compared (identical in all arms); only the rendered-bytes hash
   is excluded.
5. **Chrome-oriented checks are structurally dead on Firefox.**
   `hasMissingChromeObject`, `hasCDP`, `hasPlaywright`,
   `headlessChromeScreenResolution` and much of BotD's `distinctiveProps` list
   target Chromium automation. They are compared (and equal) but carry no
   weight, so the effective oracle surface is smaller than 185 signals.
6. **`testing=False` was used, and it matters.** With OpenWPM's testing mode on,
   legacy additionally publishes `window.instrumentJS` — a fifth global. The
   measurement deliberately reflects a production crawl instead.
7. **Single host, single Firefox build, single page.** Firefox 154.0 headless in
   one sandbox, one probe page load per run. Detectors that score behaviour over
   time (mouse movement, timing, navigation patterns) are entirely out of scope;
   HLISA and the paper's Sec. 7 cover that axis.
8. **Stealth's advantage over baseline here is `navigator.webdriver` and
   nothing else.** It is real and it is measured, but it is one property. Any
   crawl operator can set the same expectation for legacy by other means; the
   durable claim for stealth is the *instrumentation* one — zero paper tells —
   not the webdriver one.

## Reproducing

```console
$ scripts/build-extension.sh
$ pytest test/test_bot_detection.py -v
```

Nine tests, eight browser launches (module-scoped fixture runs each arm twice),
roughly 3 minutes. `-m pyonly` runs only the bundle-integrity check.
