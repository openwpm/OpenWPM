""" Set prefs and load extensions in Firefox """

from __future__ import absolute_import
from __future__ import print_function

import os
import shutil

EXT_STORAGE_DIR = 'browser-extension-data'


def privacy(browser_params, fp, fo, root_dir, browser_profile_path):
    """
    Configure the privacy settings in Firefox. This includes:
    * DNT
    * Third-part cookie blocking
    * Tracking protection
    * Privacy extensions
    """

    # Make extension storage directory
    storage_dir = os.path.join(browser_profile_path, EXT_STORAGE_DIR)
    if not os.path.isdir(storage_dir):
        os.mkdir(storage_dir)

    # Turns on Do Not Track
    if browser_params['donottrack']:
        fo.set_preference("privacy.donottrackheader.enabled", True)
        fo.set_preference("privacy.donottrackheader.value", 1)

    # Sets the third party cookie setting
    if browser_params['tp_cookies'].lower() == 'never':
        fo.set_preference("network.cookie.cookieBehavior", 1)
    elif browser_params['tp_cookies'].lower() == 'from_visited':
        fo.set_preference("network.cookie.cookieBehavior", 3)
    else:  # always allow third party cookies
        fo.set_preference("network.cookie.cookieBehavior", 0)

    # Tracking Protection
    if browser_params['tracking-protection']:
        raise RuntimeError("Firefox Tracking Protection is not currently "
                           "supported. See: "
                           "https://github.com/citp/OpenWPM/issues/101")

    # AbBlock Plus
    if browser_params['adblock-plus']:
        raise RuntimeError("AdBlock Plus is not currently supported. See: "
                           "https://github.com/citp/OpenWPM/issues/35")

    # Ghostery
    # Updated: 2017-10-7
    if browser_params['ghostery']:
        fp.add_extension(extension=os.path.join(
            root_dir, 'firefox_extensions', 'ghostery',
            'ghostery-7.3.3.7.xpi')
        )
        ghostery_dir = os.path.join(storage_dir, 'firefox@ghostery.com')
        if not os.path.isdir(ghostery_dir):
            os.mkdir(ghostery_dir)
        shutil.copy(os.path.join(root_dir, 'firefox_extensions',
                                 'ghostery', 'storage.js'), ghostery_dir)

    # Disconnect
    # Updated: 2017-10-7
    if browser_params['disconnect']:
        fp.add_extension(extension=os.path.join(
            root_dir, 'firefox_extensions', 'disconnect-5.18.21.xpi'))

    # Enable HTTPS Everywhere
    # Updated: 2017-10-7
    if browser_params['https-everywhere']:
        fp.add_extension(extension=os.path.join(
            root_dir, 'firefox_extensions',
            'https_everywhere-2017.10.4.xpi'))

    # uBlock Origin
    # Updated: 2017-10-7
    # Uses the default blocklists that ship with the XPI.
    if browser_params['ublock-origin']:
        fp.add_extension(extension=os.path.join(
            root_dir, 'firefox_extensions', 'ublock_origin',
            'ublock_origin-1.14.10.xpi')
        )
        ublock_dir = os.path.join(storage_dir, 'uBlock0@raymondhill.net')
        if not os.path.isdir(ublock_dir):
            os.mkdir(ublock_dir)
        shutil.copy(os.path.join(root_dir, 'firefox_extensions',
                                 'ublock_origin', 'storage.js'), ublock_dir)


