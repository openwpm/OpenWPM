""" Set prefs and load extensions in Firefox """

from __future__ import absolute_import
from __future__ import print_function

import sys
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
        fp.set_preference('privacy.trackingprotection.enabled', True)

    # Ghostery -> Disconnect
    if browser_params['ghostery']:
        sys.stderr.write(
            "WARNING: Using Disconnect instead of Ghostery.\n"
            "WARNING: Update to browser_params['disconnect'].\n")
        browser_params['disconnect'] = True

    # Disconnect: tracking protection
    if browser_params['disconnect']:
        fp.add_extension(extension=os.path.join(
            root_dir, 'firefox_extensions/2.0@disconnect.me.xpi'))

    # Enable HTTPS Everywhere
    if browser_params['https-everywhere']:
        fp.add_extension(extension=os.path.join(
            root_dir, 'firefox_extensions/https-everywhere@eff.org.xpi'))
        fp.set_preference(
            "extensions.https_everywhere.firstrun_context_menu", True)
        fp.set_preference("extensions.https_everywhere.prefs_version", 1)
        fp.set_preference(
            "extensions.https_everywhere.toolbar_hint_shown", True)
        fp.set_preference(
            "extensions.https_everywhere._observatory.popup_shown", True)
        fp.set_preference(
            "extensions.https_everywhere._observatory.clean_config", True)

    # ABP -> uBlock Origin
    if browser_params['adblock-plus']:
        sys.stderr.write(
            "WARNING: Using uBlock Origin instead of Adblock Plus.\n"
            "WARNING: Update to browser_params['ublock-origin'].\n")
        browser_params['ublock-origin'] = True

    # uBlock Origin, with default settings
    if browser_params['ublock-origin']:
        fp.add_extension(extension=os.path.join(
            root_dir, 'firefox_extensions/uBlock0@raymondhill.net.xpi'))


def optimize_prefs(fp):
    """
    Disable various features and checks the browser will do on startup.
    Some of these (e.g. disabling the newtab page) are required to prevent
    extraneous data in the proxy.
    """
    # Startup / Speed
    fp.set_preference('browser.shell.checkDefaultBrowser', False)
    fp.set_preference("browser.slowStartup.notificationDisabled", True)
    fp.set_preference("browser.slowStartup.maxSamples", 0)
    fp.set_preference("browser.slowStartup.samples", 0)
    fp.set_preference('extensions.checkCompatibility.nightly', False)
    fp.set_preference('browser.rights.3.shown', True)
    fp.set_preference("reader.parse-on-load.enabled", False)
    fp.set_preference('browser.pagethumbnails.capturing_disabled', True)
    fp.set_preference('devtools.profiler.enabled', False)

    # Disable health reports / telemetry / crash reports
    # FF41+ Master Switch
    fp.set_preference("datareporting.policy.dataSubmissionEnabled", False)
    fp.set_preference('datareporting.healthreport.uploadEnabled', False)
    fp.set_preference("datareporting.healthreport.service.enabled", False)
    fp.set_preference('toolkit.telemetry.enabled', False)
    fp.set_preference("toolkit.telemetry.unified", False)
    fp.set_preference("breakpad.reportURL", "")
    fp.set_preference(
        "dom.ipc.plugins.flash.subprocess.crashreporter.enabled", False)

    # Predictive Actions / Prefetch
    fp.set_preference('network.seer.enabled', False)
    fp.set_preference('network.dns.disablePrefetch', True)
    fp.set_preference('network.prefetch-next', False)
    fp.set_preference("browser.search.suggest.enabled", False)
    fp.set_preference("network.http.speculative-parallel-limit", 0)
    fp.set_preference("keyword.enabled", False)  # location bar using search
    fp.set_preference("browser.urlbar.userMadeSearchSuggestionsChoice", True)

    # Disable pinging Mozilla for geoip
    fp.set_preference('browser.search.geoip.url', '')
    fp.set_preference("browser.search.countryCode", "US")
    fp.set_preference("browser.search.region", "US")

    # Disable pinging Mozilla for geo-specific search
    fp.set_preference("browser.search.geoSpecificDefaults", False)
    fp.set_preference("browser.search.geoSpecificDefaults.url", "")

    # Disable auto-updating
    fp.set_preference("app.update.enabled", False)  # browser
    fp.set_preference("app.update.url", "")  # browser
    fp.set_preference("media.gmp-manager.url", "")  # OpenH264 Codec
    fp.set_preference("browser.search.update", False)  # search
    fp.set_preference("extensions.update.enabled", False)  # extensions
    fp.set_preference("extensions.update.autoUpdateDefault", False)  # addons
    fp.set_preference("extensions.getAddons.cache.enabled", False)
    fp.set_preference("lightweightThemes.update.enabled", False)  # Personas
    fp.set_preference(
        "browser.safebrowsing.provider.mozilla.updateURL", "")  # Safebrowsing
    fp.set_preference(
        "browser.safebrowsing.provider.mozilla.gethashURL", "")  # Safebrowsing
    fp.set_preference(
        "browser.safebrowsing.provider.mozilla.lists", "")  # Tracking Protect
    fp.set_preference(
        "browser.safebrowsing.provider.google.updateURL", "")  # Safebrowsing
    fp.set_preference(
        "browser.safebrowsing.provider.google.gethashURL", "")  # Safebrowsing
    fp.set_preference(
        "browser.safebrowsing.provider.google.lists", "")  # TrackingProtection

    # Disable Safebrowsing
    fp.set_preference("browser.safebrowsing.enabled", False)
    fp.set_preference("browser.safebrowsing.malware.enabled", False)
    fp.set_preference("browser.safebrowsing.downloads.enabled", False)
    fp.set_preference("browser.safebrowsing.downloads.remote.enabled", False)
    fp.set_preference('security.OCSP.enabled', 0)

    # Disable Experiments
    fp.set_preference("experiments.enabled", False)
    fp.set_preference("experiments.manifest.uri", "")
    fp.set_preference("experiments.supported", False)
    fp.set_preference("experiments.activeExperiment", False)
    fp.set_preference("network.allow-experiments", False)

    # Disable pinging Mozilla for newtab
    fp.set_preference("browser.newtabpage.directory.ping", "")
    fp.set_preference("browser.newtabpage.directory.source", "")
    fp.set_preference("browser.newtabpage.enabled", False)
    fp.set_preference("browser.newtabpage.enhanced", False)
    fp.set_preference("browser.newtabpage.introShown", True)

    # Disable Pocket
    fp.set_preference("browser.pocket.enabled", False)

    # Disable Hello
    fp.set_preference("loop.enabled", False)
