""" Set prefs and load extensions in Firefox """

from selenium.webdriver.firefox.options import Options

from ..config import BrowserParams


def privacy(browser_params: BrowserParams, fo: Options) -> None:
    """
    Configure the privacy settings in Firefox. This includes:
    * DNT
    * Third-part cookie blocking
    * Tracking protection
    * Privacy extensions
    """

    # Turns on Do Not Track
    if browser_params.donottrack:
        fo.set_preference("privacy.donottrackheader.enabled", True)

    # Sets the third party cookie setting
    if browser_params.tp_cookies.lower() == "never":
        fo.set_preference("network.cookie.cookieBehavior", 1)
    elif browser_params.tp_cookies.lower() == "from_visited":
        fo.set_preference("network.cookie.cookieBehavior", 3)
    else:  # always allow third party cookies
        fo.set_preference("network.cookie.cookieBehavior", 0)

    # Tracking Protection
    if browser_params.tracking_protection:
        raise RuntimeError(
            "Firefox Tracking Protection is not currently "
            "supported. See: "
            "https://github.com/citp/OpenWPM/issues/101"
        )


def optimize_prefs(fo: Options) -> None:
    """
    Disable various features and checks the browser will do on startup.
    Some of these (e.g. disabling the newtab page) are required to prevent
    extraneous data in the proxy.

    Source of prefs:
    * https://support.mozilla.org/en-US/kb/how-stop-firefox-making-automatic-connections
    * https://github.com/pyllyukko/user.js/blob/master/user.js
    """  # noqa
    # Startup / Speed
    fo.set_preference("browser.shell.checkDefaultBrowser", False)
    fo.set_preference("browser.rights.3.shown", True)
    fo.set_preference("reader.parse-on-load.enabled", False)
    fo.set_preference("browser.pagethumbnails.capturing_disabled", True)
    fo.set_preference("browser.uitour.enabled", False)

    # Disable health reports / telemetry / crash reports
    fo.set_preference("datareporting.policy.dataSubmissionEnabled", False)
    fo.set_preference("datareporting.healthreport.uploadEnabled", False)
    fo.set_preference("datareporting.healthreport.service.enabled", False)
    fo.set_preference("toolkit.telemetry.archive.enabled", False)
    fo.set_preference("toolkit.telemetry.enabled", False)
    fo.set_preference("toolkit.telemetry.unified", False)
    fo.set_preference("breakpad.reportURL", "")
    fo.set_preference("browser.tabs.crashReporting.sendReport", False)
    fo.set_preference("browser.crashReports.unsubmittedCheck.enabled", False)

    # Predictive Actions / Prefetch
    fo.set_preference("network.predictor.enabled", False)
    fo.set_preference("network.dns.disablePrefetch", True)
    fo.set_preference("network.prefetch-next", False)
    fo.set_preference("browser.search.suggest.enabled", False)
    fo.set_preference("network.http.speculative-parallel-limit", 0)
    fo.set_preference("keyword.enabled", False)  # location bar using search

    # Disable pinging Mozilla for geoip
    fo.set_preference("browser.search.geoip.url", "")
    fo.set_preference("browser.search.region", "US")

    # Disable auto-updating
    fo.set_preference("app.update.url", "")  # browser update URL
    fo.set_preference("browser.search.update", False)  # search engines
    fo.set_preference("extensions.update.enabled", False)  # extensions
    fo.set_preference("extensions.update.autoUpdateDefault", False)
    fo.set_preference("extensions.getAddons.cache.enabled", False)

    # Disable Safebrowsing and other security features
    # that require remote content
    fo.set_preference("browser.safebrowsing.phishing.enabled", False)
    fo.set_preference("browser.safebrowsing.malware.enabled", False)
    fo.set_preference("browser.safebrowsing.downloads.enabled", False)
    fo.set_preference("browser.safebrowsing.downloads.remote.enabled", False)
    fo.set_preference("browser.safebrowsing.blockedURIs.enabled", False)
    fo.set_preference("browser.safebrowsing.provider.mozilla.gethashURL", "")
    fo.set_preference("browser.safebrowsing.provider.google.gethashURL", "")
    fo.set_preference("browser.safebrowsing.provider.google4.gethashURL", "")
    fo.set_preference("browser.safebrowsing.provider.mozilla.updateURL", "")
    fo.set_preference("browser.safebrowsing.provider.google.updateURL", "")
    fo.set_preference("browser.safebrowsing.provider.google4.updateURL", "")
    fo.set_preference("browser.safebrowsing.provider.mozilla.lists", "")
    fo.set_preference("browser.safebrowsing.provider.google.lists", "")
    fo.set_preference("browser.safebrowsing.provider.google4.lists", "")
    fo.set_preference("extensions.blocklist.enabled", False)
    fo.set_preference("security.OCSP.enabled", 0)

    # Disable Content Decryption Module and OpenH264 related downloads
    fo.set_preference("media.gmp-manager.url", "")
    fo.set_preference("media.gmp-provider.enabled", False)
    fo.set_preference("media.gmp-widevinecdm.enabled", False)
    fo.set_preference("media.gmp-widevinecdm.visible", False)
    fo.set_preference("media.gmp-gmpopenh264.enabled", False)

    # Disable pinging Mozilla for newtab
    fo.set_preference("browser.newtabpage.enabled", False)

    # Disable Pocket
    fo.set_preference("extensions.pocket.enabled", False)

    # Disable Shield / Normandy studies
    fo.set_preference("app.shield.optoutstudies.enabled", False)

    # Disable Source Pragmas
    # As per https://bugzilla.mozilla.org/show_bug.cgi?id=1628853
    # sourceURL can be used to obfuscate the original origin of
    # a script, we disable it.
    fo.set_preference("javascript.options.source_pragmas", False)

    # Enable extensions and disable extension signing
    fo.set_preference("extensions.experiments.enabled", True)
    fo.set_preference("xpinstall.signatures.required", False)
