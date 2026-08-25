# Does off-the-shelf bot detection see OpenWPM's instrumentation?

**Question:** can off-the-shelf bot detection distinguish the legacy or the
stealth JS instrument from an OpenWPM browser with no JS instrument?

This is the companion to
[FingerprintJS-Visibility-Experiment.md](FingerprintJS-Visibility-Experiment.md),
which established that a commodity *fingerprinter* cannot distinguish any arm,
because FingerprintJS OSS reads values and OpenWPM's legacy wrappers are
value-transparent. Bot detectors additionally run **integrity** checks.

## Result

| comparison | result |
| --- | --- |
| legacy vs baseline | **identical** on all 181 reproducible oracle signals; all four paper instrumentation tells fire |
| stealth instrument alone (`stealth_bare`) vs baseline | **identical** on all 216 reproducible signals, oracle and paper alike |
| shipped stealth (`stealth`) vs `stealth_bare` | differs on 12 signals, every one a view of `navigator.webdriver` or an aggregate verdict |

In short:

> Two off-the-shelf OSS bot detectors — BotD 2.0.0 and fpscanner 1.0.8 — cannot
> see the legacy JS instrument: 18 BotD detectors, 21 fpscanner rules and 139
> raw readings are identical between legacy and an uninstrumented OpenWPM
> browser. Legacy is nevertheless plainly detectable — all four
> instrumentation tells named by Krumnow, Jonker & Karsch fire on it in the same
> page load. The stealth instrument fires none of them and changes nothing
> either oracle reads. What the oracles *do* see is `navigator.webdriver`, which
> the shipped stealth configuration overrides. With the browser timezone pinned
> to a non-UTC zone, that override is the difference between both oracles
> flagging the browser and neither flagging it.

What this does not show: that stealth makes OpenWPM undetectable. These two
libraries barely look at the automation tells the paper documents for
display-less modes (screen geometry, missing WebGL), and those are present in
every arm. On a host whose timezone is UTC, fpscanner's `hasUTCTimezone` rule
fires in every arm, stealth included; that is a host property, not an
automation or instrumentation tell.

## What was built

| artifact | purpose |
| --- | --- |
| `test/test_pages/vendor/botd-2.0.0.esm.js` | vendored oracle 1 (hermetic, no CDN) |
| `test/test_pages/vendor/botd-2.0.0.LICENSE.txt` | MIT license text |
| `test/test_pages/vendor/fpscanner-1.0.8.es.js` | vendored oracle 2 |
| `test/test_pages/vendor/fpscanner-1.0.8.LICENSE.txt` | MIT license text |
| `test/test_pages/vendor/README.md` | provenance + hermeticity notes (extended) |
| `test/test_pages/bot_detection.html` | probe page; publishes every check verdict on `#results/@data-results` |
| `test/test_bot_detection.py` | 5-arm harness, validity gate, activity control, assertions (one browser test) |

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

Vastel's original *fp-scanner* exposed per-test
`CONSISTENT`/`UNSURE`/`INCONSISTENT` verdicts, but it is **no longer published
on npm** (404). `fpscanner@1.0.8` is a 2025-era TypeScript rewrite by the same
author with a different output shape: 21 individually-named
`{detected, severity}` rules. The verdict vocabulary in this report is
therefore `detected: true/false`.

## Method

Five arms, one probe page, one page load per run, each arm run twice:

| arm | configuration |
| --- | --- |
| `plain` | stock Firefox 154 driven by **bare Selenium**. No OpenWPM, no extension, no OpenWPM preference set |
| `baseline` | OpenWPM, `js_instrument=False`, `stealth_js_instrument=False` |
| `legacy` | OpenWPM, `js_instrument=True`, `js_instrument_settings=["collection_fingerprinting"]` |
| `stealth_bare` | OpenWPM, `stealth_js_instrument=True`, bundled default surface **minus** its `navigator.webdriver` override |
| `stealth` | OpenWPM, `stealth_js_instrument=True`, bundled default surface as shipped |

