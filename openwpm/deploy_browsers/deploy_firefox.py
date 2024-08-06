import json
import logging
import os.path
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from easyprocess import EasyProcessError
from multiprocess import Queue
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from ..commands.profile_commands import load_profile
from ..config import BrowserParamsInternal, ConfigEncoder, ManagerParamsInternal
from ..utilities.platform_utils import get_firefox_binary_path
from . import configure_firefox
from .selenium_firefox import FirefoxLogInterceptor

DEFAULT_SCREEN_RES = (1366, 768)
logger = logging.getLogger("openwpm")


def deploy_firefox(
    status_queue: Queue,
    browser_params: BrowserParamsInternal,
    manager_params: ManagerParamsInternal,
    crash_recovery: bool,
) -> Tuple[webdriver.Firefox, Path, Optional[Display]]:
    """
    launches a firefox instance with parameters set by the input dictionary
    """
    firefox_binary_path = get_firefox_binary_path()

    root_dir = os.path.dirname(__file__)  # directory of this file

    browser_profile_path = Path(
        tempfile.mkdtemp(prefix="firefox_profile_", dir=browser_params.tmp_profile_dir)
    )
    status_queue.put(("STATUS", "Profile Created", browser_profile_path))

    # Use Options instead of FirefoxProfile to set preferences since the
    # Options method has no "frozen"/restricted options.
    # https://github.com/SeleniumHQ/selenium/issues/2106#issuecomment-320238039
    fo = Options()
    # Set a custom profile that is used in-place and is not deleted by geckodriver.
    # https://firefox-source-docs.mozilla.org/testing/geckodriver/CrashReports.html
    # Using FirefoxProfile breaks stateful crawling:
    # https://github.com/openwpm/OpenWPM/issues/423#issuecomment-521018093
    fo.add_argument("-profile")
    fo.add_argument(str(browser_profile_path))
    assert browser_params.browser_id is not None
    if browser_params.seed_tar and not crash_recovery:
        logger.info(
            "BROWSER %i: Loading initial browser profile from: %s"
            % (browser_params.browser_id, browser_params.seed_tar)
        )
        load_profile(
            browser_profile_path,
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
            browser_params,
            browser_params.recovery_tar,
        )
    status_queue.put(("STATUS", "Profile Tar", None))

    display_mode = browser_params.display_mode
    display_pid = None
    display_port = None
    display = None
    if display_mode == "headless":
        fo.add_argument("--headless")
        fo.add_argument("--width={}".format(DEFAULT_SCREEN_RES[0]))
        fo.add_argument("--height={}".format(DEFAULT_SCREEN_RES[1]))
    if display_mode == "xvfb":
        try:
            display = Display(visible=False, size=DEFAULT_SCREEN_RES)
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

    # Write config file
    extension_config: Dict[str, Any] = dict()
    extension_config.update(browser_params.to_dict())
    extension_config["logger_address"] = manager_params.logger_address
    extension_config["storage_controller_address"] = (
        manager_params.storage_controller_address
    )
    extension_config["testing"] = manager_params.testing
    ext_config_file = browser_profile_path / "browser_params.json"
    with open(ext_config_file, "w") as f:
        json.dump(extension_config, f, cls=ConfigEncoder)
    logger.debug(
        "BROWSER %i: Saved extension config file to: %s"
        % (browser_params.browser_id, ext_config_file)
    )

    # TODO restore detailed logging
    # fo.set_preference("extensions.@openwpm.sdk.console.logLevel", "all")

    # Configure privacy settings
    configure_firefox.privacy(browser_params, fo)

    # Set various prefs to improve speed and eliminate traffic to Mozilla
    configure_firefox.optimize_prefs(fo)

    # Intercept logging at the Selenium level and redirect it to the
    # main logger.
    webdriver_interceptor = FirefoxLogInterceptor(browser_params.browser_id)
    webdriver_interceptor.start()

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

    fo.binary_location = firefox_binary_path
    geckodriver_path = subprocess.check_output(
        "which geckodriver", encoding="utf-8", shell=True
    ).strip()
    driver = webdriver.Firefox(
        options=fo,
        service=Service(
            executable_path=geckodriver_path,
            log_output=open(webdriver_interceptor.fifo, "w"),
        ),
    )

    # Install extension
    ext_loc = os.path.join(root_dir, "../../Extension/openwpm.xpi")
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
    else:
        raise RuntimeError("Unable to identify Firefox process ID.")

    status_queue.put(("STATUS", "Browser Launched", int(pid)))

    return driver, browser_profile_path, display
