from selenium import webdriver
import shutil
import os
from pyvirtualdisplay import Display

# note dnt, tp_off are not supported
# in general, chrome may not be well-supported yet
def deploy_chrome(browser_params):
    # chrome driver must be installed in python $PATH (/usr/bin/)
    # Chrome browser is assumed in default install directory for OS

    # Profile Paths
    # OSX: ~/Library/Application Support/Google/Chrome/
    # Linux: ~/.config/google-chrome/
    profile_path = os.environ['HOME'] + "/.config/google-chrome/"
    co = webdriver.ChromeOptions()

    # Add user-defined chrome options
    '''
    for cmd_arg in cmd_args:
        if cmd_arg:
            co.add_argument(cmd_arg)
    '''

    # to exclude sites from traversing proxy
    # comma-separated list of bypass values: 1.2.3.0/24,.google.com
    # co.add_argument("--proxy-bypass-list=.google.com,.yahoo.com,.yimg.com")

    # Load extensions (unpacked)
    co.add_argument("--allow-legacy-extension-manifests")
    # co.add_extension(os.path.join(os.path.dirname(__file__),'extensions/....'))

    if browser_params['debugging']:
        co.add_argument("--load-extension=%s" % (os.path.join(os.path.dirname(__file__) + "/../" ,'extensions/firebug_chrome/')))
        pass

    if browser_params['proxy'] is not None:
        PROXY_HOST = "localhost"
        PROXY_PORT = browser_params['proxy']
        co.add_argument("--proxy-server=%s:%i" % (PROXY_HOST, PROXY_PORT))

    driver = webdriver.Chrome(chrome_options=co)

    #Limit page loads to 30 seconds
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)

    return (driver, profile_path, None)
