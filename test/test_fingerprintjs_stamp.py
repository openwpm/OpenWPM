"""Does OpenWPM's instrumentation change what a real fingerprinter sees?

Measures whether a commodity fingerprinting library computes the same stamp
under the stealth and legacy JS instruments as in an OpenWPM browser with no JS
instrument.

Three arms, one probe page (``test_pages/fingerprintjs_stamp.html``), identical
browser settings otherwise:

``baseline``
    OpenWPM with ``js_instrument=False``, ``stealth_js_instrument=False``: the
    extension and OpenWPM's preference set, but no JS instrument.
``stealth``
    ``stealth_js_instrument=True`` with the bundled default surface
    (``Extension/src/stealth/settings.ts``).
``legacy``
    ``js_instrument=True`` with ``js_instrument_settings=["collection_fingerprinting"]``
    -- the project's standard fingerprinting preset
    (``openwpm/js_instrumentation_collections/fingerprinting.json``), which is
    also the ``BrowserParams`` default. The two presets cover the same
    interfaces (audio nodes/contexts, RTCPeerConnection, HTMLCanvasElement,
    CanvasRenderingContext2D, Storage, Navigator, Screen, document, window).

The comparison is per COMPONENT, not just ``visitorId``, so a failure names the
surface that leaked. ``visitorId`` is a hash over all components, so a single
run-to-run-unstable source would move it for reasons unrelated to
instrumentation.

**Validity gate.** Every arm runs twice, and only probes that reproduce within
every arm are compared across arms. Unstable probes are reported and excluded.

All browser assertions live in ONE test on purpose: CI shards by test with
pytest-split, and separate tests would each relaunch the six browsers on a
different shard, with the gate checking a different sample from the verdicts.

See ``docs/developers/FingerprintJS-Visibility-Experiment.md`` for the recorded
measurement.
"""

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest
from selenium.webdriver import Firefox
from selenium.webdriver.support.ui import WebDriverWait

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams, ManagerParamsInternal
from openwpm.socket_interface import ClientSocket
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_providers import TableName
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils

from .utilities import ServerUrls

STAMP_PAGE = "/fingerprintjs_stamp.html"

# Vendored oracle. Pinned so a silently swapped bundle fails loudly rather than
# quietly changing what "the same stamp" means. See test_pages/vendor/README.md
# for provenance; the file is byte-identical to the published npm artifact
# @fingerprintjs/fingerprintjs@5.2.0 dist/fp.umd.min.js (MIT).
VENDORED_BUNDLE = Path(__file__).parent / "test_pages" / "vendor"
VENDORED_BUNDLE_NAME = "fingerprintjs-5.2.0.umd.min.js"
_VENDORED_SHA256 = "a8de5ead580c42d2e2b01a5752aa08da510852230971aa18554d67cd5de5775b"

# Custom table the probe page's JSON report is routed into. Commands run in a
# subprocess and the StorageController in yet another, so the on-disk crawl
# SQLite DB is the only reliable cross-process channel (the idiom used by
# test_custom_function_command.py and test_stealth.py). Created per-crawl in the
# test's temp DB, so it never touches schema.sql / parquet_schema.py.
STAMP_RESULTS_TABLE = TableName("fingerprintjs_stamp_results")

# The probe page runs 40+ fingerprinting sources, several of which deliberately
# wait on font loading, idle callbacks and offscreen layout. 10s (the value used
# by the stealth detection probe) is not enough headroom on a loaded CI box.
STAMP_TIMEOUT_SECONDS = 90


def _page_url(server: ServerUrls, page: str) -> str:
    """Build a full probe-page URL from the dynamic test server base."""
    return server.base + page


# --------------------------------------------------------------------------- #
# Config helpers -- one per arm. Everything except the instrument switches is
# held identical on purpose; the arms must differ in exactly one dimension.
# --------------------------------------------------------------------------- #
def _base_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params = ManagerParams(num_browsers=1)
    browser_params = [BrowserParams()]
    manager_params.data_directory = data_dir
    manager_params.log_path = data_dir / "openwpm.log"
    # testing=True makes legacy publish `window.instrumentJS`, which a real
    # crawl does not have.
    manager_params.testing = False
    browser_params[0].display_mode = "headless"
    return manager_params, browser_params


