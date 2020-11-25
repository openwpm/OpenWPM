import logging
import os
import subprocess
from pathlib import Path
from typing import Callable, List, Tuple

import pytest

from openwpm import task_manager
from openwpm.commands import browser_commands
from openwpm.storage.sql_provider import SqlLiteStorageProvider
from openwpm.task_manager import TaskManager
from openwpm.types import BrowserParams, ManagerParams

from . import utilities

EXTENSION_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "openwpm",
    "Extension",
    "firefox",
)


@pytest.fixture(scope="session")
def xpi():
    # Creates a new xpi using npm run build.
    print("Building new xpi")
    subprocess.check_call(["npm", "run", "build"], cwd=EXTENSION_DIR)


@pytest.fixture(scope="session")
def server(request):
    """Run an HTTP server during the tests."""
    print("Starting local_http_server")
    server, server_thread = utilities.start_server()
    yield
    print("\nClosing server thread...")
    server.shutdown()
    server_thread.join()


@pytest.fixture()
def default_params(
    tmp_path: Path, num_browsers: int = 1
) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Just a simple wrapper around task_manager.load_default_params"""
    data_dir = str(tmp_path)
    manager_params, browser_params = task_manager.load_default_params(num_browsers)
    manager_params["data_directory"] = data_dir
    manager_params["log_directory"] = data_dir
    for i in range(num_browsers):
        browser_params[i]["display_mode"] = "headless"
    manager_params["db"] = str(tmp_path / manager_params["database_name"])
    return manager_params, browser_params


@pytest.fixture()
def task_manager_creator(
    server, xpi
) -> Callable[[Tuple[ManagerParams, List[BrowserParams]]], TaskManager]:
    """We create a callable that returns a TaskManager that has
    been configured with the Manager and BrowserParams"""

    def _create_task_manager(
        params: Tuple[ManagerParams, List[BrowserParams]]
    ) -> TaskManager:
        manager_params, browser_params = params
        structured_provider = SqlLiteStorageProvider(manager_params["db"])
        manager = task_manager.TaskManager(
            manager_params,
            browser_params,
            structured_provider,
            None,
            # logger_kwargs={"log_level_console": logging.DEBUG},
        )
        return manager

    return _create_task_manager
