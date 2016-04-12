import pytest
import utilities
import commands


def create_xpi():
    """Creates a new xpi using jpm."""
    cmd_cd = "cd ../automation/Extension/firefox/"
    cmd_jpm = "jpm xpi"
    print commands.getstatusoutput("%s && %s" % (cmd_cd, cmd_jpm))


@pytest.fixture(scope="session", autouse=True)
def prepare_test_setup(request):
    """Run an HTTP server during the tests."""
    create_xpi()
    print "\nStarting local_http_server"
    server, server_thread = utilities.start_server()

    def local_http_server_stop():
        print "\nClosing server thread..."
        server.shutdown()
        server_thread.join()

    request.addfinalizer(local_http_server_stop)
