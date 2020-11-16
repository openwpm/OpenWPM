import os
import subprocess
from typing import List, Tuple

import pytest

from openwpm import TaskManager
from openwpm.types import BrowserParams, ManagerParams

from . import utilities

EXTENSION_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "openwpm",
    "Extension",
    "firefox",
)


def create_xpi():
    # Creates a new xpi using npm run build.
    print("Building new xpi")
    subprocess.check_call(["npm", "run", "build"], cwd=EXTENSION_DIR)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_setup(request):
    """Run an HTTP server during the tests."""

    if "pyonly" in request.config.invocation_params.args:
        return

    create_xpi()

    print("Starting local_http_server")
    server, server_thread = utilities.start_server()
    yield
    print("\nClosing server thread...")
    server.shutdown()
    server_thread.join()


@pytest.fixture()
def default_params(num_browsers, tmpdir) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Just a simple wrapper around TaskManager.load_default_params"""
    data_dir = tmpdir
    manager_params, browser_params = TaskManager.load_default_params(num_browsers)
    manager_params["data_directory"] = data_dir
    manager_params["log_directory"] = data_dir
    for i in range(num_browsers):
        browser_params[i]["display_mode"] = "headless"
    manager_params["db"] = os.sep.join(
        [manager_params["data_directory"], manager_params["database_name"]]
    )
    return manager_params, browser_params
