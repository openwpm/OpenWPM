"""Manage the relationship between pinned (environment.yaml) and unpinned
(environment-unpinned*.yaml) dependency files.

Subcommands
-----------
check   Validate every pinned package has a corresponding unpinned entry.
        Exits 0 on success, 1 on failure.  Used by pre-commit.

prune   Filter environment.yaml to only keep deps present in unpinned files
        and write the result back.  Used by repin.sh.

Run from any directory:
    python scripts/manage-environment.py check
    python scripts/manage-environment.py prune
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _resolve_paths() -> tuple[Path, Path, Path]:
    """Return (pinned, unpinned, unpinned_dev) paths relative to this script."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    return (
        project_root / "environment.yaml",
        script_dir / "environment-unpinned.yaml",
        script_dir / "environment-unpinned-dev.yaml",
    )


def load_envs() -> tuple[dict, dict, dict]:
    """Read all three YAML environment files."""
    pinned_path, unpinned_path, unpinned_dev_path = _resolve_paths()
    with open(pinned_path, encoding="utf-8") as f:
        pinned = yaml.safe_load(f)
    with open(unpinned_path, encoding="utf-8") as f:
        unpinned = yaml.safe_load(f)
    with open(unpinned_dev_path, encoding="utf-8") as f:
        unpinned_dev = yaml.safe_load(f)
    return pinned, unpinned, unpinned_dev


def extract_name(dep: str) -> str:
    """Extract package name from a dependency string.

    Handles common dependency formats, including:
    - Conda channel prefixes: ``conda-forge::numpy=1.2`` -> ``numpy``
    - Pip direct references (PEP 508): ``pkg @ url`` or ``pkg@url`` -> ``pkg``
    - Extras: ``pkg[extra]==1.2`` -> ``pkg``
    """
    name = dep.strip()

    # Strip conda channel prefixes: "channel::name" -> "name"
    if "::" in name:
        name = name.split("::", 1)[1]

    # Extract the leading distribution name token.  Distribution names consist
    # of letters, digits, underscore, dot and hyphen; this naturally stops at
    # version constraints, extras, direct reference URLs, etc.
    match = re.match(r"[A-Za-z0-9_.-]+", name)
    return match.group(0) if match else name


def parse_deps(
    dependencies: list[str | dict[str, list[str]]],
) -> tuple[set[str], set[str]]:
    """Parse conda and pip package names from a YAML dependencies list."""
    conda: set[str] = set()
    pip: set[str] = set()
    for dep in dependencies:
        if isinstance(dep, dict) and "pip" in dep:
            for p in dep["pip"]:
                pip.add(extract_name(p))
        elif isinstance(dep, str):
            conda.add(extract_name(dep))
    return conda, pip


# ---------------------------------------------------------------------------
# check subcommand
# ---------------------------------------------------------------------------


def cmd_check(pinned: dict, unpinned: dict, unpinned_dev: dict) -> int:
    """Validate every pinned package has a corresponding unpinned entry."""
    pinned_conda, pinned_pip = parse_deps(pinned["dependencies"])
    unpinned_conda, unpinned_pip = parse_deps(unpinned["dependencies"])
    dev_conda, dev_pip = parse_deps(unpinned_dev["dependencies"])

    all_unpinned_conda = unpinned_conda | dev_conda
    all_unpinned_pip = unpinned_pip | dev_pip

    orphaned_conda = pinned_conda - all_unpinned_conda
    orphaned_pip = pinned_pip - all_unpinned_pip

    if not orphaned_conda and not orphaned_pip:
        return 0

    print("ERROR: Found packages in environment.yaml without a corresponding")
    print("entry in scripts/environment-unpinned.yaml or")
    print("scripts/environment-unpinned-dev.yaml.")
    print()
    print("Add the package to the appropriate unpinned file, then run")
    print("scripts/repin.sh to regenerate environment.yaml.")
    print()

    if orphaned_conda:
        print("Orphaned conda packages:")
        for pkg in sorted(orphaned_conda):
            print(f"  - {pkg}")
    if orphaned_pip:
        print("Orphaned pip packages:")
        for pkg in sorted(orphaned_pip):
            print(f"  - {pkg}")

    return 1


# ---------------------------------------------------------------------------
# prune subcommand
# ---------------------------------------------------------------------------


def _filter_deps(
    pinned_deps: list[str],
    unpinned_names: set[str],
) -> list[str]:
    """Keep only pinned dep strings whose extracted name is in *unpinned_names*."""
    kept: list[str] = []
    for dep in pinned_deps:
        if extract_name(dep) in unpinned_names:
            kept.append(dep)
    return sorted(set(kept))


def cmd_prune(pinned: dict, unpinned: dict, unpinned_dev: dict) -> int:
    """Prune environment.yaml to only deps present in unpinned files."""
    unpinned_conda, unpinned_pip = parse_deps(unpinned["dependencies"])
    dev_conda, dev_pip = parse_deps(unpinned_dev["dependencies"])

    all_unpinned_conda = unpinned_conda | dev_conda
    all_unpinned_pip = unpinned_pip | dev_pip

    # Separate conda strings and the pip dict from the pinned dependencies
    pinned_conda_strings: list[str] = []
    pinned_pip_strings: list[str] = []
    for dep in pinned["dependencies"]:
        if isinstance(dep, dict) and "pip" in dep:
            pinned_pip_strings = dep["pip"]
        elif isinstance(dep, str):
            pinned_conda_strings.append(dep)

    kept_conda = _filter_deps(pinned_conda_strings, all_unpinned_conda)
    kept_pip = _filter_deps(pinned_pip_strings, all_unpinned_pip)

    pruned_dependencies: list = [*kept_conda]
    if kept_pip:
        pruned_dependencies.append({"pip": kept_pip})

    pinned["dependencies"] = pruned_dependencies
    pinned.pop("prefix", None)

    pinned_path = _resolve_paths()[0]
    with open(pinned_path, "w", encoding="utf-8") as f:
        yaml.dump(pinned, f)

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage pinned/unpinned environment files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Validate pins match unpinned sources")
    sub.add_parser("prune", help="Prune environment.yaml to explicit deps")
    args = parser.parse_args()

    pinned, unpinned, unpinned_dev = load_envs()

    if args.command == "check":
        return cmd_check(pinned, unpinned, unpinned_dev)
    elif args.command == "prune":
        return cmd_prune(pinned, unpinned, unpinned_dev)
    return 1


if __name__ == "__main__":
    sys.exit(main())