`plain` vs `baseline` isolates OpenWPM itself; `baseline` vs `legacy` and
`baseline` vs `stealth_bare` isolate each instrument; `stealth_bare` vs
`stealth` isolates the webdriver override
(`overwrittenProperties: [{ key: "webdriver", value: false, level: 0 }]` on
`Navigator` in `Extension/src/stealth/settings.ts`). `stealth_bare` reads that
file at test time, drops the override and passes the rest as
`stealth_js_instrument_settings`. Both arms reach the page through the same
privileged actor; the only difference in delivery is that a custom surface is
handed to it as JSON, where the default is compiled into the instrument. That
is not visible here: `stealth_bare` matches `baseline` on every reproducible
signal, and its difference from `stealth` is exactly the webdriver views and the
verdicts resting on them.

`navigator.webdriver` is checked against what each arm configures, not against
a hardcoded value. Where `BrowserParams` has an OpenWPM-wide `spoof_webdriver`
switch, the harness pins it off: it would hide `navigator.webdriver` in every
arm and leave nothing for the override to change. Pairs whose configurations
expose `navigator.webdriver` differently are compared outside the webdriver
signals and the aggregate verdicts; all other pairs on every reproducible signal.

The legacy arm uses **the project's own standard preset**
(`openwpm/js_instrumentation_collections/fingerprinting.json`), which is also
the `BrowserParams` default, spelled out explicitly in the test so it is evident
on inspection that it was not hand-tuned.

`manager_params.testing` is deliberately **`False`**, unlike the FingerprintJS
harness. With `testing=True` the legacy page script additionally publishes
`window.instrumentJS`; that is a harness artifact, and including it would have
inflated legacy's measured detectability above what a real crawl has.

Environment: Firefox 154.0 (unbranded add-on-devel, `firefox-bin/`), headless,
fresh temporary profile per launch, a container with no `/dev/snd` and no GPU.
`TZ=Europe/Berlin` is set for every arm (the test asserts the browser reports
it), because Firefox otherwise inherits the host zone and fpscanner's
`hasUTCTimezone` rule would make the result depend on the machine.

The gate, the activity control and every comparison run in one test on one
sample, so CI's per-test sharding cannot split them.

220 signals are collected per run: 185 from the two oracles and 35 from a
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

Each of the five arms was run twice, and only signals that reproduce within
**every** arm are compared. The exclusion set is derived from the data, never
hardcoded. Signals are taken over the union of all arms' keys, and a key missing
from one arm compares as `<absent>`: a collector that throws in one arm (fpscanner
then reports `"ERROR"` in place of a subtree) shows up as a difference, not as
noise. No such case occurred.

- **Stable: 216 of 220 signals**, including every one of BotD's 18 detector
  verdicts, all 21 fpscanner rules, and both aggregates. No detection verdict
  drifts.
- **Excluded: 4 signals.**

  | excluded signal | example A → B | why |
  | --- | --- | --- |
  | `fpscanner.nonce` | `gnx9qbs16zm` → `45sxxb71v2z` | `Math.random()` by construction |
  | `fpscanner.time` | `1787652659585` → `1787652663290` | wall-clock stamp |
  | `fpscanner.signal.graphics.canvas.canvasFingerprint` | `316a425d` → `12d831aa` | Firefox's canvas readback noise changes on every launch |
  | `fpscanner.fsid` | differs in the canvas sub-hash only | rolled-up id that mixes the canvas hash in, so it inherits its instability |

  The canvas instability is a **browser property, not an instrumentation
  artifact** — established by the out-of-OpenWPM control in the FingerprintJS
  experiment (plain Firefox 154, bare Selenium, no extension: byte-identical
  across three loads in one session, different across fresh launches under
  every pref combination tried). It reproduces here in every arm, `plain`
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
| `stealth_bare_a` / `stealth_bare_b` | **117** | 37 |
| `stealth_a` / `stealth_b` | **117** | 37 |

