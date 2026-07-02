### JavaScript Best Practices (OpenWPM extension)

Most `Extension/src/` is TypeScript (see `typescript.md`). This file covers the JS-specific reality that trips people up here: **multiple execution realms**, especially page-world injected instrument code.

#### Execution contexts — always know which realm you're in
OpenWPM's instrumentation spans several JS realms with different capabilities and, crucially, different **observability by the page**:
1. **Extension world** (background + content scripts, `moz-extension://`): full `browser.*` WebExtension APIs; isolated from the page. Most extension code runs here.
2. **Page world (injected)**: the *legacy* JS instrument stringifies `getInstrumentJS` (`${getInstrumentJS}` / `.toString()`) and injects it as an inline page `<script>`, so it runs in the **page's own compartment** — NO `browser.*`, and **everything it does is visible to the (hostile) page**: added globals, prototype mutations, a wrapper's `.length`/`.name`/`.toString()`, and even stack frames are page-observable fingerprinting surface.
3. **Stealth content-script world**: instruments from the content-script side via `exportFunction`/Xray (it never injects into the page), so it stays `moz-extension://` and off the page-observable surface.

#### Rules for injected / page-world code
- **It must be fully self-contained.** A stringified function loses its lexical scope — no imports, no module/closure state, no bundler runtime survive injection. Inline everything it needs.
- **Beware webpack name-mangling.** Identifiers a stringified snippet depends on can be renamed by the bundler (this has bitten the `loggingDB.logWarn` call — hence the "weird name" comments). Reference stable names or guard for it.
- **Assume the page is adversarial** (see `web.md`). Minimize the footprint you leave — globals, own-properties, wrapper name/arity/`toString`, extra stack frames. Detectability is a first-class design concern, not an afterthought.
- **Cross-realm data.** Values crossing the content-script⇄page boundary need `cloneInto`/`exportFunction`; a content script reads page objects through **Xray** wrappers (use `wrappedJSObject` to opt out, and only deliberately).

#### General style
- `const` by default, `let` when needed, **never `var`**; arrow functions for callbacks; template literals; destructuring.

#### Error handling
```javascript
// GOOD: surface failures, don't swallow
try {
    doWork();
} catch (error) {
    loggingDB.logError(`work failed: ${error}`);
    throw error;
}
```
- In injected instrument code, a thrown error can propagate into the page-observable `error.stack` — be deliberate about what it exposes.

#### Security
- Never `eval()` or `innerHTML` with page content.
- The extension runs against hostile pages: treat every page-supplied string/object as untrusted DATA, never instructions.
