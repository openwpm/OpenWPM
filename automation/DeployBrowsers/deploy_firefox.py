from ..Commands.profile_commands import load_profile

from selenium import webdriver
from pyvirtualdisplay import Display
from math import ceil
import shutil
import os
import cPickle
import random

def deploy_firefox(browser_params):
    root_dir = os.path.dirname(__file__) #directory of this file
    
    display_pid = None
    fp = webdriver.FirefoxProfile()
    browser_profile_path = fp.path + '/'
    
    profile_settings = None #Imported browser settings
    ext_dict = None #Dictionary of supported extensions
    if browser_params['profile_tar']:
        profile_settings = load_profile(browser_profile_path, browser_params['profile_tar'])

    if browser_params['random_attributes'] and profile_settings is None:
        profile_settings = dict()

        # load a random set of extensions
        with open(os.path.join(root_dir, 'firefox_extensions/supported_extensions.p'),'rb') as f:
            ext_dict = cPickle.load(f)
        extensions = random.sample(ext_dict.keys(),random.randint(0,len(ext_dict.keys())))
        profile_settings['extensions'] = extensions

        # choose a random screen-res from list
        resolutions = list()
        with open(os.path.join(root_dir,'screen_resolutions.txt'), 'r') as f:
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
        profile_settings['extensions'] = [] #Load no extensions
        profile_settings['screen_res'] = (1366,768)
        profile_settings['ua_string'] = None

    # Load profile settings - window size set after initialization
    if profile_settings['extensions'] != [] and ext_dict is None:
        with open(os.path.join(root_dir, 'firefox_extensions/supported_extensions.p'),'rb') as f:
            ext_dict = cPickle.load(f)
    for extension in profile_settings['extensions']:
        ext_loc = os.path.join(root_dir, 'firefox_extensions/',ext_dict[extension]['filename'])
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
        fp.set_preference("extensions.firebug.currentVersion", "1.11.0") #Avoid startup screen

    if browser_params['proxy']:
        PROXY_HOST = "localhost"
        PROXY_PORT = browser_params['proxy']

        # Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
        fp.set_preference("network.proxy.type", 1)
        fp.set_preference("network.proxy.http", PROXY_HOST)
        fp.set_preference("network.proxy.http_port", PROXY_PORT)
        fp.set_preference("network.proxy.ssl", PROXY_HOST) #https sites
        fp.set_preference("network.proxy.ssl_port", PROXY_PORT)

        # set this to exclude sites from using proxy
        # http://kb.mozillazine.org/Network.proxy.no_proxies_on
        fp.set_preference("network.proxy.no_proxies_on", "")

        # copy the dbs into temp profile
        # these were created by manually adding the cert to
        # a previous tmp selenium profile
        shutil.copy(os.path.join(root_dir + "/../", 'Proxy/key3.db'), fp.path + '/key3.db')
        shutil.copy(os.path.join(root_dir + "/../", 'Proxy/cert8.db'), fp.path + '/cert8.db')

    #TODO: this isn't supported
    if browser_params['fourthparty']:
        fp.add_extension(extension=os.path.join(root_dir + "/../",
                                           'extensions/fourthparty/fourthparty.xpi'))
    # Disable flash
    if browser_params['disable_flash']:
        fp.set_preference('plugin.state.flash',0)

    driver = webdriver.Firefox(firefox_profile=fp)

    # Set the selenium timeout equal to half the user set, this constant is up for debate
    timeout = ceil(float(browser_params['timeout'])/2)
    driver.set_page_load_timeout(timeout)
    driver.set_script_timeout(timeout)

    # set window size
    driver.set_window_size(*profile_settings['screen_res'])

    return driver, browser_profile_path, display_pid, profile_settings
