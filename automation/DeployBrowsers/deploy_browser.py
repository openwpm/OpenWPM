import deploy_chrome
import deploy_firefox

def deploy_browser(browser_params, crash_recovery):
    """ receives a dictionary of browser parameters and passes it to the relevant constructor """
    if browser_params['browser'].lower() == 'chrome':
        return deploy_chrome.deploy_chrome(browser_params)
    if browser_params['browser'].lower() == 'firefox':
        return deploy_firefox.deploy_firefox(browser_params, crash_recovery)
