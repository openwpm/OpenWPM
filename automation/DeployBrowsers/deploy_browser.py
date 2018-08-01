from __future__ import absolute_import

from . import deploy_firefox
from ..Errors import BrowserConfigError


def deploy_browser(status_queue, browser_params, manager_params, crash_recovery):
    """ receives a dictionary of browser parameters and passes it to the relevant constructor """
    if browser_params['browser'].lower() == 'chrome':
        raise BrowserConfigError("Chrome is not supported. OpenWPM currently "
                                 "only supports measurement with Firefox.")
    if browser_params['browser'].lower() == 'firefox':
        return deploy_firefox.deploy_firefox(status_queue, browser_params, manager_params, crash_recovery)
