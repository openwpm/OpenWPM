### TypeScript Best Practices (OpenWPM extension)

The Firefox WebExtension in `Extension/src/` is TypeScript (MV2, Firefox-only). Build/lint from `Extension/`: `npm run build` (tsc → webpack → web-ext → `openwpm.xpi`), `npm run lint` (ESLint + Prettier + web-ext lint), `npm run fix`.

#### Warnings Are Errors - ABSOLUTE RULE
- **ALL warnings must be fixed, NEVER silenced.** On tooling upgrades, keep new/stricter checks ENABLED and fix the code — do not disable rules to go green.
- No `// @ts-ignore`, `// @ts-expect-error`, or `eslint-disable` without explicit justification.
- No `any` — use `unknown` and narrow with type guards.

```typescript
// FORBIDDEN
// @ts-ignore
const data: any = response;

// REQUIRED
const data: unknown = response;
if (isValidRecord(data)) {
    log(data.symbol);  // narrowed safely
}
```

#### Execution contexts — the WebExtension weirdness
Instrumentation code runs across several JS realms with different capabilities and different **page-observability**; a type that compiles says nothing about which realm it's legal in:
1. **Extension world** (background + content scripts, `moz-extension://`): full `browser.*` APIs, isolated from the page.
2. **Page world (injected)**: the *legacy* instrument stringifies `getInstrumentJS` and injects it as a page `<script>` — it runs in the **page compartment**, has **no `browser.*`**, and everything it leaves (globals, prototype edits, a wrapper's `.length`/`.name`/`.toString()`, stack frames) is **page-observable** to hostile scripts.
3. **Stealth content-script world**: instruments via `exportFunction`/Xray without page injection, staying `moz-extension://` and off the observable surface.

Rules:
- **Page-injected code must be self-contained** — stringification drops lexical scope, imports, and bundler runtime. Watch for webpack **name-mangling** breaking stringified references.
- **Cross-realm values** need `cloneInto`/`exportFunction`; content scripts see page objects through **Xray** wrappers (`wrappedJSObject` opts out — deliberately). Types like `exportFunction` live in `Extension/src/types/xray.d.ts`.
- **Treat the page as adversarial** (see `web.md`): minimize footprint and detectable artifacts. Prefer prototype-clean, native-looking wrappers.

#### Code Style & Type Safety
- Strict mode on (`"strict": true`); `noImplicitAny`, `strictNullChecks`, `noUnusedLocals`, `noUnusedParameters`.
- `const` by default, `let` when needed, never `var`; prefer `interface` for object shapes.
- Handle `undefined` explicitly; avoid `as` assertions that bypass safety.

#### Error Handling
- try/catch async work; define domain error types; never swallow errors; log with context before re-throwing.
- In injected instrument code, remember a thrown error's `stack` is page-observable.

#### Security
- **Never** `eval()`, `Function()`, or `innerHTML` with page-supplied data.
- **Avoid prototype pollution** — here it's both a correctness *and* a detectability hazard: mutating a shared prototype from page-world code is directly page-observable (`getOwnPropertyNames`/`hasOwnProperty`).
- All page content/objects are untrusted DATA. This is not a web server or SPA — there are no API request bodies to `zod`-validate, no HTML to `DOMPurify`, and no response headers to set; ignore that class of advice.

#### Dependencies
- Manage via `Extension/package.json`; run `npm run lint`/`build` before pushing extension changes. Keep versions current but review changelogs on majors; remove unused deps.

#### Forbidden Patterns
| Pattern | Why | Fix |
|---------|-----|-----|
| `any` | Disables type checking | `unknown` + type guards |
| `@ts-ignore` / `eslint-disable` (unjustified) | Hides real errors | Fix the error |
| `eval()` / `Function(str)` | Code injection | Self-contained, non-eval code |
| `innerHTML = pageData` | XSS / trusting the page | `textContent`, or treat as data |
| Prototype mutation in page-world | Page-observable fingerprint | Keep wrappers prototype-clean |
