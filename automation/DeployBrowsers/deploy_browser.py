
from ..Errors import BrowserConfigError
from . import deploy_firefox


def deploy_browser(status_queue, browser_params,
                   manager_params, crash_recovery):
    """Deploy Firefox browser (Chrome no longer supported)"""
    if browser_params['browser'].lower() == 'chrome':
        raise BrowserConfigError("Chrome is not supported. OpenWPM currently "
                                 "only supports measurement with Firefox.")
    if browser_params['browser'].lower() == 'firefox':
        return deploy_firefox.deploy_firefox(status_queue, browser_params,
                                             manager_params, crash_recovery)
