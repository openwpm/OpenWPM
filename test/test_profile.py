import tarfile
import time
from pathlib import Path
from threading import Thread
from typing import Any

import pytest

from openwpm.command_sequence import CommandSequence
from openwpm.commands.profile_commands import load_profile
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParamsInternal
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
    tar_path = browser_params[0].profile_archive_dir / "profile.tar.gz"
    assert tar_path.is_file()
    # Test that the archived profile contains some basic items
    profile_items = [
        "cookies.sqlite",
        "places.sqlite",
        "webappsstore.sqlite",
        "prefs.js",
        "bookmarkbackups",
        "cache2",
        "storage",
    ]
    with tarfile.open(tar_path, "r:gz") as tar:
        archive_items = tar.getnames()
    for item in profile_items:
        assert item in archive_items


def test_save_incomplete_profile_error(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    browser_params[0].profile_archive_dir = (
        manager_params.data_directory / "browser_profile"
    )
    manager, _ = task_manager_creator((manager_params, browser_params[:1]))
    manager.get(BASE_TEST_URL)
    (manager.browsers[0].current_profile_path / "cookies.sqlite").unlink()
    with pytest.raises(RuntimeError) as error:
        manager.close()
    assert str(error.value) == "Profile dump not successful"


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


def test_dump_profile_command(default_params, task_manager_creator):
    """Test saving the browser profile using a command."""
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager, _ = task_manager_creator((manager_params, browser_params[:1]))
    cs = CommandSequence(url=BASE_TEST_URL)
    cs.get()
    tar_path = manager_params.data_directory / "profile.tar.gz"
    cs.dump_profile(tar_path, True)
    manager.execute_command_sequence(cs)
    manager.close()
    assert tar_path.is_file()


def test_load_tar_file(tmp_path):
    """Test that load_profile does not delete or modify the tar file."""
    tar_path = Path("profile.tar.gz")
    profile_path = tmp_path / "browser_profile"
    browser_params = BrowserParamsInternal(browser_id=1)
    modified_time_before_load = tar_path.stat().st_mtime
    load_profile(profile_path, browser_params, tar_path)
    assert modified_time_before_load == tar_path.stat().st_mtime


def test_crash_during_init(default_params, task_manager_creator):
    """Test that no profile is saved when Task Manager initialization crashes."""
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    browser_params[0].profile_archive_dir = (
        manager_params.data_directory / "browser_profile"
    )
    # This will cause the browser launch to fail
    browser_params[0].seed_tar = Path("/tmp/NOTREAL")
    with pytest.raises(ProfileLoadError):
        manager, _ = task_manager_creator((manager_params, browser_params[:1]))
    tar_path = browser_params[0].profile_archive_dir / "profile.tar.gz"
    assert not tar_path.is_file()


@pytest.mark.parametrize(
    "stateful,seed_tar",
    [(True, None), (True, Path("profile.tar.gz")), (False, Path("profile.tar.gz"))],
    ids=[
        "stateful-without_seed_tar",
        "stateful-with_seed_tar",
        "stateless-with_seed_tar",
    ],
)
@pytest.mark.parametrize(
    "testcase",
    ["on_normal_operation", "on_crash", "on_crash_during_launch", "on_timeout"],
)
# Use -k to run this test for a specific set of parameters. For example:
# pytest -vv test_profile.py::test_profile_recovery -k on_crash-stateful-with_seed_tar
def test_profile_recovery(
    monkeypatch, default_params, task_manager_creator, testcase, stateful, seed_tar
):
    """Test browser profile recovery in various scenarios."""
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    browser_params[0].seed_tar = seed_tar
    manager, db = task_manager_creator((manager_params, browser_params[:1]))
    manager.get(BASE_TEST_URL, reset=not stateful)

    if testcase == "normal_operation":
        pass
    elif testcase == "on_crash":
        # Cause a selenium crash to force browser to restart
        manager.get("example.com", reset=not stateful)
    elif testcase == "on_crash_during_launch":
        # Cause a selenium crash to force browser to restart
        manager.get("example.com", reset=not stateful)
        # This will cause browser restarts to fail
        monkeypatch.setenv("FIREFOX_BINARY", "/tmp/NOTREAL")
        # Let the launch succeed after some failed launch attempts
        def undo_monkeypatch():
            time.sleep(5)  # This should be smaller than _SPAWN_TIMEOUT
            monkeypatch.undo()

        Thread(target=undo_monkeypatch).start()
    elif testcase == "on_timeout":
        # Set a very low timeout to cause a restart
        manager.get("about:config", reset=not stateful, timeout=0.1)

    cs = CommandSequence("about:config", reset=not stateful)
    expected_value = True if seed_tar else False
    cs.append_command(AssertConfigSetCommand("test_pref", expected_value))
    tar_directory = manager_params.data_directory / "browser_profile"
    tar_path = tar_directory / "profile.tar.gz"
    cs.dump_profile(tar_path, True)
    manager.execute_command_sequence(cs)
    manager.close()

    # Check that a consistent profile is used for stateful crawls but
    # not for stateless crawls
    with tarfile.open(tar_path) as tar:
        tar.extractall(tar_directory)
    ff_db = tar_directory / "places.sqlite"
    rows = db_utils.query_db(ff_db, "SELECT url FROM moz_places")
    places = [url for (url,) in rows]
    if stateful:
        assert BASE_TEST_URL in places
    else:
        assert BASE_TEST_URL not in places

    # Check if seed_tar was loaded on restart
    rows = db_utils.query_db(
        db,
        "SELECT command_status FROM crawl_history WHERE"
        " command='AssertConfigSetCommand'",
    )
    assert rows[0][0] == "ok"
