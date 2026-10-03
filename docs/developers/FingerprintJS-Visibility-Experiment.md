# Does a real fingerprinter see OpenWPM's instrumentation?

**Question:** does the FingerprintJS stamp differ between an OpenWPM browser
with no JS instrument, one running the stealth instrument, and one running the
legacy instrument?

## Result

| comparison | result |
| --- | --- |
| stealth vs baseline | **identical** on all 42 built-in components and all 4 reproducible extra probes, visitorId included |
| legacy vs baseline | **identical** on every reproducible probe, visitorId included |

FingerprintJS cannot tell stealth from legacy from an uninstrumented browser,
so it is no evidence that legacy is more visible than stealth.

This is not a null result caused by a dead experiment. Both instruments were
verifiably live and capturing on the exact surfaces the probe page drove
(activity control below). The reason legacy is invisible is a property of the
**oracle**, not of the instrument: FingerprintJS OSS reads *values*, and
OpenWPM's legacy wrappers are value-transparent. It performs **no**
native-function integrity check on any instrumented surface — the bundle
contains exactly one `isFunctionNative` call site, guarding `window.print`
inside a Safari-detection helper Gecko never reaches. The vectors where legacy
*is* detectable (`Function.prototype.toString` on wrapped natives, prototype
shape, arity/name drift, leaked globals) belong to bot-detection scripts.
FingerprintJS OSS is not one; `test/test_stealth.py::TestStealthDetectability`
and [Bot-Detector-Visibility-Experiment.md](Bot-Detector-Visibility-Experiment.md)
cover those vectors.

## What was built

| artifact | purpose |
| --- | --- |
| `test/test_pages/vendor/fingerprintjs-5.2.0.umd.min.js` | vendored oracle (hermetic, no CDN) |
| `test/test_pages/vendor/fingerprintjs-5.2.0.LICENSE.txt` | MIT license text |
| `test/test_pages/vendor/README.md` | provenance + hermeticity note |
| `test/test_pages/fingerprintjs_stamp.html` | probe page; publishes per-component hashes on `#results/@data-results` |
| `test/test_fingerprintjs_stamp.py` | 3-arm harness, validity gate, activity control, assertions (one browser test) |

### Vendored oracle

| field | value |
| --- | --- |
| package | `@fingerprintjs/fingerprintjs` |
| version | `5.2.0` (newest release; MIT) |
| file | `package/dist/fp.umd.min.js`, **byte-identical to the npm artifact** |
| SHA-256 | `a8de5ead580c42d2e2b01a5752aa08da510852230971aa18554d67cd5de5775b` |

No header was prepended precisely so the hash reproduces against upstream with
no local edits to account for; provenance lives in `vendor/README.md` and the
hash is pinned and asserted in
`test_fingerprintjs_stamp.py::test_vendored_bundle_is_the_pinned_artifact`.

v5 is the newest MIT release. One consequence had to be worked around — see the
forced-render canvas probes below.

`FingerprintJS.load({ monitoring: false })` is mandatory and is used: `load()`
otherwise fires an install-statistics XHR to `m1.openfpcdn.io` with probability
0.001, which would make the test non-hermetic 1 run in 1000.

## Method

Three arms, same probe page, same browser settings except the instrument switch,
each run twice:

| arm | configuration |
| --- | --- |
| `baseline` | OpenWPM with `js_instrument=False`, `stealth_js_instrument=False` |
| `stealth` | `stealth_js_instrument=True`, bundled default surface (`Extension/src/stealth/settings.ts`) |
| `legacy` | `js_instrument=True`, `js_instrument_settings=["collection_fingerprinting"]` |

The legacy arm uses **the project's own standard preset**
(`openwpm/js_instrumentation_collections/fingerprinting.json`), which is also the
`BrowserParams` default — spelled out explicitly in the test so it is evident on
inspection that it was not hand-tuned. The stealth bundled default covers the
same interfaces (audio nodes/contexts, RTCPeerConnection, HTMLCanvasElement,
CanvasRenderingContext2D, Storage, Navigator, Screen, document, window), so the
arms are comparable; the observed capture symbols below confirm this empirically
rather than by reading config. The stealth default also overrides
`navigator.webdriver`; FingerprintJS 5.2.0 never reads it, so that does not
affect this comparison.

