import deploy_chrome
import deploy_firefox

# receives a dictionary of browser parameters and passes it to the relevant constructor

def deploy_browser(browser_params):
    if browser_params['browser'] == 'chrome':
        return deploy_chrome.deploy_chrome(browser_params)
    if browser_params['browser'] == 'firefox':
        return deploy_firefox.deploy_firefox(browser_params)
