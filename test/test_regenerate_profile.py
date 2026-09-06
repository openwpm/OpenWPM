"""Unit tests for the seed-profile regeneration helper.

These exercise the pure prune logic in ``scripts/regenerate-test-profile.py``
without launching a browser, guarding against the regression where uBlock
Origin's downloaded filter-list IndexedDB (which bloated the fixture ~6.7x) was
left in the archived profile. ``scripts/`` is not an importable package, so the
module is loaded directly from its path.
"""

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.pyonly

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "regenerate-test-profile.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("regenerate_test_profile", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _make_profile(root: Path) -> None:
    """Create a minimal profile tree resembling a real dumped uBlock profile."""
    # Files the archive/tests require -> must survive pruning.
    for name in ("cookies.sqlite", "places.sqlite", "storage.sqlite", "prefs.js"):
        (root / name).write_text("keep")
    # Addon registration -> must survive (drives isActive).
    (root / "extensions").mkdir()
    (root / "extensions" / "uBlock0@raymondhill.net.xpi").write_text("xpi")
    (root / "extensions.json").write_text("{}")
    (root / "addonStartup.json.lz4").write_text("startup")

    # Firefox startup caches -> pruned by name.
    for name in ("startupCache", "cache2", "safebrowsing"):
        (root / name).mkdir()
        (root / name / "blob").write_text("cache")
    (root / "favicons.sqlite").write_text("cache")

    # uBlock's regenerable IndexedDB -> pruned by glob.
    ext_idb = root / "storage" / "default" / "moz-extension+++abcd-1234^userContextId=1" / "idb"
    ext_idb.mkdir(parents=True)
    (ext_idb / "filters.sqlite").write_text("blocklist")
    (ext_idb / "filters.files").mkdir()
    (ext_idb / "filters.files" / "3").write_text("blocklist-blob")

    chrome_idb = root / "storage" / "permanent" / "chrome" / "idb"
    chrome_idb.mkdir(parents=True)
    (chrome_idb / "storage-local.sqlite").write_text("selfie")


def test_prune_removes_ublock_storage_keeps_required(tmp_path):
    module = _load_module()
    profile = tmp_path / "profile"
    profile.mkdir()
    _make_profile(profile)

    module.prune_transient_caches(profile)

    # Required + addon-registration files survive.
    for name in (
        "cookies.sqlite",
        "places.sqlite",
        "storage.sqlite",
        "prefs.js",
        "extensions.json",
        "addonStartup.json.lz4",
    ):
        assert (profile / name).exists(), f"{name} was wrongly pruned"
    assert (profile / "extensions" / "uBlock0@raymondhill.net.xpi").exists()

    # Firefox startup caches are gone.
    for name in ("startupCache", "cache2", "safebrowsing", "favicons.sqlite"):
        assert not (profile / name).exists(), f"{name} should have been pruned"

    # uBlock's downloaded filter-list IndexedDB is gone (both origins).
    assert not list((profile / "storage" / "default").glob("moz-extension+++*"))
    assert not list((profile / "storage" / "permanent" / "chrome" / "idb").glob("*"))


def test_prune_is_idempotent_on_clean_profile(tmp_path):
    module = _load_module()
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "prefs.js").write_text("keep")

    # No caches present: must not raise.
    module.prune_transient_caches(profile)
    assert (profile / "prefs.js").exists()
