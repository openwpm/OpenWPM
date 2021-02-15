from os.path import isfile, join
from pathlib import Path
from typing import Any, List, Optional, Tuple

import pytest

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.errors import CommandExecutionError, ProfileLoadError
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils

from .openwpmtest import OpenWPMTest

# TODO update these tests to make use of blocking commands


class TestProfile(OpenWPMTest):
    def get_config(
        self, data_dir: Optional[Path]
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0].profile_archive_dir = join(
            manager_params.data_directory, "browser_profile"
        )
        return manager_params, browser_params

    @pytest.mark.xfail(run=False)
    def test_saving(self):
        manager_params, browser_params = self.get_config()
        manager = TaskManager(manager_params, browser_params)
        manager.get("http://example.com")
        manager.close()
        assert isfile(join(browser_params[0].profile_archive_dir, "profile.tar.gz"))

    @pytest.mark.xfail(run=False)
    def test_crash_profile(self):
        manager_params, browser_params = self.get_config()
        manager_params.failure_limit = 2
        manager = TaskManager(manager_params, browser_params)
        try:
            manager.get("http://example.com")  # So we have a profile
            manager.get("example.com")  # Selenium requires scheme prefix
            manager.get("example.com")  # Selenium requires scheme prefix
            manager.get("example.com")  # Selenium requires scheme prefix
            manager.get("example.com")  # Requires two commands to shut down
        except CommandExecutionError:
            pass
        assert isfile(join(browser_params[0].profile_archive_dir, "profile.tar.gz"))

    @pytest.mark.xfail(run=False)
    def test_profile_error(self):
        manager_params, browser_params = self.get_config()
        browser_params[0].seed_tar = "/tmp/NOTREAL"
        with pytest.raises(ProfileLoadError):
            TaskManager(manager_params, browser_params)  # noqa

    @pytest.mark.skip(reason="proxy no longer supported, need to update")
    def test_profile_saved_when_launch_crashes(self):
        manager_params, browser_params = self.get_config()
        browser_params[0].proxy = True
        browser_params[0].save_content = "script"
        manager = TaskManager(manager_params, browser_params)
        manager.get("http://example.com")

        # Kill the LevelDBAggregator
        # This will cause the proxy launch to crash
        manager.ldb_status_queue.put("DIE")
        manager.browsers[0]._SPAWN_TIMEOUT = 2  # Have timeout occur quickly
        manager.browsers[0]._UNSUCCESSFUL_SPAWN_LIMIT = 2  # Quick timeout
        manager.get("example.com")  # Cause a selenium crash

        # The browser will fail to launch due to the proxy crashes
        try:
            manager.get("http://example.com")
        except CommandExecutionError:
            pass
        manager.close()
        assert isfile(join(browser_params[0].profile_archive_dir, "profile.tar.gz"))


def test_seed_persistance(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    p = Path("profile.tar.gz")
    for browser_param in browser_params:
        browser_param.seed_tar = p
    manager, db = task_manager_creator(default_params)

    command_sequences = []
    for _ in range(2):
        cs = CommandSequence(url="https://example.com", reset=True)
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
