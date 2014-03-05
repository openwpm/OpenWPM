from selenium import webdriver
import shutil
import os
from pyvirtualdisplay import Display

def deploy_firefox(browser_params) :
    display_pid = None
    if browser_params['headless'] :
        display = Display(visible=0, size=(1366,768))
        display.start()
        display_pid = display.pid

    fp = webdriver.FirefoxProfile()
    profile_path = fp.path + '/'

    if browser_params['debugging']:
        fp.add_extension(extension=os.path.join(os.path.dirname(__file__), 'extensions/firebug-1.11.0.xpi'))
        fp.set_preference("extensions.firebug.currentVersion", "1.11.0") #Avoid startup screen

    # TODO: re-include this support for Do Not Track and turning off Third Party cookies
    '''
    if dnt:
        fp.set_preference("privacy.donottrackheader.enabled", True)
        fp.set_preference("privacy.donottrackheader.value", 1)

    if tp_off:
            fp.set_preference("network.cookie.cookieBehavior", 1)
    '''

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
        #http://kb.mozillazine.org/Network.proxy.no_proxies_on
        fp.set_preference("network.proxy.no_proxies_on", "")

        # copy the dbs into temp profile
        # these were created by manually adding the cert to
        # a previous tmp selenium profile
        shutil.copy(os.path.join(os.path.dirname(__file__) + "/../", 'Proxy/key3.db'), fp.path + '/key3.db')
        shutil.copy(os.path.join(os.path.dirname(__file__) + "/../", 'Proxy/cert8.db'), fp.path + '/cert8.db')

    if browser_params['fourthparty']:
        fp.add_extension(extension=os.path.join(os.path.dirname(__file__) + "/../",
                                           'extensions/fourthparty/fourthparty.xpi'))

    driver = webdriver.Firefox(firefox_profile=fp)

    #Limit page loads to 30 seconds, this constant is up for debate
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)

    return (driver, profile_path, display_pid)
