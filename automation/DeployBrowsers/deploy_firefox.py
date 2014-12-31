from ..Commands.profile_commands import load_profile

from selenium import webdriver
from pyvirtualdisplay import Display
import shutil
import os
import cPickle
import random

DEFAULT_SCREEN_RES = (1366, 768)  # Default screen res when no preferences are given


def deploy_firefox(browser_params, crash_recovery):
    """ launches a firefox instance with parameters set by the input dictionary """
    root_dir = os.path.dirname(__file__)  # directory of this file
    
    display_pid = None
    fp = webdriver.FirefoxProfile()
    browser_profile_path = fp.path + '/'
    
    profile_settings = None  # Imported browser settings
    ext_dict = None  # Dictionary of supported extensions
    if browser_params['profile_tar'] and not crash_recovery:
        profile_settings = load_profile(browser_profile_path, browser_params['profile_tar'],
                                        load_flash=browser_params['disable_flash'] is False)
    elif browser_params['profile_tar']:
        profile_settings = load_profile(browser_profile_path, browser_params['profile_tar'])

    if browser_params['random_attributes'] and profile_settings is None:
        profile_settings = dict()

        # load a random set of extensions
        with open(os.path.join(root_dir, 'firefox_extensions/supported_extensions.p'), 'rb') as f:
            ext_dict = cPickle.load(f)
        extensions = random.sample(ext_dict.keys(), random.randint(0, len(ext_dict.keys())))
        profile_settings['extensions'] = extensions

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
        profile_settings['extensions'] = []  # Load no extensions
        profile_settings['screen_res'] = DEFAULT_SCREEN_RES
        profile_settings['ua_string'] = None

    # Load profile settings - window size set after initialization
    if profile_settings['extensions'] != [] and ext_dict is None:
        with open(os.path.join(root_dir, 'firefox_extensions/supported_extensions.p'), 'rb') as f:
            ext_dict = cPickle.load(f)
    for extension in profile_settings['extensions']:
        ext_loc = os.path.join(root_dir, 'firefox_extensions/', ext_dict[extension]['filename'])
        fp.add_extension(extension=ext_loc)
        # Avoid start-up screen - set the necessary flags for each extension
        for item in ext_dict[extension]['startup']:
            fp.set_preference(*item)

    if profile_settings['ua_string'] is not None:
        fp.set_preference("general.useragent.override", profile_settings['ua_string'])

    if browser_params['headless']:
        display = Display(visible=0, size=profile_settings['screen_res'])
        display.start()
        display_pid = display.pid

    if browser_params['debugging']:
        firebug_loc = os.path.join(root_dir, 'firefox_extensions/firebug-1.11.0.xpi')
        fp.add_extension(extension=firebug_loc)
        fp.set_preference("extensions.firebug.currentVersion", "1.11.0")  # Avoid startup screen

    if browser_params['proxy']:
        PROXY_HOST = "localhost"
        PROXY_PORT = browser_params['proxy']

        # Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
        fp.set_preference("network.proxy.type", 1)
        fp.set_preference("network.proxy.http", PROXY_HOST)
        fp.set_preference("network.proxy.http_port", PROXY_PORT)
        fp.set_preference("network.proxy.ssl", PROXY_HOST)  # https sites
        fp.set_preference("network.proxy.ssl_port", PROXY_PORT)

        # set this to exclude sites from using proxy
        # http://kb.mozillazine.org/Network.proxy.no_proxies_on
        fp.set_preference("network.proxy.no_proxies_on", "")

        # copy the dbs into temp profile
        # these were created by manually adding the cert to
        # a previous tmp selenium profile
        shutil.copy(os.path.join(root_dir + "/../", 'Proxy/key3.db'), fp.path + '/key3.db')
        shutil.copy(os.path.join(root_dir + "/../", 'Proxy/cert8.db'), fp.path + '/cert8.db')

    # Turns on Do Not Track
    if browser_params['donottrack']:
        fp.set_preference("privacy.donottrackheader.enabled", True)
        fp.set_preference("privacy.donottrackheader.value", 1)

    # Sets the third party cookie setting
    if browser_params['tp_cookies'].lower() == 'never':
        fp.set_preference("network.cookie.cookieBehavior", 1)
    elif browser_params['tp_cookies'].lower() == 'from_visited':
        fp.set_preference("network.cookie.cookieBehavior", 3)
    else:  # always allow third party cookies
        fp.set_preference("network.cookie.cookieBehavior", 0)
        
    # Disable flash
    if browser_params['disable_flash']:
        fp.set_preference('plugin.state.flash', 0)

    # Disable health reports
    fp.set_preference('datareporting.healthreport.uploadEnabled', False)
    fp.set_preference('toolkit.telemetry.enabled', False)

    fp.set_preference('extensions.checkCompatibility.nightly', False)
    fp.set_preference('browser.search.update', False)
    # Disable know your rights banner
    fp.set_preference('browser.rights.3.shown', True)
    fp.set_preference('browser.shell.checkDefaultBrowser', False)
    fp.set_preference('security.OCSP.enabled', "0")
    fp.set_preference('browser.safebrowsing.enabled', False)
    fp.set_preference('devtools.profiler.enabled', False)
    fp.set_preference('network.seer.enabled', False)  # predictive actions
    fp.set_preference('network.dns.disablePrefetch', True)  # no need to prefetch
    fp.set_preference('network.prefetch-next', False)  # no need to prefetch
    # Disable page thumbnails
    fp.set_preference('browser.pagethumbnails.capturing_disabled', True)

    driver = webdriver.Firefox(firefox_profile=fp)

    # set window size
    driver.set_window_size(*profile_settings['screen_res'])

    return driver, browser_profile_path, display_pid, profile_settings
