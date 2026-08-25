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
