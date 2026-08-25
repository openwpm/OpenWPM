"""Does OpenWPM's instrumentation change what a real fingerprinter sees?

The stealth JavaScript instrument's headline claim is *zero visibility*: a
commodity fingerprinting library should compute the SAME stamp under stealth as
it does in an uninstrumented browser, while the legacy ``js_instrument``
perturbs it. Until this module existed the claim was asserted in prose only,
with no artifact in the repo. This measures it.

Three arms, one probe page (``test_pages/fingerprintjs_stamp.html``), identical
browser settings otherwise:

``baseline``
    ``js_instrument=False``, ``stealth_js_instrument=False`` -- pristine Firefox.
``stealth``
    ``stealth_js_instrument=True`` with the bundled default surface
    (``Extension/src/stealth/settings.ts``).
``legacy``
    ``js_instrument=True`` with ``js_instrument_settings=["collection_fingerprinting"]``
    -- **the project's own standard fingerprinting preset**
    (``openwpm/js_instrumentation_collections/fingerprinting.json``), which is
    also the ``BrowserParams`` default. It is spelled out explicitly here so it
    is evident on inspection that the legacy arm was not hand-tuned to fail.
    The two presets cover the same interfaces (audio nodes/contexts,
    RTCPeerConnection, HTMLCanvasElement, CanvasRenderingContext2D, Storage,
    Navigator, Screen, document, window), so the arms are comparable.

The comparison is per COMPONENT, not just ``visitorId``, so a failure names the
surface that leaked. ``visitorId`` alone is a poor oracle: it is a hash over all
components including run-to-run-unstable ones, so a single flaky source would
make it differ for reasons that have nothing to do with instrumentation.

**Validity gate.** ``test_baseline_stamp_is_stable`` runs the baseline arm TWICE
and derives the set of components that are reproducible in this environment.
Only that stable subset is compared across arms; unstable components are
reported and excluded. See ``docs/developers/FingerprintJS-Visibility-Experiment.md`` for the
recorded measurement this module's expectations were derived from.
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
    manager_params.testing = True
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


def stable_probes(report_a: Dict, report_b: Dict) -> Set[str]:
    """Probes that agree across two runs of the SAME configuration.

    This is the validity gate. A probe that cannot reproduce itself under
    identical conditions cannot testify about instrumentation, so only this set
    is compared across arms. Derived from the data -- never hardcoded -- so a
    newly-flaky surface is excluded automatically instead of causing a
    misattributed failure.
    """
    a, b = component_hashes(report_a), component_hashes(report_b)
    assert a.keys() == b.keys(), "the probe set itself differs between baseline runs"
    return {name for name in a if a[name] == b[name]}


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
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def stamps(
    tmp_path_factory: pytest.TempPathFactory, server: ServerUrls, xpi: None
) -> Dict[str, Dict]:
    """Run every arm exactly once and cache the reports for the whole module.

    Module-scoped because each arm is a full browser launch; re-running them per
    test would quadruple an already slow test. ``baseline_a``/``baseline_b`` are
    two runs of the IDENTICAL configuration -- they are the validity gate, not
    an arm.
    """
    url = _page_url(server, STAMP_PAGE)
    arms = {
        "baseline_a": _baseline_params,
        "baseline_b": _baseline_params,
        "stealth": _stealth_params,
        "legacy": _legacy_params,
    }
    reports = {}
    for name, factory in arms.items():
        data_dir = tmp_path_factory.mktemp(f"fpjs_{name}")
        reports[name] = collect_stamp(factory(data_dir), url)
    return reports


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
@pytest.mark.pyonly
def test_vendored_bundle_is_the_pinned_artifact() -> None:
    """The oracle must be the exact bundle whose provenance is recorded.

    Cheap, browser-free, and it runs first: if the fixture drifted, every other
    verdict in this module is about a different library.
    """
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
# docs/developers/FingerprintJS-Visibility-Experiment.md), not what would be convenient. If a
# future Firefox, FingerprintJS version or instrument change moves them, the
# right response is to re-run the measurement and update the record -- not to
# widen the tolerance until the suite goes quiet.
# --------------------------------------------------------------------------- #
# FingerprintJS 5.2.0 ships exactly 42 built-in sources and every one of them
# yields a component on Firefox 154 -- sources that do not apply (userAgentData,
# cpuClass, deviceMemory, ...) report a value of `undefined` rather than dropping
# out. Pinned so a bundle swap that silently changes the surface is caught.
EXPECTED_BUILTIN_COMPONENTS = 42

# Extra probes expected to be excluded by the validity gate in this environment.
# Firefox re-seeds canvas readback noise PER PROFILE and OpenWPM hands every
# browser launch a fresh temporary profile, so the rendered canvas bytes differ
# on every run regardless of instrumentation. Established as a BROWSER property,
# not an instrumentation artifact, by a control outside OpenWPM entirely: plain
# Firefox 154 driven by bare Selenium with no extension produced a different
# canvas hash from each fresh profile under stock prefs, with
# privacy.fingerprintingProtection / privacy.resistFingerprinting /
# privacy.resistFingerprinting.randomization.enabled all false, and with
# privacy.fingerprintingProtection.overrides="-CanvasRandomization"; while three
# consecutive loads inside ONE profile were byte-identical.
#
# This is documentation, not the exclusion mechanism: `stable_probes` derives the
# excluded set from the two baseline runs.
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


@pytest.mark.usefixtures("xpi", "server")
class TestFingerprintJSStamp:
    """The zero-visibility claim, measured against a real fingerprinting library."""

    def test_baseline_is_reproducible(self, stamps: Dict[str, Dict]) -> None:
        """VALIDITY GATE: establish which probes can testify at all.

        Runs before every cross-arm verdict for a reason -- an oracle that
        disagrees with itself proves nothing about instrumentation. Two runs of
        the IDENTICAL baseline configuration must reproduce the whole built-in
        component set (and therefore visitorId); only the forced-render canvas
        probes are permitted to drift, for the browser-side reason recorded on
        EXPECTED_UNSTABLE_PROBES.
        """
        a, b = stamps["baseline_a"], stamps["baseline_b"]
        assert len(builtin_names(a)) == EXPECTED_BUILTIN_COMPONENTS
        stable = stable_probes(a, b)
        unstable = set(component_hashes(a)) - stable

        assert builtin_names(a) <= stable, (
            "built-in FingerprintJS components are not reproducible baseline-to-"
            f"baseline, so they cannot discriminate anything: {sorted(builtin_names(a) - stable)}"
        )
        assert a["visitorId"] == b["visitorId"], (
            "visitorId is not reproducible across two identical baseline runs; "
            "it is not a usable oracle here and only the stable subset is"
        )
        assert unstable == EXPECTED_UNSTABLE_PROBES, (
            f"the set of irreproducible probes changed: expected "
            f"{sorted(EXPECTED_UNSTABLE_PROBES)}, observed {sorted(unstable)}. "
            "Re-run the measurement in docs/developers/FingerprintJS-Visibility-Experiment.md "
            "before trusting any verdict below."
        )

    def test_each_arm_instrumented_as_configured(self, stamps: Dict[str, Dict]) -> None:
        """ACTIVITY CONTROL: the instruments really did run and really did see this page.

        Without this, an identical stamp across arms has a trivial wrong
        explanation. Both instrumented arms must have captured calls on the
        canvas, oscillator, navigator and screen interfaces the probe page
        drives; the baseline arm must have captured nothing at all.
        """
        for arm in ("baseline_a", "baseline_b"):
            capture = stamps[arm]["_capture"]
            assert capture["rows"] == 0, (
                f"{arm} is supposed to be uninstrumented but recorded "
                f"{capture['rows']} JavaScript calls"
            )

        for arm in ("stealth", "legacy"):
            symbols = stamps[arm]["_capture"]["symbols"]
            assert stamps[arm]["_capture"]["rows"] > 0, f"{arm} captured nothing"
            for prefix in REQUIRED_CAPTURE_PREFIXES:
                assert any(s.startswith(prefix) for s in symbols), (
                    f"{arm} captured no {prefix}* calls, so the stamp comparison "
                    f"says nothing about that surface. Captured: {symbols}"
                )
            assert any("toDataURL" in s for s in symbols), (
                f"{arm} never saw canvas.toDataURL, so the canvas readback path "
                "was not actually instrumented during this measurement"
            )

    def test_stealth_stamp_is_identical_to_baseline(
        self, stamps: Dict[str, Dict]
    ) -> None:
        """CLAIM, first half -- CONFIRMED.

        Every reproducible probe FingerprintJS 5.2.0 exposes reads the same under
        the stealth instrument as in a pristine browser, and so does the derived
        visitorId. The activity control above proves the instrument was attached
        and capturing on these very surfaces while this held.
        """
        baseline = stamps["baseline_a"]
        stable = stable_probes(baseline, stamps["baseline_b"])
        leaked = differing_probes(baseline, stamps["stealth"], stable)
        assert not leaked, f"stealth perturbed FingerprintJS components: {leaked}"
        assert stamps["stealth"]["visitorId"] == baseline["visitorId"]

    def test_legacy_stamp_is_also_identical_to_baseline(
        self, stamps: Dict[str, Dict]
    ) -> None:
        """CLAIM, second half -- REFUTED. This test records the refutation.

        The claim was that the legacy instrument, unlike stealth, shifts the
        FingerprintJS stamp. It does not. With the project's own standard
        `collection_fingerprinting` preset, legacy reads identically to a
        pristine browser on every reproducible probe, visitorId included --
        while demonstrably capturing 92 calls across 39 symbols on the exact
        surfaces the probe page touches.

        The reason is a property of the oracle, not of the instrument:
        FingerprintJS OSS reads VALUES, and OpenWPM's wrappers are value-
        transparent. It performs no native-function integrity check on any
        instrumented surface -- its single `isFunctionNative` call site guards
        `window.print` inside a Safari-detection helper that Gecko never reaches.
        The surfaces where legacy IS detectable (Function.prototype.toString on
        wrapped natives, prototype-shape changes, arity/name drift) are the
        province of bot-detection scripts, which FingerprintJS OSS is not; those
        vectors are covered by test_stealth.py::TestStealthDetectability.

        So this asserts the measured relationship, not the hoped-for one. If it
        ever fails, legacy has started leaking into a fingerprinting-visible
        value -- a real finding either way. Re-run the measurement rather than
        relaxing the assertion.
        """
        baseline = stamps["baseline_a"]
        stable = stable_probes(baseline, stamps["baseline_b"])
        leaked = differing_probes(baseline, stamps["legacy"], stable)
        assert not leaked, (
            "legacy perturbed FingerprintJS components, contradicting the "
            f"recorded measurement: {leaked}. Update "
            "docs/developers/FingerprintJS-Visibility-Experiment.md and the docstring above."
        )
        assert stamps["legacy"]["visitorId"] == baseline["visitorId"]

    def test_stealth_is_never_more_visible_than_legacy(
        self, stamps: Dict[str, Dict]
    ) -> None:
        """The durable invariant, independent of how the two halves came out.

        Whatever a fingerprinter can see of the legacy instrument, it must not be
        able to see MORE of stealth. Today both leak nothing, so this holds
        vacuously -- but it is the assertion that keeps holding if legacy is ever
        fixed or stealth ever regresses, which the two tests above would not.
        """
        baseline = stamps["baseline_a"]
        stable = stable_probes(baseline, stamps["baseline_b"])
        stealth_leaks = set(differing_probes(baseline, stamps["stealth"], stable))
        legacy_leaks = set(differing_probes(baseline, stamps["legacy"], stable))
        assert stealth_leaks <= legacy_leaks, (
            "stealth is visible to FingerprintJS on surfaces where legacy is not: "
            f"{sorted(stealth_leaks - legacy_leaks)}"
        )
