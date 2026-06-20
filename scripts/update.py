"""Update all OpenWPM dependencies and check for a newer Firefox release.

Steps
-----
1. Repin the conda environment (scripts/repin.sh)
2. Sync pre-commit linter revs to the freshly pinned conda env
3. Update root npm dependencies to latest, resolving peer dep conflicts
4. Update Extension npm dependencies to latest, resolving peer dep conflicts
5. Rebuild the extension
6. Check hg.mozilla.org for a newer Firefox and update install-firefox.sh if found

Run from the project root:
    python scripts/update.py
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

# Where install-firefox.sh drops the unbranded Firefox build (non-macOS).
_FIREFOX_BINARY = ROOT / "firefox-bin" / "firefox-bin"

_MAX_RESOLVE_ATTEMPTS = 10

# Mapping: conda package name → (pre-commit repo URL, rev prefix)
# The prefix is prepended to the conda version to form the pre-commit rev tag.
_LINTER_MAP: dict[str, tuple[str, str]] = {
    "black": ("https://github.com/psf/black", ""),
    "isort": ("https://github.com/timothycrosley/isort", ""),
    "mypy": ("https://github.com/pre-commit/mirrors-mypy", "v"),
}


def run(*cmd: str, cwd: Path = ROOT) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.run(list(cmd), check=True, cwd=cwd)


def conda_run(*cmd: str, cwd: Path = ROOT) -> None:
    run("conda", "run", "-n", "openwpm", *cmd, cwd=cwd)


def _versions_from_conda_list_json(json_str: str) -> dict[str, str]:
    """Parse the output of ``conda list --json`` into ``{name: version}``.

    Separated from the subprocess call so it can be unit-tested without
    invoking conda.
    """
    data = json.loads(json_str)
    return {pkg["name"]: pkg["version"] for pkg in data}


def _query_conda_versions(env_name: str = "openwpm") -> dict[str, str]:
    """Return ``{package_name: version}`` for all packages in the conda env.

    Uses ``conda list -n <env> --json`` so we get authoritative, fully-resolved
    versions without re-parsing environment.yaml ourselves.
    """
    try:
        result = subprocess.run(
            ["conda", "list", "-n", env_name, "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "conda not found on PATH. Install it via ./install.sh or activate "
            "your conda installation before running this script."
        ) from e

    if result.returncode != 0:
        raise RuntimeError(
            f"`conda list -n {env_name} --json` failed (exit {result.returncode}). "
            f"Does the env exist? Run ./install.sh to create it.\n"
            f"stderr: {result.stderr.strip()}"
        )

    return _versions_from_conda_list_json(result.stdout)


def sync_precommit_linter_versions(env_name: str = "openwpm") -> None:
    """Sync linter revs in ``.pre-commit-config.yaml`` to the conda env.

    Fails loud if a linter from ``_LINTER_MAP`` is missing from the env or
    if its hook is missing from ``.pre-commit-config.yaml`` — environment.yaml
    is supposed to be fully pinned, so silent gaps would mask real bugs.
    """
    precommit_yaml = ROOT / ".pre-commit-config.yaml"

    print("\n=== Syncing pre-commit linter versions with conda ===")

    conda_versions = _query_conda_versions(env_name)
    content = precommit_yaml.read_text()

    updated = False
    for pkg, (repo_url, prefix) in _LINTER_MAP.items():
        if pkg not in conda_versions:
            raise RuntimeError(f"{pkg} not found in conda env '{env_name}'.")

        target_rev = f"{prefix}{conda_versions[pkg]}"

        # Match the repo URL line followed by the rev line, preserving whitespace.
        pattern = re.compile(
            rf"(- repo: {re.escape(repo_url)}\s*\n\s*rev:\s*)\S+",
        )
        match = pattern.search(content)
        if not match:
            raise RuntimeError(
                f"No rev: line found for {repo_url} in .pre-commit-config.yaml"
            )

        current_rev = content[match.start(0) + len(match.group(1)) : match.end(0)]
        if current_rev == target_rev:
            print(f"  {pkg}: already in sync ({current_rev})")
            continue

        print(f"  {pkg}: {current_rev} -> {target_rev}")
        content = (
            content[: match.start(0)]
            + match.group(1)
            + target_rev
            + content[match.end(0) :]
        )
        updated = True

    if updated:
        precommit_yaml.write_text(content)
        print("Updated .pre-commit-config.yaml")
    else:
        print("All linter versions already in sync.")


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
    # typescript is pinned to 5.x: TS 6 enables stricter inference defaults
    # (TS7006/TS7008/TS2564/TS18046) that surface ~200 latent type issues
    # in Extension/src. Migration tracked in #1168; until that lands the
    # bumper stays inside 5.x.
    #
    # @babel/* is held at 7.x: Babel 8 is a major with its own migration
    # (config/preset changes). Hold the trio together — bumping preset-env to
    # 8 while core/cli stay on 7 leaves an uninstallable peer state. Bump them
    # together once a babel-8 migration is done.
    #
    # eslint is held at 9.x: @microsoft/eslint-plugin-sdl (latest 1.1.0) peers
    # eslint ^9, so bumping to eslint 10 leaves an uninstallable peer state.
    # eslint 10 needs its own migration (flat-config / API changes); bump once
    # eslint-plugin-sdl ships an eslint-10-compatible release. eslint-plugin-
    # unicorn is held alongside it: unicorn 67 peers eslint >=10.4, so it must
    # stay on its eslint-9-compatible line (64.x) until eslint moves to 10.
    conda_run(
        "npx",
        "--yes",
        "npm-check-updates",
        "--upgrade",
        "--reject",
        "typescript,@babel/core,@babel/cli,@babel/preset-env,eslint,eslint-plugin-unicorn",
        cwd=cwd,
    )

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


def sync_extension_node_engine(env_name: str = "openwpm") -> None:
    """Sync ``engines.node`` in ``Extension/package.json`` to the conda env.

    The Extension is built only inside this project, with Node provided by the
    conda env, so the engines field documents what we actually exercise rather
    than a public compatibility floor. Keeping it pinned to the conda nodejs
    version prevents the two from drifting after a repin.
    """
    pkg_json = ROOT / "Extension" / "package.json"

    print("\n=== Syncing Extension engines.node with conda nodejs ===")

    versions = _query_conda_versions(env_name)
    if "nodejs" not in versions:
        raise RuntimeError(f"nodejs not found in conda env '{env_name}'.")

    target = f">={versions['nodejs']}"
    data = json.loads(pkg_json.read_text())
    current = data.get("engines", {}).get("node")

    if current == target:
        print(f"  engines.node: already in sync ({current})")
        return

    print(f"  engines.node: {current!r} -> {target!r}")
    data.setdefault("engines", {})["node"] = target
    pkg_json.write_text(json.dumps(data, indent=2) + "\n")


_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_TAG_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def bump_version_if_behind() -> None:
    """Bump VERSION to ``<latest-tag-major>.<latest-tag-minor + 1>.0`` if it
    sits at or below the latest release tag.

    Catches the silent-drift case where a previous release tagged a version
    but forgot to bump the VERSION file (which is exactly what happened
    between v0.32.0 and v0.33.0). Idempotent: if VERSION is already ahead
    of next-minor, does nothing.

    Why next-minor and not next-patch: every OpenWPM release historically
    bumps minor (each new Firefox gets a new minor). Patch and major bumps
    are rare enough to do by hand.
    """
    version_file = ROOT / "VERSION"

    print("\n=== Checking VERSION against latest release tag ===")

    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v*"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        print("  No matching git tag found; skipping VERSION bump")
        return

    tag = result.stdout.strip()
    tag_match = _TAG_RE.match(tag)
    if not tag_match:
        print(f"  Latest tag {tag!r} doesn't match vX.Y.Z; skipping VERSION bump")
        return
    tag_v = tuple(int(x) for x in tag_match.groups())

    current_text = version_file.read_text().strip()
    current_match = _VERSION_RE.match(current_text)
    if not current_match:
        raise RuntimeError(f"Can't parse VERSION: {current_text!r}")
    current_v = tuple(int(x) for x in current_match.groups())

    next_v = (tag_v[0], tag_v[1] + 1, 0)

    if current_v >= next_v:
        print(f"  VERSION ({current_text}) already ahead of next-minor; nothing to do")
        return

    target = ".".join(str(x) for x in next_v)
    print(f"  VERSION: {current_text} -> {target} (latest tag {tag})")
    version_file.write_text(target + "\n")


def check_obsolete_firefox_prefs() -> None:
    """Probe the installed Firefox for prefs OpenWPM sets that it no longer
    recognizes, and print a non-fatal WARNING block for any that probe obsolete.

    This reads the freshly-installed Firefox (``firefox-bin/firefox-bin``, or
    ``$FIREFOX_BINARY`` if set) via ``scripts/verify_obsolete_prefs.py``, which
    imports the very pref dicts ``configure_firefox.py`` applies — so the check
    covers exactly the prefs we set, with no separate list to maintain.

    Never fatal: a missing binary, a launch failure, or obsolete prefs only emit
    a warning. The point is to surface drift after a Firefox bump, not to block
    the update.
    """
    print("\n=== Checking installed Firefox for obsolete OpenWPM prefs ===")

    binary = os.environ.get("FIREFOX_BINARY") or str(_FIREFOX_BINARY)
    if not Path(binary).is_file():
        print(
            f"  Firefox binary not found at {binary}; skipping pref check.\n"
            "  Run ./scripts/install-firefox.sh, then re-run this check with\n"
            "  `python scripts/verify_obsolete_prefs.py`."
        )
        return

    env = {**os.environ, "FIREFOX_BINARY": binary}
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "verify_obsolete_prefs.py"), "--json"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            "  WARNING: could not probe Firefox prefs (non-fatal).\n"
            f"  {result.stderr.strip()}",
            file=sys.stderr,
        )
        return

    try:
        results: dict[str, int] = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(
            "  WARNING: could not parse pref-probe output (non-fatal).",
            file=sys.stderr,
        )
        return

    # pref_type 0 == PREF_INVALID: Firefox ships no default for this pref.
    obsolete = [pref for pref, ptype in results.items() if ptype == 0]
    if not obsolete:
        print(f"  All {len(results)} prefs OpenWPM sets are still recognized.")
        return

    print(
        "\n"
        "  ============================ WARNING ============================\n"
        f"  {len(obsolete)} pref(s) OpenWPM sets are no longer recognized by the\n"
        "  installed Firefox (no default-branch entry). Consider pruning them\n"
        "  from openwpm/deploy_browsers/configure_firefox.py:\n",
        file=sys.stderr,
    )
    for pref in obsolete:
        print(f"    - {pref}", file=sys.stderr)
    print(
        "\n"
        "  Note: a default-branch absence is a strong but not absolute signal\n"
        "  (a few prefs are read with an inline fallback). Confirm against\n"
        "  searchfox/mozilla-central before removing.\n"
        "  ================================================================\n",
        file=sys.stderr,
    )


def main() -> None:
    # Repin the conda environment from unpinned sources
    run("./repin.sh", cwd=SCRIPTS)

    # Sync pre-commit linter versions to match the freshly pinned conda env
    sync_precommit_linter_versions()

    # Sync Extension's engines.node to match the freshly pinned conda env
    sync_extension_node_engine()

    # Catch silent VERSION drift relative to the latest release tag
    bump_version_if_behind()

    # Bump npm deps to latest and resolve peer dep conflicts
    npm_bump_and_resolve(ROOT)
    npm_bump_and_resolve(ROOT / "Extension")

    # Rebuild the extension XPI after dependency changes
    run(str(SCRIPTS / "build-extension.sh"))

    # Check for a newer Firefox release and update install-firefox.sh if available
    sys.path.insert(0, str(SCRIPTS))
    import firefox_version

    firefox_version.update_if_needed()

    # Verify the prefs OpenWPM sets are still recognized by the installed
    # Firefox (non-fatal warning if any have gone obsolete).
    check_obsolete_firefox_prefs()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}: {e.cmd}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
