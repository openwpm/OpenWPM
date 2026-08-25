"""Can off-the-shelf bot detection tell OpenWPM's instruments apart?

``test_fingerprintjs_stamp.py`` covers a commodity *fingerprinter*, which reads
values. Bot detectors additionally run INTEGRITY checks (is this function
native? does the prototype look right? is ``navigator.webdriver`` set? do the
iframe, the worker and the main realm agree?). This module measures two
vendored, hash-pinned OSS bot detectors in the same page load:

``@fingerprintjs/botd`` 2.0.0
    18 named detectors over 23 sources, plus one aggregate verdict.
``fpscanner`` 1.0.8
    21 named rules, each ``{detected, severity}``, over its raw signals, plus
    one aggregate.

Five arms, each compared against a reference that isolates one component:

``plain``
    Stock Firefox driven by bare Selenium: no OpenWPM, no extension, no OpenWPM
    preferences. Separates Selenium tells from OpenWPM tells.
``baseline``
    OpenWPM, ``js_instrument=False``, ``stealth_js_instrument=False``.
``legacy``
    OpenWPM, ``js_instrument=True``, ``js_instrument_settings=["collection_fingerprinting"]``
    (the project's standard preset and the ``BrowserParams`` default).
``stealth_bare``
    OpenWPM, ``stealth_js_instrument=True`` with the bundled default surface
    (``Extension/src/stealth/settings.ts``) MINUS its ``navigator.webdriver``
    override: the stealth instrument on its own, configured through
    ``stealth_js_instrument_settings``.
``stealth``
    OpenWPM, ``stealth_js_instrument=True`` with the bundled default surface as
    shipped, i.e. ``stealth_bare`` plus the webdriver override.

``navigator.webdriver`` is compared against what each arm CONFIGURES rather
than a hardcoded value: bare Selenium exposes it and the stealth override hides
it. An OpenWPM-level ``spoof_webdriver`` switch, where ``BrowserParams`` has
one, is pinned off so it cannot mask the override. Signals that are views of
that one property are measured as the override's footprint (``stealth`` vs
``stealth_bare``) and excluded from every other cross-arm comparison, which then
covers everything else.

**Timezone.** Every arm runs with ``TZ`` pinned to :data:`PINNED_TZ`. Firefox
otherwise inherits the host zone, and fpscanner's ``hasUTCTimezone`` rule would
make the aggregate verdict depend on the machine the test runs on.

**Validity gate.** Every arm runs twice, and only signals that reproduce within
every arm are compared. A key present in some arms but not others (e.g. a
collector that throws and collapses a subtree into ``"ERROR"``) is compared as
:data:`ABSENT`, so a schema change counts as a difference, not as noise.

All browser assertions live in ONE test on purpose: CI shards by test with
pytest-split, and separate tests would each relaunch every arm on a different
shard, with the gate checking a different sample from the verdicts.

``manager_params.testing`` is **False**: with ``testing=True`` the legacy page
script additionally publishes ``window.instrumentJS``, a harness artifact a real
crawl does not have.

See ``docs/developers/Bot-Detector-Visibility-Experiment.md`` for the recorded
measurement.
"""

import copy
import hashlib
import json
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pytest
from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams, ManagerParamsInternal
from openwpm.socket_interface import ClientSocket
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_providers import TableName
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils
from openwpm.utilities.platform_utils import get_firefox_binary_path

from .utilities import ServerUrls

PROBE_PAGE = "/bot_detection.html"

# Vendored oracles. Pinned so a silently swapped bundle fails loudly rather than
# quietly changing what "the detector said no" means. See test_pages/vendor/README.md
# for provenance; both files are byte-identical to the published npm artifacts.
VENDOR_DIR = Path(__file__).parent / "test_pages" / "vendor"
VENDORED_BUNDLES = {
    # @fingerprintjs/botd@2.0.0, package/dist/botd.esm.js (MIT)
    "botd-2.0.0.esm.js": (
        "f438ed251dc7414ece9d4a2b6941441ad9ffae1a1905817f5f0c7366e701dd86"
    ),
    # fpscanner@1.0.8, package/dist/fpScanner.es.js (MIT)
    "fpscanner-1.0.8.es.js": (
        "75abba497a00625ed053ce7a0bc9353fa5d5c9859cc67438141fe83d8d0946b2"
    ),
}

