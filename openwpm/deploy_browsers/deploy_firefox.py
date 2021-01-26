import json
import logging
import os.path
from typing import Any, List, Optional

from easyprocess import EasyProcessError
from multiprocess import Queue
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

from ..commands.profile_commands import load_profile
from ..config import BrowserParams, ManagerParams
from ..utilities.platform_utils import get_firefox_binary_path
from . import configure_firefox
from .selenium_firefox import FirefoxBinary, FirefoxLogInterceptor, Options

DEFAULT_SCREEN_RES = (1366, 768)
logger = logging.getLogger("openwpm")


def deploy_firefox(
    status_queue: Queue,
    browser_params: List[BrowserParams],
    manager_params: ManagerParams,
    crash_recovery: bool,
) -> (webdriver.Firefox, str, Optional[Display]):
    """
    launches a firefox instance with parameters set by the input dictionary
    """
    firefox_binary_path = get_firefox_binary_path()

    root_dir = os.path.dirname(__file__)  # directory of this file

    fp = FirefoxProfile()
    browser_profile_path = fp.path + "/"
    status_queue.put(("STATUS", "Profile Created", browser_profile_path))

    # Use Options instead of FirefoxProfile to set preferences since the
    # Options method has no "frozen"/restricted options.
    # https://github.com/SeleniumHQ/selenium/issues/2106#issuecomment-320238039
    fo = Options()

    if browser_params.seed_tar and not crash_recovery:
        logger.info(
            "BROWSER %i: Loading initial browser profile from: %s"
            % (browser_params.browser_id, browser_params.seed_tar)
        )
        load_profile(
            browser_profile_path,
            manager_params,
            browser_params,
            browser_params.seed_tar,
        )
    elif browser_params.recovery_tar:
        logger.debug(
            "BROWSER %i: Loading recovered browser profile from: %s"
            % (browser_params.browser_id, browser_params.recovery_tar)
        )
        load_profile(
            browser_profile_path,
            manager_params,
            browser_params,
            browser_params.recovery_tar,
        )
    status_queue.put(("STATUS", "Profile Tar", None))

    display_mode = browser_params.display_mode
    display_pid = None
    display_port = None
    display = None
    if display_mode == "headless":
        fo.set_headless(True)
        fo.add_argument("--width={}".format(DEFAULT_SCREEN_RES[0]))
        fo.add_argument("--height={}".format(DEFAULT_SCREEN_RES[1]))
    if display_mode == "xvfb":
        try:
            display = Display(visible=0, size=DEFAULT_SCREEN_RES)
            display.start()
            display_pid, display_port = display.pid, display.display
        except EasyProcessError:
            raise RuntimeError(
                "Xvfb could not be started. \
                Please ensure it's on your path. \
                See www.X.org for full details. \
                Commonly solved on ubuntu with `sudo apt install xvfb`"
            )
    # Must do this for all display modes,
    # because status_queue is read off no matter what.
    status_queue.put(("STATUS", "Display", (display_pid, display_port)))

    if browser_params.extension_enabled:
        # Write config file
        extension_config = dict()
        extension_config.update(browser_params.to_dict())
        extension_config["logger_address"] = manager_params.logger_address
        extension_config["aggregator_address"] = manager_params.aggregator_address
        if manager_params.ldb_address:
            extension_config["leveldb_address"] = manager_params.ldb_address
        else:
            extension_config["leveldb_address"] = None
        extension_config["testing"] = manager_params.testing
        ext_config_file = browser_profile_path + "browser_params.json"
        with open(ext_config_file, "w") as f:
            json.dump(extension_config, f)
        logger.debug(
            "BROWSER %i: Saved extension config file to: %s"
            % (browser_params.browser_id, ext_config_file)
        )

        # TODO restore detailed logging
        # fo.set_preference("extensions.@openwpm.sdk.console.logLevel", "all")

    # Configure privacy settings
    configure_firefox.privacy(browser_params, fp, fo, root_dir, browser_profile_path)

    # Set various prefs to improve speed and eliminate traffic to Mozilla
    configure_firefox.optimize_prefs(fo)

    # Intercept logging at the Selenium level and redirect it to the
    # main logger.  This will also inform us where the real profile
    # directory is hiding.
    interceptor = FirefoxLogInterceptor(browser_params.browser_id, browser_profile_path)
    interceptor.start()

    # Set custom prefs. These are set after all of the default prefs to allow
    # our defaults to be overwritten.
    for name, value in browser_params.prefs.items():
        logger.info(
            "BROWSER %i: Setting custom preference: %s = %s"
            % (browser_params.browser_id, name, value)
        )
        fo.set_preference(name, value)

    # Launch the webdriver
    status_queue.put(("STATUS", "Launch Attempted", None))
    fb = FirefoxBinary(firefox_path=firefox_binary_path)
    driver = webdriver.Firefox(
        firefox_profile=fp,
        firefox_binary=fb,
        firefox_options=fo,
        log_path=interceptor.fifo,
    )

    # Add extension
    if browser_params.extension_enabled:

        # Install extension
        ext_loc = os.path.join(root_dir, "../Extension/firefox/openwpm.xpi")
        ext_loc = os.path.normpath(ext_loc)
        driver.install_addon(ext_loc, temporary=True)
        logger.debug(
            "BROWSER %i: OpenWPM Firefox extension loaded" % browser_params.browser_id
        )

    # set window size
    driver.set_window_size(*DEFAULT_SCREEN_RES)

    # Get browser process pid
    if hasattr(driver, "service") and hasattr(driver.service, "process"):
        pid = driver.service.process.pid
    elif hasattr(driver, "binary") and hasattr(driver.binary, "process"):
        pid = driver.binary.process.pid
    else:
        raise RuntimeError("Unable to identify Firefox process ID.")

    status_queue.put(("STATUS", "Browser Launched", int(pid)))

    return driver, driver.capabilities["moz:profile"], display
