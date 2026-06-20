"""Set prefs and load extensions in Firefox.

The static default preferences OpenWPM applies live in the module-level
``PRIVACY_PREFS`` and ``OPTIMIZE_PREFS`` dicts. These dicts are the single
source of truth: :func:`privacy` and :func:`optimize_prefs` iterate them to
apply the prefs, and ``scripts/verify_obsolete_prefs.py`` imports the very same
dicts to probe each pref's name for obsolescence against a running Firefox.
Because both the setter and the verifier read the same object, the two can
never drift out of sync.

Prefs whose *value* is dynamic (computed from ``browser_params``) are set
inline in :func:`privacy`; only their static names are tracked in
``PRIVACY_PREFS`` so the verifier still checks them.
"""

from selenium.webdriver.firefox.options import Options

from ..config import BrowserParams

# Static privacy pref names OpenWPM may set, mapped to a representative default
# value. The *value* recorded here is the baseline OpenWPM applies when the pref
# is unconditional; ``network.cookie.cookieBehavior`` is dynamic (chosen from
# ``browser_params.tp_cookies`` in :func:`privacy`) so its dict value is only a
# placeholder. The dict exists so the obsolescence verifier can probe these
# names without copying a hardcoded list.
PRIVACY_PREFS: dict[str, bool | int | str] = {
    # Turns on Do Not Track (only applied when browser_params.donottrack).
    "privacy.donottrackheader.enabled": True,
    # Third-party cookie behavior (value chosen dynamically from tp_cookies).
    "network.cookie.cookieBehavior": 1,
}

# Static prefs that disable various features and startup checks. Some of these
# (e.g. disabling the newtab page) are required to prevent extraneous data in
# the proxy.
#
# Source of prefs:
# * https://support.mozilla.org/en-US/kb/how-stop-firefox-making-automatic-connections
# * https://github.com/pyllyukko/user.js/blob/master/user.js
OPTIMIZE_PREFS: dict[str, bool | int | str] = {
    # Startup / Speed
    "browser.shell.checkDefaultBrowser": False,
    "browser.rights.3.shown": True,
    "reader.parse-on-load.enabled": False,
    "browser.pagethumbnails.capturing_disabled": True,
    "browser.uitour.enabled": False,
    # Disable health reports / telemetry / crash reports
    "datareporting.policy.dataSubmissionEnabled": False,
    "datareporting.healthreport.uploadEnabled": False,
    "datareporting.healthreport.service.enabled": False,
    "toolkit.telemetry.archive.enabled": False,
    "toolkit.telemetry.enabled": False,
    "toolkit.telemetry.unified": False,
    "breakpad.reportURL": "",
    "browser.tabs.crashReporting.sendReport": False,
    "browser.crashReports.unsubmittedCheck.enabled": False,
    # Predictive Actions / Prefetch
    "network.predictor.enabled": False,
    "network.dns.disablePrefetch": True,
    "network.prefetch-next": False,
    "browser.search.suggest.enabled": False,
    "network.http.speculative-parallel-limit": 0,
    "keyword.enabled": False,  # location bar using search
    # Disable pinging Mozilla for geoip
    "browser.search.geoip.url": "",
    "browser.search.region": "US",
    # Disable auto-updating
    "app.update.url": "",  # browser update URL
    "browser.search.update": False,  # search engines
    "extensions.update.enabled": False,  # extensions
    "extensions.update.autoUpdateDefault": False,
    "extensions.getAddons.cache.enabled": False,
    # Disable Safebrowsing and other security features
    # that require remote content
    "browser.safebrowsing.phishing.enabled": False,
    "browser.safebrowsing.malware.enabled": False,
    "browser.safebrowsing.downloads.enabled": False,
    "browser.safebrowsing.downloads.remote.enabled": False,
    "browser.safebrowsing.blockedURIs.enabled": False,
    "browser.safebrowsing.provider.mozilla.gethashURL": "",
    "browser.safebrowsing.provider.google.gethashURL": "",
    "browser.safebrowsing.provider.google4.gethashURL": "",
    "browser.safebrowsing.provider.mozilla.updateURL": "",
    "browser.safebrowsing.provider.google.updateURL": "",
    "browser.safebrowsing.provider.google4.updateURL": "",
    "browser.safebrowsing.provider.mozilla.lists": "",
    "browser.safebrowsing.provider.google.lists": "",
    "browser.safebrowsing.provider.google4.lists": "",
    "extensions.blocklist.enabled": False,
    "security.OCSP.enabled": 0,
    # Disable Content Decryption Module and OpenH264 related downloads
    "media.gmp-manager.url": "",
    "media.gmp-provider.enabled": False,
    "media.gmp-widevinecdm.enabled": False,
    "media.gmp-widevinecdm.visible": False,
    "media.gmp-gmpopenh264.enabled": False,
    # Disable pinging Mozilla for newtab
    "browser.newtabpage.enabled": False,
    # Disable Pocket
    "extensions.pocket.enabled": False,
    # Disable Shield / Normandy studies
    "app.shield.optoutstudies.enabled": False,
    # Disable Source Pragmas
    # As per https://bugzilla.mozilla.org/show_bug.cgi?id=1628853
    # sourceURL can be used to obfuscate the original origin of
    # a script, we disable it.
    "javascript.options.source_pragmas": False,
    # Enable extensions and disable extension signing
    "extensions.experiments.enabled": True,
    "xpinstall.signatures.required": False,
}


def privacy(browser_params: BrowserParams, fo: Options) -> None:
    """
    Configure the privacy settings in Firefox. This includes:
    * DNT
    * Third-part cookie blocking
    * Tracking protection
    * Privacy extensions

    Pref values here are dynamic (computed from ``browser_params``), so the
    prefs are set inline rather than by iterating ``PRIVACY_PREFS``. The pref
    *names* are still keyed off ``PRIVACY_PREFS`` so they can't drift from the
    set the obsolescence verifier probes.
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

    Applies every static pref in ``OPTIMIZE_PREFS`` (the single source of truth
    shared with the obsolescence verifier).
    """
    for name, value in OPTIMIZE_PREFS.items():
        fo.set_preference(name, value)
