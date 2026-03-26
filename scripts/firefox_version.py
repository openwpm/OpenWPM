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
import urllib.request
from pathlib import Path

INSTALL_SCRIPT = Path(__file__).resolve().parent / "install-firefox.sh"
TAGS_URL = "https://hg.mozilla.org/releases/mozilla-release/json-tags"
_TAG_RE = re.compile(r"FIREFOX_\d+_\d+(?:_\d+)?_RELEASE")


def _version_key(tag: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"FIREFOX_(\d+)_(\d+)(?:_(\d+))?_RELEASE", tag)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def fetch_latest() -> tuple[str, str]:
    """Return (tag_name, commit_hash) for the newest Firefox release on hg.mozilla.org."""
    with urllib.request.urlopen(TAGS_URL, timeout=15) as resp:
        data = json.load(resp)
    tags = [(t["tag"], t["node"]) for t in data["tags"] if _TAG_RE.fullmatch(t["tag"])]
    if not tags:
        raise RuntimeError("No Firefox release tags found")
    tags.sort(key=lambda t: _version_key(t[0]), reverse=True)
    return tags[0]


def get_current() -> str:
    """Return the tag name currently pinned in install-firefox.sh."""
    text = INSTALL_SCRIPT.read_text()
    m = re.search(r"# (FIREFOX_\d+_\d+(?:_\d+)?_RELEASE)", text)
    if not m:
        raise RuntimeError(f"No Firefox tag comment found in {INSTALL_SCRIPT}")
    return m.group(1)


def update_if_needed() -> bool:
    """Rewrite install-firefox.sh if a newer Firefox is available.

    Returns True if the file was updated, False if already current.
    """
    current = get_current()
    latest_tag, latest_hash = fetch_latest()

    if latest_tag == current:
        print(f"Firefox is already at the latest release ({current}).")
        return False

    print(f"Updating Firefox: {current} → {latest_tag}")
    text = INSTALL_SCRIPT.read_text()
    new_text = re.sub(
        r"^TAG='[^']*' # .*$",
        f"TAG='{latest_hash}' # {latest_tag}",
        text,
        flags=re.MULTILINE,
    )
    INSTALL_SCRIPT.write_text(new_text)
    print(f"Updated {INSTALL_SCRIPT.name} to {latest_tag} ({latest_hash})")
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
