
import os
import subprocess

import pytest

from . import utilities

EXTENSION_DIR = os.path.join(
    os.path.dirname(
        os.path.realpath(__file__)),
    '..',
    'automation',
    'Extension',
    'firefox')


def create_xpi():
    """Creates a new xpi using npm run build."""
    if utilities.which("npm"):
        subprocess.check_call(["npm", "run", "build"],
                              cwd=EXTENSION_DIR)
    else:
        assert os.path.exists(os.path.join(EXTENSION_DIR, 'openwpm.xpi'))


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
