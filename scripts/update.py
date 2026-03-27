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

import json
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


def _npm_install(cwd: Path) -> tuple[str, bool]:
    """Run npm install and return (combined output, success).

    On a hard ERESOLVE failure npm exits non-zero; we still return the output
    so the caller can parse peer dep conflicts and retry after downgrading.
    Any other non-zero exit is re-raised as a CalledProcessError.
    """
    result = subprocess.run(
        ["conda", "run", "-n", "openwpm", "npm", "install", "--include=dev"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    print(result.stdout, end="")
    combined = result.stdout + result.stderr
    if result.returncode != 0:
        if "ERESOLVE" not in combined:
            print(result.stderr, end="", file=sys.stderr)
            raise subprocess.CalledProcessError(result.returncode, result.args)
    return combined, result.returncode == 0


def _peer_dep_conflicts(output: str) -> list[tuple[str, str]]:
    """Return unique (package, target_range) pairs to write into package.json.

    Two strategies:
    1. Tight peer constraints: ``peer X@"range" from Y`` where the range has
       no ``||`` (i.e. it actually constrains the version, e.g. ``>=4.8.4 <6.0.0``).
       Apply that range directly.
    2. "Could not resolve" direct deps: npm refused to install ``X@^N.x`` as a
       direct dependency.  Try the previous major: ``^(N-1).0.0``.

    Ranges with ``||`` (e.g. ``^6.0.0 || ^7.0.0 || >=8.0.0``) are skipped for
    strategy 1 — they are broad compatibility declarations that still include the
    latest major, so applying them never converges.
    """
    seen: set[tuple[str, str]] = set()
    conflicts = []

    # Strategy 1: tight peer constraint (no OR, actually bounds the version)
    for m in re.finditer(r'peer (\S+)@"([^"]+)" from', output):
        pkg, rng = m.group(1), m.group(2)
        if "||" not in rng and (pkg, rng) not in seen:
            seen.add((pkg, rng))
            conflicts.append((pkg, rng))

    # Strategy 2: direct dep that couldn't be resolved — try previous major
    for m in re.finditer(
        r"Could not resolve dependency:\nnpm error (?:dev|peer) (\S+)@\"\^(\d+)",
        output,
        re.MULTILINE,
    ):
        pkg, major_str = m.group(1), m.group(2)
        major = int(major_str)
        if major > 0:
            rng = f"^{major - 1}.0.0"
            if (pkg, rng) not in seen:
                seen.add((pkg, rng))
                conflicts.append((pkg, rng))

    return conflicts


def _apply_downgrades(cwd: Path, conflicts: list[tuple[str, str]]) -> None:
    """Write downgraded version ranges directly into package.json.

    Modifying package.json avoids the problem of passing space-containing
    semver ranges (e.g. ">=4.8.4 <6.0.0") to the npm CLI, and ensures all
    conflicts are applied atomically before the next npm install attempt.
    """
    pkg_json = cwd / "package.json"
    data = json.loads(pkg_json.read_text())
    for pkg, rng in conflicts:
        for section in ("dependencies", "devDependencies"):
            if section in data and pkg in data[section]:
                print(f"    {pkg}: {data[section][pkg]!r} → {rng!r}")
                data[section][pkg] = rng
                break
        else:
            print(f"    {pkg} not found in package.json deps, skipping")
    pkg_json.write_text(json.dumps(data, indent=2) + "\n")


def npm_bump_and_resolve(cwd: Path) -> None:
    """Bump all npm deps to absolute latest, then resolve peer dep conflicts.

    Strategy: restore package.json from git for a clean slate, use
    npm-check-updates to rewrite it to the newest published versions, then
    iteratively apply peer dep conflict fixes until npm install is clean.
    """
    print(f"\n=== npm bump-to-latest: {cwd.relative_to(ROOT)} ===")

    # Restore package.json to its committed state for a clean baseline.
    run("git", "checkout", "--", "package.json", cwd=cwd)

    # Rewrite package.json with the latest published versions of all deps.
    conda_run("npx", "--yes", "npm-check-updates", "--upgrade", cwd=cwd)

    for attempt in range(1, _MAX_RESOLVE_ATTEMPTS + 1):
        output, success = _npm_install(cwd)
        conflicts = _peer_dep_conflicts(output)
        if success and not conflicts:
            print(f"  Clean install on attempt {attempt}.")
            return
        print(f"  Attempt {attempt}: {len(conflicts)} peer dep conflict(s)")
        _apply_downgrades(cwd, conflicts)

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
    run(str(SCRIPTS / "build-extension.sh"))

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