`manager_params.testing` is `False`, as in a real crawl: with `testing=True`
legacy additionally publishes `window.instrumentJS`.

Environment: Firefox 154.0 (unbranded add-on-devel, `firefox-bin/`), headless,
fresh temporary profile per launch, a container with no `/dev/snd` and no GPU,
host timezone UTC.

Comparison is **per component**, not just `visitorId`, so a failure names the
surface that leaked. Each component's comparison key is
`murmurX64Hash128(JSON.stringify(value))` over the **full** value (previews in
the table are truncated; hashes are not). `duration` is dropped deliberately —
wall-clock timing differs on every run by construction and carries no signal.

## Validity gate: every arm run twice

Every arm was run **twice**, and only probes that reproduce within every arm are
compared across arms; the exclusion set is *derived from the data*, never
hardcoded. The gate and the comparisons run in one test on the same sample.

- **Stable: all 42 built-in FingerprintJS components, and `visitorId` itself.**
  `visitorId` is therefore a usable oracle in this environment — but it is still
  not used alone, because a single flaky source would move it for reasons
  unrelated to instrumentation.
- **Excluded: 2 probes**, both halves of the forced-render canvas:

  | excluded probe | baseline run A | baseline run B |
  | --- | --- | --- |
  | `unstableCanvas_geometry` | `7325f028c33c…` (8752 B PNG data URL) | `f60ef27d19ef…` (8752 B) |
  | `unstableCanvas_text` | `6b34493a2e87…` (11320 B PNG data URL) | `e126ce4ee134…` (11320 B) |

  Same byte length, different content, every launch, in every arm.

  **This is a Firefox property, not an instrumentation artifact**, established
  by a control run entirely outside OpenWPM — bare Selenium, plain Firefox 154,
  no extension:

  | control | result |
  | --- | --- |
  | 3 consecutive page loads in **one** browser session and profile | byte-identical every time |
  | 2 launches with fresh profiles, stock prefs | **differ** |
  | 2 launches with fresh profiles, `privacy.fingerprintingProtection=false`, `privacy.resistFingerprinting=false`, `privacy.resistFingerprinting.randomization.enabled=false` | **differ** |
  | 2 launches with fresh profiles, `privacy.fingerprintingProtection.overrides="-CanvasRandomization"` | **differ** |

  The canvas noise is stable within a browser session and changes across
  launches. Every launch here was also a fresh profile, so the control does not
  tell whether the seed is tied to the profile or to the session. No pref
  combination tried pins it.
  `unstableCanvas_winding` (a boolean, not readback) is stable and *is* compared.

## Activity control: were the instruments actually running?

Without this, "all three arms produced the same stamp" has a trivial and wrong
explanation. Rows in the crawl DB's `javascript` table for the single probe-page
visit:

| arm | rows captured | distinct symbols |
| --- | --- | --- |
| `baseline_a` / `baseline_b` | **0** | 0 |
| `stealth_a` / `stealth_b` | **120** | 44 |
| `legacy_a` / `legacy_b` | **92** | 39 |

Both instrumented arms captured exactly the surfaces the probe page drives —
including the canvas readback path that the whole question hangs on:

- `CanvasRenderingContext2D.{fillText, fillRect, fillStyle, font, textBaseline, arc, fill, rect, globalCompositeOperation, isPointInPath}`
- `HTMLCanvasElement.{getContext, toDataURL, width, height}`
- `OscillatorNode.{start, frequency, type}`, `OfflineAudioContext.{startRendering, oncomplete, state, destination}`, `…createOscillator`, `…createDynamicsCompressor`
- `window.navigator.{platform, oscpu, languages, language, vendor, plugins, hardwareConcurrency, maxTouchPoints, pdfViewerEnabled, appVersion}`
- `window.screen.colorDepth` (stealth additionally: `width, height, avail{Width,Height,Left,Top}`)
- `window.localStorage`, `window.sessionStorage`, `window.document.cookie`

