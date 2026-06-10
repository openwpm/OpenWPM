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
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils

from . import utilities

DETECTION_URL = f"{utilities.BASE_TEST_URL}/stealth_detection.html"
SUPPRESS_URL = f"{utilities.BASE_TEST_URL}/stealth_disruption_suppress.html"
FORGE_URL = f"{utilities.BASE_TEST_URL}/stealth_disruption_forge.html"
ATTRIBUTION_URL = f"{utilities.BASE_TEST_URL}/stealth_attribution.html"
COOKIE_URL = f"{utilities.BASE_TEST_URL}/stealth_cookie.html"
IFRAME_URL = f"{utilities.BASE_TEST_URL}/stealth_disruption_iframe.html"


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
    """Read the detection page's ``data-results`` JSON into a file.

    Commands execute in a subprocess, so results are passed back via file.
    """

    def __init__(self, results_file: Path) -> None:
        self.results_file = results_file

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
        self.results_file.write_text(results_json or "{}")


def _collect_detection(
    params: Tuple[ManagerParams, List[BrowserParams]], results_file: Path
) -> Dict:
    """Run the detection page once and return its result dict."""
    manager_params, browser_params = params
    db_path = manager_params.data_directory / "crawl-data.sqlite"
    manager = TaskManager(
        manager_params, browser_params, SQLiteStorageProvider(db_path), None
    )
    cs = CommandSequence(DETECTION_URL)
    cs.get(sleep=2)
    cs.append_command(ReadDetectionResults(results_file))
    manager.execute_command_sequence(cs)
    manager.close()
    return json.loads(results_file.read_text()) if results_file.exists() else {}


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
]

_LEGACY_DETECTABLE = [r for r in DETECTABILITY_REQUIREMENTS if r[2]]


@pytest.mark.usefixtures("xpi", "server")
class TestStealthDetectability:
    """D* — the stealth instrument must be indistinguishable from a normal Firefox."""

    @pytest.fixture(scope="class")
    def stealth_results(self, tmp_path_factory: pytest.TempPathFactory) -> Dict:
        data_dir = tmp_path_factory.mktemp("stealth_detect")
        results = _collect_detection(
            _stealth_params(data_dir), data_dir / "results.json"
        )
        assert results, "no stealth detection results collected"
        return results

    @pytest.fixture(scope="class")
    def legacy_results(self, tmp_path_factory: pytest.TempPathFactory) -> Dict:
        data_dir = tmp_path_factory.mktemp("legacy_detect")
        results = _collect_detection(
            _legacy_params(data_dir), data_dir / "results.json"
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
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """Stealth must still actually capture JS API calls to the database."""
        data_dir = tmp_path_factory.mktemp("stealth_records")
        db_path = _run_page(_stealth_params(data_dir), DETECTION_URL)
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
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """X1 control: under legacy, neutering document.dispatchEvent drops records.

        Demonstrates the attack is real before asserting stealth resists it.
        """
        data_dir = tmp_path_factory.mktemp("x1_legacy")
        db_path = _run_page(_legacy_params(data_dir), SUPPRESS_URL)
        assert _todataurl_count(db_path) == 0, (
            "X1: legacy still recorded toDataURL calls after the page neutered "
            "document.dispatchEvent — the suppression control is ineffective"
        )

    def test_x1_stealth_channel_resists_suppression(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """X1: under stealth, the same attack must NOT drop records."""
        data_dir = tmp_path_factory.mktemp("x1_stealth")
        db_path = _run_page(_stealth_params(data_dir), SUPPRESS_URL)
        assert _todataurl_count(db_path) > 0, (
            "X1: stealth lost toDataURL records after the page neutered "
            "document.dispatchEvent — privileged messaging is not isolating delivery"
        )

    def test_x2_legacy_channel_can_be_forged(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """X2 control: under legacy, a page can inject a forged record.

        The page learns the secret DOM event id from a real dispatch and emits
        its own ``CustomEvent`` with that id, writing a fabricated row.
        """
        data_dir = tmp_path_factory.mktemp("x2_legacy")
        db_path = _run_page(_legacy_params(data_dir), FORGE_URL)
        assert _forged_count(db_path) > 0, (
            "X2: legacy did NOT accept the forged record — the forgery control "
            "is ineffective, so a stealth pass would be meaningless"
        )

    def test_x2_stealth_channel_rejects_forgery(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """X2: under stealth, the same forgery must NOT enter the database."""
        data_dir = tmp_path_factory.mktemp("x2_stealth")
        db_path = _run_page(_stealth_params(data_dir), FORGE_URL)
        assert _forged_count(db_path) == 0, (
            "X2: stealth accepted a forged record — a page-reachable channel "
            "into the dataset exists"
        )

    def test_attribution_stealth_records_page_script_and_clean_stack(
        self, tmp_path_factory: pytest.TempPathFactory
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
        db_path = _run_page(_attribution_stealth_params(data_dir), ATTRIBUTION_URL)
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
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """Reference: legacy also attributes the toDataURL call to the page."""
        data_dir = tmp_path_factory.mktemp("attr_legacy")
        db_path = _run_page(_legacy_params(data_dir), ATTRIBUTION_URL)
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
        self, tmp_path_factory: pytest.TempPathFactory
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
        db_path = _run_page(_stealth_params(data_dir), IFRAME_URL)
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
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """X3 control: legacy attributes the in-iframe call only to about:blank.

        Demonstrates the differential is real: legacy records the dynamic-frame
        toDataURL solely under ``about:blank`` (the frame's own URL), never
        under the parent page URL, so it lacks the parent-context attribution
        stealth's frame protection provides.
        """
        data_dir = tmp_path_factory.mktemp("x3_legacy")
        db_path = _run_page(_legacy_params(data_dir), IFRAME_URL)
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
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """A custom surface replaces the bundled default.

        The distinctive instrumentedName proves the configured set was used:
        ``CustomCanvasMarker.toDataURL`` cannot appear under the default config.
        """
        data_dir = tmp_path_factory.mktemp("config_custom")
        db_path = _run_page(_custom_stealth_params(data_dir), ATTRIBUTION_URL)
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
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """A custom surface must remain undetectable on every vector."""
        data_dir = tmp_path_factory.mktemp("config_undetect")
        results = _collect_detection(
            _custom_stealth_params(data_dir), data_dir / "results.json"
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
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """Under the stealth DEFAULT, document.cookie get/set is recorded.

        Legacy's ``collection_fingerprinting`` instruments
        ``document -> [cookie, referrer]``; the stealth default must match (the
        ``cookie`` entry was previously missing). Asserts a ``document.cookie``
        row lands in the ``javascript`` table without any custom settings.
        """
        data_dir = tmp_path_factory.mktemp("default_cookie")
        db_path = _run_page(_stealth_params(data_dir), COOKIE_URL)
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ?",
            ("document.cookie",),
        )
        assert rows[0][0] > 0, (
            "the stealth default surface did not record document.cookie access "
            "— the 'cookie' property is missing from the default document entry"
        )
