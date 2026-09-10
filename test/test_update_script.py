"""Unit tests for scripts/update.py linter-sync helpers.

These tests do not invoke conda — the subprocess call is patched so the
parsing logic and pre-commit-config rewriting can be exercised in isolation.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.pyonly


@pytest.fixture(scope="module")
def update_module():
    """Load scripts/update.py as a module without making scripts/ a package."""
    repo_root = Path(__file__).resolve().parent.parent
    script_path = repo_root / "scripts" / "update.py"
    spec = importlib.util.spec_from_file_location("scripts_update", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["scripts_update"] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_CONDA_LIST = json.dumps(
    [
        {
            "name": "black",
            "version": "26.1.0",
            "channel": "conda-forge",
            "build_string": "pyh866005b_0",
        },
        {
            "name": "isort",
            "version": "8.0.1",
            "channel": "conda-forge",
            "build_string": "pyhd8ed1ab_0",
        },
        {
            "name": "mypy",
            "version": "1.19.1",
            "channel": "conda-forge",
            "build_string": "py314h5bd0f2a_0",
        },
        {
            "name": "pytest",
            "version": "9.0.2",
            "channel": "conda-forge",
            "build_string": "pyhd8ed1ab_0",
        },
    ]
)


# mypy is absent on purpose: it is a `language: system` hook, so it carries no
# rev for sync_precommit_linter_versions to rewrite.
PRECOMMIT_YAML_TEMPLATE = """\
repos:
  - repo: https://github.com/timothycrosley/isort
    rev: {isort_rev}
    hooks:
      - id: isort
  - repo: https://github.com/psf/black
    rev: {black_rev}
    hooks:
      - id: black
        language_version: python3
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: mypy
        language: system
"""


def test_versions_from_conda_list_json_returns_all_versions(update_module):
    versions = update_module._versions_from_conda_list_json(SAMPLE_CONDA_LIST)
    assert versions["black"] == "26.1.0"
    assert versions["isort"] == "8.0.1"
    assert versions["mypy"] == "1.19.1"
    assert versions["pytest"] == "9.0.2"


def test_versions_from_conda_list_json_invalid_json_raises(update_module):
    with pytest.raises(json.JSONDecodeError):
        update_module._versions_from_conda_list_json("not valid json")


def test_sync_updates_outdated_revs(update_module, tmp_path, monkeypatch, capsys):
    precommit = tmp_path / ".pre-commit-config.yaml"
    precommit.write_text(
        PRECOMMIT_YAML_TEMPLATE.format(isort_rev="1.0.0", black_rev="20.0.0")
    )
    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    monkeypatch.setattr(
        update_module,
        "_query_conda_versions",
        lambda env_name="openwpm": {
            "black": "26.1.0",
            "isort": "8.0.1",
            "mypy": "1.19.1",
        },
    )

    update_module.sync_precommit_linter_versions()

    new_content = precommit.read_text()
    assert "rev: 26.1.0" in new_content
    assert "rev: 8.0.1" in new_content
    assert "20.0.0" not in new_content
    assert "1.0.0" not in new_content


def test_sync_noop_when_versions_match(update_module, tmp_path, monkeypatch):
    initial = PRECOMMIT_YAML_TEMPLATE.format(isort_rev="8.0.1", black_rev="26.1.0")
    precommit = tmp_path / ".pre-commit-config.yaml"
    precommit.write_text(initial)
    mtime_before = precommit.stat().st_mtime_ns

    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    monkeypatch.setattr(
        update_module,
        "_query_conda_versions",
        lambda env_name="openwpm": {
            "black": "26.1.0",
            "isort": "8.0.1",
            "mypy": "1.19.1",
        },
    )

    update_module.sync_precommit_linter_versions()

    assert precommit.read_text() == initial
    # File should not have been rewritten when nothing changed.
    assert precommit.stat().st_mtime_ns == mtime_before


def test_sync_raises_when_linter_missing_from_env(update_module, tmp_path, monkeypatch):
    precommit = tmp_path / ".pre-commit-config.yaml"
    precommit.write_text(
        PRECOMMIT_YAML_TEMPLATE.format(isort_rev="8.0.1", black_rev="26.1.0")
    )
    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    monkeypatch.setattr(
        update_module,
        "_query_conda_versions",
        # isort intentionally missing
        lambda env_name="openwpm": {"black": "26.1.0", "mypy": "1.19.1"},
    )

    with pytest.raises(RuntimeError, match="isort"):
        update_module.sync_precommit_linter_versions()


def test_sync_raises_when_hook_missing_from_precommit_config(
    update_module, tmp_path, monkeypatch
):
    # File is missing the isort hook entirely.
    precommit = tmp_path / ".pre-commit-config.yaml"
    precommit.write_text("""\
repos:
  - repo: https://github.com/psf/black
    rev: 26.1.0
    hooks:
      - id: black
