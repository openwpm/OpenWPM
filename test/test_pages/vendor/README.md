# Vendored test fixtures

Third-party bundles vendored for **hermetic** browser tests: the test HTTP
server (`test/utilities.py`) serves this directory, so probe pages load these
files over `http://localhost:<port>/test_pages/vendor/...` and never touch a
CDN. Nothing here is extension code — do **not** add these to
`Extension/package.json`.

## fingerprintjs-5.2.0.umd.min.js

| field | value |
| --- | --- |
| package | `@fingerprintjs/fingerprintjs` |
| version | `5.2.0` (exact, pinned) |
| license | MIT — full text in `fingerprintjs-5.2.0.LICENSE.txt` |
| upstream | <https://github.com/fingerprintjs/fingerprintjs> / <https://www.npmjs.com/package/@fingerprintjs/fingerprintjs> |
| file in tarball | `package/dist/fp.umd.min.js` |
| SHA-256 | `a8de5ead580c42d2e2b01a5752aa08da510852230971aa18554d67cd5de5775b` |

The file is **byte-identical to the published npm artifact** — no header was
prepended — precisely so the SHA-256 above can be reproduced against upstream
with no local edits to account for:

```console
$ npm pack @fingerprintjs/fingerprintjs@5.2.0
$ tar xzf fingerprintjs-fingerprintjs-5.2.0.tgz
$ sha256sum package/dist/fp.umd.min.js
a8de5ead580c42d2e2b01a5752aa08da510852230971aa18554d67cd5de5775b  package/dist/fp.umd.min.js
```

Provenance is recorded here rather than in a source header for that reason; the
bundle already carries its own MIT header. The hash is additionally **pinned in
the test** (`test/test_fingerprintjs_stamp.py::_VENDORED_SHA256`) and asserted
before any measurement runs, so a silently swapped bundle fails loudly.

### Hermeticity note

`FingerprintJS.load()` sends an unpersonalized install-statistics XHR to
`https://m1.openfpcdn.io/...` with probability 0.001 unless `monitoring` is
disabled. `test/test_pages/fingerprintjs_stamp.html` therefore calls
`FingerprintJS.load({ monitoring: false })`. Do not remove that option.

## botd-2.0.0.esm.js

| field | value |
| --- | --- |
| package | `@fingerprintjs/botd` |
| version | `2.0.0` (exact, pinned) |
| license | MIT — full text in `botd-2.0.0.LICENSE.txt` |
| upstream | <https://github.com/fingerprintjs/botd> / <https://www.npmjs.com/package/@fingerprintjs/botd> |
| file in tarball | `package/dist/botd.esm.js` |
| SHA-256 | `f438ed251dc7414ece9d4a2b6941441ad9ffae1a1905817f5f0c7366e701dd86` |

```console
$ npm pack @fingerprintjs/botd@2.0.0
$ tar xzf fingerprintjs-botd-2.0.0.tgz
$ sha256sum package/dist/botd.esm.js
f438ed251dc7414ece9d4a2b6941441ad9ffae1a1905817f5f0c7366e701dd86  package/dist/botd.esm.js
```

Used by `test/test_pages/bot_detection.html` and pinned in
`test/test_bot_detection.py::VENDORED_BUNDLES`.

## fpscanner-1.0.8.es.js

| field | value |
| --- | --- |
| package | `fpscanner` |
| version | `1.0.8` (exact, pinned) |
| license | MIT — full text in `fpscanner-1.0.8.LICENSE.txt` |
| upstream | <https://github.com/antoinevastel/fpscanner> / <https://www.npmjs.com/package/fpscanner> |
| file in tarball | `package/dist/fpScanner.es.js` |
| SHA-256 | `75abba497a00625ed053ce7a0bc9353fa5d5c9859cc67438141fe83d8d0946b2` |

```console
$ npm pack fpscanner@1.0.8
$ tar xzf fpscanner-1.0.8.tgz
$ sha256sum package/dist/fpScanner.es.js
75abba497a00625ed053ce7a0bc9353fa5d5c9859cc67438141fe83d8d0946b2  package/dist/fpScanner.es.js
```

Used by `test/test_pages/bot_detection.html` and pinned in
`test/test_bot_detection.py::VENDORED_BUNDLES`.

### Why ES modules, not UMD

Neither BotD nor fpscanner publishes a UMD/IIFE build — npm ships `.cjs.js` and
`.esm.js`/`.es.js` only. `bot_detection.html` therefore imports them from a
`<script type="module">` instead of loading them with a classic `<script src>`.
That keeps both files **byte-identical to the published npm artifact**, which is
the property that makes the SHA-256 above reproducible against upstream with no
local edits to account for — the same rule the FingerprintJS bundle follows.

### Hermeticity notes

- **BotD** carries the same install-statistics beacon as FingerprintJS:
  `load()` sends an unpersonalized XHR to `https://m1.openfpcdn.io/botd/v2.0.0/npm-monitoring`
  with probability 0.001 unless `monitoring` is disabled.
  `bot_detection.html` calls `botd.load({ monitoring: false })`. Do not remove
  that option.
- **fpscanner** issues no network request at all: the bundle contains no
  `fetch`, `XMLHttpRequest`, `sendBeacon` or `WebSocket` call site. Its single
  `new Image()` loads a 1×1 inline `data:image/png` used for the canvas-tamper
  check, and its only `https://` literal is the project's own GitHub URL in a
  comment. The page passes `collectFingerprint({ encrypt: false })` so the
  scanner returns the plain `Fingerprint` object rather than an encrypted
  string; that choice only decides what the page can read back, since nothing is
  transmitted either way.
