"""Requirement-driven tests for the stealth JavaScript instrumentation.

Each test maps to a numbered requirement in
``docs/developers/Stealth-Requirements.md``. Detectability requirements (D*)
assert the stealth instrument is undetectable where the legacy instrument is
detectable; disruptability requirements (X*) assert a hostile page cannot drop
or forge records under stealth where it can under legacy.

Based on Krumnow, Jonker & Karsch, "Analysing and strengthening OpenWPM's
reliability" (arXiv:2205.08890, 2022).

These tests:
- PASS when ``stealth_js_instrument=True`` (stealth extension active)
- demonstrate detection/disruption when ``js_instrument=True`` (legacy)
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

# Custom table the detection page's self-report JSON is routed into. Commands run
# in a subprocess and the StorageController runs in yet another process, so the
# on-disk crawl SQLite DB is the only reliable cross-process channel for the
# self-report. Following the proven custom-table idiom
# (``test/test_custom_function_command.py::test_custom_function``): the test
# CREATEs this table in the crawl DB before the crawl, the command sends rows over
# the storage socket, and the test reads them back AFTER ``manager.close()``. The
# table is created per-crawl in the test's temp DB, so it never touches the
# production schema.sql / parquet_schema.py.
DETECTION_RESULTS_TABLE = TableName("stealth_detection_results")

# Probe-page paths (relative to ``server.base``). The full URL is built per-test
# from the dynamic-port ``server`` fixture via ``_page_url`` so the suite can run
# against an OS-assigned port (see test/utilities.py::ServerUrls).
DETECTION_PAGE = "/stealth_detection.html"
SUPPRESS_PAGE = "/stealth_disruption_suppress.html"
FORGE_PAGE = "/stealth_disruption_forge.html"
ATTRIBUTION_PAGE = "/stealth_attribution.html"
COOKIE_PAGE = "/stealth_cookie.html"
IFRAME_PAGE = "/stealth_disruption_iframe.html"
WINDOW_NAME_PAGE = "/stealth_window_name.html"
PREVENT_SETS_PAGE = "/stealth_prevent_sets.html"
HONEY_PROPS_PAGE = "/stealth_honey_props.html"
RECURSIVE_PAGE = "/stealth_recursive.html"


def _page_url(server: ServerUrls, page: str) -> str:
    """Build a full probe-page URL from the dynamic test server base."""
    return server.base + page


# --------------------------------------------------------------------------- #
# Config helpers
# --------------------------------------------------------------------------- #
def _stealth_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params = ManagerParams(num_browsers=1)
    browser_params = [BrowserParams()]
    manager_params.data_directory = data_dir
    manager_params.log_path = data_dir / "openwpm.log"
    manager_params.testing = True
    browser_params[0].display_mode = "headless"
    browser_params[0].stealth_js_instrument = True
    browser_params[0].js_instrument = False
    return manager_params, browser_params


def _legacy_params(data_dir: Path) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params = ManagerParams(num_browsers=1)
    browser_params = [BrowserParams()]
    manager_params.data_directory = data_dir
    manager_params.log_path = data_dir / "openwpm.log"
    manager_params.testing = True
    browser_params[0].display_mode = "headless"
    browser_params[0].stealth_js_instrument = False
    browser_params[0].js_instrument = True
    return manager_params, browser_params


# A stealth surface that instruments HTMLCanvasElement with logCallStack=True so
# the attribution test can assert a NON-EMPTY call_stack. The bundled default
# leaves logCallStack False for canvas, so capturing a stack here doubles as
# proof the per-object logCallStack flag is honoured. Navigator keeps the
# webdriver->false override so the instrument stays undetectable.
ATTRIBUTION_STEALTH_SETTINGS: List[Dict] = [
    {
        "object": "HTMLCanvasElement",
        "instrumentedName": "HTMLCanvasElement",
        "depth": 1,
        "logSettings": {
            "propertiesToInstrument": [],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": ["style", "offsetWidth", "offsetHeight"],
            "overwrittenProperties": [],
            "logCallStack": True,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
        },
    },
    {
        "object": "Navigator",
        "instrumentedName": "Navigator",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": [],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "overwrittenProperties": [{"key": "webdriver", "value": False, "level": 0}],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
        },
    },
]


def _attribution_stealth_params(
    data_dir: Path,
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = ATTRIBUTION_STEALTH_SETTINGS
    return manager_params, browser_params


# --------------------------------------------------------------------------- #
# Crawl helpers
# --------------------------------------------------------------------------- #
class ReadDetectionResults(BaseCommand):
    """Scrape the detection page's ``data-results`` JSON and send it to storage.

    Commands execute in a subprocess and the StorageController runs in yet
    another process, so the result is passed back through the on-disk crawl
    SQLite DB. Following ``test_custom_function``, this opens its OWN
    ``ClientSocket`` directly to the storage controller (NOT ``extension_socket``,
    which talks to the extension's port and would mangle a raw record), sends a
    client name, then sends ``(table_name, {...,"visit_id":..., "browser_id":...})``.
    The StorageController INSERTs it into the ``stealth_detection_results`` custom
    table, and the test reads it back from the DB after ``manager.close()``.
    """

    def __repr__(self) -> str:
        return "ReadDetectionResults"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        WebDriverWait(webdriver, 10).until(
            lambda d: d.find_element("id", "results").get_attribute("data-results")
        )
        results_json = webdriver.execute_script(
            "return document.getElementById('results').getAttribute('data-results');"
        )
        sock = ClientSocket()
        assert manager_params.storage_controller_address is not None
        sock.connect(*manager_params.storage_controller_address)
        sock.send("stealth_detection")
        sock.send(
            (
                DETECTION_RESULTS_TABLE,
                {
                    "browser_id": self.browser_id,
                    "visit_id": self.visit_id,
                    "results": results_json or "{}",
                },
            )
        )
        sock.close()


def _create_detection_results_table(db_path: Path) -> None:
    """Create the custom detection-results table in the crawl DB.

    Must run BEFORE the manager launches: the SQLiteStorageProvider INSERTs into
    a table named in the incoming record and does not create it, so the table has
    to exist on disk first (mirrors ``test_custom_function``).
    """
    db = sqlite3.connect(db_path)
    cur = db.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS %s ("
        "  browser_id INTEGER, visit_id INTEGER, results TEXT);"
        % DETECTION_RESULTS_TABLE
    )
    db.commit()
    cur.close()
    db.close()


def _read_detection_results(db_path: Path) -> Dict:
    """Read back and decode the detection JSON from the on-disk crawl DB.

    Called AFTER ``manager.close()``, which joins the StorageController
    subprocess once it has finalized the visit and flushed its cache to the
    SQLite file. A detection run visits a single page, so there is at most one
    row; absence means the self-report never reached storage.
    """
    rows = db_utils.query_db(
        db_path,
        f"SELECT results FROM {DETECTION_RESULTS_TABLE} ORDER BY rowid;",
        as_tuple=True,
    )
    if not rows:
        return {}
    return json.loads(rows[-1][0])


def _collect_results(
    params: Tuple[ManagerParams, List[BrowserParams]], url: str
) -> Dict:
    """Run a self-reporting probe page once and return its result dict.

    The probe page publishes a JSON self-check on ``#results``;
    ``ReadDetectionResults`` ships it into the ``stealth_detection_results``
    custom table over the storage socket, and we read it back from the on-disk
    crawl DB after shutdown.
    """
    manager_params, browser_params = params
    db_path = manager_params.data_directory / "crawl-data.sqlite"
    _create_detection_results_table(db_path)
    manager = TaskManager(
        manager_params, browser_params, SQLiteStorageProvider(db_path), None
    )
    cs = CommandSequence(url)
    cs.get(sleep=2)
    cs.append_command(ReadDetectionResults())
    manager.execute_command_sequence(cs)
    manager.close()
    return _read_detection_results(db_path)


def _collect_detection(
    params: Tuple[ManagerParams, List[BrowserParams]],
    url: str,
) -> Dict:
    """Run the detection page once and return its result dict."""
    return _collect_results(params, url)


def _run_page(params: Tuple[ManagerParams, List[BrowserParams]], url: str) -> Path:
    """Visit ``url`` and return the sqlite db path for inspection."""
    manager_params, browser_params = params
    db_path = manager_params.data_directory / "crawl-data.sqlite"
    manager = TaskManager(
        manager_params, browser_params, SQLiteStorageProvider(db_path), None
    )
    cs = CommandSequence(url)
    cs.get(sleep=2)
    manager.execute_command_sequence(cs)
    manager.close()
    return db_path


# --------------------------------------------------------------------------- #
# Detectability requirements (D*)
#
# (requirement id, detection-page result key, legacy_detectable)
#   legacy_detectable=True  -> legacy is expected to TRIP this check
#                              (results[key] is not True under legacy)
#   legacy_detectable=None  -> legacy behaviour is environment/path-dependent;
#                              only the stealth direction is asserted.
# See docs/developers/Stealth-Requirements.md for the rationale per row.
# --------------------------------------------------------------------------- #
# legacy_detectable values below were ratcheted from an empirical Firefox 150
# run (unbranded add-on-devel) recording the legacy detection page results:
#   webdriver_flag=False, canvas/storage/rtc native=False, navigator_native=True,
#   no_global_leaks=False, constructors_present=False ("too much recursion"),
#   bind_integrity=True, clean_error_stacks=True, no_extra_prototype_properties=False.
# A False result means the legacy instrument was DETECTED, so legacy_detectable=True.
# D3/D6/D7 legacy results were True (not detected) in this build, so they stay
# None (stealth-only assertion) rather than asserting a control that does not hold.
DETECTABILITY_REQUIREMENTS: List[Tuple[str, str, Optional[bool]]] = [
    ("D1-webdriver-flag", "webdriver_flag", True),
    ("D2-native-fn-canvas", "canvas_functions_native", True),
    ("D2-native-fn-storage", "storage_functions_native", True),
    ("D2-native-fn-rtc", "rtc_native", True),
    ("D3-native-getter-navigator", "navigator_native", None),
    ("D4-no-global-leaks", "no_global_leaks", True),
    ("D5-constructors-present", "constructors_present", True),
    ("D6-bind-integrity", "bind_integrity", None),
    ("D7-clean-error-stacks", "clean_error_stacks", None),
    ("D8-no-prototype-pollution", "no_extra_prototype_properties", True),
    # D8b: instrumented functions must report the same arity (.length) as the
    # native function they replace. The legacy wrapper is `function () {...}`
    # (arity 0), so e.g. getContext.length becomes 0 where native is 1 — a
    # fingerprint; legacy_detectable=True. Stealth copies the native arity onto
    # the exported wrapper (copyFunctionArity in instrument.ts).
    ("D8b-native-fn-arity", "function_arity_native", True),
    # D9: the stealth instrument's prototype-walk helpers
    # (getPrototypeByDepth / getPropertyNamesPerDepth / findPropertyInChain on
    # Object.prototype, getPropertyDescriptor on Object) live in the isolated
    # content-script compartment, NOT on the page's Object. A page probing its
    # own Object must not observe them. legacy_detectable=None: legacy does not
    # define these helpers either, so this asserts only the stealth direction —
    # locking in the compartment isolation that keeps the helpers undetectable.
    ("D9-no-instrument-helpers", "no_instrument_helpers_leaked", None),
]

_LEGACY_DETECTABLE = [r for r in DETECTABILITY_REQUIREMENTS if r[2]]


@pytest.mark.usefixtures("xpi", "server")
class TestStealthDetectability:
    """D* — the stealth instrument must be indistinguishable from a normal Firefox."""

    @pytest.fixture(scope="class")
    def stealth_results(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Dict:
        data_dir = tmp_path_factory.mktemp("stealth_detect")
        results = _collect_detection(
            _stealth_params(data_dir), _page_url(server, DETECTION_PAGE)
        )
        assert results, "no stealth detection results collected"
        return results

    @pytest.fixture(scope="class")
    def legacy_results(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Dict:
        data_dir = tmp_path_factory.mktemp("legacy_detect")
        results = _collect_detection(
            _legacy_params(data_dir), _page_url(server, DETECTION_PAGE)
        )
        assert results, "no legacy detection results collected"
        return results

    @pytest.mark.parametrize(
        "req_id,key",
        [(r[0], r[1]) for r in DETECTABILITY_REQUIREMENTS],
        ids=[r[0] for r in DETECTABILITY_REQUIREMENTS],
    )
    def test_stealth_undetectable(
        self, stealth_results: Dict, req_id: str, key: str
    ) -> None:
        """Stealth must pass every detection vector (appear native)."""
        assert stealth_results.get(key) is True, (
            f"{req_id}: stealth is detectable via '{key}' "
            f"(page error: {stealth_results.get(key + '_error')})"
        )

    @pytest.mark.parametrize(
        "req_id,key",
        [(r[0], r[1]) for r in _LEGACY_DETECTABLE],
        ids=[r[0] for r in _LEGACY_DETECTABLE],
    )
    def test_legacy_detectable(
        self, legacy_results: Dict, req_id: str, key: str
    ) -> None:
        """Control: legacy must TRIP the reliable detection vectors.

        Proves the detection page actually works for each vector, so a stealth
        pass is meaningful rather than a no-op.
        """
        assert legacy_results.get(key) is not True, (
            f"{req_id}: legacy was NOT detected via '{key}' — the detection "
            f"page may be ineffective for this vector, weakening the stealth claim"
        )

    def test_stealth_records_js_calls(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Stealth must still actually capture JS API calls to the database."""
        data_dir = tmp_path_factory.mktemp("stealth_records")
        db_path = _run_page(
            _stealth_params(data_dir), _page_url(server, DETECTION_PAGE)
        )
        rows = db_utils.get_javascript_entries(db_path)
        assert len(rows) > 0, "stealth instrument recorded no JS calls"


# --------------------------------------------------------------------------- #
# Disruptability requirements (X*)
# --------------------------------------------------------------------------- #
def _todataurl_count(db_path: Path) -> int:
    rows = db_utils.query_db(
        db_path,
        "SELECT COUNT(*) FROM javascript WHERE symbol LIKE ?",
        ("%toDataURL%",),
    )
    return rows[0][0]


def _forged_count(db_path: Path) -> int:
    """Count rows bearing the symbol the forgery page tries to inject."""
    rows = db_utils.query_db(
        db_path,
        "SELECT COUNT(*) FROM javascript WHERE symbol = ?",
        ("FORGED.injectedByPage",),
    )
    return rows[0][0]


@pytest.mark.usefixtures("xpi", "server")
class TestStealthDisruption:
    """X* — a hostile page must not be able to drop or forge records."""

    def test_x1_legacy_channel_can_be_suppressed(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X1 control: under legacy, neutering document.dispatchEvent drops records.

        Demonstrates the attack is real before asserting stealth resists it.
        """
        data_dir = tmp_path_factory.mktemp("x1_legacy")
        db_path = _run_page(
            _legacy_params(data_dir), _page_url(server, SUPPRESS_PAGE)
        )
        assert _todataurl_count(db_path) == 0, (
            "X1: legacy still recorded toDataURL calls after the page neutered "
            "document.dispatchEvent — the suppression control is ineffective"
        )

    def test_x1_stealth_channel_resists_suppression(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X1: under stealth, the same attack must NOT drop records."""
        data_dir = tmp_path_factory.mktemp("x1_stealth")
        db_path = _run_page(
            _stealth_params(data_dir), _page_url(server, SUPPRESS_PAGE)
        )
        assert _todataurl_count(db_path) > 0, (
            "X1: stealth lost toDataURL records after the page neutered "
            "document.dispatchEvent — privileged messaging is not isolating delivery"
        )

    def test_x2_legacy_channel_can_be_forged(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X2 control: under legacy, a page can inject a forged record.

        The page learns the secret DOM event id from a real dispatch and emits
        its own ``CustomEvent`` with that id, writing a fabricated row.
        """
        data_dir = tmp_path_factory.mktemp("x2_legacy")
        db_path = _run_page(_legacy_params(data_dir), _page_url(server, FORGE_PAGE))
        assert _forged_count(db_path) > 0, (
            "X2: legacy did NOT accept the forged record — the forgery control "
            "is ineffective, so a stealth pass would be meaningless"
        )

    def test_x2_stealth_channel_rejects_forgery(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X2: under stealth, the same forgery must NOT enter the database."""
        data_dir = tmp_path_factory.mktemp("x2_stealth")
        db_path = _run_page(_stealth_params(data_dir), _page_url(server, FORGE_PAGE))
        assert _forged_count(db_path) == 0, (
            "X2: stealth accepted a forged record — a page-reachable channel "
            "into the dataset exists"
        )

    def test_attribution_stealth_records_page_script_and_clean_stack(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Stealth must attribute records to the page script with a clean stack.

        Guards the ``instrument.ts`` call_stack fix: the recorded toDataURL row
        must be attributed to this page's script (``script_url``) and its
        ``call_stack`` must contain only page frames, never ``moz-extension://``.

        Uses a custom ``stealth_js_instrument_settings`` that sets
        ``logCallStack: True`` for the canvas object. The bundled default leaves
        ``logCallStack`` False for ``HTMLCanvasElement``, so capturing a
        non-empty stack here ALSO proves the instrument honours the per-object
        ``logCallStack`` flag from settings (configurability) rather than
        hardcoding stack collection.
        """
        data_dir = tmp_path_factory.mktemp("attr_stealth")
        db_path = _run_page(
            _attribution_stealth_params(data_dir),
            _page_url(server, ATTRIBUTION_PAGE),
        )
        rows = db_utils.query_db(
            db_path,
            "SELECT script_url, call_stack FROM javascript WHERE symbol LIKE ?",
            ("%toDataURL%",),
            as_tuple=True,
        )
        assert rows, "stealth recorded no toDataURL row for the attribution page"
        assert any(
            "stealth_attribution.html" in (script_url or "") for script_url, _ in rows
        ), "stealth did not attribute the toDataURL call to the page script"
        assert any((call_stack or "").strip() for _, call_stack in rows), (
            "stealth recorded an EMPTY call_stack despite logCallStack=True in "
            "the custom settings — the per-object logCallStack flag is ignored"
        )
        for _, call_stack in rows:
            assert "moz-extension://" not in (call_stack or ""), (
                "stealth leaked a moz-extension:// frame into call_stack — "
                "the recorded stack is polluted with extension frames"
            )

    def test_attribution_legacy_records_page_script(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Reference: legacy also attributes the toDataURL call to the page."""
        data_dir = tmp_path_factory.mktemp("attr_legacy")
        db_path = _run_page(
            _legacy_params(data_dir), _page_url(server, ATTRIBUTION_PAGE)
        )
        rows = db_utils.query_db(
            db_path,
            "SELECT script_url FROM javascript WHERE symbol LIKE ?",
            ("%toDataURL%",),
            as_tuple=True,
        )
        assert rows, "legacy recorded no toDataURL row for the attribution page"
        assert any(
            "stealth_attribution.html" in (script_url or "") for (script_url,) in rows
        ), "legacy did not attribute the toDataURL call to the page script"

    def test_x3_stealth_instruments_dynamic_iframe(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X3: stealth records the in-iframe toDataURL under the parent's URL.

        The page JS-creates an iframe (``createElement`` + ``appendChild``) and
        runs ``canvas.toDataURL`` inside the new frame's document. Stealth's
        frame protection (``stealth.ts`` contentWindow/contentDocument hooks +
        MutationObserver) injects into the dynamic frame within the parent
        page's instrumented context, so a toDataURL row is recorded bearing the
        PARENT page's ``document_url``.

        Empirical (Firefox 150, headless, 3 runs): stealth records 2 toDataURL
        rows (``about:blank`` AND the parent URL); legacy records 1 (only
        ``about:blank``). The parent-URL row is the stable differential — see
        ``test_x3_legacy_misses_dynamic_iframe_parent_attribution``.
        """
        data_dir = tmp_path_factory.mktemp("x3_stealth")
        db_path = _run_page(_stealth_params(data_dir), _page_url(server, IFRAME_PAGE))
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript "
            "WHERE symbol LIKE ? AND document_url LIKE ?",
            ("%toDataURL%", "%stealth_disruption_iframe.html%"),
        )
        assert rows[0][0] > 0, (
            "X3: stealth did not record the dynamic-iframe toDataURL under the "
            "parent page document_url — frame protection did not instrument the "
            "dynamically-created iframe"
        )

    def test_x3_legacy_misses_dynamic_iframe_parent_attribution(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X3 control: legacy attributes the in-iframe call only to about:blank.

        Demonstrates the differential is real: legacy records the dynamic-frame
        toDataURL solely under ``about:blank`` (the frame's own URL), never
        under the parent page URL, so it lacks the parent-context attribution
        stealth's frame protection provides.
        """
        data_dir = tmp_path_factory.mktemp("x3_legacy")
        db_path = _run_page(_legacy_params(data_dir), _page_url(server, IFRAME_PAGE))
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript "
            "WHERE symbol LIKE ? AND document_url LIKE ?",
            ("%toDataURL%", "%stealth_disruption_iframe.html%"),
        )
        assert rows[0][0] == 0, (
            "X3 control: legacy unexpectedly attributed the dynamic-iframe "
            "toDataURL to the parent page document_url — the stealth/legacy "
            "differential this test relies on no longer holds"
        )


# --------------------------------------------------------------------------- #
# Configurability (the stealth surface is runtime-configurable)
# --------------------------------------------------------------------------- #
# A custom stealth surface that instruments HTMLCanvasElement under a distinctive
# instrumentedName so the recorded symbol (``CustomCanvasMarker.toDataURL``) can
# ONLY appear if this config replaced the bundled default (which uses
# instrumentedName "HTMLCanvasElement"). The Navigator entry keeps the
# webdriver->false override so the instrument stays undetectable.
CUSTOM_INSTRUMENTED_NAME = "CustomCanvasMarker"
CUSTOM_STEALTH_SETTINGS: List[Dict] = [
    {
        "object": "HTMLCanvasElement",
        "instrumentedName": CUSTOM_INSTRUMENTED_NAME,
        "depth": 1,
        "logSettings": {
            "propertiesToInstrument": [],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": ["style", "offsetWidth", "offsetHeight"],
            "overwrittenProperties": [],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
        },
    },
    {
        "object": "Navigator",
        "instrumentedName": "Navigator",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": [],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "overwrittenProperties": [{"key": "webdriver", "value": False, "level": 0}],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
        },
    },
]


def _custom_stealth_params(
    data_dir: Path,
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = CUSTOM_STEALTH_SETTINGS
    return manager_params, browser_params


@pytest.mark.usefixtures("xpi", "server")
class TestStealthConfigurability:
    """The stealth instrumentation surface is configurable at runtime."""

    def test_custom_settings_take_effect(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """A custom surface replaces the bundled default.

        The distinctive instrumentedName proves the configured set was used:
        ``CustomCanvasMarker.toDataURL`` cannot appear under the default config.
        """
        data_dir = tmp_path_factory.mktemp("config_custom")
        db_path = _run_page(
            _custom_stealth_params(data_dir), _page_url(server, ATTRIBUTION_PAGE)
        )
        custom_rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ?",
            (f"{CUSTOM_INSTRUMENTED_NAME}.toDataURL",),
        )
        assert custom_rows[0][0] > 0, (
            "custom stealth_js_instrument_settings did not take effect: no "
            f"'{CUSTOM_INSTRUMENTED_NAME}.toDataURL' records were captured"
        )
        default_rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ?",
            ("HTMLCanvasElement.toDataURL",),
        )
        assert default_rows[0][0] == 0, (
            "the bundled default surface was still active alongside the custom "
            "one ('HTMLCanvasElement.toDataURL' present)"
        )

    def test_custom_settings_stay_undetectable(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """A custom surface must remain undetectable on every vector."""
        data_dir = tmp_path_factory.mktemp("config_undetect")
        results = _collect_detection(
            _custom_stealth_params(data_dir), _page_url(server, DETECTION_PAGE)
        )
        assert results, "no detection results collected for custom stealth config"
        for req_id, key, _ in DETECTABILITY_REQUIREMENTS:
            assert results.get(key) is True, (
                f"{req_id}: custom stealth config is detectable via '{key}' "
                f"(page error: {results.get(key + '_error')})"
            )


# --------------------------------------------------------------------------- #
# Default-surface coverage (the bundled stealth default captures cookies)
# --------------------------------------------------------------------------- #
@pytest.mark.usefixtures("xpi", "server")
class TestStealthDefaultSurface:
    """The bundled stealth default captures the documented fingerprint surface."""

    def test_default_captures_document_cookie(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Under the stealth DEFAULT, document.cookie get/set is recorded.

        Legacy's ``collection_fingerprinting`` instruments
        ``document -> [cookie, referrer]``; the stealth default must match (the
        ``cookie`` entry was previously missing). Asserts a ``document.cookie``
        row lands in the ``javascript`` table without any custom settings.
        """
        data_dir = tmp_path_factory.mktemp("default_cookie")
        db_path = _run_page(_stealth_params(data_dir), _page_url(server, COOKIE_PAGE))
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ?",
            ("document.cookie",),
        )
        assert rows[0][0] > 0, (
            "the stealth default surface did not record document.cookie access "
            "— the 'cookie' property is missing from the default document entry"
        )


# --------------------------------------------------------------------------- #
# window.name (and window-level localStorage / sessionStorage) capture
#
# Legacy OpenWPM instruments the window INSTANCE via
# {"window": ["name", "localStorage", "sessionStorage"]}. Those members are
# accessor properties on Window.prototype (depth 1 from the window instance);
# the stealth default reaches them via that depth and redefines the native
# accessor in place. These tests assert (a) get/set are captured at legacy
# fidelity and (b) the instrumentation stays undetectable — the page cannot tell
# window.name was touched.
# --------------------------------------------------------------------------- #
def _window_name_results(
    params: Tuple[ManagerParams, List[BrowserParams]],
    url: str,
) -> Dict:
    """Run the window.name probe page and return its self-detection dict."""
    return _collect_results(params, url)


@pytest.mark.usefixtures("xpi", "server")
class TestStealthWindowName:
    """The bundled stealth default captures window.name get/set, undetectably."""

    def test_default_captures_window_name_get_and_set(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Under the stealth DEFAULT, window.name get AND set are recorded.

        Legacy instruments the window instance with
        ``{"window": ["name", "localStorage", "sessionStorage"]}``; the stealth
        default must match. Asserts both a ``set`` and a ``get`` row for
        ``window.name`` land in the ``javascript`` table without custom settings.
        """
        data_dir = tmp_path_factory.mktemp("window_name_capture")
        db_path = _run_page(
            _stealth_params(data_dir), _page_url(server, WINDOW_NAME_PAGE)
        )
        get_rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ? AND operation = ?",
            ("window.name", "get"),
        )
        assert get_rows[0][0] > 0, (
            "the stealth default surface did not record a window.name GET — the "
            "'name' property is missing from the default window entry"
        )
        set_rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ? AND operation = ?",
            ("window.name", "set"),
        )
        assert set_rows[0][0] > 0, (
            "the stealth default surface did not record a window.name SET — the "
            "setter on Window.prototype was not instrumented"
        )

    def test_default_captures_window_storage_property_gets(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Window-level localStorage / sessionStorage property GETS are recorded.

        Legacy's narrow window list also instruments the window-level
        ``localStorage`` / ``sessionStorage`` getters (distinct from the Storage
        prototype methods). Asserts both land in the ``javascript`` table.
        """
        data_dir = tmp_path_factory.mktemp("window_storage_capture")
        db_path = _run_page(
            _stealth_params(data_dir), _page_url(server, WINDOW_NAME_PAGE)
        )
        for prop in ("window.localStorage", "window.sessionStorage"):
            rows = db_utils.query_db(
                db_path,
                "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
                (prop, "get"),
            )
            assert rows[0][0] > 0, (
                f"the stealth default surface did not record a {prop} GET — the "
                "window-level storage getter was not instrumented"
            )

    def test_window_name_instrumentation_undetectable(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Under stealth, the page cannot tell window.name was instrumented.

        The probe page reads the Window.prototype accessor descriptors and
        checks (1) the get/set still report ``[native code]`` and (2) no own
        property shadows them on the window instance. Every check must be True.
        """
        data_dir = tmp_path_factory.mktemp("window_name_stealth_detect")
        results = _window_name_results(
            _stealth_params(data_dir), _page_url(server, WINDOW_NAME_PAGE)
        )
        assert results, "no window.name probe results collected under stealth"
        for key in (
            "name_getter_native",
            "name_setter_native",
            "localStorage_getter_native",
            "sessionStorage_getter_native",
            "name_not_own_on_instance",
            "localStorage_not_own_on_instance",
            "sessionStorage_not_own_on_instance",
            "name_roundtrips",
        ):
            assert results.get(key) is True, (
                f"stealth window.name instrumentation is detectable via '{key}' "
                f"(probe error: {results.get('descriptor_error')})"
            )

    def test_legacy_window_name_is_detectable(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Control: legacy's window.name getter is NOT native (detectable).

        Proves the undetectability check above is meaningful: the legacy
        instrument replaces the accessor with a JS wrapper whose ``toString`` no
        longer reports ``[native code]``, so at least one nativeness check trips.
        """
        data_dir = tmp_path_factory.mktemp("window_name_legacy_detect")
        results = _window_name_results(
            _legacy_params(data_dir), _page_url(server, WINDOW_NAME_PAGE)
        )
        assert results, "no window.name probe results collected under legacy"
        # Legacy is detectable if it leaves ANY page-observable artifact on the
        # window.name plumbing: either the Window.prototype accessor stopped
        # reporting [native code], or a wrapper shadowed it as an own property
        # on the window instance. The stealth test above asserts NEITHER holds.
        undetectable_signals = [
            results.get("name_getter_native") is True,
            results.get("name_setter_native") is True,
            results.get("name_not_own_on_instance") is True,
        ]
        assert not all(undetectable_signals), (
            "legacy left window.name looking pristine (native accessors, no "
            "instance own-property) — the detection vector is ineffective, so a "
            "stealth pass on the same vector would be meaningless"
        )


# --------------------------------------------------------------------------- #
# logSettings fidelity: preventSets, logFunctionGets, recursive/depth,
# nonExistingPropertiesToInstrument. Each was previously inert in the stealth
# instrument (present in settings/schema but never read). These tests prove the
# stealth instrument now honours each, matching legacy semantics, while staying
# native-looking where the property is on a native object.
# --------------------------------------------------------------------------- #
def _probe_results(params: Tuple[ManagerParams, List[BrowserParams]], url: str) -> Dict:
    """Visit a probe page that publishes a self-check JSON on #results."""
    return _collect_results(params, url)


def _log_settings(**overrides: object) -> Dict:
    """A fully-defaulted stealth logSettings object with optional overrides."""
    base = {
        "propertiesToInstrument": [],
        "nonExistingPropertiesToInstrument": [],
        "excludedProperties": [],
        "overwrittenProperties": [],
        "logCallStack": False,
        "logFunctionsAsStrings": False,
        "logFunctionGets": False,
        "preventSets": False,
        "recursive": False,
        "depth": 5,
    }
    base.update(overrides)
    return base


# preventSets: instrument document.body (an accessor whose value is the <body>
# element, an object) with preventSets:true. Assignments must be logged as
# set(prevented) and blocked.
PREVENT_SETS_SETTINGS: List[Dict] = [
    {
        "object": "document",
        "instrumentedName": "document",
        "depth": 0,
        "logSettings": _log_settings(
            propertiesToInstrument=[{"depth": 1, "propertyNames": ["body"]}],
            preventSets=True,
        ),
    },
]

# nonExisting + logFunctionGets on Navigator (a honey property).
HONEY_SETTINGS: List[Dict] = [
    {
        "object": "Navigator",
        "instrumentedName": "Navigator",
        "depth": 0,
        "logSettings": _log_settings(
            nonExistingPropertiesToInstrument=["openwpmHoneyProp"],
            logFunctionGets=True,
        ),
    },
]

# recursive/depth: a honey object on Navigator instrumented recursively. Lazy
# recursion descends into the object the getter returns at access time.
RECURSIVE_SETTINGS: List[Dict] = [
    {
        "object": "Navigator",
        "instrumentedName": "Recursive",
        "depth": 0,
        "logSettings": _log_settings(
            nonExistingPropertiesToInstrument=["openwpmRecObj"],
            recursive=True,
            depth=3,
        ),
    },
]


def _params_with(
    data_dir: Path, settings: List[Dict]
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = settings
    return manager_params, browser_params


@pytest.mark.usefixtures("xpi", "server")
class TestStealthLogSettings:
    """The previously-inert logSettings are honoured by the stealth instrument."""

    def test_prevent_sets_blocks_and_logs(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """preventSets logs set(prevented) and does NOT call the original setter.

        document.body holds an object value, so under preventSets an assignment
        is recorded as set(prevented) and blocked — document.body is unchanged.
        """
        data_dir = tmp_path_factory.mktemp("prevent_sets")
        db_path = _run_page(
            _params_with(data_dir, PREVENT_SETS_SETTINGS),
            _page_url(server, PREVENT_SETS_PAGE),
        )
        prevented = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
            ("document.body", "set(prevented)"),
        )
        assert (
            prevented[0][0] > 0
        ), "preventSets did not record a set(prevented) row for document.body"
        # And the original setter must NOT have run.
        plain_set = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
            ("document.body", "set"),
        )
        assert plain_set[0][0] == 0, (
            "preventSets still emitted a plain 'set' for document.body — the "
            "write was not actually prevented"
        )

    def test_prevent_sets_stays_undetectable_and_blocks(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """The page sees the write blocked AND the accessor still native."""
        data_dir = tmp_path_factory.mktemp("prevent_sets_detect")
        results = _probe_results(
            _params_with(data_dir, PREVENT_SETS_SETTINGS),
            _page_url(server, PREVENT_SETS_PAGE),
        )
        assert results, "no preventSets probe results collected"
        assert results.get("body_unchanged") is True, (
            "preventSets did not block the document.body assignment "
            f"(probe error: {results.get('descriptor_error')})"
        )
        assert results.get("body_not_replaced") is True
        # The instrumented accessor must still report [native code].
        assert (
            results.get("body_setter_native") is True
        ), "document.body setter no longer reports [native code] under preventSets"
        assert results.get("body_getter_native") is True

    def test_non_existing_property_captured_and_native(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """A honey property is captured (get/set) and looks native.

        nonExistingPropertiesToInstrument synthesizes a native-looking accessor
        for a name absent from Navigator.prototype, so get/set on it are
        recorded under the javascript table.
        """
        data_dir = tmp_path_factory.mktemp("honey")
        db_path = _run_page(
            _params_with(data_dir, HONEY_SETTINGS),
            _page_url(server, HONEY_PROPS_PAGE),
        )
        sets = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
            ("Navigator.openwpmHoneyProp", "set"),
        )
        assert sets[0][0] > 0, (
            "nonExistingPropertiesToInstrument did not capture a set on the "
            "synthesized honey property"
        )
        gets = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
            ("Navigator.openwpmHoneyProp", "get"),
        )
        assert gets[0][0] > 0, (
            "nonExistingPropertiesToInstrument did not capture a get on the "
            "synthesized honey property"
        )

    def test_log_function_gets_emits_get_function(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """logFunctionGets records get(function) when the value is a function.

        After the page assigns a function to the honey property, reading it
        WITHOUT calling must emit a get(function) row (and no plain get for the
        function value), matching legacy.
        """
        data_dir = tmp_path_factory.mktemp("fn_gets")
        db_path = _run_page(
            _params_with(data_dir, HONEY_SETTINGS),
            _page_url(server, HONEY_PROPS_PAGE),
        )
        fn_gets = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
            ("Navigator.openwpmHoneyProp", "get(function)"),
        )
        assert fn_gets[0][0] > 0, (
            "logFunctionGets did not record a get(function) row when the honey "
            "property held a function value"
        )

    def test_honey_property_stays_native(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """The synthesized honey accessor reports [native code]."""
        data_dir = tmp_path_factory.mktemp("honey_detect")
        results = _probe_results(
            _params_with(data_dir, HONEY_SETTINGS),
            _page_url(server, HONEY_PROPS_PAGE),
        )
        assert results, "no honey-property probe results collected"
        assert results.get("value_roundtrips") is True
        assert results.get("function_roundtrips") is True
        assert results.get("honey_getter_native") is True, (
            "synthesized honey getter does not report [native code] "
            f"(probe error: {results.get('descriptor_error')})"
        )
        assert (
            results.get("honey_setter_native") is True
        ), "synthesized honey setter does not report [native code]"

    def test_recursive_captures_nested_access(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """recursive/depth instruments objects returned by instrumented getters.

        Reading a deep leaf of a nested object stored on the honey property is
        captured under the recursive symbol path.
        """
        data_dir = tmp_path_factory.mktemp("recursive")
        db_path = _run_page(
            _params_with(data_dir, RECURSIVE_SETTINGS),
            _page_url(server, RECURSIVE_PAGE),
        )
        leaf = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ?",
            ("Recursive.openwpmRecObj.inner.leaf",),
        )
        assert leaf[0][0] > 0, (
            "recursive instrumentation did not capture the nested leaf access "
            "Recursive.openwpmRecObj.inner.leaf — recursion did not descend into "
            "the object returned by the instrumented getter"
        )

    def test_recursive_roundtrips(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Recursion must not corrupt values the page reads back."""
        data_dir = tmp_path_factory.mktemp("recursive_detect")
        results = _probe_results(
            _params_with(data_dir, RECURSIVE_SETTINGS),
            _page_url(server, RECURSIVE_PAGE),
        )
        assert results, "no recursive probe results collected"
        assert results.get("leaf_roundtrips") is True, (
            "recursive instrumentation corrupted the nested leaf value the page "
            "read back"
        )
