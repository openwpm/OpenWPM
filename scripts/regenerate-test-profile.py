#!/usr/bin/env python3
"""Regenerate the seed profile fixture ``test/profile.tar.gz``.

Why this fixture exists
=======================
``test/profile.tar.gz`` is a *seed profile* used by the profile-restoration
tests (``test/test_profile.py``: ``test_seed_persistence`` and
``test_profile_recovery``). Its purpose is to verify that **Firefox N can read
a profile primed by the PREVIOUS Firefox (N-1)** — i.e. that a profile written
by the old browser still loads, recovers, and brings its installed extension
back up after we bump the pinned Firefox version.

For that check to be meaningful, the fixture must be primed with Firefox **N-1**
and committed *just before* the bump PR raises the pin to N. A profile written
by the same Firefox the tests run on (or by an ancient build) tests nothing.

Regeneration procedure (run OUT-OF-BAND, not in CI)
===================================================
Run this script with the **previous** stable Firefox, immediately before the
PR that bumps the pinned Firefox to the next version. Example for the 150 -> 151
bump (prime with 150.0.2):

    export FIREFOX_BINARY=/path/to/firefox-150/firefox-bin
    python scripts/regenerate-test-profile.py

Then commit the regenerated ``test/profile.tar.gz`` so the bump PR's CI (running
on Firefox 151) loads it and exercises the real N-1 -> N compatibility path.

What the script does
====================
1. Launches Firefox (``FIREFOX_BINARY`` from the environment) via Selenium with
   the same relevant prefs the real OpenWPM deploy uses (extension signing left
   on so a real signed AMO build is required, matching production).
2. Sets the about:config prefs the tests rely on (``test_pref=True``).
3. Installs **uBlock Origin** as a PERMANENT addon, fetched from the Mozilla
   marketplace (AMO). The signed XPI is downloaded via the AMO API
   (``current_version.file.url``) and installed with
   ``driver.install_addon(path, temporary=False)`` so it PERSISTS in the dumped
   profile. A ``temporary=True`` install would be dropped on shutdown and would
   NOT survive into the tar.

   The live AMO download happens ONLY here, out-of-band. CI never touches AMO —
   it loads the baked-in tar and asserts the extension starts up.
4. Warms up the profile by visiting a page (populates places.sqlite history).
5. Dumps the profile to ``test/profile.tar.gz``.

This file IS over jj's default ``snapshot.max-new-file-size`` (1 MB). Do NOT
raise that limit globally; instead track the regenerated tar explicitly
(``jj file track test/profile.tar.gz``) and confirm it lands in the commit.
"""

import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

# uBlock Origin's stable AMO slug and its addon ID (used to verify the install).
UBLOCK_AMO_SLUG = "ublock-origin"
UBLOCK_ADDON_ID = "uBlock0@raymondhill.net"
AMO_API = "https://addons.mozilla.org/api/v5/addons/addon/{slug}/"

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_TAR = REPO_ROOT / "test" / "profile.tar.gz"

WARMUP_URL = "https://example.com/"


def fetch_ublock_xpi(dest_dir: Path) -> Path:
    """Download the current signed uBlock Origin XPI from AMO.

    Uses the AMO v5 API to resolve the current signed build's download URL
    (``current_version.file.url``) and saves it locally. This is the only
    network call to addons.mozilla.org, and it happens only during regeneration.
    """
    api_url = AMO_API.format(slug=UBLOCK_AMO_SLUG)
    print(f"Fetching uBlock Origin metadata from {api_url}")
    with urllib.request.urlopen(api_url, timeout=60) as resp:
        meta = json.load(resp)

    current = meta["current_version"]
    version = current["version"]
    file_info = current["file"]
    xpi_url = file_info["url"]
    print(f"uBlock Origin current_version={version}")
    print(f"Downloading signed XPI from {xpi_url}")

    xpi_path = dest_dir / f"ublock_origin-{version}.xpi"
    # urlretrieve() takes no timeout, so a stalled connection would hang the
    # regeneration indefinitely. Stream via urlopen with a bounded timeout,
    # mirroring the metadata fetch above.
    with urllib.request.urlopen(xpi_url, timeout=60) as resp, open(
        xpi_path, "wb"
    ) as out:
        shutil.copyfileobj(resp, out)
    print(f"Saved XPI to {xpi_path} ({xpi_path.stat().st_size} bytes)")
    return xpi_path


