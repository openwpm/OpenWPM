"""Requirement-driven tests for the stealth JavaScript instrumentation.

Each test maps to a numbered requirement in
``docs/developers/Stealth-Requirements.rst``, which in turn ``literalinclude``s
many of these test bodies — so the spec and the tests cross-reference each
other. Detectability requirements (D*) assert the stealth instrument is
undetectable where the legacy instrument is detectable; disruptability
requirements (X*) assert a hostile page cannot drop or forge records under
stealth where it can under legacy. The detection/disruption mechanisms each
vector exploits are described in ``docs/developers/Stealth-Instrumentation.rst``,
and why the legacy instrument is kept alongside stealth in
``docs/developers/Stealth-and-Legacy-JS-Instruments.rst``.

Based on Krumnow, Jonker & Karsch, "Analysing and strengthening OpenWPM's
reliability" (arXiv:2205.08890, 2022).

These tests:
- PASS when ``stealth_js_instrument=True`` (stealth extension active)
- demonstrate detection/disruption when ``js_instrument=True`` (legacy)
"""

import json
import sqlite3
import typing
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

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
# Differential probe compared verbatim against an uninstrumented run.
NATIVE_PARITY_PAGE = "/stealth_native_parity.html"
# Page-initiated calls that a stealth crawl must record exactly once.
RECORD_INTEGRITY_PAGE = "/stealth_record_integrity.html"
POPUP_PAGE = "/stealth_popup.html"
FRAME_OWNERSHIP_PAGE = "/stealth_frame_ownership.html"
FIRST_LOAD_PAGE = "/stealth_first_load.html"
DEAD_REALM_PAGE = "/stealth_dead_realm.html"
WINDOW_NAME_PAGE = "/stealth_window_name.html"
# Provokes errors THROUGH instrumented methods (a native DOMException, a built-in
# TypeError, a page custom Error subclass, and an async rejection) and
# self-reports each observed error's identity and shape, so a stealth run can be
# diffed against an uninstrumented run for drift. See TestStealthErrorDrift.
ERROR_DRIFT_PAGE = "/stealth_error_drift.html"
# Reads screen.width and screen.height.
SCREEN_PAGE = "/stealth_screen.html"
PREVENT_SETS_PAGE = "/stealth_prevent_sets.html"
HONEY_PROPS_PAGE = "/stealth_honey_props.html"
# Calls an instrumented method (EventTarget.addEventListener) with a function as
# an argument, so the recorded ``arguments`` can be checked for whether the
# function was serialized as its source string or as the placeholder "FUNCTION".
FUNCTION_ARG_PAGE = "/stealth_function_arg.html"


# Calls EventTarget.prototype.addEventListener on two different receiver
# interfaces (HTMLDivElement and XMLHttpRequest), each tampering with its own
# `constructor`, to exercise interface-attributed shared-prototype capture: the
# targeted interface must be recorded under the static symbol
# "EventTarget.addEventListener" with the receiver interface in the dedicated
# `receiver` column, while the non-targeted interface is filtered out
# instrument-side.
SHARED_PROTOTYPE_PAGE = "/stealth_shared_prototype.html"
# Calls THREE inherited methods of EventTarget.prototype (addEventListener,
# removeEventListener, dispatchEvent) on one targeted receiver (HTMLDivElement).
# All three share ONE prototype object; a config instrumenting all three must
# capture every one, not only the first.
SHARED_PROTOTYPE_MULTI_PAGE = "/stealth_shared_prototype_multi.html"


# Recursive instrumentation is unsupported under stealth (rejected at config
# time with a ConfigError), so there is no stealth recursive probe page — the
# rejection is verified purely at the config layer.


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


def _uninstrumented_params(
    data_dir: Path,
) -> Tuple[ManagerParams, List[BrowserParams]]:
    """Neither instrument enabled — the page runs in a pristine Firefox.

    The ground truth the differential stealth tests compare against.
    """
    manager_params = ManagerParams(num_browsers=1)
    browser_params = [BrowserParams()]
    manager_params.data_directory = data_dir
    manager_params.log_path = data_dir / "openwpm.log"
    manager_params.testing = True
    browser_params[0].display_mode = "headless"
    browser_params[0].stealth_js_instrument = False
    browser_params[0].js_instrument = False
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
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": [],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
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


class ExposeWindowNuking(BaseCommand):
    """Give pages whose URL contains ``marker`` two test-only globals:
    ``innerWindowIdForTest(win)`` and ``isNukedForTest(id)``, true once
    Firefox has cut the privileged wrappers into that inner window.

    ``inner-window-nuked`` is notified in the runnable that cuts them, so a
    page task that sees it true runs after the cut.
    """

    PROCESS_SCRIPT = """
        const nuked = new Set();
        Services.obs.addObserver((id) => {
            nuked.add(id.QueryInterface(Components.interfaces.nsISupportsPRUint64).data);
        }, "inner-window-nuked");
        Services.obs.addObserver((win) => {
            if (!String(win.document?.documentURI).includes(MARKER)) {
                return;
            }
            const exp = (f, name) => Components.utils.exportFunction(f, win, { defineAs: name });
            exp((w) => w.windowGlobalChild.innerWindowId, "innerWindowIdForTest");
            exp((id) => nuked.has(id), "isNukedForTest");
        }, "content-document-global-created");
    """

    def __init__(self, marker: str) -> None:
        self.marker = marker

    def __repr__(self) -> str:
        return "ExposeWindowNuking"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        script = "const MARKER = %s;%s" % (json.dumps(self.marker), self.PROCESS_SCRIPT)
        with webdriver.context(webdriver.CONTEXT_CHROME):
            webdriver.execute_script(
                "Services.ppmm.loadProcessScript(arguments[0], true);",
                "data:," + quote(script),
            )


