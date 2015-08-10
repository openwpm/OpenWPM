""" Set prefs and load extensions in Firefox """
import shutil
import os

def privacy(browser_params, fp, root_dir, browser_profile_path):
    """
    Configure the privacy settings in Firefox. This includes:
    * DNT
    * Third-part cookie blocking
    * Tracking protection
    * Privacy extensions
    """

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

    # Tracking Protection
    if browser_params['tracking-protection']:
        fp.set_preference("privacy.trackingprotection.enabled", True)

    # Load Ghostery - Enable all blocking
    if browser_params['ghostery']:
        fp.add_extension(extension=os.path.join(root_dir,'firefox_extensions/ghostery/ghostery-5.4.6.xpi'))
        os.makedirs(browser_profile_path+'jetpack/firefox@ghostery.com/simple-storage/')
        src = os.path.join(root_dir,'firefox_extensions/ghostery/store.json') # settings - block all trackers/cookies
        dst = os.path.join(browser_profile_path,'jetpack/firefox@ghostery.com/simple-storage/store.json')
        shutil.copy(src,dst)
    
    # Enable HTTPS Everywhere
    if browser_params['https-everywhere']:
        fp.add_extension(extension=os.path.join(root_dir,'firefox_extensions/https-everywhere-5.0.7.xpi'))
        fp.set_preference("extensions.https_everywhere.firstrun_context_menu", True)
        fp.set_preference("extensions.https_everywhere.prefs_version", 1)
        fp.set_preference("extensions.https_everywhere.toolbar_hint_shown", True)
        fp.set_preference("extensions.https_everywhere._observatory.popup_shown", True)
        fp.set_preference("extensions.https_everywhere._observatory.clean_config", True)