Five of each stealth arm's rows (`navigator.{userAgent, platform, language,
hardwareConcurrency, webdriver}`) come from fpscanner's iframe while it is
still the initial `about:blank` and are recorded under that URL; legacy records
nothing there.

All instrumented arms captured exactly the surfaces the probe page drives:

- `HTMLCanvasElement.{getContext, toDataURL, width, height}` and
  `CanvasRenderingContext2D.{fillText, fillRect, fillStyle, font, textBaseline, arc, fill, rect, globalCompositeOperation, getImageData}`
  — fpscanner's canvas-tamper and canvas-fingerprint probes
- `window.navigator.{userAgent, appVersion, platform, productSub, languages, language, vendor, plugins, mimeTypes, hardwareConcurrency, permissions, mediaDevices, serial, buildID, webdriver}`
  — the bulk of both oracles' sources
- `window.screen.{colorDepth, pixelDepth}` (legacy); stealth additionally
  `{width, height, avail{Width,Height,Left,Top}}`

Both instruments watched the detectors read `navigator.webdriver`, call by
call.

## Results: the differences

### `plain` vs `baseline` — **zero differing signals**

On all 216 reproducible signals, stock Firefox driven by bare Selenium and
OpenWPM's own uninstrumented baseline read *identically*. OpenWPM's whole
preference set and the presence of the (uninstrumented) extension add nothing
either oracle or the paper's probes see. Anything that fires on `baseline`
fires on bare Selenium in the same environment too.

### `legacy` vs `baseline` — **zero oracle differences, 12 paper-probe differences**

| signal | baseline | legacy | class |
| --- | --- | --- | --- |
| *all 181 reproducible oracle signals* | — | **identical** | — |
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
on the legacy instrument. The prototype-pollution figure is
the paper's Fig. 2 effect made concrete: `HTMLCanvasElement.prototype` grows
from 10 own properties to 351, because the ancestor chain
(`Element`, `Node`, `EventTarget`, …) is flattened onto it.

`Navigator.prototype` (47), `Screen.prototype` (16) and `Document.prototype`
(232) are **unchanged** by legacy — the preset instruments the `navigator` and
`screen` *instances* at depth 0, so no prototype work happens there. Only the
class-level objects (`HTMLCanvasElement`, `CanvasRenderingContext2D`, `Storage`)
pollute.

### `stealth_bare` vs `baseline` — **zero differing signals**

The stealth instrument without the webdriver override is identical to baseline
on all 216 reproducible signals: every oracle signal and all 35 paper probes —
no `toString` leak, no globals, no extra stack frame, no prototype pollution —
while capturing 117 calls over 37 symbols on the surfaces the page drives.

### `stealth` vs `stealth_bare` — **12 differing signals, all `navigator.webdriver`**

| signal | stealth_bare | stealth |
| --- | --- | --- |
| `botd.component.webDriver` | `{"state":0,"value":true}` | `{"state":0,"value":false}` |
| `botd.detection.detectWebDriver` | `{"bot":true,"botKind":"headless_chrome"}` | `{"bot":false}` |
| `botd.verdict.bot` | `true` | **`false`** |
| `botd.verdict.botKind` | `"headless_chrome"` | `null` |
| `fpscanner.fastBotDetection` | `true` | **`false`** |
| `fpscanner.rule.hasWebdriver` | `true` | `false` |
| `fpscanner.rule.hasWebdriverWritable` | `true` | `false` |
| `fpscanner.rule.hasWebdriverIframe` | `true` | `false` |
| `fpscanner.signal.automation.webdriver` | `true` | `false` |
| `fpscanner.signal.automation.webdriverWritable` | `true` | `false` |
| `fpscanner.signal.contexts.iframe.webdriver` | `true` | `false` |
| `paper.navigatorWebdriver` | `true` | `false` |

Every one of these is the same property viewed from a different angle, plus the
two aggregates that were resting on it. `stealth` vs `baseline` gives the same
12 signals, since `stealth_bare` equals `baseline`.

- `fpscanner.signal.contexts.iframe.webdriver` — fpscanner reads
  `navigator.webdriver` from inside a freshly created **iframe**, a classic way
  to defeat main-realm patching. The override holds there too.
- The aggregates flip only because nothing else fires in this environment.
  BotD has no timezone check; its WebGL check only matches a `Mesa OffScreen`
  renderer and its window-size check only a 0×0 outer window, neither of which
  applies here. fpscanner's aggregate flips only because the timezone is pinned
  to a non-UTC zone. On a host where another rule fires (e.g. a SwiftShader GPU,
  more than 70 CPUs, a UTC timezone), the aggregates stay `true` under the
  override.

## Signal × arm matrix: every detection verdict

`FIRE` = the check reported automation. All 41 verdict signals, `TZ` pinned to
`Europe/Berlin`; none of them drifted run-to-run.

| signal | plain | baseline | legacy | stealth_bare | stealth | class |
| --- | --- | --- | --- | --- | --- | --- |
| `botd.verdict.bot` | FIRE | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by the override) |
| `botd.detection.detectWebDriver` | FIRE | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by the override) |
| `botd.detection.detectAppVersion` | — | — | — | — | — | |
| `botd.detection.detectDistinctiveProperties` | — | — | — | — | — | |
| `botd.detection.detectDocumentAttributes` | — | — | — | — | — | |
| `botd.detection.detectErrorTrace` | — | — | — | — | — | |
| `botd.detection.detectEvalLengthInconsistency` | — | — | — | — | — | |
| `botd.detection.detectFunctionBind` | — | — | — | — | — | |
| `botd.detection.detectLanguagesLengthInconsistency` | — | — | — | — | — | |
| `botd.detection.detectMimeTypesConsistent` | — | — | — | — | — | |
| `botd.detection.detectNotificationPermissions` | — | — | — | — | — | |
| `botd.detection.detectPluginsArray` | — | — | — | — | — | |
| `botd.detection.detectPluginsLengthInconsistency` | — | — | — | — | — | |
| `botd.detection.detectProcess` | — | — | — | — | — | |
| `botd.detection.detectProductSub` | — | — | — | — | — | |
| `botd.detection.detectUserAgent` | — | — | — | — | — | |
| `botd.detection.detectWebGL` | — | — | — | — | — | |
| `botd.detection.detectWindowExternal` | — | — | — | — | — | |
| `botd.detection.detectWindowSize` | — | — | — | — | — | |
| `fpscanner.fastBotDetection` | FIRE | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by the override) |
| `fpscanner.rule.hasUTCTimezone` | — | — | — | — | — | ENVIRONMENT — fires in every arm on a UTC host; not here, `TZ` is pinned |
| `fpscanner.rule.hasWebdriver` | FIRE | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by the override) |
| `fpscanner.rule.hasWebdriverIframe` | FIRE | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by the override) |
| `fpscanner.rule.hasWebdriverWritable` | FIRE | FIRE | FIRE | FIRE | — | AUTOMATION (relieved by the override) |
| `fpscanner.rule.hasBotUserAgent` | — | — | — | — | — | |
| `fpscanner.rule.hasCDP` | — | — | — | — | — | |
| `fpscanner.rule.hasGPUMismatch` | — | — | — | — | — | |
| `fpscanner.rule.hasHighCPUCount` | — | — | — | — | — | |
| `fpscanner.rule.hasImpossibleDeviceMemory` | — | — | — | — | — | |
| `fpscanner.rule.hasInconsistentEtsl` | — | — | — | — | — | |
| `fpscanner.rule.hasMismatchLanguages` | — | — | — | — | — | |
| `fpscanner.rule.hasMismatchPlatformIframe` | — | — | — | — | — | |
| `fpscanner.rule.hasMismatchPlatformWorker` | — | — | — | — | — | |
| `fpscanner.rule.hasMismatchWebGLInWorker` | — | — | — | — | — | |
| `fpscanner.rule.hasMissingChromeObject` | — | — | — | — | — | |
| `fpscanner.rule.hasPlatformMismatch` | — | — | — | — | — | |
| `fpscanner.rule.hasPlaywright` | — | — | — | — | — | |
| `fpscanner.rule.hasSeleniumProperty` | — | — | — | — | — | |
| `fpscanner.rule.hasSwiftshaderRenderer` | — | — | — | — | — | |
| `fpscanner.rule.hasWebdriverWorker` | — | — | — | — | — | |
| `fpscanner.rule.headlessChromeScreenResolution` | — | — | — | — | — | |

**No signal fires on `legacy` or `stealth_bare` that does not also fire on
`plain`.** There is not a single instrumentation tell in the entire
off-the-shelf oracle set. The only verdicts that fire anywhere are
`navigator.webdriver` and the aggregates resting on it.

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
  languages, platform`. It reads `"00000"` in every arm — legacy defines its
  wrappers on the `navigator` *instance*, leaving `Navigator.prototype`
  untouched. Its `toSourceError` and `etsl` signals are Gecko-vs-V8
  discriminators, not tamper checks.