So the instruments watched FingerprintJS compute its stamp, call by call, and
FingerprintJS still could not tell.

## Full results

Comparison keys, truncated to 12 hex chars. Identical across a row = the arms
agree. The `stealth` and `legacy` columns are run A; their run B matched on
every stable probe.

| component | baseline (run A) | baseline (run B) | stealth | legacy | value (baseline) |
| --- | --- | --- | --- | --- | --- |
| `applePay` | `edb551f5e4c5` | `edb551f5e4c5` | `edb551f5e4c5` | `edb551f5e4c5` | `-1` |
| `architecture` | `80cfcbd13233` | `80cfcbd13233` | `80cfcbd13233` | `80cfcbd13233` | `255` |
| `audio` | `2cda2f8d55d5` | `2cda2f8d55d5` | `2cda2f8d55d5` | `2cda2f8d55d5` | `35.749972093850374` |
| `audioBaseLatency` | `342115c818c8` | `342115c818c8` | `342115c818c8` | `342115c818c8` | `-2` |
| `canvas` | `1b17d62d715a` | `1b17d62d715a` | `1b17d62d715a` | `1b17d62d715a` | `{"winding":true,"geometry":"skipped","text":"skipped"}` |
| `colorDepth` | `4d46dbfe2684` | `4d46dbfe2684` | `4d46dbfe2684` | `4d46dbfe2684` | `24` |
| `colorGamut` | `ccea51677fd6` | `ccea51677fd6` | `ccea51677fd6` | `ccea51677fd6` | `"srgb"` |
| `contrast` | `2ac9debed546` | `2ac9debed546` | `2ac9debed546` | `2ac9debed546` | `0` |
| `cookiesEnabled` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `true` |
| `cpuClass` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `__undefined__` |
| `dateTimeLocale` | `45f810d1d001` | `45f810d1d001` | `45f810d1d001` | `45f810d1d001` | `"en-US"` |
| `deviceMemory` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `__undefined__` |
| `domBlockers` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `__undefined__` |
| `fontPreferences` | `95c3a99ccc23` | `95c3a99ccc23` | `95c3a99ccc23` | `95c3a99ccc23` | `{"default":164.53334045410156,"apple":164.5333404541… (189B)` |
| `fonts` | `cf252fdcd0c5` | `cf252fdcd0c5` | `cf252fdcd0c5` | `cf252fdcd0c5` | `[]` |
| `forcedColors` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `false` |
| `hardwareConcurrency` | `316d7a96b98f` | `316d7a96b98f` | `316d7a96b98f` | `316d7a96b98f` | `8` |
| `hdr` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `false` |
| `indexedDB` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `true` |
| `invertedColors` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `__undefined__` |
| `languages` | `3d05bea4b82f` | `3d05bea4b82f` | `3d05bea4b82f` | `3d05bea4b82f` | `[["en-US"],["en-US","en"]]` |
| `localStorage` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `true` |
| `math` | `c1265f087d7e` | `c1265f087d7e` | `c1265f087d7e` | `c1265f087d7e` | `{"acos":1.4473588658278522,"acosh":709.889355822726,… (646B)` |
| `monochrome` | `2ac9debed546` | `2ac9debed546` | `2ac9debed546` | `2ac9debed546` | `0` |
| `openDatabase` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `false` |
| `osCpu` | `3464b262c159` | `3464b262c159` | `3464b262c159` | `3464b262c159` | `"Linux x86_64"` |
| `pdfViewerEnabled` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `true` |
| `platform` | `3464b262c159` | `3464b262c159` | `3464b262c159` | `3464b262c159` | `"Linux x86_64"` |
| `plugins` | `65f90d432113` | `65f90d432113` | `65f90d432113` | `65f90d432113` | `[{"name":"PDF Viewer","description":"Portable Docume… (831B)` |
| `privateClickMeasurement` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `__undefined__` |
| `reducedMotion` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `c4bf6d05e5b7` | `false` |
| `reducedTransparency` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `__undefined__` |
| `screenFrame` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `__undefined__` |
| `screenResolution` | `7ba459b974d2` | `7ba459b974d2` | `7ba459b974d2` | `7ba459b974d2` | `[768,1366]` |
| `sessionStorage` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `true` |
| `timezone` | `282193a39ba3` | `282193a39ba3` | `282193a39ba3` | `282193a39ba3` | `"UTC"` |
| `touchSupport` | `4f709a195fe9` | `4f709a195fe9` | `4f709a195fe9` | `4f709a195fe9` | `{"maxTouchPoints":0,"touchEvent":false,"touchStart":false}` |
| `userAgentData` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `e151768af20d` | `__undefined__` |
| `vendor` | `1f5fe4ddb0c8` | `1f5fe4ddb0c8` | `1f5fe4ddb0c8` | `1f5fe4ddb0c8` | `""` |
| `vendorFlavors` | `cf252fdcd0c5` | `cf252fdcd0c5` | `cf252fdcd0c5` | `cf252fdcd0c5` | `[]` |
| `webGlBasics` | `edb551f5e4c5` | `edb551f5e4c5` | `edb551f5e4c5` | `edb551f5e4c5` | `-1` |
| `webGlExtensions` | `edb551f5e4c5` | `edb551f5e4c5` | `edb551f5e4c5` | `edb551f5e4c5` | `-1` |
| _extra probes_ | | | | | |
| `unstableCanvas_geometry` **UNSTABLE** | `7325f028c33c` | `f60ef27d19ef` | `9db200803796` | `d4d02b3cde26` | `"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHoAA… (8752B)` |
| `unstableCanvas_text` **UNSTABLE** | `6b34493a2e87` | `e126ce4ee134` | `8e9370e1ce00` | `beb6f938ba52` | `"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAPAAA… (11320B)` |
| `unstableCanvas_winding` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `f85e1fcc6e2d` | `true` |
| `unstableHardwareConcurrency` | `4d46dbfe2684` | `4d46dbfe2684` | `4d46dbfe2684` | `4d46dbfe2684` | `24` |
| `unstableScreenFrame` | `591f03ecd335` | `591f03ecd335` | `591f03ecd335` | `591f03ecd335` | `[0,0,0,0]` |
| `unstableScreenResolution` | `7ba459b974d2` | `7ba459b974d2` | `7ba459b974d2` | `7ba459b974d2` | `[768,1366]` |