def _baseline_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Arm 1: no JavaScript instrumentation at all."""
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].js_instrument = False
    browser_params[0].stealth_js_instrument = False
    return manager_params, browser_params


def _stealth_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Arm 2: stealth instrument, bundled default surface."""
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].js_instrument = False
    browser_params[0].stealth_js_instrument = True
    return manager_params, browser_params


def _legacy_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Arm 3: legacy instrument with the project's standard fingerprinting preset."""
    manager_params, browser_params = _base_params(data_dir)
    browser_params[0].stealth_js_instrument = False
    browser_params[0].js_instrument = True
    browser_params[0].js_instrument_settings = ["collection_fingerprinting"]
    return manager_params, browser_params


# --------------------------------------------------------------------------- #
# Crawl helpers
# --------------------------------------------------------------------------- #
class ReadStampResults(BaseCommand):
    """Scrape the probe page's ``data-results`` JSON and ship it to storage.

    Opens its OWN ``ClientSocket`` to the storage controller (NOT
    ``extension_socket``, which talks to the extension's port), mirroring
    ``test_custom_function_command.py::test_custom_function``.
    """

    def __repr__(self) -> str:
        return "ReadStampResults"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        WebDriverWait(webdriver, STAMP_TIMEOUT_SECONDS).until(
            lambda d: d.find_element("id", "results").get_attribute("data-results")
        )
        results_json = webdriver.execute_script(
            "return document.getElementById('results').getAttribute('data-results');"
        )
        sock = ClientSocket()
        assert manager_params.storage_controller_address is not None
        sock.connect(*manager_params.storage_controller_address)
        sock.send("fingerprintjs_stamp")
        sock.send(
            (
                STAMP_RESULTS_TABLE,
                {
                    "browser_id": self.browser_id,
                    "visit_id": self.visit_id,
                    "results": results_json or "{}",
                },
            )
        )
        sock.close()


def _create_stamp_results_table(db_path: Path) -> None:
    """Create the custom results table BEFORE the manager launches.

    SQLiteStorageProvider INSERTs into a table named in the incoming record and
    does not create it, so it has to exist on disk first.
    """
    db = sqlite3.connect(db_path)
    cur = db.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS %s ("
        "  browser_id INTEGER, visit_id INTEGER, results TEXT);" % STAMP_RESULTS_TABLE
    )
    db.commit()
    cur.close()
    db.close()


def _read_stamp_results(db_path: Path) -> Dict:
    rows = db_utils.query_db(
        db_path,
        f"SELECT results FROM {STAMP_RESULTS_TABLE} ORDER BY rowid;",
        as_tuple=True,
    )
    if not rows:
        return {}
    return json.loads(rows[-1][0])


