"""Update all OpenWPM dependencies and check for a newer Firefox release.

Steps
-----
1. Repin the conda environment (scripts/repin.sh)
2. Update root npm dependencies to latest, resolving peer dep conflicts
3. Update Extension npm dependencies to latest, resolving peer dep conflicts
4. Rebuild the extension
5. Check hg.mozilla.org for a newer Firefox and update install-firefox.sh if found

Run from the project root:
    python scripts/update.py
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

_MAX_RESOLVE_ATTEMPTS = 10


def run(*cmd: str, cwd: Path = ROOT) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.run(list(cmd), check=True, cwd=cwd)


def conda_run(*cmd: str, cwd: Path = ROOT) -> None:
    run("conda", "run", "-n", "openwpm", *cmd, cwd=cwd)


def _npm_install(cwd: Path) -> str:
    """Run npm install and return combined stdout+stderr."""
    result = subprocess.run(
        ["conda", "run", "-n", "openwpm", "npm", "install", "--include=dev"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args)
    return result.stdout + result.stderr


def _peer_dep_conflicts(output: str) -> list[tuple[str, str]]:
    """Return unique (package, required_range) pairs from npm peer dep warnings.

    npm emits lines like:
        npm warn   peer some-pkg@"^2.0.0" from other-pkg@3.0.0
    The package named after 'peer' is the one that is too new; downgrade it
    to the stated range to satisfy the peer requirement.
    """
    seen: set[tuple[str, str]] = set()
    conflicts = []
    for m in re.finditer(r'peer (\S+)@"([^"]+)" from', output):
        pkg, rng = m.group(1), m.group(2)
        if (pkg, rng) not in seen:
            seen.add((pkg, rng))
            conflicts.append((pkg, rng))
    return conflicts


def npm_bump_and_resolve(cwd: Path) -> None:
    """Bump all npm deps to absolute latest, then resolve peer dep conflicts.

    Strategy: use npm-check-updates to rewrite package.json to the newest
    published version of every dependency, then iteratively downgrade any
    package that triggers a peer dep warning until npm install is clean.
    """
    print(f"\n=== npm bump-to-latest: {cwd.relative_to(ROOT)} ===")

    # Rewrite package.json with the latest published versions of all deps.
    conda_run("npx", "--yes", "npm-check-updates", "--upgrade", cwd=cwd)

    for attempt in range(1, _MAX_RESOLVE_ATTEMPTS + 1):
        output = _npm_install(cwd)
        conflicts = _peer_dep_conflicts(output)
        if not conflicts:
            print(f"  Clean install on attempt {attempt}.")
            return
        print(f"  Attempt {attempt}: {len(conflicts)} peer dep conflict(s)")
        for pkg, rng in conflicts:
            print(f"    Downgrading {pkg} → '{rng}'")
            conda_run("npm", "install", f"{pkg}@{rng}", "--include=dev", cwd=cwd)

    print(
        f"WARNING: peer dep conflicts not fully resolved after {_MAX_RESOLVE_ATTEMPTS} attempts.",
        file=sys.stderr,
    )


def main() -> None:
    # Repin the conda environment from unpinned sources
    run("./repin.sh", cwd=SCRIPTS)

    # Bump npm deps to latest and resolve peer dep conflicts
    npm_bump_and_resolve(ROOT)
    npm_bump_and_resolve(ROOT / "Extension")

    # Rebuild the extension XPI after dependency changes
    run("./build-extension.sh", cwd=SCRIPTS)

    # Check for a newer Firefox release and update install-firefox.sh if available
    sys.path.insert(0, str(SCRIPTS))
    import firefox_version

    firefox_version.update_if_needed()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}: {e.cmd}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