def _collect_results(
    params: Tuple[ManagerParams, List[BrowserParams]],
    url: str,
    setup: Optional[BaseCommand] = None,
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
    if setup is not None:
        cs.append_command(setup)
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
# See the "Detectability requirements" section of
# ``docs/developers/Stealth-Requirements.rst`` (the D1-D9 table, which
# ``literalinclude``s the tests below) for the per-row rationale, and
# ``docs/developers/Stealth-Instrumentation.rst`` ("Detectability (a property of
# the legacy instrument)") for the mechanism each vector exploits.
#
# Each row is a ``DetectabilityRequirement`` with three named fields:
#   req_id            -- stable D* identifier (also the parametrize test id)
#   result_key        -- key under which the detection page self-reports the
#                        vector's pass/fail on ``#results``
#   legacy_detectable -- THREE-state control flag (kept Optional[bool], NOT
#                        collapsed to bool, because None is a distinct "N/A"
#                        state, not False):
#     True  -> legacy is expected to TRIP this check, so a control test asserts
#              legacy is detected (``results[result_key] is not True``).
#     None  -> legacy behaviour is environment/path-dependent in this build, so
#              NO legacy control is asserted; only the stealth direction is
#              tested. Collapsing None to False would wrongly claim legacy is
#              provably-undetectable here and would not change ``_LEGACY_DETECTABLE``
#              (which filters on truthiness either way) — so the third state is
#              retained to keep the documented meaning.
#   (No row is False: every vector is either an asserted control (True) or
#    not-asserted/env-dependent (None).)
# --------------------------------------------------------------------------- #
# legacy_detectable values below were ratcheted from an empirical Firefox 150
# run (unbranded add-on-devel) recording the legacy detection page results:
#   webdriver_flag=False, canvas/storage/rtc native=False, navigator_native=True,
#   no_global_leaks=False, constructors_present=False ("too much recursion"),
#   bind_integrity=True, clean_error_stacks=True, no_extra_prototype_properties=False.
# A False result means the legacy instrument was DETECTED, so legacy_detectable=True.
# D3/D6/D7 legacy results were True (not detected) in this build, so they stay
# None (stealth-only assertion) rather than asserting a control that does not hold.
class DetectabilityRequirement(typing.NamedTuple):
    """One D* detection vector: id, self-report key, and legacy control flag.

    ``legacy_detectable`` is intentionally ``Optional[bool]`` (three-state, see
    the block comment above): ``True`` asserts a legacy control, ``None`` skips
    it as environment-dependent. It is never ``False``.
    """

    req_id: str
    result_key: str
    legacy_detectable: Optional[bool]


DETECTABILITY_REQUIREMENTS: List[DetectabilityRequirement] = [
    DetectabilityRequirement("D1-webdriver-flag", "webdriver_flag", True),
    DetectabilityRequirement("D2-native-fn-canvas", "canvas_functions_native", True),
    DetectabilityRequirement("D2-native-fn-storage", "storage_functions_native", True),
    DetectabilityRequirement("D2-native-fn-rtc", "rtc_native", True),
    DetectabilityRequirement("D3-native-getter-navigator", "navigator_native", None),
    DetectabilityRequirement("D4-no-global-leaks", "no_global_leaks", True),
    DetectabilityRequirement("D5-constructors-present", "constructors_present", True),
    DetectabilityRequirement("D6-bind-integrity", "bind_integrity", None),
    DetectabilityRequirement("D7-clean-error-stacks", "clean_error_stacks", None),
    DetectabilityRequirement(
        "D8-no-prototype-pollution", "no_extra_prototype_properties", True
    ),
    # D8b: instrumented functions must report the same arity (.length) as the
    # native function they replace. The legacy wrapper is `function () {...}`
    # (arity 0), so e.g. getContext.length becomes 0 where native is 1 — a
    # fingerprint; legacy_detectable=True. Stealth codegens a forwarder that
    # NATIVELY declares the same number of params, so the exported wrapper's own
    # .length matches native (makeArityForwarder in instrument.ts).
    DetectabilityRequirement("D8b-native-fn-arity", "function_arity_native", True),
    # D8c: instrumented ACCESSORS must report the same function .name as the
    # native accessor they replace ("get userAgent" / "get name" / ...). A naive
    # computed-accessor wrapper is named the bare property, and exportFunction's
    # defineAs sets the bare name too, so `.get.name === "name"` (vs native
    # "get name") is a one-line detector latent on every wrapped accessor. Stealth
    # exports the accessor under its spec-prefixed native name ("get <prop>" /
    # "set <prop>") via exportFunction's `defineAs` (injectFunction in
    # instrument.ts).
    # legacy_detectable=None: which accessors legacy actually wraps is
    # environment/config-dependent (cf. D3 navigator_native), so this row asserts
    # only the stealth direction; the legacy .name detection is covered explicitly
    # by TestStealthWindowName.test_legacy_window_name_is_detectable.
    DetectabilityRequirement("D8c-native-accessor-name", "accessor_name_native", None),
    # D9: the stealth instrument's prototype-walk helpers
    # (getPrototypeByDepth / getPropertyNamesPerDepth / findPropertyInChain on
    # Object.prototype, getPropertyDescriptor on Object) live in the
    # instrument's sandbox compartment, NOT on the page's Object. A page probing
    # its own Object must not observe them. legacy_detectable=None: legacy does not
    # define these helpers either, so this asserts only the stealth direction —
    # locking in the compartment isolation that keeps the helpers undetectable.
    DetectabilityRequirement(
        "D9-no-instrument-helpers", "no_instrument_helpers_leaked", None
    ),
    # D10: the members a page-scope layer would hook to learn of new frames
    # (appendChild, document.write, window.open, the iframe contentWindow
    # getter) stay native. Each is probed four ways: exact same-realm toString,
    # arity (.length), .name, and the exact toString as printed by other
    # same-origin realms (an appended about:blank iframe and one inserted with
    # Element.after and reached through window[n]). legacy_detectable=None for
    # all rows: legacy does not hook this surface either.
    DetectabilityRequirement(
        "D10-fp-appendChild-native", "fp_appendChild_native", None
    ),
    DetectabilityRequirement("D10-fp-appendChild-arity", "fp_appendChild_arity", None),
    DetectabilityRequirement("D10-fp-appendChild-name", "fp_appendChild_name", None),
    DetectabilityRequirement(
        "D10-fp-appendChild-xrealm", "fp_appendChild_xrealm_native", None
    ),
    DetectabilityRequirement("D10-fp-docwrite-native", "fp_docwrite_native", None),
    DetectabilityRequirement("D10-fp-docwrite-arity", "fp_docwrite_arity", None),
    DetectabilityRequirement("D10-fp-docwrite-name", "fp_docwrite_name", None),
    DetectabilityRequirement(
        "D10-fp-docwrite-xrealm", "fp_docwrite_xrealm_native", None
    ),
    DetectabilityRequirement(
        "D10-fp-window-open-native", "fp_window_open_native", None
    ),
    DetectabilityRequirement("D10-fp-window-open-arity", "fp_window_open_arity", None),
    DetectabilityRequirement("D10-fp-window-open-name", "fp_window_open_name", None),
    DetectabilityRequirement(
        "D10-fp-window-open-xrealm", "fp_window_open_xrealm_native", None
    ),
    DetectabilityRequirement(
        "D10-fp-contentwindow-getter-native", "fp_contentwindow_getter_native", None
    ),
    DetectabilityRequirement(
        "D10-fp-contentwindow-getter-arity", "fp_contentwindow_getter_arity", None
    ),
    DetectabilityRequirement(
        "D10-fp-contentwindow-getter-name", "fp_contentwindow_getter_name", None
    ),
    DetectabilityRequirement(
        "D10-fp-contentwindow-getter-xrealm", "fp_contentwindow_xrealm_native", None
    ),
]

_LEGACY_DETECTABLE = [r for r in DETECTABILITY_REQUIREMENTS if r.legacy_detectable]


@pytest.mark.usefixtures("xpi", "server")
class TestStealthDetectability:
    """D* — the stealth instrument must be indistinguishable from a normal Firefox.

    Spec: the "Detectability requirements" section (D1-D9 table) of
    ``docs/developers/Stealth-Requirements.rst``, which ``literalinclude``s
    ``test_stealth_undetectable`` and ``test_legacy_detectable``. The mechanism
    each vector exploits is detailed under "Detectability (a property of the
    legacy instrument)" in ``docs/developers/Stealth-Instrumentation.rst``.
    """

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
        [(r.req_id, r.result_key) for r in DETECTABILITY_REQUIREMENTS],
        ids=[r.req_id for r in DETECTABILITY_REQUIREMENTS],
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
        [(r.req_id, r.result_key) for r in _LEGACY_DETECTABLE],
        ids=[r.req_id for r in _LEGACY_DETECTABLE],
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
        rows = db_utils.query_db(
            db_path,
            "SELECT DISTINCT symbol, operation FROM javascript",
            as_tuple=True,
        )
        # The page calls canvas.getContext and reads window.localStorage.
        for expected in (
            ("HTMLCanvasElement.getContext", "call"),
            ("window.localStorage", "get"),
        ):
            assert expected in rows, f"{expected} not recorded; got {rows}"


# Sections of NATIVE_PARITY_PAGE; each key it reports is "<section>.<probe>".
NATIVE_PARITY_SECTIONS = [
    "hooks",
    "ctor",
    "construct",
    "errors",
    "serialization",
    "xrealm",
    "realm",
    "framehooks",
]


# Firefox lists a window's lazily defined interface objects by
# Object.getOwnPropertyNames in the order they were first resolved, and creating
# a prototype or an instance resolves the interface for good (deleting it
# removes the name). Instrumenting a prototype therefore resolves its interface
# before any page script runs. These are the names a stealth crawl with the
# default surface resolves early. See "Known residual tells" in
# docs/developers/Stealth-Instrumentation.rst.
RESOLVED_BEFORE_PAGE_SCRIPT = {
    # The default surface (settings.ts) and the interfaces it inherits from.
    "AudioNode",
    "ScriptProcessorNode",
    "AudioWorkletNode",
    "GainNode",
    "AnalyserNode",
    "AudioScheduledSourceNode",
    "OscillatorNode",
    "BaseAudioContext",
    "OfflineAudioContext",
    "AudioContext",
    "RTCPeerConnection",
    "Element",
    "HTMLElement",
    "HTMLCanvasElement",
    "Storage",
    "Navigator",
    "CanvasRenderingContext2D",
    "Screen",
}


@pytest.mark.usefixtures("xpi", "server")
class TestStealthNativeParity:
    """Differential detection: a probe page must observe identical values in a
    pristine Firefox and under the stealth instrument's bundled default surface.

    Unlike the D* rows, which encode one detector each, every observation the
    probe page makes is compared verbatim against the uninstrumented baseline.
    """

    @pytest.fixture(scope="class")
    def observations(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Tuple[Dict, Dict]:
        url = _page_url(server, NATIVE_PARITY_PAGE)
        clean = _collect_results(
            _uninstrumented_params(tmp_path_factory.mktemp("parity_clean")), url
        )
        stealth = _collect_results(
            _stealth_params(tmp_path_factory.mktemp("parity_stealth")), url
        )
        assert clean and stealth, "the parity probe did not report"
        return clean, stealth

    @pytest.mark.parametrize("section", NATIVE_PARITY_SECTIONS)
    def test_section_matches_uninstrumented(
        self, observations: Tuple[Dict, Dict], section: str
    ) -> None:
        clean, stealth = observations
        keys = sorted(
            k for k in clean.keys() | stealth.keys() if k.startswith(section + ".")
        )
        assert keys, f"the probe reported nothing for section {section!r}"
        diffs = {
            k: {"clean": clean.get(k), "stealth": stealth.get(k)}
            for k in keys
            if clean.get(k) != stealth.get(k)
        }
        assert not diffs, json.dumps(diffs, indent=1)

    def test_global_names_differ_only_by_early_resolved_interfaces(
        self, observations: Tuple[Dict, Dict]
    ) -> None:
        clean, stealth = (o["globals.at_first_script"].split(",") for o in observations)
        assert sorted(clean) == sorted(stealth)

        def without_early(names: List[str]) -> List[str]:
            return [n for n in names if n not in RESOLVED_BEFORE_PAGE_SCRIPT]

        assert without_early(clean) == without_early(stealth)


@pytest.mark.usefixtures("xpi", "server")
class TestStealthRecordIntegrity:
    """Every instrumented call page script makes is recorded exactly once."""

    @pytest.fixture(scope="class")
    def db_path(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Path:
        return _run_page(
            _stealth_params(tmp_path_factory.mktemp("integrity")),
            _page_url(server, RECORD_INTEGRITY_PAGE),
        )

    @staticmethod
    def _todataurl_rows(db_path: Path, func_name: str) -> List[Any]:
        return db_utils.query_db(
            db_path,
            "SELECT document_url FROM javascript "
            "WHERE symbol = 'HTMLCanvasElement.toDataURL' AND func_name = ?",
            (func_name,),
            as_tuple=True,
        )

    def test_call_made_while_the_instrument_reads_arguments(
        self, db_path: Path
    ) -> None:
        """A page getter run by the native getContext calls toDataURL."""
        assert len(self._todataurl_rows(db_path, "integrity_reentrant_caller")) == 1

    def test_dynamic_iframe_call_recorded_once(self, db_path: Path) -> None:
        """The about:blank child is instrumented when its window is created and
        keeps its members when its document loads; one row."""
        assert len(self._todataurl_rows(db_path, "integrity_iframe_caller")) == 1

    @pytest.mark.parametrize(
        "func_name,symbol",
        [
            ("integrity_coerced_user_agent", "window.navigator.userAgent"),
            ("integrity_coerced_cookie", "window.document.cookie"),
            ("integrity_coerced_canvas", "HTMLCanvasElement.toDataURL"),
            ("integrity_coerced_screen", "window.screen.height"),
        ],
    )
    def test_call_made_by_a_native_during_argument_conversion(
        self, db_path: Path, func_name: str, symbol: str
    ) -> None:
        """Storage.setItem converts its argument by calling the instrumented
        getter or method the page installed as its toString / @@toPrimitive."""
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ? AND func_name = ?",
            (symbol, func_name),
        )
        assert rows[0][0] == 1

    def test_member_called_again_by_the_native(self, db_path: Path) -> None:
        """In a child frame, setItem is reached once by the page and once by
        the native converting its argument."""
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = 'Storage.setItem' "
            "AND func_name = 'integrity_nested_same_member'",
        )
        assert rows[0][0] == 2

    def test_reused_window_call_recorded_once(self, db_path: Path) -> None:
        """A srcdoc document reuses the window its parent instrumented."""
        assert len(self._todataurl_rows(db_path, "integrity_srcdoc_caller")) == 1

    @staticmethod
    def _rows(db_path: Path, func_name: str, symbol: str) -> List[Any]:
        return db_utils.query_db(
            db_path,
            "SELECT operation, arguments FROM javascript "
            "WHERE func_name LIKE ? AND symbol = ? ORDER BY id",
            (func_name + "%", symbol),
            as_tuple=True,
        )

    @pytest.mark.parametrize(
        "func_name,symbol,arguments",
        [
            (
                "integrity_hidden_setitem",
                "Storage.setItem",
                '["integrity_hidden","secret"]',
            ),
            (
                "integrity_hidden_filltext",
                "CanvasRenderingContext2D.fillText",
                '["INTEGRITY_HIDDEN_TEXT",1,2]',
            ),
        ],
    )
    def test_call_hidden_behind_a_deleted_member(
        self, db_path: Path, func_name: str, symbol: str, arguments: str
    ) -> None:
        """The page deletes the installed member and has a native call a bound
        copy of it while converting an argument."""
        rows = self._rows(db_path, func_name, symbol)
        assert ("call", arguments) in rows, rows
        assert len(rows) == 2, rows

    def test_get_hidden_behind_a_deleted_accessor(self, db_path: Path) -> None:
        """The cookie setter converts the document by calling the deleted
        cookie getter, installed as the document's toString."""
        rows = self._rows(db_path, "integrity_hidden_cookie", "window.document.cookie")
        assert sorted(op for op, _ in rows) == ["get", "set"], rows

    @pytest.mark.parametrize(
        "func_name,symbol,arguments",
        [
            (
                "integrity_symbol_arg",
                "HTMLCanvasElement.toDataURL",
                '["image/png","Symbol(s)"]',
            ),
            (
                "integrity_bigint_arg",
                "HTMLCanvasElement.toDataURL",
                '["image/png","1n"]',
            ),
            ("integrity_revoked_proxy_arg", "Storage.setItem", None),
            (
                "integrity_proxy_arg",
                "Storage.getItem",
                '["integrity_proxy","\\"[object Proxy]\\"","\\"[object Proxy]\\""]',
            ),
            ("integrity_cyclic_arg", "Storage.setItem", None),
        ],
    )
    def test_call_with_an_uncloneable_argument(
        self, db_path: Path, func_name: str, symbol: str, arguments: Optional[str]
    ) -> None:
        """An argument that structured cloning or JSON cannot carry does not
        cost the record."""
        rows = self._rows(db_path, func_name, symbol)
        assert len(rows) == 1, rows
        if arguments is not None:
            assert rows[0][1] == arguments

    def test_oversized_argument_is_truncated(self, db_path: Path) -> None:
        """The page chooses how much an argument costs to record."""
        rows = self._rows(db_path, "integrity_oversized_arg", "Storage.getItem")
        assert len(rows) == 1, rows
        assert rows[0][1].endswith('\\"TRUNCATED\\"]"]'), rows[0][1][-80:]
        assert len(rows[0][1]) < 2000

    def test_primitive_after_a_truncated_argument_is_kept(self, db_path: Path) -> None:
        """A large argument spends the value budget; later primitives are still
        recorded."""
        rows = self._rows(db_path, "integrity_budget_spent_arg", "Storage.getItem")
        assert len(rows) == 1, rows
        assert rows[0][1].endswith(',7,"after"]'), rows[0][1][-80:]

    def test_long_string_argument_is_truncated(self, db_path: Path) -> None:
        rows = self._rows(db_path, "integrity_long_string_arg", "Storage.getItem")
        assert len(rows) == 1, rows
        assert rows[0][1].endswith('TRUNCATED"]'), rows[0][1][-80:]
        assert len(rows[0][1]) < 100_000

    def test_typed_array_argument_is_previewed(self, db_path: Path) -> None:
        """Recording a 10 MB typed array reads a capped prefix of it."""
        rows = self._rows(db_path, "integrity_typed_array_arg", "Storage.getItem")
        assert len(rows) == 2, rows
        assert rows[0][1].endswith('\\"TRUNCATED\\"}"]'), rows[0][1][-80:]
        assert len(rows[0][1]) < 2000
        elapsed_ms = json.loads(rows[1][1])[1]
        assert float(elapsed_ms) < 100, elapsed_ms

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "SpiderMonkey names the page variable only when the caller frame is "
            "innermost (DecompileExpressionFromStack); any JS wrapper adds a "
            "frame. See docs: Known residual tells."
        ),
    )
    def test_conversion_error_message(self, db_path: Path) -> None:
        """A failed argument conversion reads as in an uninstrumented Firefox.

        Fails today (stealth reads "can't convert Proxy to string"); an
        unexpected pass means the residual tell is gone and the docs need
        updating.
        """
        rows = self._rows(db_path, "integrity_proxy_message", "Storage.getItem")
        assert rows == [
            ("call", '["integrity_px_message","can\'t convert px to string"]')
        ], rows

    @pytest.mark.parametrize(
        "argument,script",
        [
            ("integrity_tracker_mozext", "stealth_attribution_tracker.js?tag=mozext"),
            (
                "integrity_tracker_resource",
                "stealth_attribution_tracker.js?tag=resource",
            ),
            ("integrity_named", "stealth_record_integrity.html"),
        ],
    )
    def test_extension_scheme_in_page_frame_keeps_attribution(
        self, db_path: Path, argument: str, script: str
    ) -> None:
        """A page cannot drop its own frames by naming an extension scheme in
        its script URL or function name."""
        rows = db_utils.query_db(
            db_path,
            "SELECT script_url FROM javascript "
            "WHERE symbol = 'Storage.getItem' AND arguments = ?",
            (f'["{argument}"]',),
            as_tuple=True,
        )
        assert len(rows) == 1, rows
        assert script in rows[0][0], rows

    def test_send_beacon_not_instrumented(self, db_path: Path) -> None:
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol LIKE '%sendBeacon'",
        )
        assert rows[0][0] == 0

    def test_inherited_html_element_members_not_instrumented(
        self, db_path: Path
    ) -> None:
        """The default canvas entry covers HTMLCanvasElement's own members only,
        not hot HTMLElement accessors such as ``hidden``."""
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol LIKE '%.hidden'",
        )
        assert rows[0][0] == 0


