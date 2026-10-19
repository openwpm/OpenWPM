"""Set prefs and load extensions in Firefox.

Every pref OpenWPM sets by default is a key of ``PRIVACY_PREFS`` or
``OPTIMIZE_PREFS``; nothing else calls ``set_preference`` with a literal name.
``scripts/verify_obsolete_prefs.py`` probes the keys of both dicts against the
pinned Firefox. User-supplied ``browser_params.prefs`` are not covered.
"""

from collections.abc import Callable

from selenium.webdriver.firefox.options import Options

from ..config import BrowserParams

PrefValue = bool | int | str

# browser_params.tp_cookies -> network.cookie.cookieBehavior; anything else
# allows all third-party cookies.
_TP_COOKIES_BEHAVIOR = {"never": 1, "from_visited": 3}

# Prefs whose value depends on browser_params. A getter returning None leaves
# the pref unset.
PRIVACY_PREFS: dict[str, Callable[[BrowserParams], PrefValue | None]] = {
    "privacy.donottrackheader.enabled": lambda bp: True if bp.donottrack else None,
    "network.cookie.cookieBehavior": lambda bp: _TP_COOKIES_BEHAVIOR.get(
        bp.tp_cookies.lower(), 0
    ),
}

# Disable various features and checks the browser will do on startup. Some of
# these (e.g. disabling the newtab page) are required to prevent extraneous
# data in the proxy.
#
# Source of prefs:
# * https://support.mozilla.org/en-US/kb/how-stop-firefox-making-automatic-connections
# * https://github.com/pyllyukko/user.js/blob/master/user.js
OPTIMIZE_PREFS: dict[str, PrefValue] = {
    # Startup / Speed
    "browser.shell.checkDefaultBrowser": False,
    "reader.parse-on-load.enabled": False,
    "browser.pagethumbnails.capturing_disabled": True,
    "browser.uitour.enabled": False,
    # Disable health reports / telemetry / crash reports
    "datareporting.policy.dataSubmissionEnabled": False,
    "datareporting.healthreport.uploadEnabled": False,
    "toolkit.telemetry.archive.enabled": False,
    "toolkit.telemetry.enabled": False,
    "toolkit.telemetry.unified": False,
    "breakpad.reportURL": "",
    "browser.tabs.crashReporting.sendReport": False,
    "browser.crashReports.unsubmittedCheck.enabled": False,
    # Predictive Actions / Prefetch
    "network.dns.disablePrefetch": True,
    "network.prefetch-next": False,
    "browser.search.suggest.enabled": False,
    "network.http.speculative-parallel-limit": 0,
    "keyword.enabled": False,  # location bar using search
    # Disable pinging Mozilla for geoip
    "browser.search.region": "US",
    # Disable auto-updating
    # Honored only under remote control, which OpenWPM always is. geckodriver
    # sets it too, but Firefox expects the client to set it in the profile.
    "app.update.disabledForTesting": True,  # browser
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
    # Stops list updates for every provider; no default, read with fallback true
    "browser.safebrowsing.update.enabled": False,
    "browser.safebrowsing.provider.mozilla.gethashURL": "",
    "browser.safebrowsing.provider.google.gethashURL": "",
    "browser.safebrowsing.provider.google4.gethashURL": "",
    "browser.safebrowsing.provider.mozilla.updateURL": "",
    "browser.safebrowsing.provider.google.updateURL": "",
    "browser.safebrowsing.provider.google4.updateURL": "",
    "browser.safebrowsing.provider.mozilla.lists": "",
    "browser.safebrowsing.provider.google.lists": "",
    "browser.safebrowsing.provider.google4.lists": "",
    # google5 (on by default) takes the goog-* tables over from google4
    "browser.safebrowsing.provider.google5.lists": "",
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
    # Disable Shield / Normandy studies
    "app.shield.optoutstudies.enabled": False,
    "app.normandy.enabled": False,
    # Disable Source Pragmas
    # As per https://bugzilla.mozilla.org/show_bug.cgi?id=1628853
    # sourceURL can be used to obfuscate the original origin of
    # a script, we disable it.
    "javascript.options.source_pragmas": False,
    # Enable extensions and disable extension signing
    "extensions.experiments.enabled": True,
    "xpinstall.signatures.required": False,
    # Firefox 155 gates file:, jar: and moz-extension: subscript loads behind
    # an opt-in (mozJSSubScriptLoader's CheckAllowedURI). Our WebExtension
    # experiment APIs under Extension/bundled/privileged are loaded from a
    # jar:file: URL, so without this the API scripts never run: the extension
    # installs, its startup throws, and extension_port.txt is never written.
    # Mozilla tracks removing the need for this in bug 1976115.
    "security.allow_unsafe_subscript_loads": True,
}


def privacy(browser_params: BrowserParams, fo: Options) -> None:
    """
    Configure the privacy settings in Firefox. This includes:
    * DNT
    * Third-part cookie blocking
    * Tracking protection
    * Privacy extensions
    """
    for name, value_for in PRIVACY_PREFS.items():
        value = value_for(browser_params)
        if value is not None:
            fo.set_preference(name, value)

    # Tracking Protection
    if browser_params.tracking_protection:
        raise RuntimeError(
            "Firefox Tracking Protection is not currently "
            "supported. See: "
            "https://github.com/citp/OpenWPM/issues/101"
        )


def optimize_prefs(fo: Options) -> None:
    """Disable various features and checks the browser will do on startup."""
    for name, value in OPTIMIZE_PREFS.items():
        fo.set_preference(name, value)
