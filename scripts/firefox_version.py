"""Fetch the latest Firefox release tag and optionally update install-firefox.sh.

Subcommands
-----------
check   Print the current and latest Firefox release tags.
        Exits 0 if up to date, 1 if an update is available.

update  Update scripts/install-firefox.sh to the latest Firefox release.
        No-op (exits 0) if already up to date.

Run from any directory:
    python scripts/firefox_version.py check
    python scripts/firefox_version.py update
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

INSTALL_SCRIPT = Path(__file__).resolve().parent / "install-firefox.sh"
MANIFEST = (
    Path(__file__).resolve().parent.parent / "Extension" / "bundled" / "manifest.json"
)
TAGS_URL = "https://hg.mozilla.org/releases/mozilla-release/json-tags"
_TAG_RE = re.compile(r"FIREFOX_(\d+)_(\d+)(?:_(\d+))?_RELEASE")

# TaskCluster index for the unbranded ("add-on-devel") builds that
# install-firefox.sh downloads. Keep the platform list in sync with the
# platforms install-firefox.sh knows how to install.
_INDEX_URL = (
    "https://firefox-ci-tc.services.mozilla.com/api/index/v1/task/"
    "gecko.v2.mozilla-release.revision.{node}.firefox.{platform}-add-on-devel"
)
_PLATFORMS = ("linux64", "macosx64")

# How many release tags to walk back before giving up looking for one with
# unbranded builds. Generous enough to skip a run of unbuilt dot releases,
# small enough that a systemic TaskCluster outage fails fast.
_MAX_TAG_LOOKBACK = 10


def _version_key(tag: str) -> tuple[int, int, int]:
    m = _TAG_RE.fullmatch(tag)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def has_unbranded_build(node: str) -> bool:
    """Return True if unbranded builds exist for ``node`` on every platform.

    The revision a release is *tagged* at does not always have unbranded
    ("add-on-devel") builds indexed against it: Mozilla sometimes builds a dot
    release from a later mozilla-release revision than the one the
    FIREFOX_..._RELEASE tag points at, and expedited dot releases also ship a
    trimmed task graph that drops the unbranded builds entirely. Either way,
    pinning such a tag makes install-firefox.sh fail with a 404 at download
    time (see #964), so the index is consulted before a tag is chosen rather
    than after.

    Note this checks the tagged revision only, so a release whose builds live
    at an untagged revision is skipped rather than resolved to that revision --
    we pin one release behind instead of failing. Resolving the build revision
    from the index itself is tracked in #1221.
    """
    for platform in _PLATFORMS:
        url = _INDEX_URL.format(node=node, platform=platform)
        req = urllib.request.Request(url, method="HEAD")
        try:
            urllib.request.urlopen(req, timeout=15).close()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            raise
    return True


def fetch_latest() -> tuple[str, str]:
    """Return (tag_name, commit_hash) for the newest installable Firefox release.

    "Installable" means the tag has unbranded builds on TaskCluster for every
    platform install-firefox.sh supports. Newer tags without them are skipped,
    because pinning one would break every fresh install.
    """
    req = urllib.request.Request(TAGS_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    tags = [(t["tag"], t["node"]) for t in data["tags"] if _TAG_RE.fullmatch(t["tag"])]
    if not tags:
        raise RuntimeError("No Firefox release tags found")
    tags.sort(key=lambda t: _version_key(t[0]), reverse=True)

    for tag, node in tags[:_MAX_TAG_LOOKBACK]:
        if has_unbranded_build(node):
            return tag, node
        print(f"  Skipping {tag}: no unbranded build on TaskCluster")

    raise RuntimeError(
        f"None of the {_MAX_TAG_LOOKBACK} newest Firefox release tags have "
        f"unbranded builds on TaskCluster. This is unusual — check "
        f"https://firefox-ci-tc.services.mozilla.com/ before pinning by hand."
    )


def get_current() -> str:
    """Return the tag name currently pinned in install-firefox.sh."""
    text = INSTALL_SCRIPT.read_text()
    m = re.search(r"# (FIREFOX_\d+_\d+(?:_\d+)?_RELEASE)", text)
    if not m:
        raise RuntimeError(f"No Firefox tag comment found in {INSTALL_SCRIPT}")
    return m.group(1)


def _update_manifest_min_version(major: int) -> None:
    """Pin Extension/bundled/manifest.json's strict_min_version to ``{major}.0``.

    Each OpenWPM release ships only with the Firefox we bundle, so the
    manifest's compatibility floor should match — there is no third-party
    Firefox we need to support.
    """
    target = f"{major}.0"
    text = MANIFEST.read_text()
    data = json.loads(text)
    gecko = data.get("applications", {}).get("gecko", {})
    current = gecko.get("strict_min_version")

    if current == target:
        return

    print(f"  manifest strict_min_version: {current!r} -> {target!r}")

    # Patch the single value in place instead of re-serializing the document.
    # json.dumps(indent=2) expands short arrays onto one element per line,
    # which is not how prettier formats them, so a full rewrite would leave
    # the manifest failing the Extension lint gate after every Firefox bump.
    new_text, count = re.subn(
        r'("strict_min_version"\s*:\s*)"[^"]*"',
        lambda m: m.group(1) + json.dumps(target),
        text,
    )
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one strict_min_version in {MANIFEST}, found {count}"
        )
    MANIFEST.write_text(new_text)


def update_if_needed() -> bool:
    """Rewrite install-firefox.sh and the Extension manifest if a newer Firefox
    is available.

    Returns True if any file was updated, False if already current.
    """
    current = get_current()
    latest_tag, latest_hash = fetch_latest()

    if latest_tag == current:
        print(f"Firefox is already at the latest release ({current}).")
        # Still re-check the manifest in case it drifted independently.
        _update_manifest_min_version(_version_key(current)[0])
        return False

    print(f"Updating Firefox: {current} → {latest_tag}")
    text = INSTALL_SCRIPT.read_text()
    new_text, count = re.subn(
        r"^TAG='[^']*' # .*$",
        f"TAG='{latest_hash}' # {latest_tag}",
        text,
        flags=re.MULTILINE,
    )
    if count == 0:
        raise RuntimeError(
            f"Failed to update TAG line in {INSTALL_SCRIPT}: no matching line found"
        )
    INSTALL_SCRIPT.write_text(new_text)
    print(f"Updated {INSTALL_SCRIPT.name} to {latest_tag} ({latest_hash})")

    _update_manifest_min_version(_version_key(latest_tag)[0])

    print("Remember to run ./scripts/install-firefox.sh and test before releasing.")
    return True


def cmd_check() -> int:
    current = get_current()
    latest_tag, _ = fetch_latest()
    print(f"Current : {current}")
    print(f"Latest  : {latest_tag}")
    if latest_tag == current:
        print("Up to date.")
        return 0
    print("Update available.")
    return 1


def cmd_update() -> int:
    update_if_needed()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or update the Firefox release pinned in install-firefox.sh.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Print current vs latest Firefox tag")
    sub.add_parser("update", help="Update install-firefox.sh to latest Firefox")
    args = parser.parse_args()

    if args.command == "check":
        return cmd_check()
    if args.command == "update":
        return cmd_update()
    return 1


if __name__ == "__main__":
    sys.exit(main())
