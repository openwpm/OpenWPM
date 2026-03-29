---
title: "Firefox preference cleanup — remove obsolete prefs, document functional intent"
tags: [design-doc]
sources: []
contributors: [claude]
created: 2026-03-29
updated: 2026-03-29
---


## Design Specification

### Summary

Remove Firefox preferences from `openwpm/deploy_browsers/configure_firefox.py` that no longer exist in modern Firefox (v147+), add modern replacements where needed, and document every change with a searchfox.org citation so the intent is auditable. The primary failure mode this PR must guard against is Firefox auto-updating mid-crawl and corrupting the dataset; suppressing background connections is secondary.

### Requirements

- REQ-1: For every removed pref, a searchfox.org (mozilla-central) citation must be present as an inline comment or PR description entry proving the pref no longer exists **or** that it was superseded by a named modern equivalent.
- REQ-2: Firefox auto-update must be reliably blocked. `app.update.url = ""` alone is insufficient; `app.update.auto = False` must be explicitly set alongside it.
- REQ-3: Normandy/studies must be suppressed. If `app.normandy.enabled` exists in mozilla-central, it must be set to `False` in addition to the existing `app.shield.optoutstudies.enabled = False`.
- REQ-4: Geo-specific search customization must remain suppressed for US locale. If `browser.search.geoSpecificDefaults` / `browser.search.geoSpecificDefaults.url` no longer exist, `browser.search.region = "US"` with `browser.search.geoip.url = ""` is the documented fallback. If a modern rename exists, it must be added.
- REQ-5: Every pref retained from the original file must still exist in mozilla-central (no silently-ignored prefs left behind).
- REQ-6: No new automated tests are required; searchfox verification is the acceptance mechanism for correctness.

### Acceptance Criteria

- [ ] AC-1 (REQ-2): `app.update.auto = False` is present in `optimize_prefs()` alongside `app.update.url = ""`, with a comment citing the searchfox source confirming `app.update.enabled` was removed/replaced.
- [ ] AC-2 (REQ-3): `app.normandy.enabled = False` is present if confirmed by searchfox to exist in mozilla-central. If it does not exist, a comment on the `app.shield.optoutstudies.enabled` line explains that it is the sole modern guard.
- [ ] AC-3 (REQ-4): The geo-search section has an inline comment documenting whether `browser.search.geoSpecificDefaults` still exists. If removed: comment cites searchfox. If renamed: the modern pref is added.
- [ ] AC-4 (REQ-1): PR description (or inline comments) contains searchfox URLs for each of the 27 removed prefs confirming removal or supersession. Grouped by category is acceptable.
- [ ] AC-5 (REQ-5): A brief audit of retained prefs confirms they still exist in mozilla-central (spot-check of ≥5 retained prefs cited in PR description).
- [ ] AC-6 (REQ-1): The typo fix `browser.safebrowsing.phising.enabled` → `browser.safebrowsing.phishing.enabled` is present and the corrected pref confirmed to exist via searchfox.

### Architecture

Single file changed: `openwpm/deploy_browsers/configure_firefox.py`. The `optimize_prefs(fo: Options)` function (line 38) is the only scope of this PR.

The function is called unconditionally from `openwpm/deploy_browsers/deploy_firefox.py` for every browser instance. Changes here affect all crawl modes (`headless`, `xvfb`, `native`).

**Priority hierarchy for prefs in this file:**
1. Update prevention (`app.update.*`) — catastrophic if broken; dataset is corrupted if Firefox updates mid-crawl
2. Background connection suppression (telemetry, Normandy, newtab directory, geo pings) — pollutes `http_requests` table
3. UI suppression (startup dialogs, slow-startup metrics) — harmless in headless, safe to remove if pref is gone

**Known additions required by this design:**
- `app.update.auto = False` — add to "Disable auto-updating" section
- `app.normandy.enabled = False` — add to "Disable Shield / Normandy studies" section (conditional on searchfox confirmation)

<!-- OPEN: geo-search-modern-pref -->
### Q: Does browser.search.geoSpecificDefaults still exist or was it renamed?
Awaiting research agent result. If still exists, it must be re-added. If removed/renamed, AC-3 documents the reasoning.
**To resolve**: Update AC-3 and Architecture with research agent findings, remove this block.
<!-- /OPEN -->

<!-- OPEN: normandy-pref-exists -->
### Q: Does app.normandy.enabled exist in mozilla-central?
Awaiting research agent result. AC-2 is conditional on this answer.
**To resolve**: Update AC-2 with confirmed yes/no, remove this block.
<!-- /OPEN -->

### Out of Scope

- Automated test verifying Firefox version stability across a crawl run (pref+searchfox verification is sufficient)
- Changes to `privacy()` function or any other configure_firefox.py function
- Audit of prefs outside `optimize_prefs()` (e.g. `xpinstall.signatures.required`)
- Schema migrations or storage changes
- Any pref not in the original 27 removed by PR #1140