STEALTH_SETTINGS_TS = (
    Path(__file__).parent.parent / "Extension" / "src" / "stealth" / "settings.ts"
)

# Any fixed non-UTC zone works; it only has to be the same for every arm and
# independent of the host.
PINNED_TZ = "Europe/Berlin"

# Custom table the probe page's JSON report is routed into. Commands run in a
# subprocess and the StorageController in yet another, so the on-disk crawl
# SQLite DB is the only reliable cross-process channel (the idiom used by
# test_custom_function_command.py and test_fingerprintjs_stamp.py). Created
# per-crawl in the test's temp DB, so it never touches schema.sql /
# parquet_schema.py.
BOT_RESULTS_TABLE = TableName("bot_detection_results")

# fpscanner spins up a Web Worker and an iframe and waits on both; BotD waits on
# the Notifications permission query. 10s is not enough headroom on a loaded CI
# box.
PROBE_TIMEOUT_SECONDS = 90


def _page_url(server: ServerUrls, page: str) -> str:
    """Build a full probe-page URL from the dynamic test server base."""
    return server.base + page


# --------------------------------------------------------------------------- #
# Config helpers -- one per OpenWPM arm. Everything except the instrument
# switches is held identical.
# --------------------------------------------------------------------------- #
def _bundled_stealth_settings() -> List[Dict[str, Any]]:
    """The stealth instrument's bundled default surface, read from settings.ts.

    The file is a single JSON-shaped object literal; stripping comments, quoting
    keys and dropping trailing commas makes it JSON. OpenWPM validates the result
    against the settings schema at launch, so a misparse fails loudly.
    """
    source = STEALTH_SETTINGS_TS.read_text()
    literal = source[source.index("= [") + 2 : source.rindex("]") + 1]
    literal = re.sub(r"//[^\n]*", "", literal)
    literal = re.sub(r"(\w+):", r'"\1":', literal)
    literal = re.sub(r",(\s*[\]}])", r"\1", literal)
    settings: List[Dict[str, Any]] = json.loads(literal)
    return settings


def _hides_webdriver(settings: List[Dict[str, Any]]) -> bool:
    return any(
        override["key"] == "webdriver" and override["value"] is False
        for entry in settings
        for override in entry["logSettings"]["overwrittenProperties"]
    )


def _without_webdriver_override(
    settings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    settings = copy.deepcopy(settings)
    for entry in settings:
        log_settings = entry["logSettings"]
        log_settings["overwrittenProperties"] = [
            o for o in log_settings["overwrittenProperties"] if o["key"] != "webdriver"
        ]
    return settings


def _base_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params = ManagerParams(num_browsers=1)
    browser_params = [BrowserParams()]
    manager_params.data_directory = data_dir
    manager_params.log_path = data_dir / "openwpm.log"
    manager_params.testing = False
    browser_params[0].display_mode = "headless"
    # An OpenWPM-wide webdriver spoof would hide navigator.webdriver in every
    # arm and erase the override's footprint this module measures.
    if "spoof_webdriver" in BrowserParams.__dataclass_fields__:
        setattr(browser_params[0], "spoof_webdriver", False)
    return manager_params, browser_params


def _baseline_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].js_instrument = False
    browser_params[0].stealth_js_instrument = False
    return manager_params, browser_params


def _legacy_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].stealth_js_instrument = False
    browser_params[0].js_instrument = True
    browser_params[0].js_instrument_settings = ["collection_fingerprinting"]
    return manager_params, browser_params


def _stealth_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].js_instrument = False
    browser_params[0].stealth_js_instrument = True
    return manager_params, browser_params


