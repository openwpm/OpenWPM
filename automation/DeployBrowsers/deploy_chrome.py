from selenium import webdriver
import os


def deploy_chrome(browser_params):
    """
    deploys a chrome browser, given the list of list of browser params
    in general, not as well supported as firefox yet
    chrome driver must be installed in python $PATH (/usr/bin/)
    Chrome browser is assumed in default install directory for OS
    """

    # Profile Paths
    # OSX: ~/Library/Application Support/Google/Chrome/
    # Linux: ~/.config/google-chrome/
    profile_path = os.environ['HOME'] + "/.config/google-chrome/"
    co = webdriver.ChromeOptions()

    # to exclude sites from traversing proxy
    # comma-separated list of bypass values: 1.2.3.0/24,.google.com
    # co.add_argument("--proxy-bypass-list=.google.com,.yahoo.com,.yimg.com")

    # Load extensions (unpacked)
    co.add_argument("--allow-legacy-extension-manifests")
    # co.add_extension(os.path.join(os.path.dirname(__file__),'extensions/....'))

    if browser_params['debugging']:
        co.add_argument("--load-extension=%s" %
                        (os.path.join(os.path.dirname(__file__) + "/../", 'extensions/firebug_chrome/')))
        pass

    if browser_params['proxy'] is not None:
        PROXY_HOST = "localhost"
        PROXY_PORT = browser_params['proxy']
        co.add_argument("--proxy-server=%s:%i" % (PROXY_HOST, PROXY_PORT))

    driver = webdriver.Chrome(chrome_options=co)

    return driver, profile_path, None
