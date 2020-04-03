
import atexit
import subprocess
from os.path import dirname, join, realpath

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from automation.DeployBrowsers import configure_firefox
from automation.utilities.platform_utils import (get_firefox_binary_path,
                                                 get_geckodriver_exec_path)

from .conftest import create_xpi
from .utilities import BASE_TEST_URL, start_server

# import commonly used modules and utilities so they can be easily accessed
# in the interactive session
from automation.Commands.utils import webdriver_utils as wd_util  # noqa isort:skip
from automation.utilities import domain_utils as du  # noqa isort:skip
from selenium.webdriver.common.keys import Keys  # noqa isort:skip
from selenium.common.exceptions import *  # noqa isort:skip

OPENWPM_LOG_PREFIX = "console.log: openwpm: "
INSERT_PREFIX = "Array"
BASE_DIR = dirname(dirname(realpath(__file__)))
EXT_PATH = join(BASE_DIR, 'automation', 'Extension', 'firefox')


class Logger():
    def __init__(self):
        return

    def info(self, message):
        print(message)

    def debug(self, message):
        print(message)

    def error(self, message):
        print(message)

    def critical(self, message):
        print(message)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_command_output(command, cwd=None):
    popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, cwd=cwd)
    return iter(popen.stdout.readline, b"")


def colorize(line):
    if INSERT_PREFIX in line:  # print long DB insert lines in blue
        line = line.replace(INSERT_PREFIX, bcolors.OKBLUE + INSERT_PREFIX)
    if OPENWPM_LOG_PREFIX in line:
        line = line.replace(OPENWPM_LOG_PREFIX,
                            OPENWPM_LOG_PREFIX + bcolors.OKGREEN)
    return line


def start_webdriver(with_extension=False):
    """ Open a webdriver instance and a server for the test pages

    This is meant to be imported and run manually from a python or
    ipython shell. A webdriver instance is returned and both the webdriver
    and server will automatically clean up when the shell is exited.

    Parameters
    ----------
    with_extension : boolean
        Set to True to also load OpenWPM extension instrumentation

    Returns
    -------
    webdriver
        A selenium webdriver instance.
    """
    firefox_binary_path = get_firefox_binary_path()
    geckodriver_executable_path = get_geckodriver_exec_path()

    fb = FirefoxBinary(firefox_path=firefox_binary_path)
    server, thread = start_server()

    def register_cleanup(driver):
        driver.get(BASE_TEST_URL)

        def cleanup_server():
            print("Cleanup before shutdown...")
            server.shutdown()
            thread.join()
            print("...sever shutdown")
            driver.quit()
            print("...webdriver closed")

        atexit.register(cleanup_server)
        return driver

    fp = webdriver.FirefoxProfile()
    if with_extension:
        # TODO: Restore preference for log level in a way that works in Fx 57+
        # fp.set_preference("extensions.@openwpm.sdk.console.logLevel", "all")
        configure_firefox.optimize_prefs(fp)
    driver = webdriver.Firefox(
        firefox_binary=fb, firefox_profile=fp,
        executable_path=geckodriver_executable_path
    )
    if with_extension:
        # add openwpm extension to profile
        create_xpi()
        ext_xpi = join(EXT_PATH, 'openwpm.xpi')
        driver.install_addon(ext_xpi, temporary=True)

    return register_cleanup(driver)


def start_webext():
    firefox_binary_path = get_firefox_binary_path()
    cmd_webext_run = "npm start -- --start-url '%s' --firefox '%s'" \
        % (BASE_TEST_URL, firefox_binary_path)
    server, thread = start_server()
    try:
        # http://stackoverflow.com/a/4417735/3104416
        for line in get_command_output(cmd_webext_run, cwd=EXT_PATH):
            print(colorize(line.decode("utf-8")), bcolors.ENDC, end=' ')
    except KeyboardInterrupt:
        print("Keyboard Interrupt detected, shutting down...")
    print("\nClosing server thread...")
    server.shutdown()
    thread.join()


def main():
    import IPython
    import sys

    # TODO use some real parameter handling library
    if len(sys.argv) == 1:
        start_webext()
    elif len(sys.argv) >= 2 and sys.argv[1] == '--selenium':
        if len(sys.argv) == 3 and sys.argv[2] == '--no-extension':
            driver = start_webdriver(False)
        else:
            driver = start_webdriver(True)  # noqa
        print("\nDropping into ipython shell....\n"
              "  * Interact with the webdriver instance using `driver`\n"
              "  * The webdriver and server will close automatically\n"
              "  * Use `exit` to quit the ipython shell\n")
        logger = Logger()  # noqa
        IPython.embed()
    else:
        print("Unrecognized arguments. Usage:\n"
              "python manual_test.py ('--selenium')? ('--no-extension')?")


if __name__ == '__main__':
    main()
