from __future__ import absolute_import

import errno
import json
import os
import random
import six
from six.moves import range
import shutil
import threading
import tempfile

from . import configure_firefox
from ..Commands.profile_commands import load_profile
from ..MPLogger import loggingclient
from ..utilities.platform_utils import ensure_firefox_in_path

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver

from pyvirtualdisplay import Display

DEFAULT_SCREEN_RES = (1366, 768)

def mktempfifo(suffix="", prefix="tmp", dir=None):
    """
    Same as 'tempfile.mkdtemp' but creates a fifo instead of a
    directory.
    """
    if dir is None:
        dir = tempfile.gettempdir()
    names = tempfile._get_candidate_names()
    for seq in range(tempfile.TMP_MAX):
        name = names.next()
        file = os.path.join(dir, prefix + name + suffix)
        try:
            os.mkfifo(file, 384) # 0600
            return file
        except OSError as e:
            if e.errno == errno.EEXIST:
                continue
            raise
    if hasattr(__builtins__, 'FileExistsError'):
        exc = FileExistsError
    else:
        exc = IOError
    raise exc(errno.EEXIST, "No usable fifo name found")

class WebdriverLogInterceptor(threading.Thread):
    """
    Intercept logs from Selenium and/or geckodriver, using a named pipe
    and a detached thread, and feed them to the primary logger for this
    instance.  Also responsible for extracting the _real_ profile location
    from geckodriver's log output (geckodriver copies the profile).
    """
    def __init__(self, crawl_id, logger, profile_path):
        threading.Thread.__init__(self, name="log-interceptor-%i" % crawl_id)
        self.crawl_id = crawl_id
        self.logger = logger
        self.fifo = mktempfifo(suffix=".log", prefix="owpm_driver_")
        self.profile_path = profile_path
        self.daemon = True

    def run(self):
        # We might not ever get EOF on the FIFO, so instead we delete
        # it after we receive the first line (which means the other
        # end has actually opened it).
        try:
            with open(self.fifo, "rt") as f:
                for line in f:
                    self.logger.debug("BROWSER %i: driver: %s"
                                      % (self.crawl_id, line.strip()))
                    if "Using profile path" in line:
                        self.profile_path = \
                            line.partition("Using profile path")[-1].strip()

                    if self.fifo is not None:
                        os.unlink(self.fifo)
                        self.fifo = None

        finally:
            if self.fifo is not None:
                os.unlink(self.fifo)
                self.fifo = None

