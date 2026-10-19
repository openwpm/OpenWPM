"""Tests for scripts/per_commit_checks.py.

Git runs for real against a throwaway repository; the checks themselves are
replaced by a stand-in that passes or fails on demand.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.pyonly


@pytest.fixture(scope="module")
def gate_module():
    repo_root = Path(__file__).resolve().parent.parent
    script_path = repo_root / "scripts" / "per_commit_checks.py"
    spec = importlib.util.spec_from_file_location("per_commit_checks", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["per_commit_checks"] = module
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def commit(repo, message, files):
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path, monkeypatch, gate_module):
    # Keep an enclosing git invocation (e.g. a hook) from redirecting ours.
    for var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(var, raising=False)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "test")
    commit(tmp_path, "chore: base", {"environment.yaml": "a\n"})
    monkeypatch.setattr(gate_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gate_module, "EXTENSION_DIR", tmp_path / "Extension")
    monkeypatch.setattr(gate_module, "ENVIRONMENT_YAML", tmp_path / "environment.yaml")
    return tmp_path


class Checks:
    """Stands in for the real commands; records calls, fails on request."""

    def __init__(self, repo):
        self.repo = repo
        self.calls = []
        self.failing = set()
        self.messages = {}

    def __call__(self, real_run):
        checks = self

        def run(gate, commit, name, command, cwd=None, quiet=False):
            checks.calls.append((commit, name))
            if name == "commit message":
                edit_msg = checks.repo / ".git" / "COMMIT_EDITMSG"
                checks.messages[commit] = edit_msg.read_text()
            code = 1 if (commit, name) in checks.failing else 0
            return real_run(
                gate, commit, name, [sys.executable, "-c", f"raise SystemExit({code})"]
            )

        return run

    def names(self, commit):
        return [name for c, name in self.calls if c == commit]

    def visited(self):
        return list(dict.fromkeys(c for c, _ in self.calls))


@pytest.fixture
def checks(repo, gate_module, monkeypatch):
    checks = Checks(repo)
    monkeypatch.setattr(gate_module.Gate, "_run", checks(gate_module.Gate._run))
    return checks


def run_main(gate_module, monkeypatch, base, head):
    monkeypatch.setattr(
        sys, "argv", ["per_commit_checks", "--base", base, "--head", head]
    )
    return gate_module.main()


def test_every_commit_checked_and_all_failures_reported(
    gate_module, repo, checks, monkeypatch, capsys
):
    base = git(repo, "rev-parse", "HEAD")
    c1 = commit(repo, "fix: one", {"a.py": "1\n"})
    c2 = commit(repo, "fix: two", {"b.py": "2\n"})
    c3 = commit(repo, "fix: three", {"c.py": "3\n"})
    checks.failing = {(c1, "pre-commit"), (c3, "pytest collection")}

    assert run_main(gate_module, monkeypatch, base, c3) == 1

    assert checks.visited() == [c1, c2, c3]
    out = capsys.readouterr().out
    assert "::error::2 check(s) failed:" in out
    assert f"{c1[:12]}: pre-commit" in out
    assert f"{c3[:12]}: pytest collection" in out
    assert git(repo, "rev-parse", "HEAD") == c3


def test_passing_range_exits_zero(gate_module, repo, checks, monkeypatch, capsys):
    base = git(repo, "rev-parse", "HEAD")
    head = commit(repo, "fix: one", {"a.py": "1\n"})

    assert run_main(gate_module, monkeypatch, base, head) == 0
    assert "All checks passed on 1 commit(s)" in capsys.readouterr().out


def test_empty_range(gate_module, repo, checks, monkeypatch, capsys):
    head = git(repo, "rev-parse", "HEAD")

    assert run_main(gate_module, monkeypatch, head, head) == 0
    assert checks.calls == []
    assert "No commits in" in capsys.readouterr().out


def test_extension_checks_follow_what_the_commit_touched(
    gate_module, repo, checks, monkeypatch
):
    base = git(repo, "rev-parse", "HEAD")
    untouched = commit(repo, "fix: python", {"a.py": "1\n"})
    source = commit(repo, "fix: source", {"Extension/src/a.ts": "1\n"})
    lockfile = commit(repo, "fix: deps", {"Extension/package-lock.json": "{}\n"})

    run_main(gate_module, monkeypatch, base, lockfile)

    assert "extension build" not in checks.names(untouched)
    assert "npm ci" not in checks.names(source)
    assert "extension build" in checks.names(source)
    assert checks.names(lockfile).count("npm ci") == 1
    assert "extension build" in checks.names(lockfile)


def test_env_rebuilt_only_when_it_differs_from_the_last_build(
    gate_module, repo, checks, monkeypatch
):
    base = git(repo, "rev-parse", "HEAD")
    old_env = commit(repo, "fix: one", {"a.py": "1\n"})
    new_env = commit(repo, "build: bump", {"environment.yaml": "b\n"})
    head = commit(repo, "fix: two", {"b.py": "2\n"})

    run_main(gate_module, monkeypatch, base, head)

    # Built from the head's environment.yaml, so the first commit differs.
    assert "conda env rebuild" in checks.names(old_env)
    assert "conda env rebuild" in checks.names(new_env)
    assert "conda env rebuild" not in checks.names(head)


def test_failed_env_rebuild_ends_the_walk(
    gate_module, repo, checks, monkeypatch, capsys
):
    base = git(repo, "rev-parse", "HEAD")
    first = commit(repo, "fix: one", {"a.py": "1\n"})
    commit(repo, "build: bump", {"environment.yaml": "b\n"})
    head = commit(repo, "fix: two", {"b.py": "2\n"})
    checks.failing = {(first, "conda env rebuild")}

    assert run_main(gate_module, monkeypatch, base, head) == 1

    assert checks.visited() == [first]
    out = capsys.readouterr().out
    assert "skipping the remaining commits" in out
    assert f"{first[:12]}: conda env rebuild" in out
    assert git(repo, "rev-parse", "HEAD") == head


def test_commit_message_is_handed_to_the_hook(gate_module, repo, checks, monkeypatch):
    base = git(repo, "rev-parse", "HEAD")
    c1 = commit(repo, "fix: one", {"a.py": "1\n"})
    c2 = commit(repo, "not conventional", {"b.py": "2\n"})

    run_main(gate_module, monkeypatch, base, c2)

    assert checks.messages[c1].strip() == "fix: one"
    assert checks.messages[c2].strip() == "not conventional"


def test_dirty_tree_does_not_block_the_next_checkout(
    gate_module, repo, checks, monkeypatch
):
    base = git(repo, "rev-parse", "HEAD")
    c1 = commit(repo, "fix: one", {"a.py": "1\n"})
    c2 = commit(repo, "fix: two", {"a.py": "2\n"})
    real_run = gate_module.Gate._run

    def dirtying_run(gate, commit, name, command, cwd=None, quiet=False):
        if name == "pre-commit":
            (repo / "a.py").write_text("reformatted\n")
        return real_run(gate, commit, name, command, cwd, quiet)

    monkeypatch.setattr(gate_module.Gate, "_run", dirtying_run)

    assert run_main(gate_module, monkeypatch, base, c2) == 0
    assert checks.visited() == [c1, c2]


@pytest.fixture
def gate(repo, gate_module):
    return gate_module.Gate()


def test_run_passing_check(gate, capsys):
    assert gate._run("abc", "ok", [sys.executable, "-c", "pass"])
    assert gate.failures == []


def test_run_failing_check_is_recorded(gate, capsys):
    assert not gate._run("abc", "bad", [sys.executable, "-c", "raise SystemExit(3)"])
    assert gate.failures == ["abc: bad"]
    assert "::error::bad failed at abc" in capsys.readouterr().out


def test_run_missing_command_is_recorded_not_raised(gate):
    assert not gate._run("abc", "missing", ["definitely-not-a-real-command-xyz"])
    assert gate.failures == ["abc: missing"]


def test_run_quiet_prints_output_only_on_failure(gate, capsys):
    script = "import sys; print('noisy'); sys.exit({})"
    gate._run("abc", "q", [sys.executable, "-c", script.format(0)], quiet=True)
    assert "noisy" not in capsys.readouterr().out
    gate._run("abc", "q", [sys.executable, "-c", script.format(1)], quiet=True)
    assert "noisy" in capsys.readouterr().out


def test_range_from_arguments(gate_module):
    assert gate_module.resolve_range("a", "b") == ("a", "b")


@pytest.mark.parametrize("base, head", [("a", None), (None, "b")])
def test_range_needs_both_arguments(gate_module, base, head):
    with pytest.raises(SystemExit, match="together"):
        gate_module.resolve_range(base, head)


def test_range_outside_actions(gate_module, monkeypatch):
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    with pytest.raises(SystemExit, match="--base and --head"):
        gate_module.resolve_range(None, None)


@pytest.mark.parametrize(
    "event_name, payload",
    [
        ("merge_group", {"merge_group": {"base_sha": "b", "head_sha": "h"}}),
        (
            "pull_request",
            {"pull_request": {"base": {"sha": "b"}, "head": {"sha": "h"}}},
        ),
    ],
)
def test_range_from_event(gate_module, monkeypatch, tmp_path, event_name, payload):
    event = tmp_path / "event.json"
    event.write_text(json.dumps(payload))
    monkeypatch.setenv("GITHUB_EVENT_NAME", event_name)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    assert gate_module.resolve_range(None, None) == ("b", "h")


def test_range_rejects_other_events(gate_module, monkeypatch, tmp_path):
    event = tmp_path / "event.json"
    event.write_text("{}")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    with pytest.raises(SystemExit, match="Unsupported event: push"):
        gate_module.resolve_range(None, None)
