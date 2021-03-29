""" Set prefs and load extensions in Firefox """

import json
import re
from pathlib import Path
from typing import Any, Dict

from ..config import BrowserParams

# TODO: Remove hardcoded geckodriver default preferences. See
# https://github.com/mozilla/OpenWPM/issues/867
# Source of preferences:
# https://hg.mozilla.org/mozilla-central/file/tip/testing/geckodriver/src/prefs.rs
# https://hg.mozilla.org/mozilla-central/file/tip/testing/geckodriver/src/marionette.rs
DEFAULT_GECKODRIVER_PREFS = {
    "app.normandy.api_url": "",
    "app.update.checkInstallTime": False,
    "app.update.disabledForTesting": True,
    "app.update.auto": False,
    "browser.dom.window.dump.enabled": True,
    "devtools.console.stdout.chrome": True,
    "browser.safebrowsing.blockedURIs.enabled": False,
    "browser.safebrowsing.downloads.enabled": False,
    "browser.safebrowsing.passwords.enabled": False,
    "browser.safebrowsing.malware.enabled": False,
    "browser.safebrowsing.phishing.enabled": False,
    "browser.sessionstore.resume_from_crash": False,
    "browser.shell.checkDefaultBrowser": False,
    "browser.startup.homepage_override.mstone": "ignore",
    "browser.startup.page": 0,
    "browser.tabs.closeWindowWithLastTab": False,
    "browser.tabs.warnOnClose": False,
    "browser.uitour.enabled": False,
    "browser.warnOnQuit": False,
    "datareporting.healthreport.documentServerURI": "http://%(server)s/dummy/healthreport/",
    "datareporting.healthreport.logging.consoleEnabled": False,
    "datareporting.healthreport.service.enabled": False,
    "datareporting.healthreport.service.firstRun": False,
    "datareporting.healthreport.uploadEnabled": False,
    "datareporting.policy.dataSubmissionEnabled": False,
    "datareporting.policy.dataSubmissionPolicyBypassNotification": True,
    "dom.ipc.reportProcessHangs": False,
    "extensions.autoDisableScopes": 0,
    "extensions.enabledScopes": 5,
    "extensions.installDistroAddons": False,
    "extensions.update.enabled": False,
    "extensions.update.notifyUser": False,
    "focusmanager.testmode": True,
    "general.useragent.updates.enabled": False,
    "geo.provider.testing": True,
    "geo.wifi.scan": False,
    "hangmonitor.timeout": 0,
    "idle.lastDailyNotification": -1,
    "javascript.options.showInConsole": True,
    "media.gmp-manager.updateEnabled": False,
    "media.sanity-test.disabled": True,
    "network.http.phishy-userpass-length": 255,
    "network.manage-offline-status": False,
    "network.sntp.pools": "%(server)s",
    "plugin.state.flash": 0,
    "security.certerrors.mitm.priming.enabled": False,
    "services.settings.server": "http://%(server)s/dummy/blocklist/",
    "startup.homepage_welcome_url": "about:blank",
    "startup.homepage_welcome_url.additional": "",
    "toolkit.startup.max_resumed_crashes": -1,
    "marionette.log.level": "Info",
}


def load_existing_prefs(browser_profile_path: Path) -> Dict[str, Any]:
    """Load existing user preferences.

    If the browser profile contains a user.js file, load the preferences
    specified inside it into a dictionary.
    """
    prefs: Dict[str, Any] = {}
    prefs_path = browser_profile_path / "user.js"
    if not prefs_path.is_file():
        return prefs
    # Regular expression from https://stackoverflow.com/a/24563687
    r = re.compile(r"\s*user_pref\(([\"'])(.+?)\1,\s*(.+?)\);")
    with open(prefs_path, "r") as f:
        for line in f:
            m = r.match(line)
            if m:
                key, value = m.group(2), m.group(3)
                prefs[key] = json.loads(value)
    return prefs


def save_prefs_to_profile(prefs: Dict[str, Any], browser_profile_path: Path) -> None:
    """Save all preferences to the browser profile.

    Write preferences from the prefs dictionary to a user.js file in the
    profile directory.
    """
    with open(browser_profile_path / "user.js", "w") as f:
        for key, value in prefs.items():
            f.write('user_pref("%s", %s);\n' % (key, json.dumps(value)))


def privacy(browser_params: BrowserParams, prefs: Dict[str, Any]) -> None:
    """
    Configure the privacy settings in Firefox. This includes:
    * DNT
    * Third-part cookie blocking
    * Tracking protection
    * Privacy extensions
    """

    # Turns on Do Not Track
    if browser_params.donottrack:
        prefs["privacy.donottrackheader.enabled"] = True

    # Sets the third party cookie setting
    if browser_params.tp_cookies.lower() == "never":
        prefs["network.cookie.cookieBehavior"] = 1
    elif browser_params.tp_cookies.lower() == "from_visited":
        prefs["network.cookie.cookieBehavior"] = 3
    else:  # always allow third party cookies
        prefs["network.cookie.cookieBehavior"] = 0

    # Tracking Protection
    if browser_params.tracking_protection:
        raise RuntimeError(
            "Firefox Tracking Protection is not currently "
            "supported. See: "
            "https://github.com/citp/OpenWPM/issues/101"
        )


