"""The default prefs OpenWPM applies, and where they are allowed to come from."""

import ast
import itertools
from pathlib import Path

import pytest
from selenium.webdriver.firefox.options import Options

from openwpm.config import BrowserParams
from openwpm.deploy_browsers import configure_firefox

pytestmark = pytest.mark.pyonly

# Snapshot of what optimize_prefs() (plus the subscript-load opt-in that used to
# live in deploy_firefox.py) applied before the prefs moved into dicts. Order
# matters: browser_params.prefs are applied afterwards and must win.
EXPECTED_OPTIMIZE = [
    ("browser.shell.checkDefaultBrowser", False),
    ("reader.parse-on-load.enabled", False),
    ("browser.pagethumbnails.capturing_disabled", True),
    ("browser.uitour.enabled", False),
    ("datareporting.policy.dataSubmissionEnabled", False),
    ("datareporting.healthreport.uploadEnabled", False),
    ("toolkit.telemetry.archive.enabled", False),
    ("toolkit.telemetry.enabled", False),
    ("toolkit.telemetry.unified", False),
    ("breakpad.reportURL", ""),
    ("browser.tabs.crashReporting.sendReport", False),
    ("browser.crashReports.unsubmittedCheck.enabled", False),
    ("network.dns.disablePrefetch", True),
    ("network.prefetch-next", False),
    ("browser.search.suggest.enabled", False),
    ("network.http.speculative-parallel-limit", 0),
    ("keyword.enabled", False),
    ("browser.search.region", "US"),
    ("app.update.disabledForTesting", True),
    ("browser.search.update", False),
    ("extensions.update.enabled", False),
    ("extensions.update.autoUpdateDefault", False),
    ("extensions.getAddons.cache.enabled", False),
    ("browser.safebrowsing.phishing.enabled", False),
    ("browser.safebrowsing.malware.enabled", False),
    ("browser.safebrowsing.downloads.enabled", False),
    ("browser.safebrowsing.downloads.remote.enabled", False),
    ("browser.safebrowsing.blockedURIs.enabled", False),
    ("browser.safebrowsing.update.enabled", False),
    ("browser.safebrowsing.provider.mozilla.gethashURL", ""),
    ("browser.safebrowsing.provider.google.gethashURL", ""),
    ("browser.safebrowsing.provider.google4.gethashURL", ""),
    ("browser.safebrowsing.provider.mozilla.updateURL", ""),
    ("browser.safebrowsing.provider.google.updateURL", ""),
    ("browser.safebrowsing.provider.google4.updateURL", ""),
    ("browser.safebrowsing.provider.mozilla.lists", ""),
    ("browser.safebrowsing.provider.google.lists", ""),
    ("browser.safebrowsing.provider.google4.lists", ""),
    ("browser.safebrowsing.provider.google5.lists", ""),
    ("extensions.blocklist.enabled", False),
    ("security.OCSP.enabled", 0),
    ("media.gmp-manager.url", ""),
    ("media.gmp-provider.enabled", False),
    ("media.gmp-widevinecdm.enabled", False),
    ("media.gmp-widevinecdm.visible", False),
    ("media.gmp-gmpopenh264.enabled", False),
    ("browser.newtabpage.enabled", False),
    ("app.shield.optoutstudies.enabled", False),
    ("app.normandy.enabled", False),
    ("javascript.options.source_pragmas", False),
    ("extensions.experiments.enabled", True),
    ("xpinstall.signatures.required", False),
    ("security.allow_unsafe_subscript_loads", True),
]

COOKIE_BEHAVIOR = {"never": 1, "from_visited": 3, "always": 0, "NEVER": 1, "bogus": 0}


class RecordingOptions(Options):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, object]] = []

    def set_preference(self, name, value):
        self.calls.append((name, value))
        super().set_preference(name, value)


@pytest.mark.parametrize(
    "donottrack,tp_cookies,tracking_protection",
    list(itertools.product([False, True], COOKIE_BEHAVIOR, [False, True])),
)
def test_applied_prefs_match_snapshot(donottrack, tp_cookies, tracking_protection):
    bp = BrowserParams(
        donottrack=donottrack,
        tp_cookies=tp_cookies,
        tracking_protection=tracking_protection,
    )
    expected = [("privacy.donottrackheader.enabled", True)] if donottrack else []
    expected.append(("network.cookie.cookieBehavior", COOKIE_BEHAVIOR[tp_cookies]))

    fo = RecordingOptions()
    if tracking_protection:
        with pytest.raises(RuntimeError):
            configure_firefox.privacy(bp, fo)
        assert fo.calls == expected
        return
    configure_firefox.privacy(bp, fo)
    configure_firefox.optimize_prefs(fo)
    assert fo.calls == expected + EXPECTED_OPTIMIZE


def test_no_pref_set_outside_the_dicts():
    """Every default pref must be a dict key, or the obsolescence verifier
    (scripts/verify_obsolete_prefs.py) cannot see it."""
    package = Path(configure_firefox.__file__).resolve().parent.parent
    offenders = []
    for path in package.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(), str(path))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "set_preference"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                offenders.append(f"{path}:{node.lineno}")
    assert offenders == []
