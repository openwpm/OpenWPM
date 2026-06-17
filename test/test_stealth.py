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
import logging
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
from openwpm.config import (
    BrowserParams,
    ManagerParams,
    ManagerParamsInternal,
    validate_browser_params,
)
from openwpm.errors import ConfigError
from openwpm.js_instrumentation import clean_stealth_js_instrumentation_settings
from openwpm.socket_interface import ClientSocket
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_providers import TableName
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils, js_settings_migrator
from openwpm.utilities.js_settings_migrator import (
    UntranslatedEntry,
    _drop_unwrapped_members,
    _launch_browser,
    legacy_settings_to_stealth,
)
from openwpm.utilities.platform_utils import get_firefox_binary_path

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
# Calls window.fetch (a WebIDL [Global] member, own on the window INSTANCE not on
# Window.prototype), so the migrator's instance-own resolution can be proven to
# instrument it end to end. See TestStealthMigratedFetchCapture.
FETCH_PAGE = "/stealth_fetch.html"
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
NON_EXISTING_PROPS_PAGE = "/stealth_non_existing_props.html"
# Calls an instrumented method (EventTarget.addEventListener) with a function as
# an argument, so the recorded ``arguments`` can be checked for whether the
# function was serialized as its source string or as the placeholder "FUNCTION".
FUNCTION_ARG_PAGE = "/stealth_function_arg.html"
# Exercises a broad slice of the instrumented surface (navigator, screen,
# document, window, Storage, canvas, audio nodes/contexts, RTC) so the symbol
# strings emitted by legacy and stealth can be diffed for drop-in parity.
SYMBOL_PROBE_PAGE = "/stealth_symbol_probe.html"
# Touches navigator AND a slice of its nested interface objects (permissions,
# geolocation, mediaCapabilities, …) so a recursive legacy config and the flat
# stealth config the sweep generates from it can be diffed for surface parity.
RECURSIVE_NAV_PROBE_PAGE = "/stealth_recursive_navigator_probe.html"
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
# Calls toString() on navigator (interface Navigator, IN receiverInterfaces) AND
# on a <div> (HTMLDivElement, NOT in receiverInterfaces), exercising the opt-in
# capture_universal_prototype_members sweep at RUNTIME: the Navigator call must be
# recorded as "Object.toString" with receiver "Navigator", the div call dropped by
# the instrument's filter, and the crawl must complete despite wrapping
# Object.prototype.toString.
UNIVERSAL_TOSTRING_PAGE = "/stealth_universal_toString_probe.html"
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
    # D11: Function.prototype.toString is the untouched native, checked by
    # stringifying it with itself. legacy_detectable=None: legacy does not touch
    # it either.
    DetectabilityRequirement(
        "D11-tostring-recursive-native", "tostring_recursive_native", None
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
# Migrated legacy `window.fetch` capture (regression for the migrator walk gap)
#
# window.fetch is a WebIDL [Global] member: Firefox installs it as an OWN property
# of the window INSTANCE, not on Window.prototype. The migrator's prototype-chain
# walk once dropped it as "absent" because it never inspects the instance's own
# properties. The walk now recognises instance-own members and emits an
# instance-resolved {object:"window", depth:0} entry. This test proves that
# migrated entry actually instruments window.fetch end to end.
# --------------------------------------------------------------------------- #
@pytest.mark.usefixtures("xpi", "server")
class TestStealthMigratedFetchCapture:
    """A migrated legacy ``{"window": ["fetch"]}`` config captures fetch() calls.

    Spec: the "Instance-own members of a global object" section of the migrator
    module docstring (``openwpm/utilities/js_settings_migrator.py``).
    """

    def test_migrated_window_fetch_is_captured(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Migrate ``{"window": ["fetch"]}`` and confirm the call is recorded.

        Runs the real sweep (headless Firefox) on the legacy config, applies the
        generated stealth config, visits a page that calls ``window.fetch``, and
        asserts a ``window.fetch`` ``call`` row lands in the ``javascript`` table.
        Also pins that the sweep emits an instance-resolved ``window`` entry for
        fetch and does NOT surface ``window.fetch`` as untranslated.
        """
        data_dir = tmp_path_factory.mktemp("migrated_fetch")
        stealth_settings, untranslated = legacy_settings_to_stealth(
            [{"window": ["fetch"]}], get_firefox_binary_path()
        )
        assert any(
            e["object"] == "window"
            and "fetch" in e["logSettings"]["propertiesToInstrument"]
            for e in stealth_settings
        ), (
            "the sweep did not emit an instance-resolved window.fetch entry; got "
            f"{stealth_settings}"
        )
        assert not any(r.path == "window.fetch" for r in untranslated), (
            "window.fetch must not be surfaced as untranslated once the walk "
            f"resolves it as an instance-own member; got {untranslated}"
        )

        db_path = _run_page(
            _params_with(data_dir, stealth_settings),
            _page_url(server, FETCH_PAGE),
        )
        rows = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript WHERE symbol = ? AND operation = ?",
            ("window.fetch", "call"),
        )
        assert rows[0][0] > 0, (
            "the migrated stealth config did not record a window.fetch call — the "
            "instance-own [Global] member was not instrumented end to end"
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

# nonExisting + logFunctionGets on Navigator (a non-existing property).
NON_EXISTING_SETTINGS: List[Dict] = [
    {
        "object": "Navigator",
        "instrumentedName": "Navigator",
        "depth": 0,
        "logSettings": _log_settings(
            nonExistingPropertiesToInstrument=["openwpmNonExistingProp"],
            logFunctionGets=True,
        ),
    },
]

# recursive/depth: a non-existing object on Navigator instrumented recursively. Lazy
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
        """A non-existing property is captured (get/set) and looks native.

        nonExistingPropertiesToInstrument synthesizes a native-looking accessor
        for a name absent from Navigator.prototype, so get/set on it are
        recorded under the javascript table.
        """
        data_dir = tmp_path_factory.mktemp("non_existing")
        db_path = _run_page(
            _params_with(data_dir, NON_EXISTING_SETTINGS),
            _page_url(server, NON_EXISTING_PROPS_PAGE),
        )
        sets = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
            ("Navigator.openwpmNonExistingProp", "set"),
        )
        assert sets[0][0] > 0, (
            "nonExistingPropertiesToInstrument did not capture a set on the "
            "synthesized non-existing property"
        )
        gets = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
            ("Navigator.openwpmNonExistingProp", "get"),
        )
        assert gets[0][0] > 0, (
            "nonExistingPropertiesToInstrument did not capture a get on the "
            "synthesized non-existing property"
        )

    def test_log_function_gets_emits_get_function(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """logFunctionGets records get(function) when the value is a function.

        After the page assigns a function to the non-existing property, reading
        it WITHOUT calling must emit a get(function) row (and no plain get for the
        function value), matching legacy.
        """
        data_dir = tmp_path_factory.mktemp("fn_gets")
        db_path = _run_page(
            _params_with(data_dir, NON_EXISTING_SETTINGS),
            _page_url(server, NON_EXISTING_PROPS_PAGE),
        )
        fn_gets = db_utils.query_db(
            db_path,
            "SELECT COUNT(*) FROM javascript " "WHERE symbol = ? AND operation = ?",
            ("Navigator.openwpmNonExistingProp", "get(function)"),
        )
        assert fn_gets[0][0] > 0, (
            "logFunctionGets did not record a get(function) row when the "
            "non-existing property held a function value"
        )

    def test_non_existing_property_stays_native(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """The synthesized non-existing accessor reports [native code]."""
        data_dir = tmp_path_factory.mktemp("non_existing_detect")
        results = _probe_results(
            _params_with(data_dir, NON_EXISTING_SETTINGS),
            _page_url(server, NON_EXISTING_PROPS_PAGE),
        )
        assert results, "no non-existing-property probe results collected"
        assert results.get("value_roundtrips") is True
        assert results.get("function_roundtrips") is True
        assert results.get("non_existing_getter_native") is True, (
            "synthesized non-existing getter does not report [native code] "
            f"(probe error: {results.get('descriptor_error')})"
        )
        assert (
            results.get("non_existing_setter_native") is True
        ), "synthesized non-existing setter does not report [native code]"


# --------------------------------------------------------------------------- #
# Recursive is the ONE legacy logSetting the stealth instrument cannot support.
# It requires defining accessors on the in-page Object/Array instances returned
# by instrumented getters, which Firefox's Xray wrappers forbid for stealth's
# isolated compartment (``js/xpconnect/wrappers/XrayWrapper.cpp``,
# ``JSXrayTraits::defineProperty``); waiving to ``wrappedJSObject`` yields a
# different object identity so page-side reads never see the instrumentation.
# This is fundamental to the isolation that makes stealth undetectable, so a
# stealth surface requesting recursive is rejected at config-validation time
# rather than silently crashing the page at runtime. Legacy ``js_instrument``
# still supports recursive because it runs in the page compartment. See
# ``docs/developers/Stealth-Instrumentation.rst`` (Limitations).
# --------------------------------------------------------------------------- #
class TestStealthRecursiveRejected:
    """Recursive under stealth is rejected with an actionable ConfigError."""

    @pytest.mark.pyonly
    def test_recursive_rejected_at_config(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """A stealth surface requesting recursive is rejected at config time."""
        data_dir = tmp_path_factory.mktemp("recursive")
        _, browser_params = _params_with(data_dir, RECURSIVE_SETTINGS)
        with pytest.raises(ConfigError, match="[Rr]ecursive"):
            validate_browser_params(browser_params[0])

    @pytest.mark.pyonly
    def test_recursive_rejection_points_at_js_instrument(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """The recursive rejection points users at js_instrument as the remedy."""
        data_dir = tmp_path_factory.mktemp("recursive_detect")
        _, browser_params = _params_with(data_dir, RECURSIVE_SETTINGS)
        with pytest.raises(ConfigError, match="js_instrument"):
            validate_browser_params(browser_params[0])


# --------------------------------------------------------------------------- #
# Legacy-shaped settings pointed at stealth: a researcher who flips a custom
# legacy ``js_instrument_settings`` config over to ``stealth_js_instrument_settings``
# would otherwise hit a cryptic ``jsonschema.ValidationError`` with no guidance.
# ``clean_stealth_js_instrumentation_settings`` wraps that failure in a
# ``ConfigError`` that explains the stealth-shaped form and points at the
# ``openwpm.utilities.js_settings_migrator`` sweep utility for translating a legacy
# config — mirroring the recursive-rejection ConfigError in ``openwpm/config.py``.
# --------------------------------------------------------------------------- #
class TestStealthLegacyShapedSettingsHint:
    """Legacy-shaped stealth settings fail with a sweep-utility pointer."""

    @pytest.mark.pyonly
    def test_legacy_collection_string_points_at_sweep(self) -> None:
        """A legacy collection-name string is rejected with the sweep hint."""
        legacy_collection: List[Any] = ["collection_fingerprinting"]
        with pytest.raises(ConfigError, match="js_settings_migrator"):
            clean_stealth_js_instrumentation_settings(legacy_collection)

    @pytest.mark.pyonly
    def test_legacy_shorthand_dict_points_at_sweep(self) -> None:
        """A legacy dotted-path shorthand dict is rejected with the sweep hint."""
        legacy_shorthand: List[Any] = [{"window.navigator": ["userAgent"]}]
        with pytest.raises(ConfigError, match="js_settings_migrator"):
            clean_stealth_js_instrumentation_settings(legacy_shorthand)

    @pytest.mark.pyonly
    def test_valid_stealth_settings_pass_unchanged(self) -> None:
        """A valid stealth-shaped config still validates and passes through."""
        result = clean_stealth_js_instrumentation_settings(CUSTOM_STEALTH_SETTINGS)
        assert result == CUSTOM_STEALTH_SETTINGS


@pytest.mark.pyonly
def test_migrator_reports_send_beacon() -> None:
    """A legacy Navigator capture loses sendBeacon to the stealth default, and
    says so."""
    entry = {"logSettings": {"propertiesToInstrument": ["sendBeacon", "userAgent"]}}
    dropped = _drop_unwrapped_members(entry, "Navigator", "window.navigator")
    assert entry["logSettings"]["propertiesToInstrument"] == ["userAgent"]
    assert [d.path for d in dropped] == ["window.navigator.sendBeacon"]
    assert "pagehide" in dropped[0].reason
    assert "to wrap it anyway" in dropped[0].reason


@pytest.mark.pyonly
@pytest.mark.parametrize(
    "log_settings,warns",
    [
        ({}, True),
        ({"excludedProperties": ["sendBeacon"]}, False),
        ({"propertiesToInstrument": ["sendBeacon"]}, True),
        (
            {"propertiesToInstrument": [{"depth": 0, "propertyNames": ["sendBeacon"]}]},
            True,
        ),
        ({"propertiesToInstrument": ["userAgent"]}, False),
    ],
)
def test_wrapping_send_beacon_warns(
    caplog: pytest.LogCaptureFixture, log_settings: Dict, warns: bool
) -> None:
    """A custom surface may wrap sendBeacon, but is told what it loses."""
    settings = [
        {
            "object": "Navigator",
            "instrumentedName": "window.navigator",
            "depth": 0,
            "logSettings": _log_settings(**log_settings),
        }
    ]
    with caplog.at_level(logging.WARNING, logger="openwpm"):
        assert clean_stealth_js_instrumentation_settings(settings) == settings
    assert ("Navigator.sendBeacon" in caplog.text) == warns
    assert "anyway" not in caplog.text


@pytest.mark.pyonly
def test_stealth_settings_collision_is_reported_as_such() -> None:
    settings = [
        {
            "object": "Navigator",
            "instrumentedName": "window.navigator",
            "depth": 0,
            "logSettings": _log_settings(
                propertiesToInstrument=["userAgent"],
                excludedProperties=["userAgent"],
            ),
        }
    ]
    with pytest.raises(ConfigError, match="collide") as info:
        clean_stealth_js_instrumentation_settings(settings)
    assert "js_settings_migrator" not in str(info.value)


@pytest.mark.pyonly
def test_stealth_settings_must_be_a_list() -> None:
    with pytest.raises(TypeError, match="must be a list"):
        clean_stealth_js_instrumentation_settings({"object": "Navigator"})  # type: ignore[arg-type]


@pytest.mark.pyonly
def test_legacy_merge_rejects_stealth_shaped_entries() -> None:
    from openwpm.js_instrumentation import _merge_settings

    entry = {
        "object": "Navigator",
        "instrumentedName": "window.navigator",
        "logSettings": _log_settings(
            propertiesToInstrument=[{"depth": 0, "propertyNames": ["userAgent"]}]
        ),
    }
    with pytest.raises(RuntimeError, match="non-string"):
        _merge_settings([entry])


# --------------------------------------------------------------------------- #
# Symbol PARITY: stealth is a drop-in replacement for legacy js_instrument, so
# the ``symbol`` column it emits must match legacy byte-for-byte. Published
# OpenWPM fingerprinting analyses query exact symbols (e.g.
# ``WHERE symbol='window.navigator.userAgent'``); if stealth emitted a
# different label the query would silently return zero rows. This test runs the
# SAME probe page through BOTH modes (legacy ``collection_fingerprinting``
# default and the stealth bundled default) and asserts the DISTINCT symbol SETS
# match, except for one documented, intentional difference: the audio
# shared-prototype methods (see DOCUMENTED_SYMBOL_DELTA). It compares full
# symbols, not ``LIKE`` patterns, so a changed prefix is caught.
# --------------------------------------------------------------------------- #


def _distinct_symbols(db_path: Path) -> set:
    rows = db_utils.query_db(
        db_path,
        "SELECT DISTINCT symbol FROM javascript",
        as_tuple=True,
    )
    return {r[0] for r in rows}


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


# The ONLY intentional divergence between legacy and stealth symbols. It is a
# structural GRANULARITY difference, not a label mismatch, and is documented in
# docs/developers/Stealth-Instrumentation.rst (Limitations).
#
# Legacy instruments each AudioNode/BaseAudioContext CHILD prototype over its
# FULL inherited chain, so a method defined on the shared parent prototype
# (AudioNode.connect, BaseAudioContext.createGain, ...) is recorded once PER
# CHILD under that child's name (AnalyserNode.connect, GainNode.connect, ...).
# Stealth hooks the shared parent prototype exactly ONCE (a deliberate choice
# that keeps the instrumentation undetectable — re-defining the same shared
# accessor under several child names is observable), so those methods appear a
# single time under the parent-prototype label. The captured CALLS are the same;
# only the symbol LABEL and row multiplicity differ for these shared methods.
#
# Symbols legacy emits that stealth does not (shared methods, per-child labels):
LEGACY_ONLY_AUDIO_SYMBOLS = {
    "AnalyserNode.connect",
    "GainNode.connect",
    "OscillatorNode.connect",
    "OscillatorNode.disconnect",
    "AudioContext.createGain",
    "AudioContext.createOscillator",
    "AudioContext.sampleRate",
    "OfflineAudioContext.createAnalyser",
    "OfflineAudioContext.createGain",
    "OfflineAudioContext.createOscillator",
    "OfflineAudioContext.currentTime",
    "OfflineAudioContext.destination",
    "OfflineAudioContext.sampleRate",
}
# Symbols stealth emits that legacy does not (same shared methods, once, under
# the shared-prototype label):
STEALTH_ONLY_AUDIO_SYMBOLS = {
    "AudioNode.connect",
    "AudioNode.disconnect",
    "[AudioContext|OfflineAudioContext].createAnalyser",
    "[AudioContext|OfflineAudioContext].createGain",
    "[AudioContext|OfflineAudioContext].createOscillator",
    "[AudioContext|OfflineAudioContext].currentTime",
    "[AudioContext|OfflineAudioContext].destination",
    "[AudioContext|OfflineAudioContext].sampleRate",
}


@pytest.mark.usefixtures("xpi", "server")
class TestStealthSymbolParity:
    """Stealth emits the SAME ``symbol`` strings legacy does (drop-in parity)."""

    def test_symbols_match_legacy(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Distinct symbol sets are identical, modulo the documented audio delta.

        Runs the broad symbol probe through legacy (fingerprinting collection)
        and stealth (bundled default). After removing the documented
        shared-prototype audio remap, the two symbol sets must be EQUAL — every
        symbol a published analysis queries (e.g.
        ``window.navigator.userAgent``, ``window.screen.colorDepth``,
        ``window.document.cookie``) is emitted identically by both.
        """
        url = _page_url(server, SYMBOL_PROBE_PAGE)
        legacy_db = _run_page(
            _legacy_params(tmp_path_factory.mktemp("parity_legacy")), url
        )
        stealth_db = _run_page(
            _stealth_params(tmp_path_factory.mktemp("parity_stealth")), url
        )
        legacy_syms = _distinct_symbols(legacy_db)
        stealth_syms = _distinct_symbols(stealth_db)
        assert legacy_syms, "legacy probe recorded no symbols"
        assert stealth_syms, "stealth probe recorded no symbols"

        # Strip the one documented, intentional structural difference.
        legacy_core = legacy_syms - LEGACY_ONLY_AUDIO_SYMBOLS
        stealth_core = stealth_syms - STEALTH_ONLY_AUDIO_SYMBOLS

        missing_under_stealth = legacy_core - stealth_core
        extra_under_stealth = stealth_core - legacy_core
        assert not missing_under_stealth, (
            "stealth does NOT emit these legacy symbols (drop-in parity broken; "
            "a query like WHERE symbol='<name>' would silently return zero rows "
            f"under stealth): {sorted(missing_under_stealth)}"
        )
        assert not extra_under_stealth, (
            "stealth emits symbols legacy does not (unexpected divergence not "
            f"covered by the documented audio delta): {sorted(extra_under_stealth)}"
        )

    def test_key_fingerprint_symbols_present_under_stealth(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """The canonical analysis symbols are present verbatim under stealth.

        Pins the exact strings real studies query so a future label regression
        on any of them fails loudly rather than returning empty result sets.
        """
        url = _page_url(server, SYMBOL_PROBE_PAGE)
        stealth_db = _run_page(
            _stealth_params(tmp_path_factory.mktemp("parity_keys")), url
        )
        symbols = _distinct_symbols(stealth_db)
        for expected in (
            "window.navigator.userAgent",
            "window.navigator.platform",
            "window.screen.colorDepth",
            "window.screen.pixelDepth",
            "window.document.cookie",
            "window.document.referrer",
            "window.name",
            "window.localStorage",
            "HTMLCanvasElement.toDataURL",
            "CanvasRenderingContext2D.fillText",
        ):
            assert expected in symbols, (
                f"stealth did not emit the canonical legacy symbol '{expected}' "
                "— a drop-in query for it would return zero rows"
            )


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
# Legacy -> stealth SWEEP parity (openwpm/utilities/js_settings_migrator.py)
#
# Recursive instrumentation is rejected under stealth, but the sweep utility
# mechanically expands a legacy recursive config into an equivalent FLAT,
# non-recursive stealth config by replaying the legacy descent over a live
# object graph. This test is the correctness proof: it runs a recursive config
# under LEGACY (set A of distinct symbols), runs the SAME config through the
# sweep, runs the generated flat config under STEALTH (set B), and asserts B
# covers A modulo the documented untranslated entries (plain Object/Array nodes the sweep
# reports as untranslatable, plus their recursed subtrees, which have no global
# interface prototype for stealth to hook — the same shared-prototype/plain-node
# granularity class as the audio delta in TestStealthSymbolParity).
# --------------------------------------------------------------------------- #

# A legacy recursive surface over navigator reaching one level of nested
# interface objects (navigator.permissions, .geolocation, …). depth 1 so the
# descent is bounded and deterministic.
RECURSIVE_NAV_LEGACY_SETTINGS: List = [
    {"window.navigator": {"propertiesToInstrument": [], "recursive": True, "depth": 1}},
]


def _legacy_params_with(
    data_dir: Path, settings: List
) -> Tuple[ManagerParams, List[BrowserParams]]:
    manager_params, browser_params = _legacy_params(data_dir)
    browser_params[0].js_instrument_settings = settings
    return manager_params, browser_params


@pytest.mark.usefixtures("xpi", "server")
class TestStealthRecursiveSweepParity:
    """The sweep turns a legacy recursive config into a flat stealth config that
    covers the same API surface (modulo untranslatable plain-object nodes)."""

    def test_generated_stealth_covers_legacy_surface(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """Set B (stealth, swept config) covers set A (legacy, recursive config).

        A and B are the distinct ``symbol`` sets recorded by the SAME probe page
        under the two modes. The only symbols allowed to be in A but not B are
        those rooted at a node the sweep flagged untranslatable (a plain
        Object/Array with no global interface prototype to hook) — the documented,
        narrow set of untranslated entries.
        """
        url = _page_url(server, RECURSIVE_NAV_PROBE_PAGE)

        # Set A: legacy with the recursive config.
        legacy_db = _run_page(
            _legacy_params_with(
                tmp_path_factory.mktemp("sweep_legacy"),
                RECURSIVE_NAV_LEGACY_SETTINGS,
            ),
            url,
        )
        legacy_syms = _distinct_symbols(legacy_db)
        assert legacy_syms, "legacy recursive probe recorded no symbols"

        # Run the sweep on the SAME config to generate the flat stealth config.
        stealth_settings, untranslated = legacy_settings_to_stealth(
            RECURSIVE_NAV_LEGACY_SETTINGS
        )
        assert stealth_settings, "sweep produced no stealth entries"
        # The sweep must not emit a recursive entry (that would re-trip the
        # ConfigError) and must validate against the stealth schema.
        validate_browser_params(
            _params_with(tmp_path_factory.mktemp("sweep_validate"), stealth_settings)[
                1
            ][0]
        )

        # Set B: stealth with the generated flat config.
        stealth_db = _run_page(
            _params_with(tmp_path_factory.mktemp("sweep_stealth"), stealth_settings),
            url,
        )
        stealth_syms = _distinct_symbols(stealth_db)
        assert stealth_syms, "stealth swept probe recorded no symbols"

        # Drop every legacy symbol the sweep flagged as untranslated: untranslatable
        # plain-Object/Array nodes (and their recursed subtree), AND inherited
        # prototype-chain members the depth-0 stealth entry does not cover. These
        # are the documented, HONESTLY-REPORTED gaps — they are precisely the
        # symbols that may be in legacy set A but not stealth set B.
        untranslated_paths = {r.path for r in untranslated}

        def _is_untranslated(symbol: str) -> bool:
            for path in untranslated_paths:
                if symbol == path or symbol.startswith(path + "."):
                    return True
            return False

        legacy_core = {s for s in legacy_syms if not _is_untranslated(s)}

        # Every translated legacy symbol must be emitted under stealth too.
        missing_under_stealth = legacy_core - stealth_syms
        assert not missing_under_stealth, (
            "the swept stealth config does NOT cover these legacy symbols "
            "(surface parity broken outside the documented, reported untranslated entries "
            f"{sorted(untranslated_paths)}): {sorted(missing_under_stealth)}"
        )

        # CRITICAL honesty guard (regression test for the silent-drop defect):
        # every legacy symbol stealth does NOT cover MUST appear in the reported
        # untranslated list. A symbol that is missing-AND-unreported is the exact defect
        # this test guards against — legacy instruments an inherited member that
        # the depth-0 stealth entry drops without surfacing it.
        unreported_drops = (legacy_syms - stealth_syms) - {
            s for s in legacy_syms if _is_untranslated(s)
        }
        assert not unreported_drops, (
            "these legacy symbols are NOT covered by the swept stealth config AND "
            "are NOT reported as untranslated (silent drop): "
            f"{sorted(unreported_drops)}"
        )

        # Sanity: legacy actually descended into a NESTED interface object and
        # recorded a property of it (so set A is non-trivial and the parity
        # assertion above is not vacuous). Legacy suppresses the plain get of an
        # object-valued property under recursion (it returns the recursed child
        # without a get row — see instrumentObject in lib/js-instruments.ts), so
        # the observable evidence of the descent is a SCALAR child property like
        # ``window.navigator.mimeTypes.length``, which the probe reads.
        nested_child_syms = {
            s
            for s in legacy_core
            if s.startswith("window.navigator.")
            and s.count(".") >= 3  # window.navigator.<obj>.<prop>
        }
        assert nested_child_syms, (
            "legacy recorded no nested navigator child property — the recursive "
            "descent the sweep is meant to flatten did not happen, so the parity "
            f"check would be vacuous. legacy symbols: {sorted(legacy_core)}"
        )
        # Each such nested child symbol legacy recorded must be present under
        # stealth too (this is the core drop-in guarantee, restated narrowly).
        assert nested_child_syms <= stealth_syms, (
            "stealth did not record these nested navigator child properties that "
            f"legacy recorded: {sorted(nested_child_syms - stealth_syms)}"
        )

    def test_sweep_reports_plain_array_node_as_untranslatable(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """navigator.languages (an Array) is honestly reported as untranslatable.

        This is the narrow true ceiling: a plain Array/Object node has no global
        interface prototype for stealth to hook, so the sweep surfaces it rather
        than silently under-covering.
        """
        stealth_settings, untranslated = legacy_settings_to_stealth(
            RECURSIVE_NAV_LEGACY_SETTINGS
        )
        untranslated_paths = {r.path for r in untranslated}
        assert "window.navigator.languages" in untranslated_paths, (
            "the sweep failed to flag the plain-Array navigator.languages node as "
            f"untranslatable; reported untranslated paths: {sorted(untranslated_paths)}"
        )
        # And the reason must name it as an untranslatable plain node, not an
        # inherited-member untranslated entry.
        languages_reason = next(
            r.reason for r in untranslated if r.path == "window.navigator.languages"
        )
        assert "Array" in languages_reason, (
            "navigator.languages untranslated reason should identify it as a plain "
            f"Array node; got: {languages_reason!r}"
        )
        # And it must not have smuggled an Array/Object entry into the output.
        objects = {e["object"] for e in stealth_settings}
        assert not (
            objects & {"Array", "Object"}
        ), f"sweep emitted an untranslatable Array/Object entry: {objects}"

    def test_sweep_reports_inherited_chain_members_as_untranslated(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """Inherited prototype-chain members are reported, not silently dropped.

        Regression test for the silent-drop defect: legacy's
        ``getPropertyNames(navigator.permissions)`` covers the entire prototype
        chain (own + inherited), but the flat stealth entry the sweep emits uses
        ``depth: 0``, covering only ``Permissions.prototype``'s OWN names. The
        inherited members (``Object.prototype.toString``, …) are therefore NOT
        instrumented under stealth. The sweep must surface each as an untranslated
        entry with a clear reason — never drop it silently.

        These inherited members must not be absent from both the stealth config
        AND the untranslated list: they must appear in the untranslated list with
        an "inherited"-class reason.
        """
        stealth_settings, untranslated = legacy_settings_to_stealth(
            RECURSIVE_NAV_LEGACY_SETTINGS
        )
        untranslated_by_path = {r.path: r for r in untranslated}

        # navigator.permissions resolves to constructor Permissions, whose
        # .prototype OWN names are {query, constructor}; everything else legacy
        # reaches on the instance is inherited (toString, valueOf, hasOwnProperty,
        # …). Pick toString as a representative inherited member that the probe
        # page also calls, so the gap is real and observable.
        inherited_path = "window.navigator.permissions.toString"
        assert inherited_path in untranslated_by_path, (
            "the sweep silently dropped the inherited member "
            f"{inherited_path!r}: it is NOT instrumented under stealth (depth 0 "
            "covers only Permissions.prototype OWN names) and NOT reported as "
            f"untranslated. Reported untranslated paths: {sorted(untranslated_by_path)}"
        )

        # The reason must identify it as an inherited-chain member (distinct from
        # the untranslatable-plain-node class), and the path must NOT have leaked
        # into the emitted stealth config (stealth cannot attribute it).
        reason = untranslated_by_path[inherited_path].reason
        assert "inherited" in reason.lower(), (
            f"untranslated reason for {inherited_path} should explain the inherited-"
            f"chain gap; got: {reason!r}"
        )
        emitted_paths = {e["instrumentedName"] for e in stealth_settings}
        assert inherited_path not in emitted_paths, (
            "an inherited-chain member must not be emitted as its own stealth "
            f"entry: {inherited_path}"
        )

    def test_untranslated_entry_str_pairs_path_and_reason(self) -> None:
        """``UntranslatedEntry`` renders ``path — reason`` for honest CLI/log output."""
        entry = UntranslatedEntry(path="window.foo.bar", reason="because reasons")
        rendered = str(entry)
        assert "window.foo.bar" in rendered and "because reasons" in rendered


# A NARROW legacy request: only navigator.userAgent, nothing else.
NARROW_NAV_LEGACY_SETTINGS: List = [{"window.navigator": ["userAgent"]}]


class TestStealthNarrowSweepCapture:
    """A NARROW legacy request must migrate to a NARROW stealth entry.

    Under stealth an empty ``propertiesToInstrument`` means "instrument EVERY own
    member of the resolved prototype". So if the sweep emitted ``[]`` for a leaf
    entry, a narrow legacy request like ``{"window.navigator": ["userAgent"]}``
    would silently widen to all ~35 ``Navigator.prototype`` members — a fidelity
    divergence (over-capture) on a PR whose whole point is faithful drop-in
    translation. The sweep must instead emit the EXPLICIT set of requested own
    names.
    """

    def test_narrow_request_emits_only_requested_own_name(self) -> None:
        """``{"window.navigator": ["userAgent"]}`` → leaf ``propertiesToInstrument``
        is exactly ``["userAgent"]`` — NOT ``[]`` (everything) and NOT all 35
        Navigator.prototype members.

        The leaf entry must list the single requested own name; emitting
        ``propertiesToInstrument: []`` (everything) would silently widen the
        request.
        """
        stealth_settings, untranslated = legacy_settings_to_stealth(
            NARROW_NAV_LEGACY_SETTINGS
        )
        nav_entries = [
            e for e in stealth_settings if e["instrumentedName"] == "window.navigator"
        ]
        assert len(nav_entries) == 1, (
            "expected exactly one leaf stealth entry for window.navigator; got "
            f"{[e['instrumentedName'] for e in stealth_settings]}"
        )
        leaf = nav_entries[0]
        assert leaf["object"] == "Navigator"
        props = leaf["logSettings"]["propertiesToInstrument"]
        assert props == ["userAgent"], (
            "a narrow legacy request was silently widened: the leaf entry "
            f"instruments {props!r} instead of exactly ['userAgent']. An empty "
            "list means 'instrument every own member' under stealth, so [] here "
            "would over-capture all Navigator.prototype members."
        )

    def test_everything_request_still_covers_all_own_names(self) -> None:
        """A legacy "instrument everything" navigator entry covers EXACTLY the
        complete ``Navigator.prototype`` own-name set — no member dropped.

        The recursive/everything case must NOT change: when legacy reached the
        node via the "instrument every name" path, ``node["propertyNames"]`` is
        the full ``getPropertyNames`` chain, so its intersection with the leaf's
        own names equals the ENTIRE own set. The leaf still instruments every own
        member — just enumerated explicitly instead of via ``[]``.

        This asserts FULL own-set EQUALITY, not a loose ``len > 5`` / subset
        check: a regression that dropped some own members while keeping a handful
        would slip past a size/subset assertion but is a real over-narrowing of
        the instrument-everything surface. The expected set is computed the same
        way the sweep does — ``Object.getOwnPropertyNames(Navigator.prototype)``
        in a clean browser — via an INDEPENDENT walk, so it is a true regression
        guard rather than a comparison of the sweep against itself.
        """
        narrow_settings, _ = legacy_settings_to_stealth(NARROW_NAV_LEGACY_SETTINGS)
        everything_settings, everything_untranslated = legacy_settings_to_stealth(
            [{"window.navigator": {"propertiesToInstrument": []}}]
        )

        def _nav_props(settings: List[Dict]) -> List[str]:
            nav = [e for e in settings if e["instrumentedName"] == "window.navigator"]
            assert len(nav) == 1
            return nav[0]["logSettings"]["propertiesToInstrument"]

        # Independently compute the complete Navigator.prototype own-name set the
        # SAME way the sweep resolves stealthOwnNames: Object.getOwnPropertyNames
        # of the resolved prototype in a clean browser.
        driver = _launch_browser(get_firefox_binary_path())
        try:
            driver.get("about:blank")
            expected_own = set(
                driver.execute_script(
                    "return Object.getOwnPropertyNames(Navigator.prototype);"
                )
            )
        finally:
            driver.quit()
        assert "userAgent" in expected_own, (
            "the independent walk did not resolve Navigator.prototype own names; "
            f"got: {sorted(expected_own)}"
        )

        everything_props = _nav_props(everything_settings)
        # sendBeacon is left unwrapped, and reported instead.
        assert "window.navigator.sendBeacon" in {
            u.path for u in everything_untranslated
        }
        expected_own.discard("sendBeacon")
        # FULL own-set equality: the everything-case leaf must instrument EXACTLY
        # the complete Navigator.prototype own set — no member dropped, none added.
        assert set(everything_props) == expected_own, (
            "the 'instrument everything' navigator entry does not cover EXACTLY "
            "the complete Navigator.prototype own-name set. Missing: "
            f"{sorted(expected_own - set(everything_props))}; unexpected extra: "
            f"{sorted(set(everything_props) - expected_own)}."
        )
        # The narrow request's own name must of course be inside that full set.
        assert set(_nav_props(narrow_settings)).issubset(expected_own), (
            "the narrow request's own name is not in the complete own-name set; "
            "the explicit enumeration is inconsistent between the two."
        )
        # And the everything-case must be explicit (never the over-broad []).
        assert everything_props != [], (
            "the everything-case must enumerate own names explicitly, not emit [] "
            "(which stealth reads as 'instrument every own member')."
        )

    def test_absent_member_untranslated_reason_is_not_universal_prototype(self) -> None:
        """A member GENUINELY ABSENT from the live prototype chain is reported as
        not-present, NOT as "inherited from a universal/unknown prototype".

        ``addEventListener`` REQUESTED on ``navigator`` has no EventTarget in its
        live chain (navigator is not an EventTarget), so it is owned by NOTHING on
        the chain — the walker reports ``owner=None``. (It is requested via
        ``propertiesToInstrument``, NOT ``nonExistingPropertiesToInstrument``: a
        non-existing property is intentionally instrumented and so must NOT be
        reported as untranslated.)
        The untranslated reason for that absent-member case must say the member is
        absent from the live object, not conflate it with a universal-prototype
        member. The reason must say the member is not present on the live prototype
        chain, never "inherited from None (a universal/unknown prototype)".
        """
        stealth_settings, untranslated = legacy_settings_to_stealth(
            [{"window.navigator": ["addEventListener"]}]
        )
        untranslated_by_path = {r.path: r for r in untranslated}
        absent_path = "window.navigator.addEventListener"
        assert absent_path in untranslated_by_path, (
            "a member absent from the live navigator chain should be reported as "
            f"untranslated; reported untranslated paths: {sorted(untranslated_by_path)}"
        )
        reason = untranslated_by_path[absent_path].reason
        assert "universal" not in reason.lower(), (
            "the untranslated reason for a genuinely-absent member must NOT claim it is "
            f"inherited from a universal/unknown prototype; got: {reason!r}"
        )
        assert "None" not in reason, (
            "the untranslated reason must not surface the bare 'None' owner; got: "
            f"{reason!r}"
        )
        assert "not present" in reason.lower() or "absent" in reason.lower(), (
            "the untranslated reason should state the member is not present on / absent "
            f"from the live object's prototype chain; got: {reason!r}"
        )

    def test_narrow_inherited_only_request_emits_no_empty_leaf(self) -> None:
        """A narrow request naming ONLY inherited/absent members must NOT emit a
        leaf entry with an empty ``propertiesToInstrument``.

        ``{"window.navigator": ["addEventListener"]}`` names a member that is NOT
        own on ``Navigator.prototype`` (navigator is not an ``EventTarget``, so it
        is absent from the live chain). The requested-own intersection is therefore
        empty. If the sweep still emitted a ``window.navigator`` leaf entry, its
        ``propertiesToInstrument`` would be ``[]`` — which the stealth instrument
        reads as "instrument EVERY own member of the resolved prototype", silently
        widening a single-member request to all ~35 ``Navigator.prototype``
        members. The requested member is not lost: it is surfaced in the
        untranslated list (asserted by
        ``test_absent_member_untranslated_reason_is_not_universal_prototype``).
        """
        stealth_settings, untranslated = legacy_settings_to_stealth(
            [{"window.navigator": ["addEventListener"]}]
        )
        nav_entries = [
            e for e in stealth_settings if e["instrumentedName"] == "window.navigator"
        ]
        assert nav_entries == [], (
            "a narrow request naming only an inherited/absent member emitted a "
            "leaf stealth entry for window.navigator, wholesale-instrumenting "
            f"Navigator.prototype. Emitted nav entries: {nav_entries!r}"
        )
        # Belt and suspenders: no leaf entry anywhere may carry the over-broad
        # empty propertiesToInstrument that means "instrument everything".
        empty_leaves = [
            e
            for e in stealth_settings
            if e["logSettings"].get("propertiesToInstrument") == []
            and not e["logSettings"].get("nonExistingPropertiesToInstrument")
            and not e["logSettings"].get("receiverInterfaces")
        ]
        assert empty_leaves == [], (
            "an over-broad leaf entry with empty propertiesToInstrument (reads as "
            f"'instrument every own member' under stealth) was emitted: {empty_leaves!r}"
        )

    def test_non_existing_property_is_not_reported_as_untranslated(self) -> None:
        """A non-existing property (``nonExistingPropertiesToInstrument``) is
        CAPTURED, not reported as untranslated.

        A non-existing property is absent from the live prototype chain BY DESIGN,
        so the walk reports ``owner=None`` for it. But it is NOT a coverage gap:
        the emitted leaf entry carries the same ``nonExistingPropertiesToInstrument``,
        and the stealth instrument synthesizes a native-looking accessor for it
        (proven by ``test_non_existing_property_captured_and_native``). Reporting
        it as untranslated would double-classify a captured member as uncovered,
        lying in the honesty report. It must therefore NOT appear in the
        untranslated list even though its absent-member branch (``owner is None``)
        could otherwise misclassify it.
        """
        stealth_settings, untranslated = legacy_settings_to_stealth(
            [
                {
                    "window.navigator": {
                        "propertiesToInstrument": ["userAgent"],
                        "nonExistingPropertiesToInstrument": ["openwpmNonExistingProp"],
                    }
                }
            ]
        )
        non_existing_path = "window.navigator.openwpmNonExistingProp"
        untranslated_paths = {r.path for r in untranslated}
        assert non_existing_path not in untranslated_paths, (
            "a non-existing property is captured by the leaf entry's "
            "nonExistingPropertiesToInstrument, so it must NOT be reported as "
            f"uncovered/untranslated; reported untranslated paths: {sorted(untranslated_paths)}"
        )
        # And it must actually be carried on the emitted leaf entry so the stealth
        # instrument synthesizes the accessor (i.e. it really is captured, which is
        # WHY excluding it from the untranslated list is honest, not a silent drop).
        nav = [
            e for e in stealth_settings if e["instrumentedName"] == "window.navigator"
        ]
        assert len(nav) == 1, (
            "expected exactly one leaf stealth entry for window.navigator; got "
            f"{[e['instrumentedName'] for e in stealth_settings]}"
        )
        assert "openwpmNonExistingProp" in nav[0]["logSettings"].get(
            "nonExistingPropertiesToInstrument", []
        ), (
            "the non-existing property was excluded from the untranslated list but is also NOT "
            "carried on the leaf entry — that would be a genuine silent drop. Leaf "
            f"logSettings: {nav[0]['logSettings']!r}"
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
# docs/developers/Stealth-Instrumentation.rst and
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


@pytest.mark.usefixtures("xpi", "server")
class TestStealthSweepSharedPrototype:
    """The sweep emits interface-attributed shared-prototype entries for inherited
    METHODS owned by a real interface, and leaves the rest untranslated."""

    def test_sweep_emits_shared_prototype_entry_for_inherited_method(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """An inherited method on a real interface prototype becomes a
        shared-prototype entry with receiverInterfaces — not an untranslated entry.

        Sweeping a recursive config over ``window.document`` (an EventTarget /
        Node / Document) reaches ``addEventListener``
        (EventTarget.prototype.addEventListener), which is NOT an own name of
        ``HTMLDocument.prototype``. The sweep must emit a single entry instrumenting
        ``EventTarget.addEventListener`` with ``receiverInterfaces`` containing the
        leaf interface (``HTMLDocument``), and must NOT report it as untranslated.
        """
        legacy = [
            {
                "window.document": {
                    "propertiesToInstrument": [],
                    "recursive": True,
                    "depth": 0,
                }
            }
        ]
        stealth_settings, untranslated = legacy_settings_to_stealth(legacy)

        # The generated config must validate against the stealth schema (proves
        # the new receiverInterfaces field is accepted end-to-end).
        validate_browser_params(
            _params_with(
                tmp_path_factory.mktemp("sweep_shared_validate"), stealth_settings
            )[1][0]
        )

        shared = [
            e
            for e in stealth_settings
            if e["object"] == "EventTarget"
            and e["logSettings"].get("receiverInterfaces")
            and "addEventListener" in e["logSettings"]["propertiesToInstrument"]
        ]
        assert shared, (
            "the sweep did not emit an interface-attributed shared-prototype entry "
            "for EventTarget.addEventListener reached via window.document; entries: "
            f"{[(e['object'], e['logSettings']['propertiesToInstrument']) for e in stealth_settings]}"
        )
        recv = shared[0]["logSettings"]["receiverInterfaces"]
        assert "HTMLDocument" in recv, (
            "the shared-prototype entry's receiverInterfaces must contain the leaf "
            f"interface HTMLDocument; got {recv}"
        )

        # Consolidation guard: ALL inherited methods of EventTarget must land in
        # ONE entry. Emitting one entry per (owner, member) creates several entries
        # resolving to the SAME EventTarget.prototype; the sweep consolidates them
        # into one so the config stays one entry per prototype. So there must be
        # exactly ONE EventTarget entry,
        # and it must carry the OTHER inherited EventTarget methods alongside
        # addEventListener — not just one.
        all_eventtarget = [e for e in stealth_settings if e["object"] == "EventTarget"]
        assert len(all_eventtarget) == 1, (
            "EventTarget inherited methods were split across multiple entries; the "
            "sweep must consolidate them into one. Entries "
            f"for EventTarget: {[e['logSettings']['propertiesToInstrument'] for e in all_eventtarget]}"
        )
        et_members = set(all_eventtarget[0]["logSettings"]["propertiesToInstrument"])
        assert {
            "addEventListener",
            "removeEventListener",
            "dispatchEvent",
        } <= et_members, (
            "the consolidated EventTarget entry must list every inherited method "
            "(addEventListener, removeEventListener, dispatchEvent), so a single "
            f"entry hooks them all; got {sorted(et_members)}"
        )

        # addEventListener must NOT also appear as untranslated (it is now covered).
        untranslated_paths = {r.path for r in untranslated}
        assert "window.document.addEventListener" not in untranslated_paths, (
            "addEventListener was reported as untranslated despite being covered by an "
            "interface-attributed shared-prototype entry (double-counted)"
        )

    def test_sweep_leaves_inherited_universal_and_accessor_members_untranslated(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """Universal-prototype members and inherited accessors stay untranslated.

        ``toString`` (Object.prototype, universal) and an inherited ACCESSOR like
        ``URL`` (Document.prototype, real interface but not a method) must NOT be
        instrumented — only methods are interface-attributable. Both stay
        untranslated with reasons that explain why.
        """
        legacy = [
            {
                "window.document": {
                    "propertiesToInstrument": [],
                    "recursive": True,
                    "depth": 0,
                }
            }
        ]
        _, untranslated = legacy_settings_to_stealth(legacy)
        untranslated_by_path = {r.path: r.reason for r in untranslated}

        assert "window.document.toString" in untranslated_by_path, (
            "the universal-prototype member toString must be untranslated; "
            f"untranslated: {sorted(untranslated_by_path)}"
        )
        assert (
            "universal" in untranslated_by_path["window.document.toString"].lower()
        ), untranslated_by_path["window.document.toString"]

        assert "window.document.URL" in untranslated_by_path, (
            "the inherited accessor URL must be untranslated (only methods are "
            f"interface-attributable); untranslated: {sorted(untranslated_by_path)}"
        )
        assert (
            "non-method" in untranslated_by_path["window.document.URL"].lower()
        ), untranslated_by_path["window.document.URL"]


# A recursive navigator surface that reaches several interfaces (Navigator,
# Permissions, Geolocation, …), every one of which inherits the universal
# Object.prototype methods (toString, valueOf, …). Used by both the flag-OFF and
# flag-ON universal-capture tests below.
UNIVERSAL_SWEEP_LEGACY_SETTINGS: List = [
    {"window.navigator": {"propertiesToInstrument": [], "recursive": True, "depth": 1}},
]


class TestStealthSweepUniversalPrototypeCapture:
    """Opt-in ``capture_universal_prototype_members`` flag on the sweep.

    By DEFAULT (flag OFF) inherited methods owned by a universal prototype
    (``Object.prototype.toString``/``valueOf``/…) are left untranslated — hooking
    them would fire on every object page-wide for zero tracking signal. A
    researcher who wants strict legacy-``recursive`` parity can opt in: the flag
    routes those universal METHODS into the same interface-attributed
    shared-prototype path used for real interfaces (a single
    ``{object: "Object", …}`` entry with ``receiverInterfaces``), and they are no
    longer untranslated. Non-method universal members (accessors) stay untranslated
    regardless.
    """

    def test_flag_off_universal_methods_are_untranslated(self) -> None:
        """DEFAULT (flag OFF): universal-prototype methods stay untranslated, NOT
        captured.

        Pins the unchanged default: ``toString``/``valueOf`` reached via the
        recursive navigator surface appear in the untranslated list with a
        ``universal``-class reason, and NO ``{object: "Object"/"Array"}`` entry is
        emitted. This is the control companion to the flag-ON capture test.
        """
        stealth_settings, untranslated = legacy_settings_to_stealth(
            UNIVERSAL_SWEEP_LEGACY_SETTINGS
        )
        untranslated_by_path = {r.path: r.reason for r in untranslated}

        for member in ("toString", "valueOf"):
            path = f"window.navigator.{member}"
            assert path in untranslated_by_path, (
                f"with the flag OFF the universal method {member!r} must be "
                f"untranslated; reported untranslated paths: {sorted(untranslated_by_path)}"
            )
            assert "universal" in untranslated_by_path[path].lower(), (
                f"untranslated reason for {path} should name the universal-prototype "
                f"class; got: {untranslated_by_path[path]!r}"
            )

        emitted_universal = {
            e["object"] for e in stealth_settings if e["object"] in {"Object", "Array"}
        }
        assert not emitted_universal, (
            "with the flag OFF the sweep must NOT emit an Object/Array universal-"
            f"prototype entry; emitted: {emitted_universal}"
        )

    def test_flag_on_universal_methods_become_shared_prototype_entry(self) -> None:
        """FLAG ON: universal-prototype methods become an ``{object: "Object"}``
        shared-prototype entry and leave the untranslated list.

        The SAME recursive navigator config, swept with
        ``capture_universal_prototype_members=True``, must:
          * emit exactly one ``{object: "Object"}`` shared-prototype entry whose
            ``propertiesToInstrument`` includes ``toString`` (and the other
            universal Object.prototype methods),
          * carry ``receiverInterfaces`` covering the leaf interfaces the recursive
            surface reached (Navigator, Permissions, …),
          * NOT report those universal methods as untranslated any more, and
          * still leave the universal ACCESSOR ``__proto__`` untranslated (only
            methods are interface-attributable).

        With the flag OFF (the companion test above) these members are
        untranslated and there is no Object entry; with the flag ON they are
        captured here.
        """
        stealth_settings, untranslated = legacy_settings_to_stealth(
            UNIVERSAL_SWEEP_LEGACY_SETTINGS,
            capture_universal_prototype_members=True,
        )
        untranslated_paths = {r.path for r in untranslated}

        object_entries = [e for e in stealth_settings if e["object"] == "Object"]
        assert len(object_entries) == 1, (
            "the flag must emit exactly ONE consolidated Object shared-prototype "
            "entry (one entry hooking every member); "
            f"got {len(object_entries)} Object entries"
        )
        entry = object_entries[0]
        assert entry["instrumentedName"] == "Object" and entry["depth"] == 0

        members = set(entry["logSettings"]["propertiesToInstrument"])
        assert {"toString", "valueOf"} <= members, (
            "the Object shared-prototype entry must carry the universal methods "
            f"(toString, valueOf, …); got {sorted(members)}"
        )

        receiver_interfaces = set(entry["logSettings"].get("receiverInterfaces", []))
        assert {"Navigator", "Permissions"} <= receiver_interfaces, (
            "receiverInterfaces must cover the leaf interfaces the recursive "
            f"surface reached (Navigator, Permissions, …); got "
            f"{sorted(receiver_interfaces)}"
        )

        # No universal METHOD reached this way may remain untranslated (they are now
        # captured); the companion flag-OFF test asserts the opposite default.
        for member in ("toString", "valueOf"):
            path = f"window.navigator.{member}"
            assert path not in untranslated_paths, (
                f"with the flag ON the universal method {member!r} must NOT be "
                f"untranslated (it is now captured); untranslated paths: {sorted(untranslated_paths)}"
            )

        # Non-method universal members (accessors) stay untranslated regardless of the
        # flag — the receiver-interface filter only applies to methods at call time.
        assert "window.navigator.__proto__" in untranslated_paths, (
            "the universal ACCESSOR __proto__ must stay untranslated even with the flag "
            f"ON (only methods are interface-attributable); untranslated paths: "
            f"{sorted(untranslated_paths)}"
        )

    def test_flag_on_generated_config_validates(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """The flag-ON output, including the Object entry, passes schema validation.

        This is a CONFIG-SHAPE check only (``validate_browser_params``); it proves
        the generated entry is well-formed, NOT that it captures correctly at
        runtime. The end-to-end runtime behaviour — navigator.toString() recorded,
        a <div>'s toString() dropped, and no reentrancy hang — is asserted
        separately by ``test_flag_on_universal_capture_runs_and_filters``.
        """
        stealth_settings, _ = legacy_settings_to_stealth(
            UNIVERSAL_SWEEP_LEGACY_SETTINGS,
            capture_universal_prototype_members=True,
        )
        validate_browser_params(
            _params_with(
                tmp_path_factory.mktemp("sweep_universal_validate"), stealth_settings
            )[1][0]
        )

    @pytest.mark.usefixtures("xpi")
    def test_flag_on_universal_capture_runs_and_filters(
        self, tmp_path_factory: pytest.TempPathFactory, server: ServerUrls
    ) -> None:
        """RUNTIME proof of the flag: capture, filter, and no reentrancy.

        Sweeps the recursive navigator config with the flag ON, runs a STEALTH
        crawl with the generated config over a probe page that calls
        ``navigator.toString()`` (interface Navigator, IN ``receiverInterfaces``)
        and ``someDiv.toString()`` (HTMLDivElement, NOT in it), and asserts:

        (a) the navigator call IS recorded under the static symbol
            ``Object.toString`` with the receiver interface ``Navigator`` in the
            dedicated ``receiver`` column (the universal method was actually
            hooked and attributed by receiver);
        (b) the div call is NOT recorded — no ``Object.toString`` row whose
            ``receiver`` is ``HTMLDivElement`` (the instrument's receiver filter
            works on the UNIVERSAL method, not just real interfaces);
        (c) the crawl COMPLETES — the probe reaches its ``data-results`` sentinel
            (read back via ``ReadDetectionResults``). Wrapping
            ``Object.prototype.toString`` means the instrument's own
            ``serializeObject``/``JSON.stringify`` re-enter the wrapped method while
            building each log record would re-enter the wrapped method if the
            instrument ran page code. A reentrancy hang or stack blow-up would
            surface here
            as the crawl never finishing / no sentinel.

        This is the runtime counterpart to the config-shape tests above and the
        evidence for the flag's actual effect.
        """
        stealth_settings, _ = legacy_settings_to_stealth(
            UNIVERSAL_SWEEP_LEGACY_SETTINGS,
            capture_universal_prototype_members=True,
        )

        # The Object shared-prototype entry must carry Navigator (so the navigator
        # call is recorded) and must NOT carry HTMLDivElement (so the div call is
        # dropped). Pin both preconditions so a config regression can't make the
        # runtime assertions below vacuously pass.
        object_entries = [e for e in stealth_settings if e["object"] == "Object"]
        assert len(object_entries) == 1, (
            "expected exactly one Object shared-prototype entry from the flag-ON "
            f"sweep; got {len(object_entries)}"
        )
        recv_interfaces = set(
            object_entries[0]["logSettings"].get("receiverInterfaces", [])
        )
        assert "Navigator" in recv_interfaces, (
            "Navigator must be in the Object entry's receiverInterfaces for the "
            f"navigator.toString() call to be recorded; got {sorted(recv_interfaces)}"
        )
        assert "HTMLDivElement" not in recv_interfaces, (
            "HTMLDivElement must NOT be in receiverInterfaces (the navigator surface "
            "never reaches it) or the div-drop assertion would be vacuous; got "
            f"{sorted(recv_interfaces)}"
        )

        params = _params_with(
            tmp_path_factory.mktemp("universal_runtime"), stealth_settings
        )
        # ReadDetectionResults reads the page's #results sentinel and ships it into
        # the crawl DB; its presence proves the page (and the instrumented toString
        # path) ran to completion with no reentrancy hang/blow-up.
        results = _collect_results(params, _page_url(server, UNIVERSAL_TOSTRING_PAGE))
        assert results.get("done") is True, (
            "the probe page did not reach its sentinel — the crawl did not complete "
            "(possible reentrancy hang/blow-up from wrapping Object.prototype."
            f"toString); self-report: {results!r}"
        )

        pairs = _distinct_symbol_receiver_pairs(
            params[0].data_directory / "crawl-data.sqlite"
        )
        # (a) navigator.toString() captured under the static universal symbol with
        # the Navigator receiver attributed.
        assert ("Object.toString", "Navigator") in pairs, (
            "the flag-ON universal capture did not record navigator.toString() as "
            "symbol='Object.toString' with receiver='Navigator'; recorded "
            f"(symbol, receiver) pairs: {sorted(pairs)}"
        )
        # (b) someDiv.toString() dropped by the instrument's receiver filter — no
        # Object.toString row attributed to HTMLDivElement.
        assert ("Object.toString", "HTMLDivElement") not in pairs, (
            "the instrument's receiver filter did not drop the non-targeted "
            "HTMLDivElement toString() call; an Object.toString row was attributed "
            f"to HTMLDivElement. Recorded pairs: {sorted(pairs)}"
        )
        divs = {recv for (sym, recv) in pairs if sym == "Object.toString"}
        assert divs == {"Navigator"}, (
            "Object.toString must be recorded for the Navigator receiver only; the "
            f"receiver filter let other interfaces through: {sorted(divs)}"
        )

    def test_function_universal_methods_are_gated_like_object_and_array(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All THREE universal constructors (Object/Function/Array) are gated by the
        flag consistently — Function is not special-cased into always-capture.

        Function-owned inherited members are vanishingly rare in real configs (a
        function node's leaf own-set already IS Function.prototype's own names, so
        ``call``/``apply``/``bind`` are covered by its leaf entry, not as inherited
        members). To exercise the classification deterministically without depending
        on that, this test feeds the sweep a SYNTHETIC walk result via a fake driver:
        one leaf node that inherits a METHOD owned by ``Function`` (``bind``) and a
        METHOD owned by ``Object`` (``toString``), both reported by the walk as
        ``realInterface=True`` (as they are when reached via a real page object,
        where the page-realm prototype identity differs from the content script's —
        see the module docstring).

        Gating contract: the inherited-member branch must NOT admit a
        ``realInterface`` method merely because its owner is not Object/Array, so a
        ``Function``-owned ``bind`` must not be captured in both flag states.
        ``Function`` is treated as a universal owner like ``Object``/``Array``:
          * flag OFF  -> ``bind`` (Function) AND ``toString`` (Object) are
                         untranslated; no ``{object: "Function"|"Object"}``
                         shared-prototype entry.
          * flag ON   -> both become consolidated shared-prototype entries.
        """
        # One leaf node (a fictional "Widget" interface) whose chain inherits a
        # Function-owned method (bind) and an Object-owned method (toString).
        synthetic = {
            "reached": [
                {
                    "instrumentedName": "window.widget",
                    "constructorName": "Widget",
                    "propertyNames": ["doThing", "bind", "toString"],
                    # Leaf own-set: only the interface's own method.
                    "stealthOwnNames": ["doThing"],
                    "inheritedOwners": [
                        {
                            "member": "bind",
                            "owner": "Function",
                            "realInterface": True,
                            "isFunction": True,
                        },
                        {
                            "member": "toString",
                            "owner": "Object",
                            "realInterface": True,
                            "isFunction": True,
                        },
                    ],
                }
            ],
            "errors": [],
        }

        class _FakeDriver:
            def get(self, _url: str) -> None:
                pass

            def execute_script(self, _js: str, _arg: Any) -> str:
                return json.dumps(synthetic)

            def quit(self) -> None:
                pass

        monkeypatch.setattr(
            "openwpm.utilities.js_settings_migrator._launch_browser",
            lambda _binary: _FakeDriver(),
        )

        legacy = [{"window.widget": {"propertiesToInstrument": [], "recursive": False}}]

        # Flag OFF: both universal methods are untranslated; no Function/Object entry.
        off_settings, off_untranslated = legacy_settings_to_stealth(
            legacy, firefox_binary="unused"
        )
        off_untranslated_paths = {r.path for r in off_untranslated}
        assert "window.widget.bind" in off_untranslated_paths, (
            "with the flag OFF a Function-owned inherited method must be untranslated "
            "(gated like Object/Array), not captured; untranslated: "
            f"{sorted(off_untranslated_paths)}"
        )
        assert "window.widget.toString" in off_untranslated_paths
        off_universal_objects = {
            e["object"] for e in off_settings if e["object"] in {"Object", "Function"}
        }
        assert not off_universal_objects, (
            "with the flag OFF the sweep must NOT emit a Function/Object universal "
            f"shared-prototype entry; emitted: {off_universal_objects}"
        )

        # Flag ON: both become consolidated shared-prototype entries; Function is
        # captured exactly like Object — consistent gating.
        on_settings, on_untranslated = legacy_settings_to_stealth(
            legacy,
            firefox_binary="unused",
            capture_universal_prototype_members=True,
        )
        on_untranslated_paths = {r.path for r in on_untranslated}
        function_entries = [e for e in on_settings if e["object"] == "Function"]
        assert len(function_entries) == 1, (
            "with the flag ON a Function-owned method must be captured as a single "
            "consolidated {object: 'Function'} shared-prototype entry (gated like "
            f"Object/Array); Function entries: {function_entries}"
        )
        assert "bind" in function_entries[0]["logSettings"]["propertiesToInstrument"]
        assert "window.widget.bind" not in on_untranslated_paths, (
            "with the flag ON the Function-owned method must NOT remain untranslated "
            f"(it is now captured); untranslated: {sorted(on_untranslated_paths)}"
        )
        # The Object-owned method is captured the same way — confirming all three
        # universal constructors share one gating path.
        object_entries = [e for e in on_settings if e["object"] == "Object"]
        assert len(object_entries) == 1 and (
            "toString" in object_entries[0]["logSettings"]["propertiesToInstrument"]
        )


# --------------------------------------------------------------------------- #
# Regression: a narrow legacy config requesting DIFFERENT members on two
# receivers that share one prototype (e.g. addEventListener on document,
# dispatchEvent on body — both inherit EventTarget) once tripped a bogus
# "impossible under inheritance" RuntimeError in _shared_prototype_entries,
# because the sweep records only the REQUESTED members (not the owner's full
# inherited set), so the per-owner receiver-interface sets legitimately differ
# per member. The consolidation now unions the per-member receiver sets; this
# config must translate cleanly into one shared-prototype entry for the shared
# owner that carries every requested member, with receiverInterfaces covering
# each member's own reaching interface(s) — and never crash.
# --------------------------------------------------------------------------- #
NARROW_DISJOINT_SHARED_LEGACY_SETTINGS: List[Dict] = [
    {"window.document": ["addEventListener"]},
    {"window.document.body": ["dispatchEvent"]},
]


class TestStealthSweepNarrowSharedPrototype:
    """The sweep must not crash on a narrow config whose two receivers share a
    prototype but request disjoint members (the false "impossible" invariant).

    This drives a headless Firefox via ``legacy_settings_to_stealth`` (no built
    ``xpi`` or local ``server`` involved), so it deliberately carries no
    ``usefixtures`` — adding them would needlessly serialize it behind the
    session-scoped server.
    """

    def test_disjoint_narrow_members_consolidate_without_crash(self) -> None:
        stealth_settings, untranslated = legacy_settings_to_stealth(
            NARROW_DISJOINT_SHARED_LEGACY_SETTINGS,
            get_firefox_binary_path(),
        )
        # One shared-prototype entry for the EventTarget owner, carrying BOTH
        # requested members, with receiverInterfaces covering the leaf
        # interfaces that reached each member.
        event_target_entries = [
            e
            for e in stealth_settings
            if e.get("object") == "EventTarget"
            and e.get("logSettings", {}).get("receiverInterfaces")
        ]
        assert event_target_entries, (
            "sweep produced no EventTarget shared-prototype entry for the narrow "
            "disjoint config (it must not crash and must consolidate the owner)"
        )
        members: set = set()
        receivers: set = set()
        for e in event_target_entries:
            members.update(e["logSettings"]["propertiesToInstrument"])
            receivers.update(e["logSettings"]["receiverInterfaces"])
        assert {"addEventListener", "dispatchEvent"} <= members, (
            "the consolidated EventTarget entry must union BOTH narrowly "
            f"requested members; got {sorted(members)}"
        )
        # HTMLDocument reached addEventListener, an HTMLBodyElement reached
        # dispatchEvent — both must appear as receiver interfaces.
        assert {"HTMLDocument", "HTMLBodyElement"} <= receivers, (
            "receiverInterfaces must cover each requested member's reaching "
            f"interface; got {sorted(receivers)}"
        )

        # union-and-NOTE, not just union-and-no-crash: the interface-level
        # over-capture (addEventListener now also fires on HTMLBodyElement, and
        # dispatchEvent on HTMLDocument) MUST be honestly recorded as an
        # untranslated note keyed ``<owner>.<shared-prototype>``, not silently
        # swallowed. A future refactor that drops the note would otherwise keep this
        # test green; assert against the real untranslated shape emitted by
        # ``_shared_prototype_entries`` (path + per-member reaching-set reason).
        note = next(
            (r for r in untranslated if r.path == "EventTarget.<shared-prototype>"),
            None,
        )
        assert note is not None, (
            "the disjoint-narrow union must emit an "
            "'EventTarget.<shared-prototype>' over-capture untranslated note; got "
            f"untranslated paths {sorted(r.path for r in untranslated)}"
        )
        assert "over-capture" in note.reason.lower(), note.reason
        # The reason must name each member's own reaching receiver set, so a
        # researcher can see exactly which (symbol, receiver) pairs were widened.
        assert "addEventListener->" in note.reason, note.reason
        assert "dispatchEvent->" in note.reason, note.reason
        assert "HTMLDocument" in note.reason, note.reason
        assert "HTMLBodyElement" in note.reason, note.reason


# A synthetic walk result: ONE reached node on a real, non-universal interface
# (EventTarget) that inherits the three base Function.prototype methods
# (call/apply/bind) from a prototype whose constructor.name is "Function". The
# node's OWN names do NOT include them, so they are classified as inherited
# members. With "Function" in UNIVERSAL_PROTOTYPE_CONSTRUCTORS they must be left
# UNTRANSLATED (instrumenting them would fire on virtually every callable page-wide);
# this fake exercises that classification gate with no browser.
_FUNCTION_UNIVERSAL_WALK = {
    "errors": [],
    "reached": [
        {
            "instrumentedName": "window.eventTarget",
            "constructorName": "EventTarget",
            # own names of the leaf prototype (none of call/apply/bind)
            "stealthOwnNames": ["addEventListener"],
            # legacy requested the own method plus the three inherited Function
            # base-prototype methods
            "propertyNames": ["addEventListener", "call", "apply", "bind"],
            "inheritedOwners": [
                {
                    "member": "call",
                    "owner": "Function",
                    "realInterface": True,
                    "isFunction": True,
                },
                {
                    "member": "apply",
                    "owner": "Function",
                    "realInterface": True,
                    "isFunction": True,
                },
                {
                    "member": "bind",
                    "owner": "Function",
                    "realInterface": True,
                    "isFunction": True,
                },
            ],
        }
    ],
}


class _FakeWalkDriver:
    """Stand-in Selenium driver: ``execute_script`` returns a canned walk JSON,
    so the sweep's classification runs with no real Firefox."""

    def __init__(self, walk: Dict) -> None:
        self._walk = walk

    def get(self, _url: str) -> None:
        pass

    def execute_script(self, _script: str, _arg: object) -> str:
        return json.dumps(self._walk)

    def quit(self) -> None:
        pass


class TestStealthSweepFunctionUniversalDefault:
    """Pin the DEFAULT-OFF classification of universal Function.prototype members.

    With the default config (no opt-in universal-capture flag), inherited
    ``Function.prototype`` members (call/apply/bind) MUST be left untranslated, not
    captured page-wide. This guards ``UNIVERSAL_PROTOTYPE_CONSTRUCTORS``: a future
    edit dropping ``"Function"`` from that set would silently re-classify these as
    interface-attributed shared-prototype entries (page-wide capture) — this test
    goes red instead. Driven by a synthetic walk so it needs no browser.
    """

    @pytest.mark.pyonly
    def test_function_prototype_members_untranslated_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            js_settings_migrator,
            "_launch_browser",
            lambda _binary: _FakeWalkDriver(_FUNCTION_UNIVERSAL_WALK),
        )
        legacy = [
            {
                "window.eventTarget": {
                    "propertiesToInstrument": [
                        "addEventListener",
                        "call",
                        "apply",
                        "bind",
                    ],
                    "recursive": False,
                    "depth": 0,
                }
            }
        ]
        stealth_settings_out, untranslated = legacy_settings_to_stealth(
            legacy, firefox_binary="unused"
        )

        untranslated_by_path = {r.path: r.reason for r in untranslated}
        for member in ("call", "apply", "bind"):
            path = f"window.eventTarget.{member}"
            assert path in untranslated_by_path, (
                f"inherited Function.prototype member {member!r} must be untranslated "
                f"by default (got untranslated paths {sorted(untranslated_by_path)})"
            )
            assert (
                "universal" in untranslated_by_path[path].lower()
            ), untranslated_by_path[path]

        # And they must NOT have leaked into a page-wide capture entry: no emitted
        # stealth entry may instrument call/apply/bind. (Dropping "Function" from
        # UNIVERSAL_PROTOTYPE_CONSTRUCTORS makes exactly this assertion fail.)
        captured = {
            prop
            for entry in stealth_settings_out
            for prop in entry["logSettings"].get("propertiesToInstrument", [])
        }
        assert not ({"call", "apply", "bind"} & captured), (
            "Function.prototype base methods were captured page-wide instead of "
            f"left untranslated; captured properties: {sorted(captured)}"
        )


_PREVENT_SETS_WALK = {
    "errors": [],
    "reached": [
        {
            "instrumentedName": "window.navigator",
            "constructorName": "Navigator",
            "stealthOwnNames": ["userAgent"],
            "propertyNames": ["userAgent"],
            "inheritedOwners": [],
        }
    ],
}


class TestStealthSweepDropsPreventSets:
    """The sweep drops ``preventSets`` (not carried over) and warns about it.

    Unlike ``recursive`` (rejected at config time because stealth cannot honour
    it), stealth could technically block page writes — but doing so distorts the
    measured behaviour, so the migrator drops it and observes the page's real
    writes instead. Driven by a synthetic walk so it needs no browser.
    """

    @pytest.mark.pyonly
    def test_prevent_sets_is_dropped_and_warned(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.setattr(
            js_settings_migrator,
            "_launch_browser",
            lambda _binary: _FakeWalkDriver(_PREVENT_SETS_WALK),
        )
        legacy = [
            {
                "window.navigator": {
                    "propertiesToInstrument": ["userAgent"],
                    "preventSets": True,
                    "recursive": False,
                    "depth": 0,
                }
            }
        ]
        with caplog.at_level(logging.WARNING, logger="openwpm"):
            stealth_settings_out, _ = legacy_settings_to_stealth(
                legacy, firefox_binary="unused"
            )

        # No emitted stealth entry may carry preventSets — it is forced off.
        for entry in stealth_settings_out:
            assert entry["logSettings"]["preventSets"] is False, (
                "preventSets must be dropped (forced off) on translation; got "
                f"{entry['logSettings']}"
            )

        # The drop is surfaced, naming the requesting legacy path.
        assert any(
            "preventSets" in rec.message and "window.navigator" in rec.message
            for rec in caplog.records
        ), (
            "the sweep must warn that preventSets was dropped, naming the path; "
            f"got warnings: {[rec.message for rec in caplog.records]}"
        )


# --------------------------------------------------------------------------- #
# GOLDEN migration tests: pin the EXACT legacy -> stealth migration output
# for a small representative table of configs, so a future migrator change cannot
# silently drift the emitted stealth config or the UntranslatedEntry list.
#
# All cases are driven by a SYNTHETIC walk through ``_FakeWalkDriver`` (the same
# mocked-sweep pattern the other ``TestStealthSweep*`` classes use), so they run
# under ``-m pyonly`` with no real Firefox: the only browser-dependent step
# (``_launch_browser`` + the live object-graph walk) is replaced by a canned walk
# result, and the deterministic Python classification/emit logic under test runs
# unchanged. Each case fixes BOTH halves of the migrator's return tuple — the
# emitted ``stealth_settings`` list AND the ``UntranslatedEntry`` list.
# --------------------------------------------------------------------------- #


def _run_sweep_with_walk(
    monkeypatch: pytest.MonkeyPatch,
    walk: Dict,
    legacy: List[Any],
    **kwargs: Any,
) -> Tuple[List[Dict[str, Any]], List[UntranslatedEntry]]:
    """Drive ``legacy_settings_to_stealth`` against a canned ``walk`` (no browser).

    Patches ``_launch_browser`` to return a ``_FakeWalkDriver`` whose
    ``execute_script`` yields ``walk``; everything downstream (classification,
    shared-prototype consolidation, untranslated reporting) is the real code.
    """
    monkeypatch.setattr(
        js_settings_migrator,
        "_launch_browser",
        lambda _binary: _FakeWalkDriver(walk),
    )
    return legacy_settings_to_stealth(legacy, firefox_binary="unused", **kwargs)


# A clean, fully translatable narrow request: a single interface-typed leaf node
# whose requested member is its OWN prototype member (no inheritance, no
# untranslatable nodes). The narrow request must stay narrow (explicit
# propertiesToInstrument, NOT [] which stealth reads as "instrument everything").
_GOLDEN_CLEAN_WALK = {
    "errors": [],
    "reached": [
        {
            "instrumentedName": "window.navigator",
            "constructorName": "Navigator",
            # Navigator.prototype has these own members; legacy only asked for one.
            "stealthOwnNames": ["userAgent", "platform"],
            "propertyNames": ["userAgent"],
            "inheritedOwners": [],
        }
    ],
}
_GOLDEN_CLEAN_LEGACY: List[Any] = [{"window.navigator": ["userAgent"]}]
_GOLDEN_CLEAN_EXPECTED_SETTINGS: List[Dict[str, Any]] = [
    {
        "object": "Navigator",
        "instrumentedName": "window.navigator",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": ["userAgent"],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
            "overwrittenProperties": [],
        },
    }
]


# An untranslatable plain-object node: the resolved node's ``constructor.name`` is
# ``Array`` (a plain container, not a global interface with a hookable prototype),
# so the WHOLE node is surfaced as an UntranslatedEntry and emits NO stealth entry.
_GOLDEN_UNTRANSLATABLE_WALK = {
    "errors": [],
    "reached": [
        {
            "instrumentedName": "window.navigator.languages",
            "constructorName": "Array",
            "stealthOwnNames": None,
            "propertyNames": ["length"],
            "inheritedOwners": [],
        }
    ],
}
_GOLDEN_UNTRANSLATABLE_LEGACY: List[Any] = [{"window.navigator.languages": []}]
_GOLDEN_UNTRANSLATABLE_EXPECTED_SETTINGS: List[Dict[str, Any]] = []
_GOLDEN_UNTRANSLATABLE_EXPECTED_UNTRANSLATED = [
    UntranslatedEntry(
        path="window.navigator.languages",
        reason=(
            "constructor is 'Array' (Object/Array/unknown); no global interface "
            "prototype for stealth to hook, so the node cannot be expressed as a "
            "stealth entry"
        ),
    )
]


# The disjoint-members-on-shared-prototype UNION / over-capture case: two leaves
# (HTMLDocument, HTMLBodyElement) that each request a DIFFERENT inherited method of
# the SAME shared owner prototype (EventTarget). The sweep must consolidate them
# into ONE EventTarget shared-prototype entry whose receiverInterfaces UNIONS both
# leaves, AND emit an honest over-capture UntranslatedEntry note. The two leaf
# entries carry empty propertiesToInstrument (the requested members are inherited,
# not the leaf's own names).
_GOLDEN_UNION_WALK = {
    "errors": [],
    "reached": [
        {
            "instrumentedName": "window.document",
            "constructorName": "HTMLDocument",
            "stealthOwnNames": ["createElement"],
            "propertyNames": ["addEventListener"],
            "inheritedOwners": [
                {
                    "member": "addEventListener",
                    "owner": "EventTarget",
                    "realInterface": True,
                    "isFunction": True,
                }
            ],
        },
        {
            "instrumentedName": "window.document.body",
            "constructorName": "HTMLBodyElement",
            "stealthOwnNames": ["text"],
            "propertyNames": ["dispatchEvent"],
            "inheritedOwners": [
                {
                    "member": "dispatchEvent",
                    "owner": "EventTarget",
                    "realInterface": True,
                    "isFunction": True,
                }
            ],
        },
    ],
}
_GOLDEN_UNION_LEGACY: List[Any] = [
    {"window.document": ["addEventListener"]},
    {"window.document.body": ["dispatchEvent"]},
]


_GOLDEN_UNION_EXPECTED_SETTINGS: List[Dict[str, Any]] = [
    {
        "object": "EventTarget",
        "instrumentedName": "EventTarget",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": ["addEventListener", "dispatchEvent"],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "overwrittenProperties": [],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
            "receiverInterfaces": ["HTMLBodyElement", "HTMLDocument"],
        },
    },
]
_GOLDEN_UNION_EXPECTED_UNTRANSLATED = [
    UntranslatedEntry(
        path="EventTarget.<shared-prototype>",
        reason=(
            "Your legacy config asked to instrument different members on objects "
            "that share the EventTarget prototype (addEventListener->"
            "['HTMLDocument'], dispatchEvent->['HTMLBodyElement']). The stealth "
            "instrument can't instrument them separately, so it instruments all of "
            "them together (['HTMLBodyElement', 'HTMLDocument']). Every member you "
            "asked for is still captured — but some calls may also be recorded "
            "under an interface that only another member needed (over-capture). To "
            "recover exactly the members you requested, filter the results by "
            "(symbol, receiver) in post-processing."
        ),
    )
]


# Instance-own member of a [Global] object. window.fetch is an OWN property of the
# window INSTANCE (WebIDL [Global] members are installed on the global object
# itself), absent from Window.prototype. The constructor-prototype leaf entry
# (object="Window", depth 0) resolves to Window.prototype and misses it, and
# inheritedOwners (walking the prototype chain ABOVE the instance) never sees it —
# so it arrives with owner=None, which the migrator once dropped as "absent". The
# walk now marks it instance-own (instanceOwnNames) and instance-resolvable
# (instanceObjectName), so the sweep emits a dedicated instance-resolved entry
# (object="window", depth 0) — the same convention the bundled default uses for
# window.name/localStorage. Regression pin for the migrator walk-resolution gap.
_GOLDEN_INSTANCE_OWN_WALK = {
    "errors": [],
    "reached": [
        {
            "instrumentedName": "window",
            "constructorName": "Window",
            # Window.prototype's OWN names do NOT include fetch (it is instance-own).
            "stealthOwnNames": ["length", "document"],
            # fetch is an OWN property of the window INSTANCE.
            "instanceOwnNames": ["fetch", "length", "document"],
            "instanceObjectName": "window",
            "propertyNames": ["fetch"],
            "inheritedOwners": [],
        }
    ],
}
_GOLDEN_INSTANCE_OWN_LEGACY: List[Any] = [{"window": ["fetch"]}]
_GOLDEN_INSTANCE_OWN_EXPECTED_SETTINGS: List[Dict[str, Any]] = [
    {
        "object": "window",
        "instrumentedName": "window",
        "depth": 0,
        "logSettings": {
            "propertiesToInstrument": ["fetch"],
            "nonExistingPropertiesToInstrument": [],
            "excludedProperties": [],
            "logCallStack": False,
            "logFunctionsAsStrings": False,
            "logFunctionGets": False,
            "preventSets": False,
            "recursive": False,
            "depth": 5,
            "overwrittenProperties": [],
        },
    }
]


class TestStealthSweepInstanceOwnGlobalMember:
    """The instance-own [Global] member path (regression for the walk gap).

    ``window.fetch`` (and structurally-similar WebIDL ``[Global]`` members —
    ``atob``, ``setTimeout``, ...) live as OWN properties of the window INSTANCE,
    not on ``Window.prototype``. The migrator once dropped them as "absent" because
    the prototype-chain walk never inspects the instance's own properties. The
    sweep must instead emit a dedicated instance-resolved ``{object: "window",
    depth: 0}`` entry that instruments them, and must NOT report ``window.fetch``
    as untranslated. Driven by a synthetic walk (no browser).
    """

    def test_instance_own_member_translates_and_is_not_untranslated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        settings, untranslated = _run_sweep_with_walk(
            monkeypatch,
            _GOLDEN_INSTANCE_OWN_WALK,
            _GOLDEN_INSTANCE_OWN_LEGACY,
        )
        assert settings == _GOLDEN_INSTANCE_OWN_EXPECTED_SETTINGS, (
            "window.fetch (instance-own [Global] member) did not translate to the "
            f"expected instance-resolved entry; got {settings}"
        )
        assert not any(r.path == "window.fetch" for r in untranslated), (
            "window.fetch must NOT be surfaced as untranslated once the walk "
            f"resolves it as an instance-own member; got {untranslated}"
        )
        # And no over-broad leaf entry: the constructor-prototype leaf (which would
        # resolve Window.prototype and miss fetch) must be suppressed, not emitted
        # with an empty (== instrument-everything) propertiesToInstrument.
        assert all(
            e["object"] != "Window" for e in settings
        ), f"an unwanted Window.prototype leaf entry was emitted: {settings}"


class TestStealthSweepDisjointSharedPrototypeUnion:
    """The disjoint-members-on-shared-prototype UNION / over-capture path.

    A narrow legacy config asks two receivers that share ONE prototype
    (``HTMLDocument`` and ``HTMLBodyElement``, both inheriting ``EventTarget``) to
    instrument DIFFERENT inherited members. One entry per prototype carries one
    receiver filter, so the sweep must UNION the members' receiver sets into one
    ``EventTarget`` entry — capturing everything requested —
    and emit the over-capture warning. Driven by a synthetic walk (no browser).
    """

    @pytest.mark.pyonly
    def test_union_consolidates_and_warns(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="openwpm"):
            settings, untranslated = _run_sweep_with_walk(
                monkeypatch, _GOLDEN_UNION_WALK, _GOLDEN_UNION_LEGACY
            )

        # UNION behaviour: exactly one EventTarget shared-prototype entry carrying
        # BOTH requested members and BOTH reaching interfaces (the union).
        event_target = [e for e in settings if e["object"] == "EventTarget"]
        assert len(event_target) == 1, (
            "the two disjoint requests on a shared prototype must consolidate into "
            f"exactly ONE EventTarget entry; got {event_target}"
        )
        ls = event_target[0]["logSettings"]
        assert ls["propertiesToInstrument"] == ["addEventListener", "dispatchEvent"]
        assert ls["receiverInterfaces"] == ["HTMLBodyElement", "HTMLDocument"], (
            "receiverInterfaces must UNION both leaves' interfaces; got "
            f"{ls['receiverInterfaces']}"
        )

        # The over-capture warning fires as an UntranslatedEntry note.
        note = next(
            (r for r in untranslated if r.path == "EventTarget.<shared-prototype>"),
            None,
        )
        assert note is not None, (
            "the union must emit an 'EventTarget.<shared-prototype>' over-capture "
            f"note; got {sorted(r.path for r in untranslated)}"
        )
        # Plain-language wording (not the old needsWrapper/receiverInterfaces
        # jargon): researcher-readable, names the over-capture and the post-process
        # recovery, and interpolates the per-member reaching sets ({detail}) and the
        # unioned leaf set ({leaves}).
        reason = note.reason
        assert "over-capture" in reason.lower(), reason
        assert "share the EventTarget prototype" in reason, reason
        assert "filter the results by (symbol, receiver)" in reason, reason
        assert "addEventListener->['HTMLDocument']" in reason, reason
        assert "dispatchEvent->['HTMLBodyElement']" in reason, reason
        # The dropped insider terms must NOT reappear in the reworded warning.
        assert "needsWrapper" not in reason, reason
        assert "receiverInterfaces" not in reason, reason

        # And the library-side one-line warning fires (untranslated is non-empty).
        assert any("NOT representable" in rec.message for rec in caplog.records), [
            rec.message for rec in caplog.records
        ]

    @pytest.mark.pyonly
    def test_union_golden_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Pin the EXACT emitted settings + untranslated list for the union case."""
        settings, untranslated = _run_sweep_with_walk(
            monkeypatch, _GOLDEN_UNION_WALK, _GOLDEN_UNION_LEGACY
        )
        assert settings == _GOLDEN_UNION_EXPECTED_SETTINGS
        assert untranslated == _GOLDEN_UNION_EXPECTED_UNTRANSLATED


@pytest.mark.parametrize(
    "walk, legacy, expected_settings, expected_untranslated",
    [
        pytest.param(
            _GOLDEN_CLEAN_WALK,
            _GOLDEN_CLEAN_LEGACY,
            _GOLDEN_CLEAN_EXPECTED_SETTINGS,
            [],
            id="clean-translatable-narrow",
        ),
        pytest.param(
            _GOLDEN_UNTRANSLATABLE_WALK,
            _GOLDEN_UNTRANSLATABLE_LEGACY,
            _GOLDEN_UNTRANSLATABLE_EXPECTED_SETTINGS,
            _GOLDEN_UNTRANSLATABLE_EXPECTED_UNTRANSLATED,
            id="untranslatable-plain-object",
        ),
        pytest.param(
            _GOLDEN_UNION_WALK,
            _GOLDEN_UNION_LEGACY,
            _GOLDEN_UNION_EXPECTED_SETTINGS,
            _GOLDEN_UNION_EXPECTED_UNTRANSLATED,
            id="disjoint-shared-prototype-union",
        ),
        pytest.param(
            _GOLDEN_INSTANCE_OWN_WALK,
            _GOLDEN_INSTANCE_OWN_LEGACY,
            _GOLDEN_INSTANCE_OWN_EXPECTED_SETTINGS,
            [],
            id="instance-own-global-member",
        ),
    ],
)
@pytest.mark.pyonly
def test_migration_golden_table(
    monkeypatch: pytest.MonkeyPatch,
    walk: Dict,
    legacy: List[Any],
    expected_settings: List[Dict[str, Any]],
    expected_untranslated: List[UntranslatedEntry],
) -> None:
    """Pin legacy -> stealth migration input->output exactly.

    For each (legacy ``js_instrument_settings`` input, canned walk) pair, assert
    the EXACT migrated stealth config AND the EXACT ``UntranslatedEntry`` list. A
    migrator change that drifts either half goes red here. Driven by a synthetic
    walk so it runs under ``-m pyonly`` with no real Firefox.
    """
    settings, untranslated = _run_sweep_with_walk(monkeypatch, walk, legacy)
    assert settings == expected_settings
    assert untranslated == expected_untranslated


# Two legacy paths reaching the same prototype: ``window.screen`` and ``Screen``
# both resolve to Screen.prototype and both request ``width``.
_SAME_PROTOTYPE_WALK = {
    "errors": [],
    "reached": [
        {
            "instrumentedName": "window.screen",
            "constructorName": "Screen",
            "stealthOwnNames": ["width", "height", "colorDepth"],
            "propertyNames": ["width", "colorDepth"],
            "inheritedOwners": [],
        },
        {
            "instrumentedName": "Screen",
            "constructorName": "Screen",
            "stealthOwnNames": ["width", "height", "colorDepth"],
            "propertyNames": ["width", "height"],
            "inheritedOwners": [],
        },
    ],
}


@pytest.mark.pyonly
def test_migration_reports_member_requested_twice_on_one_prototype(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A member is recorded under one label only, so the second request for it
    is reported instead of emitted; the disjoint members of both paths stay."""
    settings, untranslated = _run_sweep_with_walk(
        monkeypatch,
        _SAME_PROTOTYPE_WALK,
        [{"window.screen": ["width", "colorDepth"]}, {"Screen": ["width", "height"]}],
    )
    assert [
        (e["object"], e["instrumentedName"], e["logSettings"]["propertiesToInstrument"])
        for e in settings
    ] == [
        ("Screen", "window.screen", ["colorDepth", "width"]),
        ("Screen", "Screen", ["height"]),
    ]
    assert [u.path for u in untranslated] == ["Screen.width"]
    assert "window.screen.width" in untranslated[0].reason
