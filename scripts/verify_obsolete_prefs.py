#!/usr/bin/env python3
"""Probe whether Firefox still recognizes the default prefs OpenWPM sets.

Methodology (inverts the searchfox approach): instead of trying to prove that
Firefox does *not* read a pref by grepping mozilla-central, we ask the actual
bundled Firefox binary whether it ships a *default* for the pref. A pref that
Firefox no longer defines on the default branch is, for OpenWPM's purposes, an
obsolescence candidate: setting it in the profile has no built-in counterpart
to override.

For each pref we read ``Services.prefs.getDefaultBranch("").getPrefType(name)``
on a *fresh* profile, inside the privileged chrome context. The returned type:

    0   PREF_INVALID  -> Firefox ships NO default  -> obsolescence candidate
    32  PREF_STRING   -> Firefox ships a string default  -> LIVE
    64  PREF_INT      -> Firefox ships an int default     -> LIVE
    128 PREF_BOOL     -> Firefox ships a bool default     -> LIVE

We use the *default* branch (not the user branch) deliberately: the user branch
would be polluted by anything Selenium/our own options set. The default branch
reflects only what the shipped Firefox build itself defines.

Important caveat — this is a strong signal, NOT an absolute proof. A handful of
prefs are read at runtime without a compiled-in default (the code calls
``getBoolPref(name, fallback)`` with an inline fallback), so they legitimately
have no default-branch entry yet are still honored. Therefore prefs that probe
INVALID are reported as **review candidates**, not auto-removed: a human should
confirm against searchfox/mozilla-central before pruning them from
``configure_firefox.py``.

The pref list is NOT hardcoded here. It is imported directly from
``openwpm.deploy_browsers.configure_firefox`` (``PRIVACY_PREFS`` and
``OPTIMIZE_PREFS``), the single source of truth that the Firefox setter also
reads. This structural interlock guarantees the verifier always checks exactly
the prefs OpenWPM applies — the two cannot drift.

Usage:
    FIREFOX_BINARY=/path/to/firefox-bin python scripts/verify_obsolete_prefs.py
    # JSON output:
    FIREFOX_BINARY=... python scripts/verify_obsolete_prefs.py --json

Requires: selenium + geckodriver on PATH, and a Firefox launched with
``-remote-allow-system-access`` (Firefox 138+ gates chrome-context system
access behind that flag).
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

# Make the openwpm package importable when run as a bare script from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openwpm.deploy_browsers.configure_firefox import (  # noqa: E402
    OPTIMIZE_PREFS,
    PRIVACY_PREFS,
)

PREF_TYPE_NAMES = {
    0: "INVALID (no default -> review candidate)",
    32: "STRING (default -> LIVE)",
    64: "INT (default -> LIVE)",
    128: "BOOL (default -> LIVE)",
}

# Single source of truth: every static pref OpenWPM sets, deduplicated and
# ordered (privacy first, then optimize) for stable output.
PREFS: list[str] = list(dict.fromkeys([*PRIVACY_PREFS, *OPTIMIZE_PREFS]))


def make_driver() -> webdriver.Firefox:
    binary = os.environ.get("FIREFOX_BINARY")
    if not binary:
        sys.exit("Set FIREFOX_BINARY to the Firefox binary to probe.")
    options = Options()
    options.binary_location = binary
    # Required for chrome-context system access in Firefox 138+.
    options.add_argument("-remote-allow-system-access")
    options.add_argument("-headless")
    # Prefer an explicit geckodriver on PATH; fall back to selenium-manager.
    geckodriver = shutil.which("geckodriver")
    service = Service(executable_path=geckodriver) if geckodriver else Service()
    return webdriver.Firefox(options=options, service=service)


def probe(driver: webdriver.Firefox, pref: str) -> int:
    """Return the default-branch pref type for ``pref`` (see PREF_TYPE_NAMES)."""
    with driver.context(driver.CONTEXT_CHROME):
        return driver.execute_script(
            "return Services.prefs.getDefaultBranch('')" ".getPrefType(arguments[0]);",
            pref,
        )


def probe_all() -> dict[str, int]:
    """Probe every pref in ``PREFS`` and return ``{pref: pref_type}``."""
    driver = make_driver()
    results: dict[str, int] = {}
    try:
        for pref in PREFS:
            results[pref] = probe(driver, pref)
    finally:
        driver.quit()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    results = probe_all()

    if args.json:
        print(json.dumps(results, indent=2))
        return

    width = max(len(p) for p in PREFS)
    for pref in PREFS:
        ptype = results[pref]
        label = PREF_TYPE_NAMES.get(ptype, f"UNKNOWN({ptype})")
        print(f"{pref.ljust(width)}  {ptype:>3}  {label}")

    invalid = [p for p, t in results.items() if t == 0]
    if invalid:
        print(f"\n{len(invalid)} pref(s) probe INVALID (review candidates):")
        for pref in invalid:
            print(f"  {pref}")


if __name__ == "__main__":
    main()