def optimize_prefs(fo):
    """
    Disable various features and checks the browser will do on startup.
    Some of these (e.g. disabling the newtab page) are required to prevent
    extraneous data in the proxy.
    """
    # Startup / Speed
    fo.set_preference('browser.shell.checkDefaultBrowser', False)
    fo.set_preference("browser.slowStartup.notificationDisabled", True)
    fo.set_preference("browser.slowStartup.maxSamples", 0)
    fo.set_preference("browser.slowStartup.samples", 0)
    fo.set_preference('extensions.checkCompatibility.nightly', False)
    fo.set_preference('browser.rights.3.shown', True)
    fo.set_preference("reader.parse-on-load.enabled", False)
    fo.set_preference('browser.pagethumbnails.capturing_disabled', True)
    fo.set_preference('devtools.profiler.enabled', False)

    # Disable health reports / telemetry / crash reports
    # FF41+ Master Switch
    fo.set_preference("datareporting.policy.dataSubmissionEnabled", False)
    fo.set_preference('datareporting.healthreport.uploadEnabled', False)
    fo.set_preference("datareporting.healthreport.service.enabled", False)
    fo.set_preference('toolkit.telemetry.enabled', False)
    fo.set_preference("toolkit.telemetry.unified", False)
    fo.set_preference("breakpad.reportURL", "")
    fo.set_preference(
        "dom.ipc.plugins.flash.subprocess.crashreporter.enabled", False)

    # Predictive Actions / Prefetch
    fo.set_preference('network.seer.enabled', False)
    fo.set_preference('network.dns.disablePrefetch', True)
    fo.set_preference('network.prefetch-next', False)
    fo.set_preference("browser.search.suggest.enabled", False)
    fo.set_preference("network.http.speculative-parallel-limit", 0)
    fo.set_preference("keyword.enabled", False)  # location bar using search
    fo.set_preference("browser.urlbar.userMadeSearchSuggestionsChoice", True)

    # Disable pinging Mozilla for geoip
    fo.set_preference('browser.search.geoip.url', '')
    fo.set_preference("browser.search.countryCode", "US")
    fo.set_preference("browser.search.region", "US")

    # Disable pinging Mozilla for geo-specific search
    fo.set_preference("browser.search.geoSpecificDefaults", False)
    fo.set_preference("browser.search.geoSpecificDefaults.url", "")

    # Disable auto-updating
    fo.set_preference("app.update.enabled", False)  # browser
    fo.set_preference("app.update.url", "")  # browser
    fo.set_preference("media.gmp-manager.url", "")  # OpenH264 Codec
    fo.set_preference("browser.search.update", False)  # search
    fo.set_preference("extensions.update.enabled", False)  # extensions
    fo.set_preference("extensions.update.autoUpdateDefault", False)  # addons
    fo.set_preference("extensions.getAddons.cache.enabled", False)
    fo.set_preference("lightweightThemes.update.enabled", False)  # Personas
    fo.set_preference(
        "browser.safebrowsing.provider.mozilla.updateURL", "")  # Safebrowsing
    fo.set_preference(
        "browser.safebrowsing.provider.mozilla.gethashURL", "")  # Safebrowsing
    fo.set_preference(
        "browser.safebrowsing.provider.mozilla.lists", "")  # Tracking Protect
    fo.set_preference(
        "browser.safebrowsing.provider.google.updateURL", "")  # Safebrowsing
    fo.set_preference(
        "browser.safebrowsing.provider.google.gethashURL", "")  # Safebrowsing
    fo.set_preference(
        "browser.safebrowsing.provider.google.lists", "")  # TrackingProtection

    # Disable Safebrowsing
    fo.set_preference("browser.safebrowsing.enabled", False)
    fo.set_preference("browser.safebrowsing.malware.enabled", False)
    fo.set_preference("browser.safebrowsing.downloads.enabled", False)
    fo.set_preference("browser.safebrowsing.downloads.remote.enabled", False)
    fo.set_preference('security.OCSP.enabled', 0)

    # Disable Experiments
    fo.set_preference("experiments.enabled", False)
    fo.set_preference("experiments.manifest.uri", "")
    fo.set_preference("experiments.supported", False)
    fo.set_preference("experiments.activeExperiment", False)
    fo.set_preference("network.allow-experiments", False)

    # Disable pinging Mozilla for newtab
    fo.set_preference("browser.newtabpage.directory.ping", "")
    fo.set_preference("browser.newtabpage.directory.source", "")
    fo.set_preference("browser.newtabpage.enabled", False)
    fo.set_preference("browser.newtabpage.enhanced", False)
    fo.set_preference("browser.newtabpage.introShown", True)

    # Disable Pocket
    fo.set_preference("browser.pocket.enabled", False)

    # Disable Hello
    fo.set_preference("loop.enabled", False)