`visitorId` — **`adb59d565c781837fa88a1929fcd66fe` in all six runs**.

## Which components carry each result

- **stealth == baseline** is carried by every one of the 42 built-in
  components, but the load-bearing ones — the components whose sources the
  stealth instrument demonstrably intercepted during the run — are `audio`
  (a real, non-degraded value: `35.749972093850374`), `canvas` (`winding`
  branch, plus the forced-render probe's `winding`), `screenResolution`,
  `colorDepth`, `hardwareConcurrency`, `languages`, `osCpu`, `platform`,
  `plugins`, `pdfViewerEnabled`, `touchSupport`, `vendor`, `localStorage`,
  `sessionStorage`, `cookiesEnabled`, and the extra probes
  `unstableScreenResolution`, `unstableScreenFrame`,
  `unstableHardwareConcurrency`.
- **legacy == baseline** holds on the same components. There is no component,
  built-in or extra, reproducible or not, on which legacy differs from baseline
  in a way baseline does not also differ from itself.

## Arms run, including discarded ones

Every arm executed is listed; nothing was retried-until-green.

| # | arm set | outcome | kept? |
| --- | --- | --- | --- |
| 1 | baseline ×1 (smoke) | probe page worked end to end | superseded by #2 |
| 2 | baseline ×2, stealth, legacy — built-in components only | all 42 components + visitorId identical across all four | **superseded by #3**, because the built-in `canvas` source returned `{"geometry":"skipped","text":"skipped"}`: FingerprintJS v5 deliberately skips canvas image rendering on Firefox 120+. Canvas is the most heavily instrumented surface in the preset, so this run's canvas verdict was vacuous. |
| 3 | baseline ×2, stealth, legacy — with forced-render canvas + screen extras | all 42 components + 4 extras identical; `unstableCanvas_*` unstable baseline-vs-baseline | **kept** (superseded in form by #6, same conclusion) |
| 4 | baseline ×2, stealth, legacy — **canvas randomization prefs disabled** | canvas *still* unstable baseline-vs-baseline; all else identical | discarded as a fix; **kept as evidence** that the prefs are not the cause |
| 5 | plain Firefox controls, no OpenWPM: 3 loads in one session; 2 fresh launches × 3 pref sets | canvas stable within a session, unstable across launches under every pref set | **kept** — this is what licenses the exclusion |
| 6 | baseline ×2, stealth, legacy — with per-part canvas split + activity control | same as #7 | superseded by #7 |
| 7 | every arm ×2, `testing=False`, gate and comparisons in one test | the tables above | **kept — the reported measurement** |

Nothing was hand-picked: the legacy arm is the shipped default preset, the
compared set is derived from the paired runs rather than chosen, and the answer
did not change across any of runs 2, 3, 4, 6 or 7.

## Caveats

1. **Canvas image data was not compared.** Firefox 154's canvas readback noise
   changed on every launch here, so the rendered-bytes probes are excluded. If
   legacy leaks into rendered canvas bytes, this experiment could not see it.
   Untried: reusing one profile across launches (`BrowserParams.seed_tar`),
   which would make canvas comparable if the noise seed is stored in the
   profile.
2. **WebGL is absent**, not merely instrumented-and-equal: `webGlBasics` and
   `webGlExtensions` both report `-1` (unavailable) in this headless sandbox. The
   fingerprinting preset does not instrument WebGL anyway, so nothing is lost
   relative to the question — but a GPU-backed host would exercise more surface.
3. **No audio device** (`/dev/snd` absent). Despite that, the `audio` component
   returned a genuine `OfflineAudioContext` value (`35.749972093850374`), stable
   across all four runs — offline rendering needs no device. `audioBaseLatency`
   is `-2` (unavailable). So the audio surface *was* really exercised.
4. **`fonts` is `[]`** — no extra fonts in the sandbox, so that source
   contributes no entropy. `fontPreferences` did return real measurements.
5. **`applePay` `-1`, `userAgentData`/`domBlockers`/`screenFrame` `undefined`** —
   platform-inapplicable sources. They are compared (and equal) but carry no
   weight.
6. **FingerprintJS OSS does not probe the vectors legacy actually leaks.** This
   is the central caveat: the result says
   "legacy is invisible *to a fingerprinter*", **not** "legacy is undetectable".
   `test/test_stealth.py::TestStealthDetectability` shows legacy failing 8
   detection vectors on this same Firefox build.
7. **Single host, single Firefox build.** Firefox 154.0 headless in one sandbox.
   A different platform could plausibly move `math`, `fontPreferences` or the
   audio value — but only equally for all arms, so the *comparison* should hold.
8. **The instrumented surfaces are not identical between arms.** Stealth captured
   44 symbols vs. legacy's 39. Stealth additionally covers several
   `window.screen` dimensions; legacy additionally covers
   `HTMLCanvasElement.addEventListener`. The rest is labelling: stealth records
   the oscillator's `connect` as `AudioNode.connect` and the members
   `OfflineAudioContext` shares with `AudioContext` as
   `[AudioContext|OfflineAudioContext].*`, where legacy uses the concrete class.
   Both cover every surface FingerprintJS reads, so the comparison is sound, but
   the two presets are near-, not exactly-, equal.

## Reproducing

```console
$ scripts/build-extension.sh
$ pytest test/test_fingerprintjs_stamp.py -v
```

One browser test, six browser launches (each arm twice), about 2.5 minutes.
`-m pyonly` runs only the bundle-integrity check.
