from utilities import BASE_TEST_URL, start_server
from conftest import create_xpi
from os.path import dirname, join, realpath
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver
import subprocess
import atexit

OPENWPM_LOG_PREFIX = "console.log: openwpm: "
INSERT_PREFIX = "Array"
BASE_DIR = dirname(dirname(realpath(__file__)))
EXT_PATH = join(BASE_DIR, 'automation', 'Extension', 'firefox')
FF_BIN_PATH = join(BASE_DIR, 'firefox-bin', 'firefox')


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
    fb = FirefoxBinary(FF_BIN_PATH)
    server, thread = start_server()

    def register_cleanup(driver):
        driver.get(BASE_TEST_URL)

        def cleanup_server():
            print "Cleanup before shutdown..."
            server.shutdown()
            thread.join()
            print "...sever shutdown"
            driver.quit()
            print "...webdriver closed"

        atexit.register(cleanup_server)
        return driver

    if not with_extension:
        return register_cleanup(webdriver.Firefox(firefox_binary=fb))

    # add openwpm extension to profile
    create_xpi()
    fp = webdriver.FirefoxProfile()
    ext_xpi = join(EXT_PATH, 'openwpm.xpi')
    fp.add_extension(extension=ext_xpi)
    fp.set_preference("extensions.@openwpm.sdk.console.logLevel", "all")

    return register_cleanup(
        webdriver.Firefox(firefox_binary=fb, firefox_profile=fp))


def start_jpm():
    cmd_jpm_run = "jpm run --binary-args 'url %s' -b %s" % (BASE_TEST_URL,
                                                            FF_BIN_PATH)
    server, thread = start_server()
    try:
        # http://stackoverflow.com/a/4417735/3104416
        for line in get_command_output(cmd_jpm_run, cwd=EXT_PATH):
            print colorize(line), bcolors.ENDC,
    except KeyboardInterrupt:
        print "Keyboard Interrupt detected, shutting down..."
    print "\nClosing server thread..."
    server.shutdown()
    thread.join()


if __name__ == '__main__':
    import IPython
    import sys

    # TODO use some real parameter handling library
    if len(sys.argv) == 1:
        start_jpm()
    elif len(sys.argv) >= 2 and sys.argv[1] == '--selenium':
        if len(sys.argv) == 3 and sys.argv[2] == '--no-extension':
            driver = start_webdriver(False)
        else:
            driver = start_webdriver(True)
        print "\nDropping into ipython shell...."
        print "  * Interact with the webdriver instance using `driver`"
        print "  * The webdriver and test page server will close automatically"
        print "  * Use `exit` to quit the ipython shell\n"
        IPython.embed()
    else:
        print ("Unrecognized arguments. Usage:\n"
               "python manual_test.py ('--selenium')? ('--no-extension')?")
