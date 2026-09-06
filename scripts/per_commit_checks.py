"""Run the fast static checks on every commit in a range.

Rebase-and-merge lands every PR commit on master individually, but CI only
tests the tip, so a commit that is broken on its own can still ship. This walks
the range and runs the cheap checks on each commit. It does not run the browser
suite.

Each commit is checked out into the working tree and the head commit restored
at the end, so run it on a clean tree:

    python scripts/per_commit_checks.py --base master --head HEAD

In CI the range comes from the GitHub event payload instead.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTENSION_DIR = REPO_ROOT / "Extension"
ENVIRONMENT_YAML = REPO_ROOT / "environment.yaml"


def log(message: str) -> None:
    print(message, flush=True)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    # stderr is left alone so git's own complaints reach the job log.
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=check, stdout=subprocess.PIPE, text=True
    )


def touched(commit: str, *paths: str) -> bool:
    diff = git("diff", "--quiet", f"{commit}~1", commit, "--", *paths, check=False)
    return diff.returncode != 0


def checkout(commit: str) -> None:
    # --force: pre-commit's black and isort rewrite files and dirty the tree.
    git("checkout", "--force", "-q", commit)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GateAborted(RuntimeError):
    """The walk cannot meaningfully continue."""


class Gate:
    def __init__(self) -> None:
        # The env was built from the tip's environment.yaml; only rebuild when
        # a commit actually changes it.
        self.env_hash = sha256(ENVIRONMENT_YAML)
        self.failures: list[str] = []
        self.checked = 0

    def report(self) -> None:
        if self.failures:
            log(f"::error::{len(self.failures)} check(s) failed:")
            for failure in self.failures:
                log(f"  {failure}")
        else:
            log(f"All checks passed on {self.checked} commit(s)")

    def check(self, commit: str) -> None:
        self.checked += 1
        log(f"::group::{git('log', '-1', '--format=%h %s', commit).stdout.strip()}")
        try:
            checkout(commit)
            self._check_environment(commit)
            # --all-files, not this commit's diff: every commit has to leave
            # the whole tree clean, and this way it does not depend on
            # pre-commit's change selection.
            self._run(commit, "pre-commit", ["pre-commit", "run", "--all-files"])
            self._check_commit_message(commit)
            self._check_extension(commit)
            # Import-time breakage that mypy's per-file view misses.
            self._run(
                commit, "import openwpm", [sys.executable, "-c", "import openwpm"]
            )
            self._run(
                commit,
                "pytest collection",
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                quiet=True,
            )
        finally:
            log("::endgroup::")

    def _check_environment(self, commit: str) -> None:
        commit_env_hash = sha256(ENVIRONMENT_YAML)
        if commit_env_hash == self.env_hash:
            return
        # install.sh deletes the env before re-creating it, so a failed rebuild
        # leaves nothing to check the rest of the range against.
        if not self._run(commit, "conda env rebuild", [str(REPO_ROOT / "install.sh")]):
            raise GateAborted(f"conda env rebuild failed at {commit}")
        self.env_hash = commit_env_hash

    def _check_commit_message(self, commit: str) -> None:
        # `run --all-files` only runs pre-commit-stage hooks, so nothing else
        # checks the message. The commitlint hook is pass_filenames: false and
        # its entry is `commitlint --edit`, which reads COMMIT_EDITMSG.
        git_dir = REPO_ROOT / git("rev-parse", "--git-dir").stdout.strip()
        message = git_dir / "COMMIT_EDITMSG"
        message.write_text(git("log", "-1", "--format=%B", commit).stdout)
        self._run(
            commit,
            "commit message",
            [
                "pre-commit",
                "run",
                "--hook-stage",
                "commit-msg",
                "--commit-msg-filename",
                str(message),
            ],
        )

    def _check_extension(self, commit: str) -> None:
        if not touched(commit, "Extension/"):
            return
        # node_modules came from the tip's lockfile; refresh it if this commit
        # moved it.
        if touched(commit, "Extension/package.json", "Extension/package-lock.json"):
            self._run(commit, "npm ci", ["npm", "ci"], cwd=EXTENSION_DIR)
        self._run(commit, "extension build", ["npm", "run", "build"], cwd=EXTENSION_DIR)

    def _run(
        self,
        commit: str,
        name: str,
        command: list[str],
        cwd: Path = REPO_ROOT,
        quiet: bool = False,
    ) -> bool:
        """Run one check, recording rather than raising on failure."""
        try:
            result = subprocess.run(command, cwd=cwd, capture_output=quiet, text=True)
        except OSError as error:
            # Missing command at this commit: the commit's failure, not ours.
            log(str(error))
        else:
            if result.returncode == 0:
                return True
            if quiet:
                print(result.stdout, result.stderr, flush=True)
        log(f"::error::{name} failed at {commit}")
        self.failures.append(f"{commit[:12]}: {name}")
        return False


def resolve_range(base: str | None, head: str | None) -> tuple[str, str]:
    if base or head:
        if not (base and head):
            raise SystemExit("--base and --head must be given together")
        return base, head
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise SystemExit("Not running on GitHub Actions: pass --base and --head")
    event = json.loads(Path(event_path).read_text())
    if event_name == "merge_group":
        group = event["merge_group"]
        return group["base_sha"], group["head_sha"]
    if event_name == "pull_request":
        # The PR's own commits, not the synthetic merge commit.
        pull_request = event["pull_request"]
        return pull_request["base"]["sha"], pull_request["head"]["sha"]
    raise SystemExit(f"Unsupported event: {event_name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="commit before the first one to check")
    parser.add_argument("--head", help="last commit to check")
    args = parser.parse_args()

    base, head = resolve_range(args.base, args.head)
    commits = git("rev-list", "--reverse", f"{base}..{head}").stdout.split()
    if not commits:
        log(f"No commits in {base}..{head}")
        return 0

    gate = Gate()
    try:
        for commit in commits:
            gate.check(commit)
    except GateAborted as aborted:
        log(f"::error::{aborted}: skipping the remaining commits")
    finally:
        gate.report()
        checkout(head)
    return 1 if gate.failures else 0


if __name__ == "__main__":
    sys.exit(main())