""")
    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    monkeypatch.setattr(
        update_module,
        "_query_conda_versions",
        lambda env_name="openwpm": {
            "black": "26.1.0",
            "isort": "8.0.1",
            "mypy": "1.19.1",
        },
    )

    with pytest.raises(RuntimeError, match="isort"):
        update_module.sync_precommit_linter_versions()


def test_mypy_is_not_rev_synced(update_module):
    """mypy runs as a `language: system` hook, so it has no rev to sync.

    Putting it back in _LINTER_MAP would make sync_precommit_linter_versions
    raise on the next repin, since the local hook carries no `rev:` line.
    """
    assert "mypy" not in update_module._LINTER_MAP


PYPROJECT_TEMPLATE = """\
[tool.black]
line-length = 88

[tool.mypy]
follow_imports = "silent"
python_version = "{python_version}"
warn_unused_configs = true

[[tool.mypy.overrides]]
module = "test.*"
python_version = "1.0"

[tool.coverage.run]
parallel = true
"""


def _patch_conda_python(update_module, monkeypatch, version):
    monkeypatch.setattr(
        update_module,
        "_query_conda_versions",
        lambda env_name="openwpm": {"python": version},
    )


def test_sync_mypy_python_version_updates_stale_setting(
    update_module, tmp_path, monkeypatch
):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(PYPROJECT_TEMPLATE.format(python_version="3.10"))
    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    _patch_conda_python(update_module, monkeypatch, "3.14.7")

    update_module.sync_mypy_python_version()

    new_content = pyproject.read_text()
    # The feature level, not the patch release.
    assert 'python_version = "3.14"' in new_content
    assert '"3.10"' not in new_content
    # A python_version in a later table is left alone -- only [tool.mypy] itself
    # is rewritten.
    assert 'python_version = "1.0"' in new_content


def test_sync_mypy_python_version_noop_when_in_sync(
    update_module, tmp_path, monkeypatch
):
    initial = PYPROJECT_TEMPLATE.format(python_version="3.14")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(initial)
    mtime_before = pyproject.stat().st_mtime_ns

    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    _patch_conda_python(update_module, monkeypatch, "3.14.7")

    update_module.sync_mypy_python_version()

    assert pyproject.read_text() == initial
    # File should not have been rewritten when nothing changed.
    assert pyproject.stat().st_mtime_ns == mtime_before


def test_sync_mypy_python_version_raises_when_python_missing_from_env(
    update_module, tmp_path, monkeypatch
):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(PYPROJECT_TEMPLATE.format(python_version="3.10"))
    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    monkeypatch.setattr(
        update_module,
        "_query_conda_versions",
        lambda env_name="openwpm": {"mypy": "1.19.1"},
    )

    with pytest.raises(RuntimeError, match="python not found"):
        update_module.sync_mypy_python_version()


def test_sync_mypy_python_version_raises_when_section_missing(
    update_module, tmp_path, monkeypatch
):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.black]\nline-length = 88\n")
    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    _patch_conda_python(update_module, monkeypatch, "3.14.7")

    with pytest.raises(RuntimeError, match=r"\[tool\.mypy\]"):
        update_module.sync_mypy_python_version()


def test_sync_mypy_python_version_raises_when_setting_missing(
    update_module, tmp_path, monkeypatch
):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.mypy]\nwarn_unused_configs = true\n")
    monkeypatch.setattr(update_module, "ROOT", tmp_path)
    _patch_conda_python(update_module, monkeypatch, "3.14.7")

    with pytest.raises(RuntimeError, match="python_version"):
        update_module.sync_mypy_python_version()


def test_query_conda_versions_raises_when_conda_missing(update_module, monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("conda")

    monkeypatch.setattr(update_module.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="conda not found"):
        update_module._query_conda_versions()


def test_query_conda_versions_raises_when_env_missing(update_module, monkeypatch):
    class FakeResult:
        returncode = 1
        stdout = ""
        stderr = "EnvironmentLocationNotFound: Not a conda environment"

    monkeypatch.setattr(update_module.subprocess, "run", lambda *a, **kw: FakeResult())

    with pytest.raises(RuntimeError, match="install.sh"):
        update_module._query_conda_versions("nonexistent-env")


def test_query_conda_versions_parses_subprocess_output(update_module, monkeypatch):
    class FakeResult:
        returncode = 0
        stdout = SAMPLE_CONDA_LIST
        stderr = ""

    captured_args = {}

    def fake_run(args, **kwargs):
        captured_args["args"] = args
        return FakeResult()

    monkeypatch.setattr(update_module.subprocess, "run", fake_run)

    versions = update_module._query_conda_versions("openwpm")
    assert versions["black"] == "26.1.0"
    assert captured_args["args"] == [
        "conda",
        "list",
        "-n",
        "openwpm",
        "--json",
    ]
