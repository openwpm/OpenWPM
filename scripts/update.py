"""Update all OpenWPM dependencies and check for a newer Firefox release.

Steps
-----
1. Repin the conda environment (scripts/repin.sh)
2. Update root npm dependencies
3. Update Extension npm dependencies
4. Rebuild the extension
5. Check hg.mozilla.org for a newer Firefox and update install-firefox.sh if found

Run from the project root:
    python scripts/update.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def run(*cmd: str, cwd: Path = ROOT) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.run(list(cmd), check=True, cwd=cwd)


def conda_run(*cmd: str, cwd: Path = ROOT) -> None:
    run("conda", "run", "-n", "openwpm", *cmd, cwd=cwd)


def main() -> None:
    # Repin the conda environment from unpinned sources
    run("./repin.sh", cwd=SCRIPTS)

    # Update npm dependencies (root package.json and Extension/package.json)
    conda_run("npm", "update", "--include=dev")
    conda_run("npm", "update", "--include=dev", cwd=ROOT / "Extension")

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