def deploy_firefox(status_queue, browser_params, manager_params, crash_recovery):
    """
    launches a firefox instance with parameters set by the input dictionary
    """
    ensure_firefox_in_path()

    root_dir = os.path.dirname(__file__)  # directory of this file
    logger = loggingclient(*manager_params['logger_address'])


    display_pid = None
    display_port = None
    fp = webdriver.FirefoxProfile()
    browser_profile_path = fp.path + '/'
    status_queue.put(('STATUS','Profile Created',browser_profile_path))

    profile_settings = None  # Imported browser settings
    if browser_params['profile_tar'] and not crash_recovery:
        logger.debug("BROWSER %i: Loading initial browser profile from: %s"
                     % (browser_params['crawl_id'],
                        browser_params['profile_tar']))
        load_flash = browser_params['disable_flash'] is False
        profile_settings = load_profile(browser_profile_path,
                                        manager_params,
                                        browser_params,
                                        browser_params['profile_tar'],
                                        load_flash=load_flash)
    elif browser_params['profile_tar']:
        logger.debug("BROWSER %i: Loading recovered browser profile from: %s"
                     % (browser_params['crawl_id'],
                        browser_params['profile_tar']))
        profile_settings = load_profile(browser_profile_path,
                                        manager_params,
                                        browser_params,
                                        browser_params['profile_tar'])
    status_queue.put(('STATUS','Profile Tar',None))

    if browser_params['random_attributes'] and profile_settings is None:
        logger.debug("BROWSER %i: Loading random attributes for browser"
                     % browser_params['crawl_id'])
        profile_settings = dict()

        # choose a random screen-res from list
        resolutions = list()
        with open(os.path.join(root_dir, 'screen_resolutions.txt'), 'r') as f:
            for line in f:
                resolutions.append(tuple(line.strip().split(',')))
        profile_settings['screen_res'] = random.choice(resolutions)

        # set a random user agent from list
        ua_strings = list()
        with open(os.path.join(root_dir, 'user_agent_strings.txt'), 'r') as f:
            for line in f:
                ua_strings.append(line.strip())
        profile_settings['ua_string'] = random.choice(ua_strings)

    # If profile settings still not set - set defaults
    if profile_settings is None:
        profile_settings = dict()
        profile_settings['screen_res'] = DEFAULT_SCREEN_RES
        profile_settings['ua_string'] = None

    if profile_settings['ua_string'] is not None:
        logger.debug("BROWSER %i: Overriding user agent string to '%s'"
                     % (browser_params['crawl_id'],
                        profile_settings['ua_string']))
        fp.set_preference("general.useragent.override",
                          profile_settings['ua_string'])

    if browser_params['headless']:
        display = Display(visible=0, size=profile_settings['screen_res'])
        display.start()
        display_pid = display.pid
        display_port = display.cmd_param[5][1:]
    status_queue.put(('STATUS','Display',(display_pid, display_port)))

    # Write extension configuration
    if browser_params['extension_enabled']:
        ext_loc = os.path.join(root_dir, '../Extension/firefox/openwpm.xpi')
        ext_loc = os.path.normpath(ext_loc)
        fp.add_extension(extension=ext_loc)
        fp.set_preference("extensions.@openwpm.sdk.console.logLevel", "all")
        extension_config = dict()
        extension_config.update(browser_params)
        extension_config['logger_address'] = manager_params['logger_address']
        extension_config['sqlite_address'] = manager_params['aggregator_address']
        if 'ldb_address' in manager_params:
            extension_config['leveldb_address'] = manager_params['ldb_address']
        else:
            extension_config['leveldb_address'] = None
        extension_config['testing'] = manager_params['testing']
        with open(browser_profile_path + 'browser_params.json', 'w') as f:
            json.dump(extension_config, f)
        logger.debug("BROWSER %i: OpenWPM Firefox extension loaded"
                     % browser_params['crawl_id'])

    if browser_params['proxy']:
        logger.error("BROWSER %i: MITMProxy support has been removed. "
                     "Use http_instrument instead. ")

    # Disable flash
    if browser_params['disable_flash']:
        fp.set_preference('plugin.state.flash', 0)

    # Configure privacy settings
    configure_firefox.privacy(browser_params, fp, root_dir, browser_profile_path)

    # Set various prefs to improve speed and eliminate traffic to Mozilla
    configure_firefox.optimize_prefs(fp)

    # Intercept logging at the Selenium level and redirect it to the
    # main logger.  This will also inform us where the real profile
    # directory is hiding.
    webdriver_logger = WebdriverLogInterceptor(
        browser_params['crawl_id'], logger, browser_profile_path)
    webdriver_logger.start()

    # Launch the webdriver
    status_queue.put(('STATUS','Launch Attempted',None))
    fb = FirefoxBinary()
    driver = webdriver.Firefox(firefox_profile=fp, firefox_binary=fb,
                               log_path=webdriver_logger.fifo)

    # set window size
    driver.set_window_size(*profile_settings['screen_res'])

    if hasattr(driver, 'service') and hasattr(driver.service, 'process'):
        pid = driver.service.process.pid
    elif hasattr(driver, 'binary') and hasattr(driver.binary, 'process'):
        pid = driver.binary.process.pid
    else:
        raise RuntimeError("Unable to identify Firefox process ID.")

    status_queue.put(('STATUS','Browser Launched',
                      (int(pid), profile_settings)))

    return driver, webdriver_logger.profile_path, profile_settings