def _javascript_capture(db_path: Path) -> Dict[str, object]:
    """How many JS API calls the arm actually recorded, and on which symbols.

    This is the arm's ACTIVITY CONTROL. Without it, "all three arms produced the
    same stamp" has a trivial and wrong explanation: the instrument never
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


def collect_stamp(params: Tuple[ManagerParams, List[BrowserParams]], url: str) -> Dict:
    """Run one arm once and return the probe page's report.

    The returned dict carries an extra ``_capture`` key (not produced by the
    page) holding the arm's JavaScript-capture activity control.
    """
    manager_params, browser_params = params
    db_path = manager_params.data_directory / "crawl-data.sqlite"
    _create_stamp_results_table(db_path)
    manager = TaskManager(
        manager_params, browser_params, SQLiteStorageProvider(db_path), None
    )
    cs = CommandSequence(url)
    cs.get(sleep=3)
    cs.append_command(ReadStampResults())
    manager.execute_command_sequence(cs)
    manager.close()
    report = _read_stamp_results(db_path)
    assert report, f"probe page produced no report for {manager_params.data_directory}"
    assert report.get("ok") is True, f"probe page errored: {report.get('error')}"
    report["_capture"] = _javascript_capture(db_path)
    return report


def component_hashes(report: Dict) -> Dict[str, str]:
    """Map probe name -> comparison key (its hash, or its error string).

    Spans BOTH the built-in FingerprintJS component set and the page's extra
    probes; the extras are named distinctly (``unstableCanvas_*`` etc.) so the
    two namespaces cannot collide.
    """
    out: Dict[str, str] = {}
    for section in ("components", "extras"):
        for name, entry in report[section].items():
            out[name] = entry["error"] if entry["error"] is not None else entry["hash"]
    return out


def builtin_names(report: Dict) -> Set[str]:
    """Just the built-in FingerprintJS sources -- the ones that feed visitorId."""
    return set(report["components"])


def stable_probes(reports: Dict[str, Dict], arms: List[str]) -> Set[str]:
    """Probes that reproduce across the two runs of EVERY arm.

    This is the validity gate. A probe that cannot reproduce itself under
    identical conditions cannot testify about instrumentation, so only this set
    is compared across arms. Derived from the data, never hardcoded.
    """
    runs = {name: component_hashes(report) for name, report in reports.items()}
    keysets = {name: frozenset(hashes) for name, hashes in runs.items()}
    assert len(set(keysets.values())) == 1, (
        "the probe set itself differs between runs: "
        f"{ {name: sorted(keys) for name, keys in keysets.items()} }"
    )
    stable: Set[str] = set(runs[f"{arms[0]}_a"])
    for arm in arms:
        a, b = runs[f"{arm}_a"], runs[f"{arm}_b"]
        stable &= {name for name in a if a[name] == b[name]}
    return stable


def differing_probes(
    report_a: Dict, report_b: Dict, restrict_to: Set[str]
) -> Dict[str, Tuple[str, str]]:
    """Probes in ``restrict_to`` whose value differs between two reports."""
    a, b = component_hashes(report_a), component_hashes(report_b)
    return {
        name: (a[name], b[name])
        for name in sorted(restrict_to)
        if a.get(name) != b.get(name)
    }


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
@pytest.mark.pyonly
def test_vendored_bundle_is_the_pinned_artifact() -> None:
    """The oracle must be the exact bundle whose provenance is recorded."""
    path = VENDORED_BUNDLE / VENDORED_BUNDLE_NAME
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == _VENDORED_SHA256, (
        f"{VENDORED_BUNDLE_NAME} does not match its pinned SHA-256. "
        "Update test_pages/vendor/README.md and _VENDORED_SHA256 together, and "
        "re-run the measurement in docs/developers/FingerprintJS-Visibility-Experiment.md."
    )


# --------------------------------------------------------------------------- #
# Recorded expectations
#
# These constants describe what was MEASURED (see
# docs/developers/FingerprintJS-Visibility-Experiment.md). If a future Firefox,
# FingerprintJS version or instrument change moves them, re-run the measurement
# and update the record rather than widening the tolerance.
# --------------------------------------------------------------------------- #
# FingerprintJS 5.2.0 ships exactly 42 built-in sources and every one of them
# yields a component on Firefox 154 -- sources that do not apply (userAgentData,
# cpuClass, deviceMemory, ...) report a value of `undefined` rather than dropping
# out. Pinned so a bundle swap that silently changes the surface is caught.
EXPECTED_BUILTIN_COMPONENTS = 42

# The forced-render canvas bytes differ on every launch. A bare-Selenium control
# with no OpenWPM shows the same (identical within one browser session, different
# across fresh launches, with every canvas-randomization pref off), so this is a
# Firefox property, not an instrumentation artifact. Documentation only:
# `stable_probes` derives the excluded set from the data.
EXPECTED_UNSTABLE_PROBES = {"unstableCanvas_geometry", "unstableCanvas_text"}

# Interfaces the probe page is known to drive that BOTH presets instrument. The
# activity control asserts capture on these, so "the stamps matched" can never be
# explained by "the instrument never attached".
REQUIRED_CAPTURE_PREFIXES = (
    "CanvasRenderingContext2D.",
    "HTMLCanvasElement.",
    "OscillatorNode.",
    "window.navigator.",
    "window.screen.",
)

ARMS = ["baseline", "stealth", "legacy"]
INSTRUMENTED_ARMS = ["stealth", "legacy"]
ARM_PARAMS = {
    "baseline": _baseline_params,
    "stealth": _stealth_params,
    "legacy": _legacy_params,
}


def _check_gate(stamps: Dict[str, Dict]) -> Set[str]:
    """VALIDITY GATE: which probes can testify at all.

    Two runs of each arm must reproduce the whole built-in component set (and
    therefore visitorId); only the forced-render canvas probes may drift.
    """
    for name, report in stamps.items():
        assert report["vendored"] == [VENDORED_BUNDLE_NAME], (
            f"{name}: probe page loaded {report['vendored']}, "
            f"not the pinned {VENDORED_BUNDLE_NAME}"
        )
    builtins = builtin_names(stamps["baseline_a"])
    assert len(builtins) == EXPECTED_BUILTIN_COMPONENTS
    stable = stable_probes(stamps, ARMS)
    unstable = set(component_hashes(stamps["baseline_a"])) - stable
    assert builtins <= stable, (
        "built-in FingerprintJS components are not reproducible run-to-run, so "
        f"they cannot discriminate anything: {sorted(builtins - stable)}"
    )
    for arm in ARMS:
        assert (
            stamps[f"{arm}_a"]["visitorId"] == stamps[f"{arm}_b"]["visitorId"]
        ), f"visitorId is not reproducible across two {arm} runs"
    assert unstable == EXPECTED_UNSTABLE_PROBES, (
        f"the set of irreproducible probes changed: expected "
        f"{sorted(EXPECTED_UNSTABLE_PROBES)}, observed {sorted(unstable)}. "
        "Re-run the measurement in "
        "docs/developers/FingerprintJS-Visibility-Experiment.md."
    )
    return stable


def _check_activity(stamps: Dict[str, Dict]) -> None:
    """ACTIVITY CONTROL: the instruments really ran and really saw this page.

    Without this, an identical stamp across arms has a trivial wrong
    explanation.
    """
    for run in ("baseline_a", "baseline_b"):
        capture = stamps[run]["_capture"]
        assert capture["rows"] == 0, (
            f"{run} is supposed to be uninstrumented but recorded "
            f"{capture['rows']} JavaScript calls"
        )
    for arm in INSTRUMENTED_ARMS:
        for run in ("a", "b"):
            capture = stamps[f"{arm}_{run}"]["_capture"]
            symbols = capture["symbols"]
            assert capture["rows"] > 0, f"{arm}_{run} captured nothing"
            for prefix in REQUIRED_CAPTURE_PREFIXES:
                assert any(s.startswith(prefix) for s in symbols), (
                    f"{arm}_{run} captured no {prefix}* calls, so the stamp "
                    f"comparison says nothing about that surface. Captured: {symbols}"
                )
            assert any("toDataURL" in s for s in symbols), (
                f"{arm}_{run} never saw canvas.toDataURL, so the canvas readback "
                "path was not instrumented during this measurement"
            )


@pytest.mark.usefixtures("xpi")
def test_fingerprintjs_cannot_distinguish_the_arms(
    tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
) -> None:
    """Neither stealth nor legacy moves a reproducible FingerprintJS component.

    Legacy is identical too, while capturing calls on the very surfaces the
    library reads: FingerprintJS OSS reads VALUES, and OpenWPM's wrappers are
    value-transparent. Its single `isFunctionNative` call site guards
    `window.print` inside a Safari-detection helper that Gecko never reaches.
    The vectors that do expose legacy (toString on wrapped natives, prototype
    shape) are covered by test_stealth.py::TestStealthDetectability. If this
    starts failing, an instrument has started leaking into a
    fingerprinting-visible value: re-run the measurement rather than relaxing
    the assertion.
    """
    url = _page_url(server, STAMP_PAGE)
    stamps: Dict[str, Dict] = {}
    for arm in ARMS:
        for run in ("a", "b"):
            data_dir = tmp_path_factory.mktemp(f"fpjs_{arm}_{run}")
            stamps[f"{arm}_{run}"] = collect_stamp(ARM_PARAMS[arm](data_dir), url)

    stable = _check_gate(stamps)
    _check_activity(stamps)

    baseline = stamps["baseline_a"]
    for arm in INSTRUMENTED_ARMS:
        leaked = differing_probes(baseline, stamps[f"{arm}_a"], stable)
        assert not leaked, (
            f"{arm} perturbed FingerprintJS components: {leaked}. Update "
            "docs/developers/FingerprintJS-Visibility-Experiment.md."
        )
        assert stamps[f"{arm}_a"]["visitorId"] == baseline["visitorId"]