def _stealth_bare_params(
    data_dir: Path,
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = _without_webdriver_override(
        _bundled_stealth_settings()
    )
    return manager_params, browser_params


def _exposes_webdriver(browser_params: BrowserParams) -> bool:
    """Whether this configuration leaves ``navigator.webdriver`` true."""
    if getattr(browser_params, "spoof_webdriver", False):
        return False
    if browser_params.stealth_js_instrument:
        settings = browser_params.stealth_js_instrument_settings
        return not _hides_webdriver(
            settings if settings is not None else _bundled_stealth_settings()
        )
    return True


# --------------------------------------------------------------------------- #
# Crawl helpers
# --------------------------------------------------------------------------- #
class ReadBotResults(BaseCommand):
    """Scrape the probe page's ``data-results`` JSON and ship it to storage.

    Opens its OWN ``ClientSocket`` to the storage controller (NOT
    ``extension_socket``, which talks to the extension's port), mirroring
    ``test_custom_function_command.py::test_custom_function``.
    """

    def __repr__(self) -> str:
        return "ReadBotResults"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        results_json = _scrape_results(webdriver)
        sock = ClientSocket()
        assert manager_params.storage_controller_address is not None
        sock.connect(*manager_params.storage_controller_address)
        sock.send("bot_detection")
        sock.send(
            (
                BOT_RESULTS_TABLE,
                {
                    "browser_id": self.browser_id,
                    "visit_id": self.visit_id,
                    "results": results_json or "{}",
                },
            )
        )
        sock.close()


def _scrape_results(driver: Firefox) -> str:
    """Wait for the probe page to publish, then read its report back."""
    WebDriverWait(driver, PROBE_TIMEOUT_SECONDS).until(
        lambda d: d.find_element("id", "results").get_attribute("data-results")
    )
    return driver.execute_script(
        "return document.getElementById('results').getAttribute('data-results');"
    )


def _create_results_table(db_path: Path) -> None:
    """Create the custom results table BEFORE the manager launches.

    SQLiteStorageProvider INSERTs into a table named in the incoming record and
    does not create it, so it has to exist on disk first.
    """
    db = sqlite3.connect(db_path)
    cur = db.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS %s ("
        "  browser_id INTEGER, visit_id INTEGER, results TEXT);" % BOT_RESULTS_TABLE
    )
    db.commit()
    cur.close()
    db.close()


def _read_results(db_path: Path) -> Dict:
    rows = db_utils.query_db(
        db_path,
        f"SELECT results FROM {BOT_RESULTS_TABLE} ORDER BY rowid;",
        as_tuple=True,
    )
    if not rows:
        return {}
    return json.loads(rows[-1][0])


def _javascript_capture(db_path: Path) -> Dict[str, object]:
    """How many JS API calls the arm actually recorded, and on which symbols.

    This is the arm's ACTIVITY CONTROL. Without it, "no detector could tell the
    arms apart" has a trivial and wrong explanation: the instrument never
    attached. An arm that claims to instrument must show captured rows on the
    surfaces the probe page touches; the baseline arm must show none.
    """
    try:
        rows = db_utils.query_db(
            db_path,
            "SELECT symbol, COUNT(*) FROM javascript GROUP BY symbol;",
            as_tuple=True,
        )
    except sqlite3.OperationalError:
        # No `javascript` table at all -- neither instrument ran.
        return {"rows": 0, "symbols": []}
    return {
        "rows": sum(count for _, count in rows),
        "symbols": sorted(symbol for symbol, _ in rows),
    }


def collect_openwpm(
    params: Tuple[ManagerParams, List[BrowserParams]], url: str
) -> Dict:
    """Run one OpenWPM arm once and return the probe page's report.

    The returned dict carries two extra keys not produced by the page:
    ``_capture``, the arm's JavaScript-capture activity control, and
    ``_webdriver_exposed``, what the arm's configuration implies for
    ``navigator.webdriver``.
    """
    manager_params, browser_params = params
    db_path = manager_params.data_directory / "crawl-data.sqlite"
    _create_results_table(db_path)
    manager = TaskManager(
        manager_params, browser_params, SQLiteStorageProvider(db_path), None
    )
    cs = CommandSequence(url)
    cs.get(sleep=3)
    cs.append_command(ReadBotResults())
    manager.execute_command_sequence(cs)
    manager.close()
    report = _read_results(db_path)
    assert report, f"probe page produced no report for {manager_params.data_directory}"
    assert report.get("ok") is True, f"probe page errored: {report.get('error')}"
    report["_capture"] = _javascript_capture(db_path)
    report["_webdriver_exposed"] = _exposes_webdriver(browser_params[0])
    return report


def collect_plain(url: str) -> Dict:
    """Run the ``plain`` arm: stock Firefox, bare Selenium, no OpenWPM at all.

    Deliberately minimal -- no extension, no OpenWPM preference set, no profile
    seeding. The ONLY things it shares with the OpenWPM arms are the Firefox
    binary (``firefox-bin/``, the same build OpenWPM uses, so the comparison is
    not confounded by browser version), headless mode (so it matches the
    OpenWPM arms' ``display_mode="headless"``) and the ``TZ`` the test pins.

    Its ``_capture`` is ``None``: there is no crawl database, and "no
    instrumentation ran" is true by construction rather than by measurement.
    """
    options = Options()
    options.add_argument("-headless")
    options.binary_location = get_firefox_binary_path()
    # Resolve geckodriver explicitly, the same way deploy_firefox does. Leaving
    # Service() empty defers to Selenium Manager, which tries to *download* a
    # driver: that makes the arm non-hermetic and it fails outright wherever the
    # download is unavailable, even though a usable geckodriver is on PATH.
    geckodriver_path = shutil.which("geckodriver")
    if not geckodriver_path:
        raise RuntimeError(
            "geckodriver not found on PATH; cannot launch the plain-Firefox arm"
        )
    driver = webdriver.Firefox(
        options=options, service=Service(executable_path=geckodriver_path)
    )
    try:
        driver.get(url)
        results_json = _scrape_results(driver)
    finally:
        driver.quit()
    report = json.loads(results_json or "{}")
    assert report, "probe page produced no report for the plain-Firefox arm"
    assert report.get("ok") is True, f"probe page errored: {report.get('error')}"
    report["_capture"] = None
    report["_webdriver_exposed"] = True
    return report


# --------------------------------------------------------------------------- #
# Flattening -- turn the nested report into one signal -> value map
#
# Values are NOT hashed (unlike the FingerprintJS probe). A bot detector's
# output is small booleans, short strings and counts, and the readable value IS
# the finding; hashing would throw away exactly what the report needs to show.
# --------------------------------------------------------------------------- #
def _key(value: Any) -> str:
    """Canonical, order-independent string form of a JSON value."""
    return json.dumps(value, sort_keys=True)


def _walk(value: Any, prefix: str, out: Dict[str, str]) -> None:
    """Flatten nested dicts into dotted paths; anything else is a leaf."""
    if isinstance(value, dict):
        for name in sorted(value):
            _walk(value[name], f"{prefix}.{name}", out)
    else:
        out[prefix] = _key(value)


# Signal namespaces that carry a DETECTION verdict, as opposed to a raw reading.
# Only these can "fire".
BOTD_DETECTION_PREFIX = "botd.detection."
FPSCANNER_RULE_PREFIX = "fpscanner.rule."
AGGREGATE_SIGNALS = ("botd.verdict.bot", "fpscanner.fastBotDetection")
# The aggregates flip with the webdriver override only when nothing else fires,
# which depends on the host (e.g. fpscanner's hasSwiftshaderRenderer or
# hasHighCPUCount), so they may or may not be part of its footprint.
AGGREGATES = {*AGGREGATE_SIGNALS, "botd.verdict.botKind"}


def flatten(report: Dict) -> Dict[str, str]:
    """Map signal name -> comparison key across both oracles and the extras."""
    out: Dict[str, str] = {}

    botd = report["botd"]
    # BotD's aggregate verdict is `{bot: false}` with NO botKind when it sees
    # nothing, and `{bot: true, botKind: ...}` when it does. Normalised to a
    # fixed key set so an arm that stops being detected registers as a CHANGED
    # botKind rather than as a vanished signal -- the validity gate intersects
    # signal names across arms and would otherwise silently drop it as
    # "irreproducible" when it is a real difference.
    out["botd.verdict.bot"] = _key(botd["verdict"].get("bot"))
    out["botd.verdict.botKind"] = _key(botd["verdict"].get("botKind"))
    for name, verdict in botd["detections"].items():
        out[f"{BOTD_DETECTION_PREFIX}{name}"] = _key(verdict)
    for name, component in botd["components"].items():
        out[f"botd.component.{name}"] = _key(component)

    fingerprint = report["fpscanner"]["fingerprint"]
    out["fpscanner.fastBotDetection"] = _key(fingerprint["fastBotDetection"])
    for name, rule in fingerprint["fastBotDetectionDetails"].items():
        # `severity` is static metadata baked into the library, not a reading;
        # comparing it across arms would be comparing the library to itself.
        out[f"{FPSCANNER_RULE_PREFIX}{name}"] = _key(rule["detected"])
    _walk(fingerprint["signals"], "fpscanner.signal", out)
    for field in ("fsid", "nonce", "time", "url"):
        out[f"fpscanner.{field}"] = _key(fingerprint[field])

    _walk(report["paperProbes"], "paper", out)
    return out


def fires(signal: str, value: str) -> bool:
    """Is this signal a detection verdict, and did it say 'bot'?"""
    if signal in AGGREGATE_SIGNALS:
        return json.loads(value) is True
    if signal.startswith(FPSCANNER_RULE_PREFIX):
        return json.loads(value) is True
    if signal.startswith(BOTD_DETECTION_PREFIX):
        return bool(json.loads(value).get("bot"))
    return False


def firing_signals(report: Dict) -> Set[str]:
    """Every detection verdict in this report that came back positive."""
    flat = flatten(report)
    return {name for name, value in flat.items() if fires(name, value)}


# Stands in for a key missing from one report, so a key that exists in only some
# arms is compared as a value instead of being dropped from the comparison.
ABSENT = "<absent>"


def stable_signals(reports: Dict[str, Dict], arms: List[str]) -> Set[str]:
    """Signals that reproduce across the two runs of EVERY arm.

    This is the validity gate. A signal that cannot reproduce itself under
    identical conditions cannot testify about instrumentation, so only this set
    is compared across arms. Derived from the data, never hardcoded. Computed
    over the UNION of all arms' keys: a key only some arms produce stays in the
    set (as :data:`ABSENT` elsewhere) as long as each arm agrees with itself, so
    a cross-arm schema change surfaces as a difference rather than as noise.
    """
    flat = {name: flatten(report) for name, report in reports.items()}
    names: Set[str] = set().union(*flat.values())
    stable = set(names)
    for arm in arms:
        a, b = flat[f"{arm}_a"], flat[f"{arm}_b"]
        assert a.keys() == b.keys(), (
            f"the signal set itself differs within arm {arm}: "
            f"{sorted(a.keys() ^ b.keys())}"
        )
        stable -= {n for n in names if a.get(n, ABSENT) != b.get(n, ABSENT)}
    return stable


def differing_signals(
    report_a: Dict, report_b: Dict, restrict_to: Set[str]
) -> Dict[str, Tuple[str, str]]:
    """Signals in ``restrict_to`` whose value differs between two reports."""
    a, b = flatten(report_a), flatten(report_b)
    return {
        name: (a.get(name, ABSENT), b.get(name, ABSENT))
        for name in sorted(restrict_to)
        if a.get(name, ABSENT) != b.get(name, ABSENT)
    }


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
@pytest.mark.pyonly
def test_vendored_bundles_are_the_pinned_artifacts() -> None:
    """The oracles must be the exact bundles whose provenance is recorded."""
    for name, expected in VENDORED_BUNDLES.items():
        digest = hashlib.sha256((VENDOR_DIR / name).read_bytes()).hexdigest()
        assert digest == expected, (
            f"{name} does not match its pinned SHA-256. Update "
            "test_pages/vendor/README.md and VENDORED_BUNDLES together, and "
            "re-run the measurement in "
            "docs/developers/Bot-Detector-Visibility-Experiment.md."
        )


@pytest.mark.pyonly
def test_bundled_stealth_settings_parse() -> None:
    """``stealth_bare`` drops the webdriver override and nothing else."""
    settings = _bundled_stealth_settings()
    assert _hides_webdriver(settings), (
        "the bundled stealth surface no longer overrides navigator.webdriver; "
        "the stealth/stealth_bare split in this module is moot"
    )
    bare = _without_webdriver_override(settings)
    assert not _hides_webdriver(bare)
    assert [e["object"] for e in bare] == [e["object"] for e in settings]


# --------------------------------------------------------------------------- #
# Recorded expectations
#
# These constants describe what was MEASURED (see
# docs/developers/Bot-Detector-Visibility-Experiment.md). If a future Firefox,
# oracle version or instrument change moves them, re-run the measurement and
# update the record rather than widening the tolerance.
# --------------------------------------------------------------------------- #
EXPECTED_BOTD_DETECTORS = 18
EXPECTED_FPSCANNER_RULES = 21

# Documentation, not the exclusion mechanism: `stable_signals` derives the
# excluded set from the paired runs. `nonce` is Math.random() and `time` a
# wall-clock stamp. `canvasFingerprint` hashes rendered canvas bytes, which
# Firefox randomizes per launch (see
# docs/developers/FingerprintJS-Visibility-Experiment.md); `fsid` mixes that
# hash in.
EXPECTED_UNSTABLE_SIGNALS = {
    "fpscanner.nonce",
    "fpscanner.time",
    "fpscanner.signal.graphics.canvas.canvasFingerprint",
    "fpscanner.fsid",
}

# Every signal that is a view of `navigator.webdriver`: the raw readings (main
# realm, writability, iframe) and the detectors built on them. Measured as the
# difference between `stealth` and `stealth_bare`.
WEBDRIVER_SIGNALS = {
    "botd.component.webDriver",
    "botd.detection.detectWebDriver",
    "fpscanner.rule.hasWebdriver",
    "fpscanner.rule.hasWebdriverIframe",
    "fpscanner.rule.hasWebdriverWritable",
    "fpscanner.signal.automation.webdriver",
    "fpscanner.signal.automation.webdriverWritable",
    "fpscanner.signal.contexts.iframe.webdriver",
    "paper.navigatorWebdriver",
}

# Interfaces the probe page is known to drive that every instrumented arm
# covers. The activity control asserts capture on these, so "no detector could
# tell the arms apart" can never be explained by "the instrument never attached".
REQUIRED_CAPTURE_PREFIXES = (
    "CanvasRenderingContext2D.",
    "HTMLCanvasElement.",
    "window.navigator.",
    "window.screen.",
)

# The paper's four instrumentation tells (arXiv:2205.08890 Sec. 4.1): leaked
# globals, `[native code]` missing from wrapped natives, a wrapper frame in a
# provoked stack, and prototype flattening.
LEGACY_PAPER_TELLS = {
    "paper.globalsOnWindow",
    "paper.globalsInScope",
    "paper.nativeToString.HTMLCanvasElement.prototype.getContext",
    "paper.nativeToString.HTMLCanvasElement.prototype.toDataURL",
    "paper.nativeToString.CanvasRenderingContext2D.prototype.fillText",
    "paper.nativeToString.Storage.prototype.setItem",
    "paper.errorStack.raw",
    "paper.errorStack.frameCount",
    "paper.errorStack.frameFunctions",
    "paper.prototypeOwnPropertyCounts.HTMLCanvasElement.prototype",
    "paper.prototypeOwnPropertyCounts.CanvasRenderingContext2D.prototype",
    "paper.prototypeOwnPropertyCounts.Storage.prototype",
}

# `paper.*` is not part of either oracle -- see the probe page.
PAPER_PREFIX = "paper."

ARMS = ["plain", "baseline", "legacy", "stealth_bare", "stealth"]
INSTRUMENTED_ARMS = ["legacy", "stealth_bare", "stealth"]
ARM_PARAMS = {
    "baseline": _baseline_params,
    "legacy": _legacy_params,
    "stealth_bare": _stealth_bare_params,
    "stealth": _stealth_params,
}


def _oracle(signals: Set[str]) -> Set[str]:
    return {name for name in signals if not name.startswith(PAPER_PREFIX)}


def _paper(signals: Set[str]) -> Set[str]:
    return {name for name in signals if name.startswith(PAPER_PREFIX)}


def _check_gate(probes: Dict[str, Dict]) -> Set[str]:
    """VALIDITY GATE: which signals can testify at all.

    Every detection VERDICT must be reproducible; only raw readings may drift.
    """
    for name, report in probes.items():
        assert report["vendored"] == sorted(VENDORED_BUNDLES), (
            f"{name}: probe page loaded {report['vendored']}, not the pinned "
            f"{sorted(VENDORED_BUNDLES)}"
        )
        timezone = flatten(report)[
            "fpscanner.signal.locale.internationalization.timezone"
        ]
        assert (
            json.loads(timezone) == PINNED_TZ
        ), f"{name}: browser timezone is {timezone}, so the TZ pin did not take"

    stable = stable_signals(probes, ARMS)
    observed: Set[str] = set().union(*(flatten(r) for r in probes.values()))
    unstable = observed - stable
    assert unstable == EXPECTED_UNSTABLE_SIGNALS, (
        f"the set of irreproducible signals changed: expected "
        f"{sorted(EXPECTED_UNSTABLE_SIGNALS)}, observed {sorted(unstable)}. "
        "Re-run the measurement in "
        "docs/developers/Bot-Detector-Visibility-Experiment.md."
    )

    detectors = {n for n in observed if n.startswith(BOTD_DETECTION_PREFIX)}
    rules = {n for n in observed if n.startswith(FPSCANNER_RULE_PREFIX)}
    assert len(detectors) == EXPECTED_BOTD_DETECTORS, sorted(detectors)
    assert len(rules) == EXPECTED_FPSCANNER_RULES, sorted(rules)
    verdicts = detectors | rules | set(AGGREGATE_SIGNALS)
    assert verdicts <= stable, (
        "a detection VERDICT is not reproducible run-to-run: "
        f"{sorted(verdicts - stable)}"
    )
    return stable


def _check_activity(probes: Dict[str, Dict]) -> None:
    """ACTIVITY CONTROL: the instruments really ran and really saw this page."""
    assert probes["plain_a"]["_capture"] is None
    for run in ("baseline_a", "baseline_b"):
        assert probes[run]["_capture"]["rows"] == 0, (
            f"{run} is supposed to be uninstrumented but recorded "
            f"{probes[run]['_capture']['rows']} JavaScript calls"
        )
    for arm in INSTRUMENTED_ARMS:
        for run in ("a", "b"):
            capture = probes[f"{arm}_{run}"]["_capture"]
            symbols = capture["symbols"]
            assert capture["rows"] > 0, f"{arm}_{run} captured nothing"
            for prefix in REQUIRED_CAPTURE_PREFIXES:
                assert any(str(s).startswith(prefix) for s in symbols), (
                    f"{arm}_{run} captured no {prefix}* calls, so the comparison "
                    f"says nothing about that surface. Captured: {symbols}"
                )
            assert any(
                "toDataURL" in str(s) for s in symbols
            ), f"{arm}_{run} never saw canvas.toDataURL"


def _check_webdriver(probes: Dict[str, Dict], stable: Set[str]) -> None:
    """``navigator.webdriver`` reads as each arm configures it, and the
    override's footprint is WEBDRIVER_SIGNALS plus, at most, the aggregates."""
    for arm in ARMS:
        report = probes[f"{arm}_a"]
        exposed = report["_webdriver_exposed"]
        flat = flatten(report)
        observed = json.loads(flat["paper.navigatorWebdriver"])
        assert observed is exposed, (
            f"{arm}: navigator.webdriver reads {observed}, but the arm's "
            f"configuration implies {exposed}"
        )
        assert json.loads(flat["fpscanner.rule.hasWebdriver"]) is exposed, arm
        assert (
            json.loads(flat["botd.detection.detectWebDriver"]).get("bot", False)
            is exposed
        ), arm
    footprint = set(
        differing_signals(probes["stealth_bare_a"], probes["stealth_a"], stable)
    )
    if probes["stealth_bare_a"]["_webdriver_exposed"] == (
        probes["stealth_a"]["_webdriver_exposed"]
    ):
        assert not footprint, (
            "stealth and stealth_bare expose navigator.webdriver alike, yet "
            f"differ on {sorted(footprint)}"
        )
    else:
        assert WEBDRIVER_SIGNALS <= footprint <= WEBDRIVER_SIGNALS | AGGREGATES, (
            "the webdriver override's footprint changed: expected "
            f"{sorted(WEBDRIVER_SIGNALS)} plus at most {sorted(AGGREGATES)}, "
            f"observed {sorted(footprint)}"
        )


@pytest.mark.usefixtures("xpi")
def test_oss_bot_detectors_across_arms(
    tmp_path_factory: pytest.TempPathFactory,
    server: ServerUrls,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """What BotD and fpscanner can and cannot see, per arm.

    Arms whose configurations expose ``navigator.webdriver`` differently are
    compared outside WEBDRIVER_SIGNALS and AGGREGATES; all other pairs on every
    reproducible signal.

    - ``baseline`` reads like ``plain``: OpenWPM's extension and preferences add
      nothing either oracle or the paper's probes see.
    - ``legacy`` reads like ``baseline`` on every oracle signal, while the
      ``paper.*`` probes in the same page load catch all four instrumentation
      tells. The oracles do not probe those surfaces: BotD's integrity checks
      are on ``eval``, ``Function.prototype.bind`` (whose string it never
      compares) and its own stack trace, and fpscanner's one prototype check
      reads ``Navigator.prototype`` while legacy patches the instance.
    - ``stealth_bare`` reads like ``baseline`` on every signal, oracle and
      paper alike: the stealth instrument itself adds nothing either oracle or
      the paper's probes see.
    - ``stealth`` differs from ``stealth_bare`` only on WEBDRIVER_SIGNALS and
      the aggregates. Anything the oracles stop flagging under ``stealth`` is
      the override's doing, not the instrument's.

    If an equality here fails, an oracle has started seeing an instrument: a
    real finding. Re-run the measurement rather than relaxing the assertion.
    """
    monkeypatch.setenv("TZ", PINNED_TZ)
    url = _page_url(server, PROBE_PAGE)
    probes: Dict[str, Dict] = {}
    for arm in ARMS:
        for run in ("a", "b"):
            name = f"{arm}_{run}"
            if arm == "plain":
                probes[name] = collect_plain(url)
            else:
                data_dir = tmp_path_factory.mktemp(f"botdet_{name}")
                probes[name] = collect_openwpm(ARM_PARAMS[arm](data_dir), url)

    stable = _check_gate(probes)
    _check_activity(probes)
    _check_webdriver(probes, stable)

    for reference, arm, oracle_only in (
        ("plain", "baseline", False),
        ("baseline", "legacy", True),
        ("baseline", "stealth_bare", False),
        ("baseline", "stealth", False),
    ):
        ref, other = probes[f"{reference}_a"], probes[f"{arm}_a"]
        signals = _oracle(stable) if oracle_only else set(stable)
        if ref["_webdriver_exposed"] != other["_webdriver_exposed"]:
            signals -= WEBDRIVER_SIGNALS | AGGREGATES
        drift = differing_signals(ref, other, signals)
        assert not drift, (
            f"{arm} is distinguishable from {reference}: {drift}. Update "
            "docs/developers/Bot-Detector-Visibility-Experiment.md."
        )

    legacy_tells = set(
        differing_signals(probes["baseline_a"], probes["legacy_a"], _paper(stable))
    )
    assert legacy_tells == LEGACY_PAPER_TELLS, (
        "legacy's paper-probe tells changed: expected "
        f"{sorted(LEGACY_PAPER_TELLS)}, observed {sorted(legacy_tells)}"
    )
