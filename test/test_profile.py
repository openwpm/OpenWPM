from pathlib import Path
from typing import Any

import pytest

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.errors import CommandExecutionError, ProfileLoadError
from openwpm.utilities import db_utils

from .utilities import BASE_TEST_URL

# TODO update these tests to make use of blocking commands


def test_saving(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    browser_params[0].profile_archive_dir = (
        manager_params.data_directory / "browser_profile"
    )
    manager, _ = task_manager_creator((manager_params, browser_params[:1]))
    manager.get(BASE_TEST_URL)
    manager.close()
    assert (browser_params[0].profile_archive_dir / "profile.tar.gz").is_file()


def test_crash_profile(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager_params.failure_limit = 2
    browser_params[0].profile_archive_dir = (
        manager_params.data_directory / "browser_profile"
    )
    manager, _ = task_manager_creator((manager_params, browser_params[:1]))
    try:
        manager.get(BASE_TEST_URL)  # So we have a profile
        manager.get("example.com")  # Selenium requires scheme prefix
        manager.get("example.com")  # Selenium requires scheme prefix
        manager.get("example.com")  # Selenium requires scheme prefix
        manager.get("example.com")  # Requires two commands to shut down
    except CommandExecutionError:
        pass
    assert (browser_params[0].profile_archive_dir / "profile.tar.gz").is_file()


def test_profile_error(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    browser_params[0].seed_tar = Path("/tmp/NOTREAL")
    with pytest.raises(ProfileLoadError):
        task_manager_creator((manager_params, browser_params[:1]))


def test_profile_saved_when_launch_crashes(
    monkeypatch, default_params, task_manager_creator
):
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    browser_params[0].profile_archive_dir = (
        manager_params.data_directory / "browser_profile"
    )
    manager, _ = task_manager_creator((manager_params, browser_params[:1]))
    manager.get(BASE_TEST_URL)

    # This will cause browser restarts to fail
    monkeypatch.setenv("FIREFOX_BINARY", "/tmp/NOTREAL")
    manager.browsers[0]._SPAWN_TIMEOUT = 2  # Have timeout occur quickly
    manager.browsers[0]._UNSUCCESSFUL_SPAWN_LIMIT = 2  # Quick timeout
    manager.get("example.com")  # Cause a selenium crash to force browser to restart

    try:
        manager.get(BASE_TEST_URL)
    except CommandExecutionError:
        pass
    manager.close()
    assert (browser_params[0].profile_archive_dir / "profile.tar.gz").is_file()


def test_seed_persistence(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    p = Path("profile.tar.gz")
    for browser_param in browser_params:
        browser_param.seed_tar = p
    manager, db = task_manager_creator(default_params)

    command_sequences = []
    for _ in range(2):
        cs = CommandSequence(url=BASE_TEST_URL)
        cs.get()
        cs.append_command(AssertConfigSetCommand("test_pref", True))
        command_sequences.append(cs)

    for cs in command_sequences:
        manager.execute_command_sequence(cs)
    manager.close()
    query_result = db_utils.query_db(
        db,
        "SELECT * FROM crawl_history;",
    )
    assert len(query_result) > 0
    for row in query_result:
        assert row["command_status"] == "ok", f"Command {tuple(row)} was not ok"


class AssertConfigSetCommand(BaseCommand):
    def __init__(self, pref_name: str, expected_value: Any) -> None:
        self.pref_name = pref_name
        self.expected_value = expected_value

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        webdriver.get("about:config")
        result = webdriver.execute_script(
            f"""
                var prefs = Components
                            .classes["@mozilla.org/preferences-service;1"]
                            .getService(Components.interfaces.nsIPrefBranch);
                try {{
                    return prefs.getBoolPref("{self.pref_name}")
                }} catch (e) {{
                    return false;
                }}
            """
        )
        assert result == self.expected_value
