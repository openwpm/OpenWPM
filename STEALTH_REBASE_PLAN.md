# Stealth Extension Rebase Plan

## Context

PR #1037 adds a stealth extension to OpenWPM that makes JS instrumentation
undetectable by websites (based on Krumnow et al.'s research). The branch
(`stealth_extension`) was last rebased in Feb 2024 and is now 36 commits behind
master. A naive rebase is complex due to interleaved merge commits, WIP changes,
and conflicts with master's refactoring.

## Recommended Strategy: Fresh Branch with Cherry-Picked Changes

Instead of rebasing all 18 commits (many of which are merges, WIP, or
superseded), create a clean branch from master and port only the stealth-specific
changes. This avoids dragging in stale code that conflicts with master.

---

## Phase 1: New Stealth Files (No Conflicts)

These files are entirely new and can be copied directly from the
`stealth_extension` branch:

| File | Description |
|------|-------------|
| `Extension/src/stealth/error.ts` | Error stack cleaning to hide extension URLs |
| `Extension/src/stealth/instrument.ts` | Non-polluting JS instrumentation using Proxy/exportFunction |
| `Extension/src/stealth/settings.ts` | Default instrumentation settings (Audio, Canvas, Navigator, etc.) |
| `Extension/src/stealth/stealth.ts` | Entry point: intercepts windows/frames, sets up Proxy-based instrumentation |
| `Extension/src/types/js_instrument_settings.d.ts` | TypeScript types generated from JSON schema |
| `schemas/js_instrument_settings.schema.json` | Extended schema with `depth`, `overwrittenProperties` fields |
| `test/test_pages/stealth_detection.html` | Detection test page (written in this session) |
| `test/test_stealth.py` | Stealth detection tests (written in this session) |

**Steps:**
```bash
# From master, create new branch
jj new master -m "feat(stealth): add stealth JS instrumentation extension"

# Copy new files from stealth_extension
git show origin/stealth_extension:Extension/src/stealth/error.ts > Extension/src/stealth/error.ts
git show origin/stealth_extension:Extension/src/stealth/instrument.ts > Extension/src/stealth/instrument.ts
git show origin/stealth_extension:Extension/src/stealth/settings.ts > Extension/src/stealth/settings.ts
git show origin/stealth_extension:Extension/src/stealth/stealth.ts > Extension/src/stealth/stealth.ts
git show origin/stealth_extension:Extension/src/types/js_instrument_settings.d.ts > Extension/src/types/js_instrument_settings.d.ts
# Copy the updated schema
git show origin/stealth_extension:schemas/js_instrument_settings.schema.json > schemas/js_instrument_settings.schema.json
```

## Phase 2: Minimal Modifications to Existing Files

### 2a. `openwpm/config.py` — Add stealth config option

Add `stealth_js_instrument: bool = False` to `BrowserParams`.

**DO NOT** re-add `extension_enabled` — master intentionally removed it in
commit `d1a60fb`.

```python
# In BrowserParams class, after http_instrument:
stealth_js_instrument: bool = False
```

### 2b. `Extension/src/feature.ts` — Add stealth instrument activation

Add the stealth JS instrument initialization block. This should be added
before the regular `js_instrument` block:

```typescript
if (config.stealth_js_instrument) {
    loggingDB.logDebug("Stealth JavaScript Instrumentation enabled");
    const stealthJSInstrument = new JavascriptInstrument(loggingDB, false);
    stealthJSInstrument.run(config.browser_id);
    await stealthJSInstrument.registerContentScript();
}
```

Also add `stealth_js_instrument: false` to the fallback config object.

### 2c. `Extension/src/background/javascript-instrument.ts` — Add legacy flag

Add a `legacy: boolean` parameter to `JavascriptInstrument`:

1. Add `private legacy: boolean = true;` field
2. Update constructor to accept `legacy` parameter
3. Make `registerContentScript` params optional (for stealth mode)
4. Guard the content script config injection with `if (... && this.legacy)`
5. Select entry script based on mode: `const entryScript = this.legacy ? "/content.js" : "/stealth.js";`

### 2d. `Extension/webpack.config.js` — Add stealth entry point

```javascript
entry: {
    feature: "./src/feature.ts",
    content: "./src/content.ts",
    stealth: "./src/stealth/stealth.ts",  // NEW
},
```

### 2e. `Extension/package.json` — Add schema codegen dependency

1. Add `"json-schema-to-typescript": "^13.1.2"` to devDependencies
2. Add build step: `"build:generate_from_schema": "json2ts --input ../schemas/js_instrument_settings.schema.json --output src/types/js_instrument_settings.d.ts"`
3. Update `"build"` script to include `npm run build:generate_from_schema` before `build:main`

### 2f. Build config files

1. Add `bundled/stealth.js` to `Extension/.gitignore`
2. Add `bundled/stealth.js` to `Extension/.eslintrc.js` ignorePatterns
3. Add `Extension/src/stealth.js` to `.dockerignore`

### 2g. `Extension/package-lock.json`

**Do NOT** try to merge the lock files. After making changes to package.json:
```bash
cd Extension && npm install
```
This regenerates the lock file cleanly.

## Phase 3: Files to NOT Bring Over

These changes from the stealth branch are **superseded or conflicting** with
master and should be dropped:

| File | Reason |
|------|--------|
| `openwpm/deploy_browsers/deploy_firefox.py` | Re-adds `extension_enabled` checks that master removed; uses deprecated `FirefoxBinary` |
| `openwpm/deploy_browsers/selenium_firefox.py` | Imports deprecated `FirefoxBinary`; adds `is_webdriver` param not needed |
| `openwpm/deploy_browsers/configure_firefox.py` | Import path change not needed on master |
| `openwpm/browser_manager.py` | Uses `Process` from multiprocess directly (conflicts with master's wrapper); adds `extension_enabled` check |
| `openwpm/utilities/multiprocess_utils.py` | Removes `run_impl` pattern and coverage support that master added |
| `openwpm/utilities/storage_watchdog.py` | Uses `du` subprocess (master's `os.walk` approach is fine) |
| `openwpm/utilities/platform_utils.py` | `firefox-bin` vs `firefox` path change is stale |
| `openwpm/commands/browser_commands.py` | Has typo "visitit" and removes error recovery that master added |
| `openwpm/commands/profile_commands.py` | Uses `webappsstore.sqlite` (master correctly uses `storage.sqlite`) |
| `openwpm/task_manager.py` | Only formatting differences |
| `openwpm/storage/storage_providers.py` | Only whitespace change |
| `hide_commands/` | Screen resolution/position commands — nice-to-have but not core stealth |
| `environment.yaml` | Completely stale; different Firefox version, different pins |
| `LICENSE` | GPLv3 addition — discuss separately (licensing decision) |
| `VERSION`, `README.md`, `CONTRIBUTING.md`, etc. | Stale docs/metadata |
| CI/workflow files | Stale CI config |

## Phase 4: Build and Verify

```bash
# Build the extension
cd Extension && npm ci && npm run build

# Run the existing tests to ensure nothing is broken
pytest test/ -x -v

# Run the stealth-specific tests
pytest test/test_stealth.py -v
```

## Phase 5: Known Issues to Address

### 5a. Type Definition for `javascript-instrument.d.ts`

The stealth branch adds a type file at `Extension/src/types/javascript-instrument.d.ts`
that declares `exportFunction` on the global scope. Master already has this file
with the `openWpmContentScriptConfig` interface. The stealth version adds:

```typescript
declare global {
    function exportFunction(
        vfunction: any, scope: any,
        options: { defineAs: string; allowCrossOriginArguments: boolean }
    ): any;
}
```

This needs to be merged with the existing file content.

### 5b. Object Prototype Extensions in `instrument.ts`

The stealth `instrument.ts` adds methods to `Object.prototype`:
- `getPrototypeByDepth`
- `getPropertyNamesPerDepth`
- `findPropertyInChain`

And adds `getPropertyDescriptor` to `Object`. These need proper TypeScript
declarations (the `declare global` block).

### 5c. Prototype Pollution Tradeoff

As noted by @bkrumnow in issue #1081, the stealth extension avoids prototype
pollution at the cost of tracing origin. This means if multiple objects share a
prototype and a function is called from that prototype, you cannot determine
which object made the call. A future enhancement would be to support both modes.

### 5d. JSON Schema Validation

The stealth branch modifies `schemas/js_instrument_settings.schema.json` to
support both the old string-based `propertiesToInstrument` format and the new
object-based format with `depth` and `propertyNames`. This needs to be verified
against Python-side validation in `openwpm/js_instrumentation.py`.

## Effort Estimate

| Phase | Complexity |
|-------|-----------|
| Phase 1: New files | Low — direct copy |
| Phase 2: Modifications | Medium — 6 files, well-understood changes |
| Phase 3: Verification | Low — just don't include these |
| Phase 4: Build & test | Medium — npm install + build + test suite |
| Phase 5: Edge cases | Medium — type definitions, schema validation |
| **Total** | **Half a day of focused work** |

## Open Questions

1. **License**: The stealth branch adds a GPLv3 `LICENSE` file. OpenWPM is
   currently under GPLv3 already, but the stealth code is derived from
   CanvasBlocker (MPL 2.0). The compatibility is fine (MPL → GPL is allowed),
   but this should be reviewed.

2. **`hide_commands/`**: The window resize/position commands are useful for
   stealth (avoiding the 1366x768 fingerprint) but are orthogonal to the
   core extension work. Consider including them in a follow-up PR.

3. **`json-schema-to-typescript`**: This adds a build-time dependency to
   generate TypeScript types from the JSON schema. Consider whether to
   keep this or maintain the types manually.
