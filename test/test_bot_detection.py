"""Can off-the-shelf bot detection tell OpenWPM's instruments apart?

``test_fingerprintjs_stamp.py`` answered the *fingerprinting* half of this
question and got a null result in both directions: a commodity fingerprinter
reads VALUES, OpenWPM's wrappers are value-transparent, and so FingerprintJS
5.2.0 cannot distinguish baseline, legacy or stealth. Bot detectors are a
different animal -- they run INTEGRITY checks (is this function native? does the
prototype look right? is ``navigator.webdriver`` set? do the iframe, the worker
and the main realm agree?). That is the gap this module fills.

Two off-the-shelf OSS oracles, both vendored and hash-pinned, both run in the
same page load:

``@fingerprintjs/botd`` 2.0.0
    The actual bot detector from the FingerprintJS authors: 23 sources feeding
    18 named detectors, each with its own verdict, plus one aggregate.
``fpscanner`` 1.0.8
    Antoine Vastel's scanner: ~150 leaf signals and 21 individually-named
    detection rules, each ``{detected, severity}``, plus one aggregate.

FOUR arms, not three, because "OpenWPM with no instrument" and "a browser that
is not OpenWPM" are different references and the difference is the whole point:

``plain``
    Stock Firefox driven by bare Selenium. No OpenWPM, no extension, no OpenWPM
    preference set. This is the "what does a non-OpenWPM browser look like"
    reference. It is still WebDriver-driven, so ``navigator.webdriver`` is still
    true here -- which is exactly what makes it the right control for separating
    *Selenium* tells from *OpenWPM* tells.
``baseline``
    OpenWPM, ``js_instrument=False``, ``stealth_js_instrument=False``.
``legacy``
    OpenWPM, ``js_instrument=True`` with ``js_instrument_settings=["collection_fingerprinting"]``
    -- **the project's own standard preset**
    (``openwpm/js_instrumentation_collections/fingerprinting.json``), which is
    also the ``BrowserParams`` default. Spelled out explicitly so it is evident
    on inspection that the legacy arm was not hand-tuned to fail.
``stealth``
    OpenWPM, ``stealth_js_instrument=True``, bundled default surface
    (``Extension/src/stealth/settings.ts``).

Every signal is compared individually, never as one boolean, so a verdict names
the check that carries it. Signals are then classified:

INSTRUMENTATION tell
    fires on ``legacy`` but not on ``baseline``. This is what the PR is about.
AUTOMATION tell
    fires on ``baseline`` too -- inherent to OpenWPM/Selenium, and NOT something
    any JS instrument claims to fix.
STEALTH-ONLY difference
    ``stealth`` differs from ``baseline``. Expected on ``navigator.webdriver``,
    which stealth actively suppresses (``Extension/src/stealth/settings.ts``
    sets ``overwrittenProperties: [{key:"webdriver", value:false, level:0}]``).

**Validity gate.** EVERY arm is run twice and only signals that reproduce in all
four arms are compared. The excluded set is derived from the data, never
hardcoded, so a newly-flaky signal is dropped automatically instead of being
misattributed to instrumentation.

``manager_params.testing`` is deliberately **False** in the OpenWPM arms. With
``testing=True`` the legacy page script additionally publishes
``window.instrumentJS``, which would be a harness artifact inflating legacy's
detectability rather than a property of a real crawl.

See ``docs/developers/Bot-Detector-Visibility-Experiment.md`` for the recorded
measurement this module's expectations were derived from.
"""

import hashlib
import json
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
# switches is held identical on purpose; the arms must differ in exactly one
# dimension.
# --------------------------------------------------------------------------- #
def _base_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params = ManagerParams(num_browsers=1)
    browser_params = [BrowserParams()]
    manager_params.data_directory = data_dir
    manager_params.log_path = data_dir / "openwpm.log"
    # NOT the usual `testing = True`. See the module docstring: testing mode
    # makes the legacy page script publish `window.instrumentJS`, a harness-only
    # global that would show up as legacy detectability that no real crawl has.
    manager_params.testing = False
    browser_params[0].display_mode = "headless"
    return manager_params, browser_params