def launch_firefox(profile_dir: Path) -> webdriver.Firefox:
    """Launch Firefox with the prefs the seed profile and tests rely on."""
    firefox_binary = os.environ.get("FIREFOX_BINARY")
    if not firefox_binary:
        sys.exit(
            "FIREFOX_BINARY is not set. Point it at the PREVIOUS (N-1) Firefox "
            "binary, e.g. export FIREFOX_BINARY=/path/to/firefox-150/firefox-bin"
        )
    if not Path(firefox_binary).is_file():
        sys.exit(f"FIREFOX_BINARY does not exist: {firefox_binary}")

    fo = Options()
    fo.binary_location = firefox_binary
    fo.add_argument("-profile")
    fo.add_argument(str(profile_dir))
    # Needed (Firefox 138+) so WebDriver can switch into the chrome context to
    # set the preference, mirroring openwpm/deploy_browsers/deploy_firefox.py.
    fo.add_argument("-remote-allow-system-access")
    fo.add_argument("--headless")

    # The marker preference the restoration tests assert survives save/restore.
    fo.set_preference("test_pref", True)
    # Don't auto-update or disable the freshly installed addon.
    fo.set_preference("extensions.update.enabled", False)
    fo.set_preference("extensions.update.autoUpdateDefault", False)
    fo.set_preference("app.update.enabled", False)
    # Keep AMO signing enforced so we bake in a real signed extension (matches
    # production OpenWPM, which does not disable signature checks for addons it
    # did not build).

    service = Service()  # geckodriver resolved from PATH
    print(f"Launching Firefox: {firefox_binary}")
    driver = webdriver.Firefox(options=fo, service=service)
    return driver


def assert_ublock_active(driver: webdriver.Firefox) -> None:
    """Confirm uBlock Origin is installed AND active via the AddonManager."""
    script = """
        const callback = arguments[arguments.length - 1];
        const { AddonManager } = ChromeUtils.importESModule(
            "resource://gre/modules/AddonManager.sys.mjs"
        );
        AddonManager.getAddonByID(%r).then((addon) => {
            if (!addon) {
                callback({ installed: false });
                return;
            }
            callback({
                installed: true,
                isActive: addon.isActive,
                userDisabled: addon.userDisabled,
                version: addon.version,
            });
        }, (err) => callback({ error: String(err) }));
    """ % UBLOCK_ADDON_ID
    with driver.context(driver.CONTEXT_CHROME):
        driver.set_script_timeout(30)
        result = driver.execute_async_script(script)
    print(f"uBlock AddonManager status: {result}")
    if not result.get("installed"):
        raise RuntimeError("uBlock Origin was not installed into the profile")
    if not result.get("isActive"):
        raise RuntimeError("uBlock Origin is installed but not active")


# Transient caches that Firefox regenerates on startup. They balloon the
# fixture (tens of MB) without contributing to the N-1 -> N compatibility or
# extension-startup checks, so we prune them before archiving.
PRUNE_DIRS = ("startupCache", "cache2", "safebrowsing")
PRUNE_FILES = ("favicons.sqlite", "favicons.sqlite-wal", "favicons.sqlite-shm")


def prune_transient_caches(profile_dir: Path) -> None:
    for name in PRUNE_DIRS:
        target = profile_dir / name
        if target.is_dir():
            shutil.rmtree(target)
            print(f"Pruned cache dir: {name}")
    for name in PRUNE_FILES:
        target = profile_dir / name
        if target.exists():
            target.unlink()
            print(f"Pruned cache file: {name}")


def dump_profile(profile_dir: Path, tar_path: Path) -> None:
    """Tar+gzip the profile directory into ``tar_path`` (arcname-relative)."""
    prune_transient_caches(profile_dir)
    if tar_path.exists():
        tar_path.unlink()
    tar_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "w:gz", errorlevel=1) as tar:
        tar.add(profile_dir, arcname="")
        names = tar.getnames()
    required = ["cookies.sqlite", "places.sqlite", "storage.sqlite", "prefs.js"]
    missing = [item for item in required if item not in names]
    if missing:
        raise RuntimeError(f"Dumped profile missing required items: {missing}")
    print(f"Wrote {tar_path} ({tar_path.stat().st_size} bytes)")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="regen_profile_") as workdir:
        work = Path(workdir)
        profile_dir = work / "profile"
        profile_dir.mkdir()

        xpi_path = fetch_ublock_xpi(work)

        driver = launch_firefox(profile_dir)
        try:
            # Permanent install so the addon persists in the dumped profile.
            driver.install_addon(str(xpi_path), temporary=False)
            print(f"Installed addon {UBLOCK_ADDON_ID} (permanent)")
            # Give the addon a moment to register/start.
            time.sleep(3)
            assert_ublock_active(driver)

            # Warm up the profile so places.sqlite has history.
            driver.get(WARMUP_URL)
            time.sleep(2)
        finally:
            # Closing the driver leaves the -profile dir intact (it is not a
            # geckodriver-managed temp profile), so we can tar it afterwards.
            driver.quit()

        # Let SQLite checkpoint after shutdown before archiving.
        time.sleep(3)
        dump_profile(profile_dir, OUTPUT_TAR)

    print("Done. Remember to track the new tar:")
    print("  jj file track test/profile.tar.gz   # (jj users; tar > 1 MB limit)")


if __name__ == "__main__":
    main()