- **Neither library ever calls `Function.prototype.toString` on a DOM method**,
  which is the single check that would have caught legacy on four surfaces at
  once.

So the accurate framing is: *off-the-shelf commodity bot detection does
not catch legacy either — but legacy is trivially catchable, and the vendors
whose products the paper found in the wild (Akamai, Incapsula, Cloudflare,
PerimeterX, and CHEQ, which the paper observed reading `jsInstruments` on 331
sites) are not shipping BotD OSS.*

## Automation tells present in every arm

Present identically in all five arms, and outside what any JS instrument could
fix:

| tell | value | paper reference |
| --- | --- | --- |
| `screen` / window geometry | `1366×768`, inner `1366×682`, `screenX/Y = 0`, `availTop/availLeft = 0` | Table 3 — "standard values … cannot be changed from OpenWPM" |
| WebGL | **absent entirely** (`getContext("webgl")` returns null; fpscanner reports vendor/renderer `"NA"`) | Table 4 — headless mode, "the lack of a WebGL implementation" |

Neither oracle turns these into a verdict here: fpscanner's WebGL rules report
"no data" when WebGL is absent, and BotD's WebGL and window-size checks match
only a `Mesa OffScreen` renderer and a 0×0 outer window. A detector that treats
"no WebGL" or these fixed geometries as suspicious would flag every arm; the
paper concludes that "every mode of running OpenWPM is identifiable as a web
bot". This experiment does not test such a detector.

