import atexit
import shutil
import subprocess
import tempfile
from os.path import dirname, join, realpath
from pathlib import Path

import click
import IPython
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options

from openwpm import js_instrumentation as jsi
from openwpm.config import BrowserParams
from openwpm.deploy_browsers import configure_firefox
from openwpm.utilities.platform_utils import get_firefox_binary_path

from .conftest import xpi
from .utilities import BASE_TEST_URL, start_server

# import commonly used modules and utilities so they can be easily accessed
# in the interactive session
from openwpm.commands.utils import webdriver_utils as wd_util  # noqa isort:skip
import domain_utils as du  # noqa isort:skip
from selenium.common.exceptions import *  # noqa isort:skip
from selenium.webdriver.common.keys import Keys  # noqa isort:skip

OPENWPM_LOG_PREFIX = "console.log: openwpm: "
INSERT_PREFIX = "Array"
BASE_DIR = dirname(dirname(realpath(__file__)))
EXT_PATH = join(BASE_DIR, "Extension", "firefox")


class Logger:
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
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def get_command_output(command, cwd=None):
    popen = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd
    )
    assert popen.stdout is not None
    return iter(popen.stdout.readline, b"")


def colorize(line):
    if INSERT_PREFIX in line:  # print long DB insert lines in blue
        line = line.replace(INSERT_PREFIX, bcolors.OKBLUE + INSERT_PREFIX)
    if OPENWPM_LOG_PREFIX in line:
        line = line.replace(OPENWPM_LOG_PREFIX, OPENWPM_LOG_PREFIX + bcolors.OKGREEN)
    return line


def start_webdriver(
    with_extension=True, load_browser_params=True, browser_params_file=None
):
    """Open a webdriver instance and a server for the test pages

    This is meant to be imported and run manually from a python or
    ipython shell. A webdriver instance is returned and both the webdriver
    and server will automatically clean up when the shell is exited.

    Parameters
    ----------
    with_extension : boolean
        Set to True to also load OpenWPM extension instrumentation
    load_browser_params : boolean
        Set to True to load browser_params
    browser_params_file : string
        Specify the browser_params.json to load.
        If None, default params from openwpm/config.py::BrowserParams will be loaded.

    Returns
    -------
    webdriver
        A selenium webdriver instance.
    """
    firefox_binary_path = get_firefox_binary_path()

    fb = FirefoxBinary(firefox_path=firefox_binary_path)
    server, thread = start_server()

    def register_cleanup(driver):
        driver.get(BASE_TEST_URL)

        def cleanup_server():
            print("Cleanup before shutdown...")
            server.shutdown()
            thread.join()
            print("...server shutdown")
            driver.quit()
            print("...webdriver closed")
            shutil.rmtree(driver.capabilities["moz:profile"], ignore_errors=True)
            print("...browser profile removed")

        atexit.register(cleanup_server)
        return driver

    browser_profile_path = Path(tempfile.mkdtemp(prefix="firefox_profile_"))
    fo = Options()
    fo.add_argument("-profile")
    fo.add_argument(str(browser_profile_path))

    if with_extension:
        # TODO: Restore preference for log level in a way that works in Fx 57+
        # fp.set_preference("extensions.@openwpm.sdk.console.logLevel", "all")
        configure_firefox.optimize_prefs(fo)

    driver = webdriver.Firefox(firefox_binary=fb, options=fo)
    if load_browser_params is True:
        # There's probably more we could do here
        # to set more preferences and better emulate
        # what happens in TaskManager. But this lets
        # us pass some basic things.

        browser_params = BrowserParams()
        if browser_params_file is not None:
            with open(browser_params_file, "r") as f:
                browser_params.from_json(f.read())
        js_request = browser_params.js_instrument_settings
        js_request_as_string = jsi.clean_js_instrumentation_settings(js_request)
        browser_params.js_instrument_settings = js_request_as_string

        with open(browser_profile_path / "browser_params.json", "w") as f:
            f.write(browser_params.to_json())

    if with_extension:
        # add openwpm extension to profile
        xpi()
        ext_xpi = join(EXT_PATH, "dist", "openwpm-1.0.zip")
        driver.install_addon(ext_xpi, temporary=True)

    return register_cleanup(driver)


def start_webext():
    firefox_binary_path = get_firefox_binary_path()
    cmd_webext_run = f"""
    npm start -- \
            --start-url '{BASE_TEST_URL}' \
            --firefox '{firefox_binary_path}'
    """
    server, thread = start_server()
    try:
        # http://stackoverflow.com/a/4417735/3104416
        for line in get_command_output(cmd_webext_run, cwd=EXT_PATH):
            print(colorize(line.decode("utf-8")), bcolors.ENDC, end=" ")
    except KeyboardInterrupt:
        print("Keyboard Interrupt detected, shutting down...")
    print("\nClosing server thread...")
    server.shutdown()
    thread.join()


@click.command()
@click.option(
    "--selenium",
    help="""
    Run a selenium webdriver instance, and drop into an IPython shell""",
    is_flag=True,
    default=False,
)
@click.option(
    "--no-extension",
    help="""
    Use this to prevent the openwpm webextension being loaded.
    Only applies if --selenium is being used.""",
    is_flag=True,
    default=False,
)
@click.option(
    "--browser-params",
    help="""Set flag to load browser_params.""",
    is_flag=True,
    default=False,
)
@click.option(
    "--browser-params-file",
    help="""
    Specify a browser_params.json file. If none provided and
    --browser-params is enabled the default params from
    openwpm/config.py::BrowserParams will be loaded. Pass an
    absolute path or a path relative to the test directory.""",
)
def main(selenium, no_extension, browser_params, browser_params_file):

    if selenium:
        driver = start_webdriver(  # noqa
            with_extension=not no_extension,
            load_browser_params=browser_params,
            browser_params_file=browser_params_file,
        )
        print(
            "\nDropping into ipython shell....\n"
            "  * Interact with the webdriver instance using `driver`\n"
            "  * The webdriver and server will close automatically\n"
            "  * Use `exit` to quit the ipython shell\n"
        )
        logger = Logger()  # noqa
        IPython.embed()
    else:
        start_webext()


if __name__ == "__main__":
    main()  # type: ignore