@pytest.mark.usefixtures("xpi", "server")
class TestStealthOverflowErrors:
    """An instrumented call that fails near the stack limit throws an error of
    the page's realm, never one of the instrument's sandboxes."""

    def test_no_foreign_error_reaches_the_page(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        results = _collect_results(
            _stealth_params(tmp_path_factory.mktemp("overflow")),
            _page_url(server, "/stealth_overflow.html"),
        )
        assert results["caught"] > 0, results
        assert results["foreign"] == 0, results


@pytest.mark.usefixtures("xpi", "server")
class TestStealthPopup:
    """An about:blank popup keeps working, and keeps being recorded, after its
    opener has navigated away (with and without the bfcache)."""

    POPUP_SYMBOLS = {
        "window.navigator.userAgent",
        "window.navigator.webdriver",
        "window.document.cookie",
        "Storage.getItem",
        "HTMLCanvasElement.toDataURL",
        "window.screen.width",
    }

    @staticmethod
    def _sample(
        params: Tuple[ManagerParams, List[BrowserParams]], url: str
    ) -> Tuple[Dict, Path]:
        params[1][0].prefs["dom.disable_open_during_load"] = False
        return _collect_results(params, url), (
            params[0].data_directory / "crawl-data.sqlite"
        )

    @pytest.mark.parametrize("query", ["", "?nobf"], ids=["bfcache", "no_bfcache"])
    def test_popup_outlives_its_opener(
        self,
        tmp_path_factory: pytest.TempPathFactory,
        server: ServerUrls,
        query: str,
    ) -> None:
        url = _page_url(server, POPUP_PAGE) + query
        clean, _ = self._sample(
            _uninstrumented_params(tmp_path_factory.mktemp("popup_clean")), url
        )
        stealth, db_path = self._sample(
            _stealth_params(tmp_path_factory.mktemp("popup_stealth")), url
        )
        assert clean and not any(v.startswith("THROW") for v in clean.values())
        assert stealth == {**clean, "webdriver": "false"}
        symbols = {
            symbol
            for (symbol,) in db_utils.query_db(
                db_path,
                "SELECT DISTINCT symbol FROM javascript "
                # document.write gave the popup's document its opener's URL.
                "WHERE func_name LIKE 'popup_sample%' AND frame_id = 0",
                as_tuple=True,
            )
        }
        assert self.POPUP_SYMBOLS <= symbols, symbols


@pytest.mark.usefixtures("xpi", "server")
class TestStealthFrameOwnership:
    """A frame keeps working after the frame that reached it is removed, keeps
    its members when a same-origin document reuses its window, and is
    instrumented in blob:, data: and opaque-origin documents."""

    OWN_DOCUMENTS = {
        "blob_after": "blob:",
        "data_frame": "data:",
        "sandboxed_srcdoc": "about:srcdoc",
        "blob_popup": "blob:",
        "reuse": "/stealth_frame_ownership_child.html?reuse",
    }

    @pytest.fixture(scope="class")
    def observations(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Tuple[Dict, Dict, Path]:
        url = _page_url(server, FRAME_OWNERSHIP_PAGE)
        runs = []
        for name, make in (
            ("clean", _uninstrumented_params),
            ("stealth", _stealth_params),
        ):
            params = make(tmp_path_factory.mktemp("ownership_" + name))
            params[1][0].prefs["dom.disable_open_during_load"] = False
            runs.append((_collect_results(params, url), params[0].data_directory))
        (clean, _), (stealth, data_dir) = runs
        assert clean and stealth, "the ownership probe did not report"
        return clean, stealth, data_dir / "crawl-data.sqlite"

    def test_page_observes_an_uninstrumented_firefox(
        self, observations: Tuple[Dict, Dict, Path]
    ) -> None:
        clean, stealth, _ = observations
        webdriver = {k for k in clean if k.startswith("webdriver.")}
        assert webdriver and all(clean[k] == "true" for k in webdriver)
        assert stealth == {**clean, **{k: "false" for k in webdriver}}

    @pytest.mark.parametrize("tag,document", OWN_DOCUMENTS.items())
    def test_recorded_under_its_own_document(
        self, observations: Tuple[Dict, Dict, Path], tag: str, document: str
    ) -> None:
        rows = db_utils.query_db(
            observations[2],
            "SELECT document_url FROM javascript "
            "WHERE symbol = 'HTMLCanvasElement.toDataURL' AND arguments = ?",
            (f'["image/png","ownership_{tag}"]',),
            as_tuple=True,
        )
        assert len(rows) == 1, rows
        url = rows[0][0]
        assert url.startswith(document) or url.endswith(document), url


@pytest.mark.usefixtures("xpi", "server")
class TestStealthDeadRealm:
    """Members taken from a frame or popup behave like Firefox's own after that
    window is removed, navigated away or closed, and their calls are recorded
    under the document they belong to."""

    DOCUMENTS = {
        "blank_removed": "about:blank",
        "blank_removed_now": "about:blank",
        "loaded_removed": "/stealth_frame_ownership_child.html?dead_loaded",
        "navigated": "/stealth_frame_ownership_child.html?dead_nav_a",
        "navigated_xsite": "/stealth_frame_ownership_child.html?dead_xnav_a",
        "popup_closed": "/stealth_frame_ownership_child.html?dead_popup",
    }

    @pytest.fixture(scope="class")
    def observations(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Tuple[Dict, Dict, Path]:
        url = _page_url(server, DEAD_REALM_PAGE)
        runs = []
        for name, make in (
            ("clean", _uninstrumented_params),
            ("stealth", _stealth_params),
        ):
            params = make(tmp_path_factory.mktemp("dead_realm_" + name))
            params[1][0].prefs["dom.disable_open_during_load"] = False
            results = _collect_results(params, url, ExposeWindowNuking(DEAD_REALM_PAGE))
            runs.append((results, params[0].data_directory))
        (clean, _), (stealth, data_dir) = runs
        assert clean and stealth, "the dead-realm probe did not report"
        return clean, stealth, data_dir / "crawl-data.sqlite"

    def test_page_observes_an_uninstrumented_firefox(
        self, observations: Tuple[Dict, Dict, Path]
    ) -> None:
        clean, stealth, _ = observations
        assert stealth == clean

    @pytest.mark.parametrize("tag,document", DOCUMENTS.items())
    def test_recorded_under_its_own_document(
        self, observations: Tuple[Dict, Dict, Path], tag: str, document: str
    ) -> None:
        rows = db_utils.query_db(
            observations[2],
            "SELECT document_url, tab_id FROM javascript "
            "WHERE symbol = 'HTMLCanvasElement.toDataURL' AND arguments = ?",
            (f'["image/png","dead_{tag}"]',),
            as_tuple=True,
        )
        assert len(rows) == 1, rows
        url, tab_id = rows[0]
        assert url == document or url.endswith(document), url
        if tag != "popup_closed":
            top_tabs = db_utils.query_db(
                observations[2],
                "SELECT DISTINCT tab_id FROM javascript WHERE document_url LIKE ?",
                ("%" + DEAD_REALM_PAGE,),
                as_tuple=True,
            )
            assert top_tabs == [(tab_id,)], (top_tabs, tab_id)

    @pytest.mark.parametrize("marker", ["dead_xsite_pagehide", "dead_xsite_at_load"])
    def test_recorded_after_a_cross_site_navigation(
        self, observations: Tuple[Dict, Dict, Path], marker: str
    ) -> None:
        """The old document's process no longer hosts its frame: its pagehide
        and later calls on its members are still recorded, in the live tab."""
        rows = db_utils.query_db(
            observations[2],
            "SELECT document_url, tab_id FROM javascript "
            "WHERE symbol = 'HTMLCanvasElement.toDataURL' AND arguments = ?",
            (f'["image/png","{marker}"]',),
            as_tuple=True,
        )
        assert len(rows) == 1, rows
        url, tab_id = rows[0]
        assert url.endswith("?dead_xnav_a"), url
        top_tabs = db_utils.query_db(
            observations[2],
            "SELECT DISTINCT tab_id FROM javascript WHERE document_url LIKE ?",
            ("%" + DEAD_REALM_PAGE,),
            as_tuple=True,
        )
        assert top_tabs == [(tab_id,)], (top_tabs, tab_id)


@pytest.mark.usefixtures("xpi", "server")
class TestStealthFirstLoad:
    """A popup's and a frame's initial about:blank, which no content script
    runs in, are instrumented before the opener's next statement, and keep
    their members when their same-origin document loads."""

    @pytest.fixture(scope="class")
    def observations(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Tuple[Dict, Dict, Path]:
        url = _page_url(server, FIRST_LOAD_PAGE)
        runs = []
        for name, make in (
            ("clean", _uninstrumented_params),
            ("stealth", _stealth_params),
        ):
            params = make(tmp_path_factory.mktemp("first_load_" + name))
            params[1][0].prefs["dom.disable_open_during_load"] = False
            runs.append((_collect_results(params, url), params[0].data_directory))
        (clean, _), (stealth, data_dir) = runs
        assert clean and stealth, "the first-load probe did not report"
        return clean, stealth, data_dir / "crawl-data.sqlite"

    def test_page_observes_an_uninstrumented_firefox(
        self, observations: Tuple[Dict, Dict, Path]
    ) -> None:
        clean, stealth, _ = observations
        webdriver = {k for k in clean if k.startswith("webdriver.")}
        assert webdriver and all(clean[k] == "true" for k in webdriver)
        assert clean["frame.same_getter"] == clean["popup.same_getter"] == "true"
        assert stealth == {**clean, **{k: "false" for k in webdriver}}

    @pytest.mark.parametrize(
        "marker,document",
        [
            ("first_load_popup", "about:blank"),
            ("first_load_frame", "about:blank"),
            ("ownership_first_load_popup", "child.html?first_load_popup"),
            ("ownership_first_load_frame", "child.html?first_load_frame"),
        ],
    )
    def test_recorded_under_its_own_document(
        self, observations: Tuple[Dict, Dict, Path], marker: str, document: str
    ) -> None:
        rows = db_utils.query_db(
            observations[2],
            "SELECT document_url FROM javascript "
            "WHERE symbol = 'HTMLCanvasElement.toDataURL' AND arguments = ?",
            (f'["image/png","{marker}"]',),
            as_tuple=True,
        )
        assert len(rows) == 1 and rows[0][0].endswith(document), rows


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
    """X* — a hostile page must not be able to drop or forge records.

    Spec: the "Disruptability requirements" section (X1-X3) of
    ``docs/developers/Stealth-Requirements.rst`` (suppression / forgery /
    dynamic-iframe attribution) and the "Attribution requirement" (A1). Why the
    off-DOM channel does — and does not — buy tamper resistance is argued under
    "Disruptability: what the off-DOM channel does and does not buy" (the
    ``stealth-disruptability`` ref) in
    ``docs/developers/Stealth-Instrumentation.rst``.
    """

    def test_x1_legacy_channel_can_be_suppressed(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X1 control: under legacy, neutering document.dispatchEvent drops records.

        Demonstrates the attack is real before asserting stealth resists it.
        """
        data_dir = tmp_path_factory.mktemp("x1_legacy")
        db_path = _run_page(_legacy_params(data_dir), _page_url(server, SUPPRESS_PAGE))
        assert _todataurl_count(db_path) == 0, (
            "X1: legacy still recorded toDataURL calls after the page neutered "
            "document.dispatchEvent — the suppression control is ineffective"
        )

    def test_x1_stealth_channel_resists_suppression(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X1: under stealth, the same attack must NOT drop records."""
        data_dir = tmp_path_factory.mktemp("x1_stealth")
        db_path = _run_page(_stealth_params(data_dir), _page_url(server, SUPPRESS_PAGE))
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
        """X3: stealth records the in-iframe toDataURL once, under the frame.

        The page JS-creates an iframe navigating to a same-origin page and runs
        ``canvas.toDataURL`` in the frame's initial about:blank document, which
        gets no content script. The actor instruments every window global when
        it is created, so the row bears that document's URL and the frame's id.
        """
        data_dir = tmp_path_factory.mktemp("x3_stealth")
        db_path = _run_page(_stealth_params(data_dir), _page_url(server, IFRAME_PAGE))
        rows = db_utils.query_db(
            db_path,
            "SELECT document_url, frame_id FROM javascript WHERE symbol LIKE ?",
            ("%toDataURL%",),
            as_tuple=True,
        )
        assert len(rows) == 1, f"X3: expected one toDataURL row, got {rows}"
        assert rows[0][0] == "about:blank" and rows[0][1] != 0, rows

    def test_x3_legacy_misses_dynamic_iframe_call(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """X3 control: legacy does not record the in-iframe call.

        Legacy instruments a frame only through its own content script, which
        never runs in the initial about:blank document of a navigating frame.
        """
        data_dir = tmp_path_factory.mktemp("x3_legacy")
        db_path = _run_page(_legacy_params(data_dir), _page_url(server, IFRAME_PAGE))
        rows = db_utils.query_db(
            db_path,
            "SELECT document_url FROM javascript WHERE symbol LIKE ?",
            ("%toDataURL%",),
            as_tuple=True,
        )
        assert rows == [], (
            f"X3 control: legacy recorded the dynamic-iframe toDataURL ({rows}) "
            "— the stealth/legacy differential this test relies on no longer holds"
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
        "depth": 0,
        "logSettings": {
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
    """The stealth instrumentation surface is configurable at runtime.

    Spec: requirement C1, the "Configurability requirement" section of
    ``docs/developers/Stealth-Requirements.rst`` (which ``literalinclude``s
    ``test_custom_settings_take_effect`` and ``test_custom_settings_stay_undetectable``).
    How the surface is configured is described under "Configuring the instrumented
    surface" in ``docs/developers/Stealth-Instrumentation.rst``.
    """

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

    def test_empty_settings_instrument_nothing(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """``[]`` is an empty surface, not a request for the bundled default."""
        manager_params, browser_params = _stealth_params(
            tmp_path_factory.mktemp("config_empty")
        )
        browser_params[0].stealth_js_instrument_settings = []
        db_path = _run_page(
            (manager_params, browser_params), _page_url(server, ATTRIBUTION_PAGE)
        )
        assert db_utils.get_javascript_entries(db_path) == []

    def test_entries_sharing_a_prototype_all_take_effect(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Two entries resolving to Screen.prototype each instrument their own
        member under their own label."""
        manager_params, browser_params = _stealth_params(
            tmp_path_factory.mktemp("config_same_prototype")
        )
        browser_params[0].stealth_js_instrument_settings = [
            {
                "object": "Screen",
                "instrumentedName": label,
                "depth": 0,
                "logSettings": _log_settings(propertiesToInstrument=[member]),
            }
            for label, member in (("window.screen", "width"), ("Screen", "height"))
        ]
        db_path = _run_page(
            (manager_params, browser_params), _page_url(server, SCREEN_PAGE)
        )
        rows = db_utils.query_db(
            db_path, "SELECT DISTINCT symbol FROM javascript", as_tuple=True
        )
        assert {r[0] for r in rows} == {"window.screen.width", "Screen.height"}

    def test_instance_rooted_entry_counts_depth_from_the_instance(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """For a global instance such as ``document``, ``depth`` counts from the
        instance on both the named-list and the instrument-everything path:
        ``Document.prototype.cookie`` is depth 2 either way."""
        manager_params, browser_params = _stealth_params(
            tmp_path_factory.mktemp("config_instance_depth")
        )
        browser_params[0].stealth_js_instrument_settings = [
            {
                "object": "document",
                "instrumentedName": "D",
                "depth": 2,
                "logSettings": _log_settings(),
            }
        ]
        db_path = _run_page(
            (manager_params, browser_params), _page_url(server, COOKIE_PAGE)
        )
        rows = db_utils.query_db(
            db_path,
            "SELECT DISTINCT operation FROM javascript WHERE symbol = 'D.cookie'",
            as_tuple=True,
        )
        assert sorted(r[0] for r in rows) == ["get", "set"], rows

    def test_overwritten_method_is_refused(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """``overwrittenProperties`` replaces an accessor's value; on a method it
        would be ignored, so the member is refused rather than wrapped."""
        manager_params, browser_params = _stealth_params(
            tmp_path_factory.mktemp("config_overwritten_method")
        )
        browser_params[0].stealth_js_instrument_settings = [
            {
                "object": "Storage",
                "instrumentedName": "Storage",
                "depth": 0,
                "logSettings": _log_settings(
                    propertiesToInstrument=["setItem"],
                    overwrittenProperties=[
                        {"key": "getItem", "value": "x", "level": 0}
                    ],
                ),
            }
        ]
        db_path = _run_page(
            (manager_params, browser_params),
            _page_url(server, RECORD_INTEGRITY_PAGE),
        )
        rows = db_utils.query_db(
            db_path,
            "SELECT DISTINCT symbol FROM javascript",
            as_tuple=True,
        )
        assert {r[0] for r in rows} == {"Storage.setItem"}, rows

    def test_constructor_members_are_left_native(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """A forwarder cannot be constructed, so a configured interface object
        is refused rather than broken."""
        url = _page_url(server, "/stealth_constructor.html")
        clean = _collect_results(
            _uninstrumented_params(tmp_path_factory.mktemp("ctor_clean")), url
        )
        manager_params, browser_params = _stealth_params(
            tmp_path_factory.mktemp("ctor_stealth")
        )
        browser_params[0].stealth_js_instrument_settings = [
            {
                "object": "window",
                "instrumentedName": "window",
                "depth": 0,
                "logSettings": _log_settings(
                    propertiesToInstrument=["Image", "OfflineAudioContext", "name"]
                ),
            }
        ]
        stealth = _collect_results((manager_params, browser_params), url)
        assert clean and stealth == clean

    def test_custom_settings_stay_undetectable(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """A custom surface must remain undetectable on every vector."""
        data_dir = tmp_path_factory.mktemp("config_undetect")
        results = _collect_detection(
            _custom_stealth_params(data_dir), _page_url(server, DETECTION_PAGE)
        )
        assert results, "no detection results collected for custom stealth config"
        for req in DETECTABILITY_REQUIREMENTS:
            assert results.get(req.result_key) is True, (
                f"{req.req_id}: custom stealth config is detectable via "
                f"'{req.result_key}' "
                f"(page error: {results.get(req.result_key + '_error')})"
            )


# --------------------------------------------------------------------------- #
# Error-drift coverage.
#
# An exception raised while an instrumented method runs must reach the page as
# the identical object a pristine Firefox would deliver: same identity, class,
# own properties, ``lineNumber`` and ``stack``. The stealth wrapper does not
# catch it; the native runs in the page realm, so the error is a page object
# and exportFunction hands it back unchanged.
#
# These tests run the SAME probe page (``stealth_error_drift.html``)
# UNINSTRUMENTED and under STEALTH and compare the observations. The
# instrumented surface targets methods whose NATIVE call throws:
#   - ``CanvasRenderingContext2D.getImageData`` -> ``DOMException``
#     (IndexSizeError) for a zero-sized rect.
#   - ``Array.forEach`` -> synchronously invokes a page callback and re-raises
#     its throw, so the page can route a built-in ``TypeError`` or a custom Error
#     subclass THROUGH an instrumented native call.
#
# BROWSER-ONLY: every test here launches a real Firefox (no ``pyonly`` marker).
# --------------------------------------------------------------------------- #
# Methods whose NATIVE implementation throws. getImageData(0,0,0,0) raises a
# DOMException; Array.forEach re-raises whatever its callback throws.
ERROR_DRIFT_STEALTH_SETTINGS: List[Dict] = [
    {
        "object": "CanvasRenderingContext2D",
        "instrumentedName": "CanvasRenderingContext2D",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": ["getImageData"],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
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
        "object": "Array",
        "instrumentedName": "Array",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": ["forEach"],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "overwrittenProperties": [],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
        },
    },
]


def _error_drift_stealth_params(
    data_dir: Path,
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = ERROR_DRIFT_STEALTH_SETTINGS
    return manager_params, browser_params


@pytest.mark.usefixtures("xpi", "server")
class TestStealthErrorDrift:
    """An error thrown through an instrumented method must look native."""

    @pytest.fixture(scope="class")
    def uninstrumented(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Dict:
        """Ground truth: the error shapes a pristine Firefox observes."""
        data_dir = tmp_path_factory.mktemp("error_drift_native")
        results = _collect_results(
            _uninstrumented_params(data_dir), _page_url(server, ERROR_DRIFT_PAGE)
        )
        assert results, "no uninstrumented error-drift results collected"
        return results

    @pytest.fixture(scope="class")
    def stealth(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> Dict:
        """The error shapes observed with the stealth instrument active."""
        data_dir = tmp_path_factory.mktemp("error_drift_stealth")
        results = _collect_results(
            _error_drift_stealth_params(data_dir),
            _page_url(server, ERROR_DRIFT_PAGE),
        )
        assert results, "no stealth error-drift results collected"
        return results

    def test_every_observation_matches_uninstrumented(
        self, uninstrumented: Dict, stealth: Dict
    ) -> None:
        """Identity, class, own keys, lineNumber and stack all match native."""
        diffs = {
            k: (uninstrumented.get(k), stealth.get(k))
            for k in uninstrumented.keys() | stealth.keys()
            if uninstrumented.get(k) != stealth.get(k)
        }
        assert not diffs, diffs
        for label in ("typeerror", "custom"):
            assert stealth.get(f"{label}_identity") is True

    def test_native_domexception_parity(
        self, uninstrumented: Dict, stealth: Dict
    ) -> None:
        """A native DOMException raised through an instrumented method is identical.

        ``getImageData(0,0,0,0)`` throws an ``IndexSizeError`` (a ``DOMException``).
        Its ``name`` / ``message`` / ``instanceof DOMException`` must match the
        uninstrumented page exactly, or a page could tell the call was wrapped.
        """
        assert uninstrumented.get("domexception_threw") is True, (
            "the probe's getImageData call did not throw uninstrumented — the "
            "DOMException control is ineffective"
        )
        assert stealth.get("domexception_threw") is True, (
            "getImageData did not throw under stealth — the instrumented wrapper "
            "swallowed the native DOMException"
        )
        for field in ("domexception_name", "domexception_message"):
            assert stealth.get(field) == uninstrumented.get(field), (
                f"stealth altered the DOMException's {field}: native="
                f"{uninstrumented.get(field)!r} stealth={stealth.get(field)!r}"
            )
        assert stealth.get("domexception_is_domexception") is True, (
            "the error is no longer an instanceof DOMException under stealth — a "
            "page can detect the instrument by the changed error type"
        )
        assert stealth.get("domexception_is_domexception") == uninstrumented.get(
            "domexception_is_domexception"
        )

    def test_builtin_typeerror_subclass_preserved(
        self, uninstrumented: Dict, stealth: Dict
    ) -> None:
        """A built-in TypeError routed through an instrumented method keeps its type.

        ``instanceof TypeError``, name and message must hold under stealth exactly
        as they do uninstrumented.
        """
        assert uninstrumented.get("typeerror_threw") is True
        assert stealth.get("typeerror_threw") is True
        assert stealth.get("typeerror_name") == uninstrumented.get("typeerror_name")
        assert stealth.get("typeerror_message") == uninstrumented.get(
            "typeerror_message"
        )
        assert stealth.get("typeerror_is_typeerror") is True, (
            "a built-in TypeError thrown through an instrumented method lost its "
            "subclass under stealth (no longer instanceof TypeError) — detectable "
            "drift from the uninstrumented page"
        )
        assert stealth.get("typeerror_is_typeerror") == uninstrumented.get(
            "typeerror_is_typeerror"
        )

    def test_custom_error_subclass_preserved(
        self, uninstrumented: Dict, stealth: Dict
    ) -> None:
        """A page's own Error subclass reaches the page as the same object."""
        assert uninstrumented.get("custom_is_pagecustom") is True, (
            "uninstrumented page did not preserve its own PageCustomError — the "
            "control is ineffective"
        )
        for field in ("identity", "is_pagecustom", "ctor", "name", "message"):
            assert stealth.get(f"custom_{field}") == uninstrumented.get(
                f"custom_{field}"
            ), field

    def test_async_rejection_reason_does_not_drift(
        self, uninstrumented: Dict, stealth: Dict
    ) -> None:
        """An async rejection surfaced from an instrumented call is unchanged.

        A ``Promise.reject(new TypeError(...))`` scheduled inside an instrumented
        ``forEach`` callback surfaces via ``unhandledrejection``. Its name /
        message / ``instanceof TypeError`` must match the uninstrumented page.
        """
        assert uninstrumented.get("rejection_observed") is True, (
            "the uninstrumented page observed no unhandled rejection — the async "
            "control is ineffective"
        )
        assert stealth.get("rejection_observed") is True, (
            "no unhandled rejection observed under stealth — the instrumented call "
            "swallowed or altered the async rejection"
        )
        assert stealth.get("rejection_name") == uninstrumented.get("rejection_name")
        assert stealth.get("rejection_message") == uninstrumented.get(
            "rejection_message"
        )
        assert stealth.get("rejection_is_typeerror") == uninstrumented.get(
            "rejection_is_typeerror"
        ), "the async rejection reason's type drifted under stealth"

    def test_instrumented_throw_stack_has_no_extension_frames(
        self, uninstrumented: Dict, stealth: Dict
    ) -> None:
        """A throw THROUGH an instrumented method leaks no extension frame.

        The exception is created while extension frames are on the stack; the
        page's view of ``e.stack`` must still contain only page frames.
        """
        for label in ("domexception", "typeerror", "custom"):
            assert uninstrumented.get(f"{label}_stack_has_extension") is False, (
                f"uninstrumented {label} throw reported an extension frame — the "
                "probe is miscalibrated"
            )
            assert stealth.get(f"{label}_threw") is True
            assert stealth.get(f"{label}_stack_has_extension") is False, (
                f"the {label} error's stack contains a moz-extension:// frame "
                "under stealth, leaking the instrument to the page"
            )


# --------------------------------------------------------------------------- #
# Default-surface coverage (the bundled stealth default captures cookies)
# --------------------------------------------------------------------------- #
@pytest.mark.usefixtures("xpi", "server")
class TestStealthDefaultSurface:
    """The bundled stealth default captures the documented fingerprint surface.

    Spec: "Configuring the instrumented surface" (the "Data capture: differences
    from legacy ``js_instrument``" subsection, which enumerates the default
    ``window.document.cookie`` / ``window.document.referrer`` entries) in
    ``docs/developers/Stealth-Instrumentation.rst``.
    """

    def test_default_captures_document_cookie(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Under the stealth DEFAULT, document.cookie get/set is recorded.

        Legacy's ``collection_fingerprinting`` instruments
        ``window.document -> [cookie, referrer]``; the stealth default must match.
        The recorded symbol is the
        legacy-identical ``window.document.cookie`` (the stealth default labels
        the document entry ``window.document`` for drop-in parity). Asserts such
        a row lands in the ``javascript`` table without any custom settings.
        """
        data_dir = tmp_path_factory.mktemp("default_cookie")
        db_path = _run_page(_stealth_params(data_dir), _page_url(server, COOKIE_PAGE))
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ?",
            ("window.document.cookie",),
        )
        assert rows[0][0] > 0, (
            "the stealth default surface did not record window.document.cookie "
            "access — the 'cookie' property is missing from the default document "
            "entry, or its symbol label diverged from legacy"
        )


# --------------------------------------------------------------------------- #
# window.name (and window-level localStorage / sessionStorage) capture
#
# Legacy OpenWPM instruments the window INSTANCE via
# {"window": ["name", "localStorage", "sessionStorage"]}. In Firefox those
# members are NATIVE accessor properties that live as OWN properties on the
# window INSTANCE (depth 0), NOT on Window.prototype — verified against a clean
# Firefox: Object.getOwnPropertyDescriptor(Window.prototype, "name") is undefined
# while Object.getOwnPropertyDescriptor(window, "name") is a native accessor. The
# stealth default reaches them at depth 0 and redefines the native accessor on
# the instance in place. These tests assert (a) get/set are captured at legacy
# fidelity and (b) the instrumentation stays undetectable — the page cannot tell
# window.name was touched (the instance descriptor still looks native:
# own-on-instance, [native code], spec-prefixed accessor name).
# --------------------------------------------------------------------------- #
def _window_name_results(
    params: Tuple[ManagerParams, List[BrowserParams]],
    url: str,
) -> Dict:
    """Run the window.name probe page and return its self-detection dict."""
    return _collect_results(params, url)


@pytest.mark.usefixtures("xpi", "server")
class TestStealthWindowName:
    """The bundled stealth default captures window.name get/set, undetectably.

    Spec: "Configuring the instrumented surface" in
    ``docs/developers/Stealth-Instrumentation.rst`` documents why instrumenting
    the window-instance ``window.name`` / ``localStorage`` / ``sessionStorage``
    accessors stays undetectable (the masquerade-preserving in-place accessor
    redefine) and why the default ``window`` list is deliberately restricted.
    """

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
            "setter on the window instance was not instrumented"
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

        The probe page reads the window INSTANCE accessor descriptors (window.name
        / localStorage / sessionStorage are native OWN accessors on the instance in
        Firefox, not on Window.prototype) and checks the instrumented descriptor
        matches the native shape: (1) get/set still report ``[native code]``,
        (2) the accessor functions carry the spec-prefixed native name
        (``get name`` / ``set name`` / ``get localStorage`` / ...), (3) they stay
        own properties of the window instance (as Firefox natively has them), and
        (4) the getter-only storage props gained no synthetic setter. Every check
        must be True.
        """
        data_dir = tmp_path_factory.mktemp("window_name_stealth_detect")
        results = _window_name_results(
            _stealth_params(data_dir), _page_url(server, WINDOW_NAME_PAGE)
        )
        assert results, "no window.name probe results collected under stealth"
        for key in (
            "name_getter_native",
            "name_setter_native",
            "name_getter_name_native",
            "name_setter_name_native",
            "localStorage_getter_native",
            "localStorage_getter_name_native",
            "localStorage_no_setter",
            "sessionStorage_getter_native",
            "sessionStorage_getter_name_native",
            "sessionStorage_no_setter",
            "name_own_on_instance",
            "localStorage_own_on_instance",
            "sessionStorage_own_on_instance",
            "name_roundtrips",
        ):
            assert results.get(key) is True, (
                f"stealth window.name instrumentation is detectable via '{key}' "
                f"(probe error: {results.get('descriptor_error')})"
            )

    def test_legacy_window_name_is_detectable(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Control: legacy's window.name accessor is NOT native (detectable).

        Proves the undetectability check above is meaningful. The legacy
        instrument replaces the window-instance accessor with a JS wrapper whose
        ``toString`` no longer reports ``[native code]`` and whose ``.name`` is not
        the spec-prefixed native value (legacy does not fix ``.name``/``toString``),
        so at least one nativeness check on the instance descriptor trips.
        """
        data_dir = tmp_path_factory.mktemp("window_name_legacy_detect")
        results = _window_name_results(
            _legacy_params(data_dir), _page_url(server, WINDOW_NAME_PAGE)
        )
        assert results, "no window.name probe results collected under legacy"
        # Legacy is detectable if it leaves ANY page-observable artifact on the
        # window-instance window.name plumbing: the accessor stopped reporting
        # [native code], or its function name is no longer the spec-prefixed native
        # value ("get name"/"set name"). The stealth test above asserts the
        # instance descriptor matches the native shape on ALL these signals.
        undetectable_signals = [
            results.get("name_getter_native") is True,
            results.get("name_setter_native") is True,
            results.get("name_getter_name_native") is True,
            results.get("name_setter_name_native") is True,
        ]
        assert not all(undetectable_signals), (
            "legacy left window.name looking pristine (native accessors with "
            "spec-prefixed names) — the detection vector is ineffective, so a "
            "stealth pass on the same vector would be meaningless"
        )


# --------------------------------------------------------------------------- #
# logSettings fidelity: preventSets, logFunctionGets, recursive/depth,
# nonExistingPropertiesToInstrument: each is honoured with legacy semantics and
# stays native-looking where the property is on a native object.
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
            propertiesToInstrument=[{"depth": 2, "propertyNames": ["body"]}],
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


def _params_with(
    data_dir: Path, settings: List[Dict]
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = settings
    return manager_params, browser_params


@pytest.mark.usefixtures("xpi", "server")
class TestStealthLogSettings:
    """preventSets, logFunctionGets and nonExistingPropertiesToInstrument are
    honoured by the stealth instrument.

    Spec: the "logSettings semantics" section (the per-field table) of
    ``docs/developers/Stealth-Instrumentation.rst``, which documents which legacy
    ``logSettings`` fields stealth honours (every field except ``recursive``).
    """

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


def _distinct_symbol_receiver_pairs(db_path: Path) -> set:
    """Distinct (symbol, receiver) pairs recorded in the javascript table.

    ``receiver`` is the interface-attribution column populated by
    interface-attributed shared-prototype capture (B′); it is NULL for ordinary
    instrumentation. Returned as ``(symbol, receiver_or_None)`` tuples.
    """
    rows = db_utils.query_db(
        db_path,
        "SELECT DISTINCT symbol, receiver FROM javascript",
        as_tuple=True,
    )
    return {(r[0], r[1]) for r in rows}


# --------------------------------------------------------------------------- #
# logFunctionsAsStrings parity for call arguments
# --------------------------------------------------------------------------- #
# Distinctive token embedded in the listener function's source on the probe page
# (test/test_pages/stealth_function_arg.html). It can only appear in a recorded
# call's ``arguments`` if the function argument was serialized as its SOURCE
# STRING (logFunctionsAsStrings:true), never if it was serialized as the
# placeholder "FUNCTION" (logFunctionsAsStrings:false).
FUNCTION_ARG_MARKER = "STEALTH_FN_MARKER"


def _function_arg_settings(log_functions_as_strings: bool) -> List[Dict]:
    """Stealth surface instrumenting ``EventTarget.addEventListener``.

    The probe page calls ``document.addEventListener(type, listener)`` with a
    named function, which dispatches through ``EventTarget.prototype`` — so this
    captures the function-valued second argument. ``logFunctionsAsStrings`` is
    set per the parameter to exercise both serialization directions.
    """
    return [
        {
            "object": "EventTarget",
            "instrumentedName": "EventTarget",
            "depth": 0,
            "logSettings": {
                "propertiesToInstrument": ["addEventListener"],
                "nonExistingPropertiesToInstrument": [],
                "excludedProperties": [],
                "overwrittenProperties": [],
                "logCallStack": False,
                "logFunctionsAsStrings": log_functions_as_strings,
                "logFunctionGets": False,
                "preventSets": False,
                "recursive": False,
                "depth": 5,
            },
        },
    ]


def _function_arg_params(
    data_dir: Path, log_functions_as_strings: bool
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = _function_arg_settings(
        log_functions_as_strings
    )
    return manager_params, browser_params


def _addeventlistener_arguments(db_path: Path) -> List[str]:
    """Return the recorded ``arguments`` JSON for every addEventListener call."""
    rows = db_utils.query_db(
        db_path,
        "SELECT arguments FROM javascript " "WHERE symbol = ? AND operation = 'call'",
        ("EventTarget.addEventListener",),
    )
    return [row[0] for row in rows if row[0] is not None]


@pytest.mark.usefixtures("xpi", "server")
class TestStealthLogFunctionsAsStrings:
    """Call ARGUMENTS honour ``logFunctionsAsStrings`` (drop-in parity).

    Legacy serializes each call argument with
    ``serializeObject(arg, logSettings.logFunctionsAsStrings)``
    (Extension/src/lib/js-instruments.ts), and the stealth instrument does the
    same for property VALUES. These tests pin that the stealth ARGUMENTS path is
    consistent with both: a function passed to an instrumented method is recorded
    as its source string when the setting is true, and as "FUNCTION" when false.

    Spec: the ``logFunctionsAsStrings`` row of the "logSettings semantics" table
    in ``docs/developers/Stealth-Instrumentation.rst``.
    """

    def test_function_arg_recorded_as_source_when_true(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """logFunctionsAsStrings:true -> argument recorded as its source string."""
        data_dir = tmp_path_factory.mktemp("logfnstr_true")
        db_path = _run_page(
            _function_arg_params(data_dir, True),
            _page_url(server, FUNCTION_ARG_PAGE),
        )
        all_args = _addeventlistener_arguments(db_path)
        assert all_args, (
            "no EventTarget.addEventListener call was recorded — the probe page "
            "did not exercise the instrumented surface"
        )
        assert any(FUNCTION_ARG_MARKER in args for args in all_args), (
            "logFunctionsAsStrings:true did not serialize the function argument "
            f"to its source string (no '{FUNCTION_ARG_MARKER}' in recorded "
            f"arguments): {all_args}"
        )
        assert not any('"FUNCTION"' in args for args in all_args), (
            "logFunctionsAsStrings:true still recorded the placeholder "
            f'"FUNCTION" for a function argument: {all_args}'
        )

    def test_function_arg_recorded_as_placeholder_when_false(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """logFunctionsAsStrings:false -> argument recorded as "FUNCTION"."""
        data_dir = tmp_path_factory.mktemp("logfnstr_false")
        db_path = _run_page(
            _function_arg_params(data_dir, False),
            _page_url(server, FUNCTION_ARG_PAGE),
        )
        all_args = _addeventlistener_arguments(db_path)
        assert all_args, (
            "no EventTarget.addEventListener call was recorded — the probe page "
            "did not exercise the instrumented surface"
        )
        assert any('"FUNCTION"' in args for args in all_args), (
            'logFunctionsAsStrings:false did not record the "FUNCTION" '
            f"placeholder for a function argument: {all_args}"
        )
        assert not any(FUNCTION_ARG_MARKER in args for args in all_args), (
            "logFunctionsAsStrings:false leaked the function source string "
            f"(found '{FUNCTION_ARG_MARKER}'): {all_args}"
        )


# --------------------------------------------------------------------------- #
# Interface-attributed shared-prototype capture (B′)
#
# A method on a SHARED prototype (e.g. EventTarget.prototype.addEventListener) is
# hooked ONCE, but at call time the receiver's INTERFACE is read (through the
# Xray, immune to page tampering) and:
#   (a) the record is EMITTED only if that interface is in a configured
#       receiverInterfaces set (a instrument-side filter), and
#   (b) the concrete receiver interface is recorded in a DEDICATED ``receiver``
#       column while ``symbol`` stays the STATIC shared-prototype method
#       (e.g. symbol="EventTarget.addEventListener", receiver="HTMLDivElement").
# Interface-level attribution is the goal; distinguishing two instances of the
# same interface is explicitly NOT needed. See
# docs/developers/Stealth-Instrumentation.md and
# Extension/src/stealth/instrument.ts (logCall / getReceiverInterfaceName).
# --------------------------------------------------------------------------- #
# The probe page (stealth_shared_prototype.html) calls addEventListener on an
# HTMLDivElement (TARGETED) and an XMLHttpRequest (NON-targeted). The config below
# lists ONLY HTMLDivElement, so the filter must keep the div call and drop the xhr
# call.
TARGETED_INTERFACE = "HTMLDivElement"
NON_TARGETED_INTERFACE = "XMLHttpRequest"
SHARED_PROTOTYPE_STEALTH_SETTINGS: List[Dict] = [
    {
        "object": "EventTarget",
        "instrumentedName": "EventTarget",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": ["addEventListener"],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "overwrittenProperties": [],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
            "receiverInterfaces": [TARGETED_INTERFACE],
        },
    },
]


def _shared_prototype_params(
    data_dir: Path,
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _stealth_params(data_dir)
    browser_params[0].stealth_js_instrument_settings = SHARED_PROTOTYPE_STEALTH_SETTINGS
    return manager_params, browser_params


@pytest.mark.usefixtures("xpi", "server")
class TestStealthSharedPrototypeCapture:
    """B′: interface-attributed, instrument-filtered shared-prototype capture.

    Spec: the "Interface-attributed shared-prototype capture" section of
    ``docs/developers/Stealth-Instrumentation.rst``, which describes hooking a
    shared prototype once, reading the receiver interface through the Xray, and
    filtering/attributing via the dedicated ``receiver`` column.
    """

    @pytest.fixture(scope="class")
    def shared_prototype_pairs(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> set:
        """Distinct (symbol, receiver) pairs for the shared-prototype probe.

        One crawl; ``receiver`` is the dedicated interface-attribution column
        (NULL for ordinary rows).
        """
        data_dir = tmp_path_factory.mktemp("shared_proto")
        db_path = _run_page(
            _shared_prototype_params(data_dir),
            _page_url(server, SHARED_PROTOTYPE_PAGE),
        )
        return _distinct_symbol_receiver_pairs(db_path)

    def test_targeted_interface_is_captured_in_receiver_column(
        self, shared_prototype_pairs: set
    ) -> None:
        """addEventListener on the TARGETED interface is recorded with the STATIC
        ``symbol`` and the receiver interface in the dedicated ``receiver`` column.

        Proves (a) the shared-prototype method is captured under the static
        symbol ``EventTarget.addEventListener``, and (b) the concrete RECEIVER
        interface (HTMLDivElement) lands in the ``receiver`` column — not in
        ``symbol`` — even though the page redefined the receiver's ``constructor``
        (the Xray read sees through it).
        """
        expected = ("EventTarget.addEventListener", TARGETED_INTERFACE)
        assert expected in shared_prototype_pairs, (
            "shared-prototype capture did not record symbol="
            f"'EventTarget.addEventListener' with receiver='{TARGETED_INTERFACE}'; "
            "the targeted interface call was not captured / not attributed to the "
            f"receiver column. Recorded (symbol, receiver) pairs: "
            f"{sorted(shared_prototype_pairs)}"
        )

    def test_non_targeted_interface_is_filtered_out(
        self, shared_prototype_pairs: set
    ) -> None:
        """addEventListener on a NON-targeted interface is NOT recorded.

        The discriminating filter test: the probe calls addEventListener on BOTH
        an HTMLDivElement (in receiverInterfaces) and an XMLHttpRequest (NOT in
        it). The instrument-side filter must drop the xhr call entirely — no
        row whose ``receiver`` is the non-targeted interface, and (since the call
        is dropped) no ``EventTarget.addEventListener`` row attributed to it.
        """
        receivers = {recv for (_sym, recv) in shared_prototype_pairs}
        assert NON_TARGETED_INTERFACE not in receivers, (
            "the instrument-side receiver-interface filter did not drop "
            "non-targeted calls: a row was recorded with receiver="
            f"'{NON_TARGETED_INTERFACE}', which is NOT in receiverInterfaces. "
            f"Recorded (symbol, receiver) pairs: {sorted(shared_prototype_pairs)}"
        )

    def test_absent_receiver_interfaces_is_unchanged(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Regression: an entry WITHOUT receiverInterfaces behaves as before.

        The same probe page, instrumented with a plain (no-receiverInterfaces)
        EventTarget.addEventListener entry, must record the call under the STATIC
        symbol ``EventTarget.addEventListener`` for BOTH receivers, with the
        ``receiver`` column NULL — no interface attribution, no filtering. This
        pins that the new column is purely additive: when receiverInterfaces is
        absent, the static-symbol/always-emit path is unchanged and ``receiver``
        is NULL.
        """
        plain_settings = [
            {
                "object": "EventTarget",
                "instrumentedName": "EventTarget",
                "depth": 0,
                "logSettings": {
                    "propertiesToInstrument": ["addEventListener"],
                    "nonExistingPropertiesToInstrument": [],
                    "excludedProperties": [],
                    "overwrittenProperties": [],
                    "logCallStack": False,
                    "logFunctionsAsStrings": False,
                    "logFunctionGets": False,
                    "preventSets": False,
                    "recursive": False,
                    "depth": 5,
                },
            },
        ]
        manager_params, browser_params = _stealth_params(
            tmp_path_factory.mktemp("shared_proto_plain")
        )
        browser_params[0].stealth_js_instrument_settings = plain_settings
        db_path = _run_page(
            (manager_params, browser_params),
            _page_url(server, SHARED_PROTOTYPE_PAGE),
        )
        pairs = _distinct_symbol_receiver_pairs(db_path)
        symbols = {sym for (sym, _recv) in pairs}
        assert "EventTarget.addEventListener" in symbols, (
            "without receiverInterfaces the shared-prototype method must record "
            "under the STATIC symbol 'EventTarget.addEventListener' (unchanged "
            f"behaviour); recorded symbols: {sorted(symbols)}"
        )
        # No entry in this crawl uses receiverInterfaces, so EVERY row — the
        # shared-prototype method AND any ordinary (non-shared) instrumentation
        # row — must have a NULL receiver. This pins the regression: ordinary
        # instrumentation never populates the new column.
        non_null = {(sym, recv) for (sym, recv) in pairs if recv is not None}
        assert not non_null, (
            "without any receiverInterfaces config the receiver column must be "
            f"NULL for every row; these rows populated it: {sorted(non_null)}"
        )


# Multiple inherited methods of ONE shared prototype, instrumented together. All
# three resolve to the SAME EventTarget.prototype object, and the stealth
# instrument must hook every one of them.
SHARED_PROTOTYPE_MULTI_STEALTH_SETTINGS: List[Dict] = [
    {
        "object": "EventTarget",
        "instrumentedName": "EventTarget",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": [
                "addEventListener",
                "removeEventListener",
                "dispatchEvent",
            ],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "overwrittenProperties": [],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
            "receiverInterfaces": [TARGETED_INTERFACE],
        },
    },
]


@pytest.mark.usefixtures("xpi", "server")
class TestStealthSharedPrototypeMultiMember:
    """B′: ALL methods of one shared prototype are captured, not just the first.

    Guards against a per-prototype gate: a config instrumenting
    several members of one shared prototype (EventTarget.addEventListener,
    .removeEventListener, .dispatchEvent) resolves every member to the SAME
    ``EventTarget.prototype`` object; every one must be hooked, not only the
    first. The probe page calls all three on a
    targeted-interface receiver; all three must be recorded with the right
    ``receiver``.

    Spec: the "Interface-attributed shared-prototype capture" section of
    ``docs/developers/Stealth-Instrumentation.rst``.
    """

    def test_all_shared_prototype_methods_are_captured(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        manager_params, browser_params = _stealth_params(
            tmp_path_factory.mktemp("shared_proto_multi")
        )
        browser_params[0].stealth_js_instrument_settings = (
            SHARED_PROTOTYPE_MULTI_STEALTH_SETTINGS
        )
        db_path = _run_page(
            (manager_params, browser_params),
            _page_url(server, SHARED_PROTOTYPE_MULTI_PAGE),
        )
        pairs = _distinct_symbol_receiver_pairs(db_path)
        expected = {
            ("EventTarget.addEventListener", TARGETED_INTERFACE),
            ("EventTarget.removeEventListener", TARGETED_INTERFACE),
            ("EventTarget.dispatchEvent", TARGETED_INTERFACE),
        }
        missing = expected - pairs
        assert not missing, (
            "not every instrumented member of the shared EventTarget.prototype was "
            "captured — a per-prototype gate dropped all but the "
            f"first. Missing (symbol, receiver) pairs: {sorted(missing)}. "
            f"Recorded pairs: {sorted(pairs)}"
        )