def optimize_prefs(prefs: Dict[str, Any]) -> None:
    """
    Disable various features and checks the browser will do on startup.
    Some of these (e.g. disabling the newtab page) are required to prevent
    extraneous data in the proxy.

    Source of prefs:
    * https://support.mozilla.org/en-US/kb/how-stop-firefox-making-automatic-connections
    * https://github.com/pyllyukko/user.js/blob/master/user.js
    """  # noqa
    # Startup / Speed
    prefs["browser.shell.checkDefaultBrowser"] = False
    prefs["browser.slowStartup.notificationDisabled"] = True
    prefs["browser.slowStartup.maxSamples"] = 0
    prefs["browser.slowStartup.samples"] = 0
    prefs["extensions.checkCompatibility.nightly"] = False
    prefs["browser.rights.3.shown"] = True
    prefs["reader.parse-on-load.enabled"] = False
    prefs["browser.pagethumbnails.capturing_disabled"] = True
    prefs["browser.uitour.enabled"] = False
    prefs["dom.flyweb.enabled"] = False

    # Disable health reports / telemetry / crash reports
    prefs["datareporting.policy.dataSubmissionEnabled"] = False
    prefs["datareporting.healthreport.uploadEnabled"] = False
    prefs["datareporting.healthreport.service.enabled"] = False
    prefs["toolkit.telemetry.archive.enabled"] = False
    prefs["toolkit.telemetry.enabled"] = False
    prefs["toolkit.telemetry.unified"] = False
    prefs["breakpad.reportURL"] = ""
    prefs["dom.ipc.plugins.reportCrashURL"] = False
    prefs["browser.selfsupport.url"] = ""
    prefs["browser.tabs.crashReporting.sendReport"] = False
    prefs["browser.crashReports.unsubmittedCheck.enabled"] = False
    prefs["dom.ipc.plugins.flash.subprocess.crashreporter.enabled"] = False

    # Predictive Actions / Prefetch
    prefs["network.predictor.enabled"] = False
    prefs["network.dns.disablePrefetch"] = True
    prefs["network.prefetch-next"] = False
    prefs["browser.search.suggest.enabled"] = False
    prefs["network.http.speculative-parallel-limit"] = 0
    prefs["keyword.enabled"] = False  # location bar using search
    prefs["browser.urlbar.userMadeSearchSuggestionsChoice"] = True
    prefs["browser.casting.enabled"] = False

    # Disable pinging Mozilla for geoip
    prefs["browser.search.geoip.url"] = ""
    prefs["browser.search.countryCode"] = "US"
    prefs["browser.search.region"] = "US"

    # Disable pinging Mozilla for geo-specific search
    prefs["browser.search.geoSpecificDefaults"] = False
    prefs["browser.search.geoSpecificDefaults.url"] = ""

    # Disable auto-updating
    prefs["app.update.enabled"] = False  # browser
    prefs["app.update.url"] = ""  # browser
    prefs["browser.search.update"] = False  # search
    prefs["extensions.update.enabled"] = False  # extensions
    prefs["extensions.update.autoUpdateDefault"] = False
    prefs["extensions.getAddons.cache.enabled"] = False
    prefs["lightweightThemes.update.enabled"] = False  # Personas

    # Disable Safebrowsing and other security features
    # that require on remote content
    prefs["browser.safebrowsing.phising.enabled"] = False
    prefs["browser.safebrowsing.malware.enabled"] = False
    prefs["browser.safebrowsing.downloads.enabled"] = False
    prefs["browser.safebrowsing.downloads.remote.enabled"] = False
    prefs["browser.safebrowsing.blockedURIs.enabled"] = False
    prefs["browser.safebrowsing.provider.mozilla.gethashURL"] = ""
    prefs["browser.safebrowsing.provider.google.gethashURL"] = ""
    prefs["browser.safebrowsing.provider.google4.gethashURL"] = ""
    prefs["browser.safebrowsing.provider.mozilla.updateURL"] = ""
    prefs["browser.safebrowsing.provider.google.updateURL"] = ""
    prefs["browser.safebrowsing.provider.google4.updateURL"] = ""
    prefs["browser.safebrowsing.provider.mozilla.lists"] = ""  # TP
    prefs["browser.safebrowsing.provider.google.lists"] = ""  # TP
    prefs["browser.safebrowsing.provider.google4.lists"] = ""  # TP
    prefs["extensions.blocklist.enabled"] = False  # extensions
    prefs["security.OCSP.enabled"] = 0

    # Disable Content Decryption Module and OpenH264 related downloads
    prefs["media.gmp-manager.url"] = ""
    prefs["media.gmp-provider.enabled"] = False
    prefs["media.gmp-widevinecdm.enabled"] = False
    prefs["media.gmp-widevinecdm.visible"] = False
    prefs["media.gmp-gmpopenh264.enabled"] = False

    # Disable Experiments
    prefs["experiments.enabled"] = False
    prefs["experiments.manifest.uri"] = ""
    prefs["experiments.supported"] = False
    prefs["experiments.activeExperiment"] = False
    prefs["network.allow-experiments"] = False

    # Disable pinging Mozilla for newtab
    prefs["browser.newtabpage.directory.ping"] = ""
    prefs["browser.newtabpage.directory.source"] = ""
    prefs["browser.newtabpage.enabled"] = False
    prefs["browser.newtabpage.enhanced"] = False
    prefs["browser.newtabpage.introShown"] = True
    prefs["browser.aboutHomeSnippets.updateUrl"] = ""

    # Disable Pocket
    prefs["extensions.pocket.enabled"] = False

    # Disable Shield
    prefs["app.shield.optoutstudies.enabled"] = False
    prefs["extensions.shield-recipe-client.enabled"] = False

    # Disable Source Pragmas
    # As per https://bugzilla.mozilla.org/show_bug.cgi?id=1628853
    # sourceURL can be used to obfuscate the original origin of
    # a script, we disable it.
    prefs["javascript.options.source_pragmas"] = False

    # Enable extensions and disable extension signing
    prefs["extensions.experiments.enabled"] = True
    prefs["xpinstall.signatures.required"] = False
