from os.path import isfile, join

import pytest

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.errors import CommandExecutionError, ProfileLoadError
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils

from .openwpmtest import OpenWPMTest

# TODO update these tests to make use of blocking commands


class TestProfile(OpenWPMTest):
    def get_config(self, data_dir=""):
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
    def test_crash(self):
        manager_params, browser_params = self.get_config()
        manager_params.failure_limit = 0
        manager = TaskManager(manager_params, browser_params)
        with pytest.raises(CommandExecutionError):
            manager.get("http://example.com")  # So we have a profile
            manager.get("example.com")  # Selenium requires scheme prefix
            manager.get("example.com")  # Requires two commands to shut down

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
        manager.get("example.com")  # Cause a selenium crasht

        # The browser will fail to launch due to the proxy crashes
        try:
            manager.get("http://example.com")
        except CommandExecutionError:
            pass
        manager.close()
        assert isfile(join(browser_params[0].profile_archive_dir, "profile.tar.gz"))

    def test_seed_persistance(self):
        manager_params, browser_params = self.get_test_config(num_browsers=1)
        browser_params[0].seed_tar = "."
        command_sequences = []
        for _ in range(2):
            cs = CommandSequence(url="https://example.com", reset=True)
            cs.get()
            cs.append_command(TestConfigSetCommand("test_pref", True))
            command_sequences.append(cs)
        manager = TaskManager(manager_params, browser_params)
        for cs in command_sequences:
            manager.execute_command_sequence(cs)
        manager.close()
        query_result = db_utils.query_db(
            manager_params.database_name,
            "SELECT * FROM crawl_history;",
        )
        assert len(query_result) > 0
        for row in query_result:
            assert row["command_status"] == "ok", f"Command {tuple(row)} was not ok"


class TestConfigSetCommand(BaseCommand):
    def __init__(self, pref_name, expected_value) -> None:
        self.pref_name = pref_name
        self.expected_value = expected_value

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ) -> None:
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