## Arms run, including discarded ones

Every arm-set executed is listed; nothing was retried-until-green.

| # | arm set | outcome | kept? |
| --- | --- | --- | --- |
| 1 | plain Firefox ×1, bare Selenium, oracles only | both bundles loaded and reported; BotD verdict `{bot:true, botKind:"headless_chrome"}` | superseded by #3 — the page had no `paper.*` probes yet, so instrumentation tells could not be classified |
| 2 | all 4 arms ×2, oracles + first `paper.*` draft | same conclusions as the final run | **discarded as a measurement.** Two defects: (a) it was assembled from two batches started against *different* test-server ports, so the port-bearing signals (`fpscanner.url`, `botd.component.errorTrace`, `paper.errorStack.raw`) were falsely unstable; (b) `botd.verdict.botKind` vanishes from stealth's report rather than changing value, so the validity gate mislabelled the headline result as "irreproducible" |
| 3 | all 4 arms ×2, one server, normalised `botd.verdict` keys, stack probe reporting frame *names* rather than origin-filtered frames | same comparisons as #4, but `hasUTCTimezone` fired in every arm because the host timezone was UTC, keeping fpscanner's aggregate `true` for stealth | superseded by #4 |
| 4 | 5 arms ×2 (adds `stealth_bare`), `TZ=Europe/Berlin` for every arm, gate and comparisons in one test | the tables above | **kept — the reported measurement** |

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
3. **Headless, no GPU, no audio device, pinned timezone.** WebGL is absent
   entirely, so every WebGL-based check (`detectWebGL`, `hasGPUMismatch`,
   `hasSwiftshaderRenderer`, `hasMismatchWebGLInWorker`) is vacuous here — they
   report "no data", not "consistent". A GPU-backed host would exercise them,
   and the paper's Table 4 shows they are exactly where Docker and Xvfb modes
   get caught. The timezone is pinned to `Europe/Berlin`; on a UTC host
   `hasUTCTimezone` fires in every arm.
4. **Canvas image bytes were not compared**, as in the FingerprintJS
   experiment: Firefox's canvas readback noise changes on every launch here.
   fpscanner's `hasModifiedCanvas` *flag* is stable and was compared (identical
   in all arms); only the rendered-bytes hash is excluded.
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
8. **Stealth's advantage over baseline here is the `navigator.webdriver`
   override and nothing else.** `stealth_bare` shows the instrument itself
   changes nothing either oracle reads. The override is a configuration knob
   any OpenWPM mode could apply; the claim that belongs to the stealth
   *instrument* is the paper-probe one — zero instrumentation tells.

## Reproducing

```console
$ scripts/build-extension.sh
$ pytest test/test_bot_detection.py -v
```

One browser test, ten browser launches (five arms, twice each), roughly 3.5
minutes. `-m pyonly` runs only the bundle-integrity and settings-parse checks.
