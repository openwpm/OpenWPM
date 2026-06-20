#!/usr/bin/env python3
"""Probe whether Firefox still defines the default prefs OpenWPM sets.

For every key of ``PRIVACY_PREFS`` and ``OPTIMIZE_PREFS`` (imported from
``openwpm.deploy_browsers.configure_firefox``, so there is no second list to
maintain) this reads
``Services.prefs.getDefaultBranch("").getPrefType(name)`` in a fresh profile
and then reads the default value, which exists only if the Firefox build
itself ships one; values set by geckodriver or the profile do not count:

    0   PREF_INVALID  no default  -> review candidate
    32  PREF_STRING   string default
    64  PREF_INT      int default
    128 PREF_BOOL     bool default

The signal is strong but not proof, in both directions:

* Some prefs are read with an inline fallback (``getBoolPref(name, false)``)
  and have no default. They probe INVALID yet are honored; the known ones are
  listed in ``READ_WITHOUT_DEFAULT`` and are not reported.
* A default can outlive the code that read it. Such a pref probes live even
  though nothing reads it any more.

The probe only re-checks shipped defaults. It cannot catch a pref that has
no default but is still read through any of these, and neither can a search
of the build for the name:

* names built at runtime (``"browser.search." + "update"``,
  ``"provider." + name + ".lists"``, ``extensions.checkCompatibility.<ver>``);
* prefix readers such as ``getBranch(prefix).getChildList("")``, which act on
  whatever is set below the prefix (Normandy migrates every
  ``extensions.shield-recipe-client.*`` pref into ``app.normandy.*``);
* compressed omni.ja entries, which ``strings`` on the archive does not see.

Confirm a candidate against the Firefox source, including these patterns,
before removing it.

Usage:
    FIREFOX_BINARY=/path/to/firefox-bin python scripts/verify_obsolete_prefs.py

Exit status: 0 if every pref is accounted for, 1 if any is a review
candidate, 2 if Firefox could not be probed.

Requires geckodriver on PATH. Reading prefs from the chrome context needs
system access (Firefox 138+), which geckodriver 0.37.1+ grants only via its
own ``--allow-system-access`` flag, never via capabilities.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openwpm.deploy_browsers.configure_firefox import (  # noqa: E402
    OPTIMIZE_PREFS,
    PRIVACY_PREFS,
)

PREFS: list[str] = [*PRIVACY_PREFS, *OPTIMIZE_PREFS]

# Prefs Firefox reads with an inline fallback instead of a shipped default,
# mapped to the reader that proves it.
READ_WITHOUT_DEFAULT: dict[str, str] = {
    "app.update.disabledForTesting": "toolkit/mozapps/update/UpdateServiceStub.sys.mjs",
    "browser.pagethumbnails.capturing_disabled": "toolkit/components/thumbnails/PageThumbs.sys.mjs",
    "browser.safebrowsing.update.enabled": "toolkit/components/url-classifier/SafeBrowsing.sys.mjs",
    "browser.search.region": "toolkit/modules/Region.sys.mjs",
}

PREF_TYPE_NAMES = {0: "INVALID", 32: "STRING", 64: "INT", 128: "BOOL"}

EXIT_CANDIDATES = 1
EXIT_PROBE_FAILED = 2


# getPrefType on the default branch also reports prefs that only have a user
# value (e.g. the ones geckodriver writes to user.js), so read the default
# value to tell whether one exists.
_PROBE_JS = """
const branch = Services.prefs.getDefaultBranch("");
const name = arguments[0];
const type = branch.getPrefType(name);
const read = {
  [branch.PREF_BOOL]: n => branch.getBoolPref(n),
  [branch.PREF_INT]: n => branch.getIntPref(n),
  [branch.PREF_STRING]: n => branch.getCharPref(n),
}[type];
if (!read) {
  return 0;
}
try {
  read(name);
  return type;
} catch (e) {
  return 0;
}
"""


def make_driver(binary: str) -> webdriver.Firefox:
    options = Options()
    options.binary_location = binary
    options.add_argument("-headless")
    geckodriver = shutil.which("geckodriver")
    if geckodriver is None:
        raise RuntimeError("geckodriver not found on PATH")
    service = Service(
        executable_path=geckodriver, service_args=["--allow-system-access"]
    )
    return webdriver.Firefox(options=options, service=service)


def probe_all(binary: str) -> dict[str, int]:
    """Return ``{pref: default-branch pref type}`` for every pref in ``PREFS``."""
    driver = make_driver(binary)
    try:
        with driver.context(driver.CONTEXT_CHROME):
            return {pref: driver.execute_script(_PROBE_JS, pref) for pref in PREFS}
    finally:
        driver.quit()


def candidates(results: dict[str, int]) -> list[str]:
    return [p for p, t in results.items() if t == 0 and p not in READ_WITHOUT_DEFAULT]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.parse_args()

    binary = os.environ.get("FIREFOX_BINARY")
    if not binary:
        print("Set FIREFOX_BINARY to the Firefox binary to probe.", file=sys.stderr)
        return EXIT_PROBE_FAILED
    try:
        results = probe_all(binary)
    except Exception as e:
        print(f"Could not probe {binary}: {type(e).__name__}: {e}", file=sys.stderr)
        return EXIT_PROBE_FAILED
    obsolete = candidates(results)

    width = max(len(p) for p in PREFS)
    for pref in PREFS:
        ptype = results[pref]
        label = PREF_TYPE_NAMES.get(ptype, f"UNKNOWN({ptype})")
        if ptype == 0 and pref in READ_WITHOUT_DEFAULT:
            label += f" (read without default in {READ_WITHOUT_DEFAULT[pref]})"
        print(f"{pref.ljust(width)}  {ptype:>3}  {label}")

    if obsolete:
        print(f"\n{len(obsolete)} pref(s) have no default (review candidates):")
        for pref in obsolete:
            print(f"  {pref}")
        return EXIT_CANDIDATES
    print(f"\nAll {len(results)} prefs are defined or known to be read.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
