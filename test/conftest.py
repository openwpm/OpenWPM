import logging
import os
import subprocess
from pathlib import Path
from typing import Callable, List, Tuple

import pytest

from openwpm import task_manager
from openwpm.mp_logger import MPLogger
from openwpm.storage.sql_provider import SqlLiteStorageProvider
from openwpm.task_manager import TaskManager
from openwpm.types import BrowserParams, ManagerParams

from . import utilities
from .openwpmtest import NUM_BROWSERS

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
    tmp_path: Path, num_browsers: int = NUM_BROWSERS
) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Just a simple wrapper around task_manager.load_default_params"""
    assert len(tmp_path.iterdir()) == 0
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
        )
        return manager

    return _create_task_manager


@pytest.fixture()
def http_params(
    default_params,
) -> Callable[[str], Tuple[ManagerParams, List[BrowserParams]]]:
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param["http_instrument"] = True

    def parameterize(
        display_mode: str = "headless",
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        for browser_param in browser_params:
            browser_param["display_mode"] = display_mode
        return manager_params, browser_params

    return parameterize


@pytest.fixture()
def mp_logger(tmp_path):
    logger = MPLogger(tmp_path / "openwpm.log")
    yield logger
    logger.close()