def _baseline_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Arm 2: OpenWPM with no JavaScript instrumentation at all."""
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].js_instrument = False
    browser_params[0].stealth_js_instrument = False
    return manager_params, browser_params


def _legacy_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Arm 3: legacy instrument with the project's standard fingerprinting preset."""
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].stealth_js_instrument = False
    browser_params[0].js_instrument = True
    browser_params[0].js_instrument_settings = ["collection_fingerprinting"]
    return manager_params, browser_params


def _stealth_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Arm 4: stealth instrument, bundled default surface."""
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].js_instrument = False
    browser_params[0].stealth_js_instrument = True
    return manager_params, browser_params


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

    The returned dict carries an extra ``_capture`` key (not produced by the
    page) holding the arm's JavaScript-capture activity control.
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
    return report


def collect_plain(url: str) -> Dict:
    """Run the ``plain`` arm: stock Firefox, bare Selenium, no OpenWPM at all.

    Deliberately minimal -- no extension, no OpenWPM preference set, no profile
    seeding. The ONLY things it shares with the OpenWPM arms are the Firefox
    binary (``firefox-bin/``, the same build OpenWPM uses, so the comparison is
    not confounded by browser version) and headless mode (so it matches the
    OpenWPM arms' ``display_mode="headless"``).

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


def flatten(report: Dict) -> Dict[str, str]:
    """Map signal name -> comparison key across both oracles and the extras."""
    out: Dict[str, str] = {}

    botd = report["botd"]
    # BotD's aggregate verdict is `{bot: false}` with NO botKind when it sees
    # nothing, and `{bot: true, botKind: ...}` when it does. Normalised to a
    # fixed key set so an arm that stops being detected registers as a CHANGED
    # botKind rather than as a vanished signal -- the validity gate intersects
    # signal names across arms and would otherwise silently drop it as
    # "irreproducible" when it is in fact the headline result.
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


def stable_signals(reports: Dict[str, Dict], arms: List[str]) -> Set[str]:
    """Signals that reproduce across the two runs of EVERY arm.

    This is the validity gate. A signal that cannot reproduce itself under
    identical conditions cannot testify about instrumentation, so only this set
    is compared across arms. Derived from the data -- never hardcoded -- so a
    newly-flaky signal is excluded automatically instead of causing a
    misattributed failure. Intersecting over all four arms rather than just one
    is the conservative choice: a signal only gets to testify if it is stable
    everywhere it was observed.
    """
    stable: Set[str] | None = None
    for arm in arms:
        a, b = flatten(reports[f"{arm}_a"]), flatten(reports[f"{arm}_b"])
        assert a.keys() == b.keys(), f"the signal set itself differs within arm {arm}"
        agreeing = {name for name in a if a[name] == b[name]}
        stable = agreeing if stable is None else (stable & agreeing)
    assert stable is not None
    return stable


def differing_signals(
    report_a: Dict, report_b: Dict, restrict_to: Set[str]
) -> Dict[str, Tuple[str, str]]:
    """Signals in ``restrict_to`` whose value differs between two reports."""
    a, b = flatten(report_a), flatten(report_b)
    return {
        name: (a[name], b[name])
        for name in sorted(restrict_to)
        if a.get(name) != b.get(name)
    }


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
ARMS = ["plain", "baseline", "legacy", "stealth"]
OPENWPM_ARMS = ["baseline", "legacy", "stealth"]
INSTRUMENTED_ARMS = ["legacy", "stealth"]


@pytest.fixture(scope="module")
def probes(
    tmp_path_factory: pytest.TempPathFactory, server: ServerUrls, xpi: None
) -> Dict[str, Dict]:
    """Run every arm exactly twice and cache the reports for the whole module.

    Module-scoped because each run is a full browser launch; re-running them per
    test would multiply an already slow module. The ``_a``/``_b`` pair for each
    arm is that arm's half of the validity gate, not two different arms.
    """
    url = _page_url(server, PROBE_PAGE)
    reports: Dict[str, Dict] = {}
    factories = {
        "baseline": _baseline_params,
        "legacy": _legacy_params,
        "stealth": _stealth_params,
    }
    for arm in ARMS:
        for run in ("a", "b"):
            name = f"{arm}_{run}"
            if arm == "plain":
                reports[name] = collect_plain(url)
            else:
                data_dir = tmp_path_factory.mktemp(f"botdet_{name}")
                reports[name] = collect_openwpm(factories[arm](data_dir), url)
    return reports


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
@pytest.mark.pyonly
def test_vendored_bundles_are_the_pinned_artifacts() -> None:
    """The oracles must be the exact bundles whose provenance is recorded.

    Cheap, browser-free, and it runs first: if a fixture drifted, every other
    verdict in this module is about a different library.
    """
    for name, expected in VENDORED_BUNDLES.items():
        digest = hashlib.sha256((VENDOR_DIR / name).read_bytes()).hexdigest()
        assert digest == expected, (
            f"{name} does not match its pinned SHA-256. Update "
            "test_pages/vendor/README.md and VENDORED_BUNDLES together, and "
            "re-run the measurement in "
            "docs/developers/Bot-Detector-Visibility-Experiment.md."
        )


# --------------------------------------------------------------------------- #
# Recorded expectations
#
# These constants describe what was MEASURED (see
# docs/developers/Bot-Detector-Visibility-Experiment.md), not what would be
# convenient. If a future Firefox, oracle version or instrument change moves
# them, the right response is to re-run the measurement and update the record --
# not to widen the tolerance until the suite goes quiet.
# --------------------------------------------------------------------------- #
# BotD 2.0.0 ships 18 detectors; fpscanner 1.0.8 ships 21 named rules. Pinned so
# a bundle swap that silently changes the surface is caught rather than
# shrinking the measurement in silence.
EXPECTED_BOTD_DETECTORS = 18
EXPECTED_FPSCANNER_RULES = 21

# Signals expected to be excluded by the validity gate in this environment, and
# why. This is DOCUMENTATION, not the exclusion mechanism -- `stable_signals`
# derives the excluded set from the paired runs.
#
# `nonce` is Math.random() by construction and `time` is a wall-clock stamp;
# neither carries any signal. `canvasFingerprint` is a hash of rendered canvas
# bytes: Firefox re-seeds canvas readback noise PER PROFILE and every launch
# here gets a fresh profile, so it differs on every run regardless of
# instrumentation -- established as a browser property, not an instrumentation
# artifact, by the plain-Firefox control in
# docs/developers/FingerprintJS-Visibility-Experiment.md. `fsid` is fpscanner's
# rolled-up id, which mixes the canvas hash in and therefore inherits its
# instability.
EXPECTED_UNSTABLE_SIGNALS = {
    "fpscanner.nonce",
    "fpscanner.time",
    "fpscanner.signal.graphics.canvas.canvasFingerprint",
    "fpscanner.fsid",
}

# The signals on which stealth differs from baseline: every one of them is
# `navigator.webdriver` seen from a different angle (raw reading, the writability
# of the property, the same property read inside an iframe, the detectors built
# on top, and BotD's aggregate verdict). Stealth suppresses it deliberately --
# Extension/src/stealth/settings.ts sets
# `overwrittenProperties: [{key: "webdriver", value: false, level: 0}]` on
# Navigator -- so this set is the CLAIM, listed exhaustively rather than
# summarised, and any addition to it is a new stealth-visible surface that must
# be explained before the expectation is widened.
EXPECTED_STEALTH_ONLY_DIFFERENCES = {
    "botd.component.webDriver",
    "botd.detection.detectWebDriver",
    "botd.verdict.bot",
    "botd.verdict.botKind",
    "fpscanner.rule.hasWebdriver",
    "fpscanner.rule.hasWebdriverIframe",
    "fpscanner.rule.hasWebdriverWritable",
    "fpscanner.signal.automation.webdriver",
    "fpscanner.signal.automation.webdriverWritable",
    "fpscanner.signal.contexts.iframe.webdriver",
    "paper.navigatorWebdriver",
}

# Interfaces the probe page is known to drive that BOTH presets instrument. The
# activity control asserts capture on these, so "no detector could tell the arms
# apart" can never be explained by "the instrument never attached".
REQUIRED_CAPTURE_PREFIXES = (
    "CanvasRenderingContext2D.",
    "HTMLCanvasElement.",
    "window.navigator.",
    "window.screen.",
)

# The `paper.*` namespace is NOT part of either oracle -- see the probe page for
# why it exists. Verdicts about what off-the-shelf detection can see must be
# restricted to the oracle namespaces, or the experiment answers a question
# nobody asked.
PAPER_PREFIX = "paper."


def oracle_signals(signals: Set[str]) -> Set[str]:
    """Drop the paper-probe namespace: only BotD and fpscanner are the oracles."""
    return {name for name in signals if not name.startswith(PAPER_PREFIX)}


def paper_signals(signals: Set[str]) -> Set[str]:
    """Only the paper-probe namespace."""
    return {name for name in signals if name.startswith(PAPER_PREFIX)}


@pytest.mark.usefixtures("xpi", "server")
class TestBotDetection:
    """What two off-the-shelf OSS bot detectors can and cannot see."""

    def test_every_arm_is_reproducible(self, probes: Dict[str, Dict]) -> None:
        """VALIDITY GATE: establish which signals can testify at all.

        Runs before every cross-arm verdict for a reason -- an oracle that
        disagrees with itself proves nothing about instrumentation. Each arm is
        run twice and only signals that reproduce in ALL FOUR arms are compared.
        Crucially, every DETECTION VERDICT must be stable: the drifting signals
        are allowed to be raw readings, never a detector's answer.
        """
        stable = stable_signals(probes, ARMS)
        observed = set(flatten(probes["plain_a"]))
        unstable = observed - stable

        assert unstable == EXPECTED_UNSTABLE_SIGNALS, (
            f"the set of irreproducible signals changed: expected "
            f"{sorted(EXPECTED_UNSTABLE_SIGNALS)}, observed {sorted(unstable)}. "
            "Re-run the measurement in "
            "docs/developers/Bot-Detector-Visibility-Experiment.md before "
            "trusting any verdict below."
        )

        detectors = {n for n in observed if n.startswith(BOTD_DETECTION_PREFIX)}
        rules = {n for n in observed if n.startswith(FPSCANNER_RULE_PREFIX)}
        assert len(detectors) == EXPECTED_BOTD_DETECTORS, (
            f"expected {EXPECTED_BOTD_DETECTORS} BotD detectors, got "
            f"{len(detectors)}: the vendored bundle's surface changed"
        )
        assert len(rules) == EXPECTED_FPSCANNER_RULES, (
            f"expected {EXPECTED_FPSCANNER_RULES} fpscanner rules, got "
            f"{len(rules)}: the vendored bundle's surface changed"
        )
        verdicts = detectors | rules | set(AGGREGATE_SIGNALS)
        assert verdicts <= stable, (
            "a detection VERDICT is not reproducible run-to-run, so no "
            f"classification below can be trusted: {sorted(verdicts - stable)}"
        )

    def test_each_arm_instrumented_as_configured(self, probes: Dict[str, Dict]) -> None:
        """ACTIVITY CONTROL: the instruments really ran and really saw this page.

        Without this, "the detectors could not tell the arms apart" has a
        trivial wrong explanation. Both instrumented arms must have captured
        calls on the canvas, navigator and screen interfaces the probe page
        drives; the OpenWPM baseline must have captured nothing at all.
        """
        for arm in ("baseline_a", "baseline_b"):
            capture = probes[arm]["_capture"]
            assert capture is not None
            assert capture["rows"] == 0, (
                f"{arm} is supposed to be uninstrumented but recorded "
                f"{capture['rows']} JavaScript calls"
            )

        for arm in INSTRUMENTED_ARMS:
            capture = probes[f"{arm}_a"]["_capture"]
            assert capture is not None
            symbols = capture["symbols"]
            assert capture["rows"] > 0, f"{arm} captured nothing"
            for prefix in REQUIRED_CAPTURE_PREFIXES:
                assert any(str(s).startswith(prefix) for s in symbols), (
                    f"{arm} captured no {prefix}* calls, so the comparison says "
                    f"nothing about that surface. Captured: {symbols}"
                )
            assert any("toDataURL" in str(s) for s in symbols), (
                f"{arm} never saw canvas.toDataURL, so the canvas readback path "
                "was not actually instrumented during this measurement"
            )

        assert (
            probes["plain_a"]["_capture"] is None
        ), "the plain arm must not be running OpenWPM at all"

    def test_openwpm_baseline_looks_exactly_like_plain_firefox(
        self, probes: Dict[str, Dict]
    ) -> None:
        """CONTROL: OpenWPM without a JS instrument adds no bot-detectable surface.

        This is what licenses calling everything that fires on `baseline` an
        AUTOMATION tell rather than an OpenWPM tell. Stock Firefox 154 driven by
        bare Selenium and OpenWPM's own baseline read IDENTICALLY on every
        reproducible signal -- including OpenWPM's whole preference set and the
        presence of the (uninstrumented) extension.
        """
        stable = stable_signals(probes, ARMS)
        drift = differing_signals(probes["plain_a"], probes["baseline_a"], stable)
        assert not drift, (
            "OpenWPM's baseline is distinguishable from plain Firefox, which "
            "would mean OpenWPM itself -- not its JS instrument -- adds a "
            f"bot-detectable surface: {drift}"
        )

    def test_no_oss_bot_detector_distinguishes_legacy_from_baseline(
        self, probes: Dict[str, Dict]
    ) -> None:
        """THE HEADLINE RESULT, and it is a null one. Do not "fix" it.

        Neither BotD nor fpscanner sees ANY difference between the legacy
        `js_instrument` and an uninstrumented OpenWPM browser -- not one of
        BotD's 18 detectors, not one of fpscanner's 21 rules, not one of their
        ~190 underlying readings -- while legacy demonstrably wrapped the canvas,
        navigator and screen surfaces the page drove (activity control above).

        The reason is coverage, not innocence. Legacy IS detectable: the
        `paper.*` probes in the same page load catch it on all four tells
        Krumnow, Jonker & Karsch document (arXiv:2205.08890 Sec. 4.1), and
        test_stealth.py::TestStealthDetectability catches it on more. But
        neither of these two commodity libraries probes those surfaces: BotD's
        only integrity checks are on `eval`, `Function.prototype.bind` and its
        OWN stack trace, none of which any OpenWPM preset wraps, and fpscanner's
        `navigatorPropertyDescriptors` looks at `Navigator.prototype` while
        legacy defines its wrappers on the `navigator` instance.

        So the honest claim the PR can make is "off-the-shelf bot detection does
        not catch legacy either" -- which is a weaker claim than "legacy trips
        bot detectors", and the report says so. If this test ever fails, an
        oracle has started seeing legacy: a real finding. Re-run the measurement
        rather than relaxing the assertion.
        """
        stable = oracle_signals(stable_signals(probes, ARMS))
        leaked = differing_signals(probes["baseline_a"], probes["legacy_a"], stable)
        assert not leaked, (
            "an off-the-shelf bot detector now distinguishes legacy from "
            f"baseline, contradicting the recorded measurement: {leaked}. "
            "Update docs/developers/Bot-Detector-Visibility-Experiment.md and "
            "the docstring above."
        )

    def test_stealth_differs_from_baseline_only_by_suppressing_webdriver(
        self, probes: Dict[str, Dict]
    ) -> None:
        """Stealth IS distinguishable from baseline -- in stealth's favour.

        The PR must not claim "bot detection cannot tell stealth from an
        uninstrumented browser": it can, trivially, because stealth sets
        `navigator.webdriver` to false and an uninstrumented OpenWPM browser
        leaves it true. Every differing signal is that one property viewed from
        a different angle, and each difference makes stealth look MORE like a
        human browser, never less.
        """
        stable = stable_signals(probes, ARMS)
        drift = set(
            differing_signals(probes["baseline_a"], probes["stealth_a"], stable)
        )
        assert drift == EXPECTED_STEALTH_ONLY_DIFFERENCES, (
            "the set of signals on which stealth differs from baseline changed. "
            f"Expected {sorted(EXPECTED_STEALTH_ONLY_DIFFERENCES)}, observed "
            f"{sorted(drift)}. Anything new here is a stealth-visible surface "
            "that must be explained, not absorbed into the expectation."
        )

    def test_stealth_is_never_more_detectable_than_baseline_or_legacy(
        self, probes: Dict[str, Dict]
    ) -> None:
        """The durable invariant, independent of how the comparisons came out.

        Whatever a bot detector fires on for an uninstrumented browser or for
        legacy, it must not fire on MORE for stealth. Today stealth fires on
        strictly fewer checks than both, so this holds with room to spare -- but
        it is the assertion that keeps holding if legacy is ever hardened or
        stealth ever regresses, which the equality tests above would not.
        """
        stealth = firing_signals(probes["stealth_a"])
        for reference in ("baseline_a", "legacy_a", "plain_a"):
            fired = firing_signals(probes[reference])
            assert stealth <= fired, (
                f"stealth trips bot-detection checks that {reference} does not: "
                f"{sorted(stealth - fired)}"
            )

    def test_every_arm_including_stealth_is_still_detectable_as_a_bot(
        self, probes: Dict[str, Dict]
    ) -> None:
        """HONESTY GUARD: stealth does not make OpenWPM undetectable.

        Krumnow, Jonker & Karsch conclude that "every mode of running OpenWPM is
        identifiable as a web bot", and the tells they name in that class --
        `navigator.webdriver`, screen position/dimension properties that
        "cannot be changed from OpenWPM", WebGL in display-less modes -- are
        outside what any JavaScript instrument can fix. This measurement agrees:
        fpscanner's aggregate verdict is `true` in ALL FOUR arms, stealth and
        plain Firefox included, and the screen signature the paper's Table 4
        gives for display-less modes (availTop/availLeft = 0) is present
        everywhere.

        This test exists so that no future edit can quietly turn this module
        into evidence for "stealth makes OpenWPM undetectable". It cannot, and
        the PR must not say so.
        """
        for arm in ARMS:
            flat = flatten(probes[f"{arm}_a"])
            assert json.loads(flat["fpscanner.fastBotDetection"]) is True, (
                f"{arm} is no longer flagged as automated by fpscanner. That "
                "would be a genuine change worth investigating -- but until the "
                "measurement is redone, the report's central caveat is stale."
            )
            assert json.loads(flat["fpscanner.rule.hasUTCTimezone"]) is True
            assert json.loads(flat["paper.screen.availTop"]) == 0
            assert json.loads(flat["paper.screen.availLeft"]) == 0

    def test_paper_tells_separate_instrumentation_from_automation(
        self, probes: Dict[str, Dict]
    ) -> None:
        """The classification the oracles were too blunt to make.

        These probes are NOT part of BotD or fpscanner -- see the probe page.
        They are the four instrumentation tells Krumnow, Jonker & Karsch name in
        Sec. 4.1, measured in the same page load as the oracles so the two are
        directly comparable:

        1. `Function.prototype.toString` on overwritten natives (their Listing 1)
        2. the `getInstrumentJS` global, "not present in any common desktop browser"
        3. OpenWPM wrapper functions appearing in stack traces
        4. prototype-chain pollution (their Fig. 2)

        Legacy fires all four. Stealth fires none: it is indistinguishable from
        an uninstrumented browser on every paper probe EXCEPT `navigatorWebdriver`,
        which it suppresses on purpose. That -- not the null oracle result -- is
        the evidence for the PR's stance.
        """
        stable = paper_signals(stable_signals(probes, ARMS))
        legacy_tells = set(
            differing_signals(probes["baseline_a"], probes["legacy_a"], stable)
        )
        stealth_tells = set(
            differing_signals(probes["baseline_a"], probes["stealth_a"], stable)
        )

        for expected in (
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
        ):
            assert expected in legacy_tells, (
                f"legacy no longer trips the paper's {expected} tell. If legacy "
                "was hardened, that is good news -- re-run the measurement and "
                "update docs/developers/Bot-Detector-Visibility-Experiment.md."
            )

        assert stealth_tells == {"paper.navigatorWebdriver"}, (
            "stealth is supposed to be indistinguishable from an uninstrumented "
            "browser on every paper probe except the webdriver flag it "
            f"deliberately suppresses; observed: {sorted(stealth_tells)}"
        )
