from __future__ import absolute_import, print_function

import os
import subprocess

import pytest

from . import utilities

EXTENSION_DIR = os.path.join(
    os.path.dirname(__file__), "..", "automation", "Extension", "firefox"
)


def create_xpi():
    """Creates a new xpi using jpm."""
    if utilities.which("jpm"):
        subprocess.check_call(["jpm", "xpi"], cwd=EXTENSION_DIR)
    else:
        assert os.path.exists(os.path.join(EXTENSION_DIR, "openwpm.xpi"))


@pytest.fixture(scope="session", autouse=True)
def prepare_test_setup(request):
    """Run an HTTP server during the tests."""
    create_xpi()
    print("\nStarting local_http_server")
    server, server_thread = utilities.start_server()

    def local_http_server_stop():
        print("\nClosing server thread...")
        server.shutdown()
        server_thread.join()

    request.addfinalizer(local_http_server_stop)
