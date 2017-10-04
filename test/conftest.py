from __future__ import absolute_import
from __future__ import print_function

import os
import pytest
import subprocess

from . import utilities

def create_xpi():
    """Creates a new xpi using jpm."""
    if utilities.which("jpm"):
        subprocess.check_call(["jpm", "xpi"],
                              cwd="../automation/Extension/firefox/")
    else:
        assert os.path.exists("../automation/Extension/firefox/openwpm.xpi")


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
