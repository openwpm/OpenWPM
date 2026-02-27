"""Tests that verify the stealth extension makes OpenWPM undetectable.

These tests are based on the detection methods described in:
- Krumnow et al., "Fingerprint surface-based detection of web bot detectors" (ESORICS 2019)
- https://github.com/bkrumnow/DetectOpenWPM
- https://github.com/IAIK/jstemplate

Each test visits a detection page and checks that the browser appears
indistinguishable from a normal (non-instrumented) Firefox browser.

These tests are expected to:
- PASS when stealth_js_instrument=True (stealth extension active)
- FAIL when js_instrument=True (legacy instrumentation, which pollutes prototypes)
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple

import pytest
from selenium.webdriver import Firefox

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket

from . import utilities
from .openwpmtest import OpenWPMTest

STEALTH_DETECTION_URL = f"{utilities.BASE_TEST_URL}/stealth_detection.html"


class ReadDetectionResults(BaseCommand):
    """Command that reads detection test results from the page DOM."""

    def __init__(self) -> None:
        self.results = None

    def __repr__(self) -> str:
        return "ReadDetectionResults"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        results_json = webdriver.execute_script(
            "return document.getElementById('results').getAttribute('data-results');"
        )
        if results_json:
            self.results = json.loads(results_json)


def _run_detection(
    manager_params: ManagerParams,
    browser_params: List[BrowserParams],
) -> dict:
    """Run the detection page and return results."""
    from openwpm.storage.sql_provider import SQLiteStorageProvider
    from openwpm.task_manager import TaskManager

    db_path = manager_params.data_directory / "crawl-data.sqlite"
    structured_provider = SQLiteStorageProvider(db_path)
    manager = TaskManager(
        manager_params,
        browser_params,
        structured_provider,
        None,
    )

    cs = CommandSequence(STEALTH_DETECTION_URL)
    cs.get(sleep=2)
    read_cmd = ReadDetectionResults()
    cs.append_command(read_cmd)
    manager.execute_command_sequence(cs)
    manager.close()

    return read_cmd.results or {}


@pytest.mark.usefixtures("xpi", "server")
class TestStealthDetection:
    """Tests that verify stealth mode defeats common detection vectors.

    These tests PASS when the stealth extension is active, meaning
    the browser appears as a normal, non-instrumented Firefox.
    """

    @pytest.fixture(autouse=True)
    def set_tmpdir(self, tmp_path: Path) -> None:
        self.tmpdir = tmp_path

    def _get_stealth_config(
        self,
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params = ManagerParams(num_browsers=1)
        browser_params = [BrowserParams()]
        manager_params.data_directory = self.tmpdir
        manager_params.log_path = self.tmpdir / "openwpm.log"
        manager_params.testing = True
        browser_params[0].display_mode = "headless"
        browser_params[0].stealth_js_instrument = True
        browser_params[0].js_instrument = False
        return manager_params, browser_params

    def _get_legacy_config(
        self,
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params = ManagerParams(num_browsers=1)
        browser_params = [BrowserParams()]
        manager_params.data_directory = self.tmpdir
        manager_params.log_path = self.tmpdir / "openwpm.log"
        manager_params.testing = True
        browser_params[0].display_mode = "headless"
        browser_params[0].stealth_js_instrument = False
        browser_params[0].js_instrument = True
        return manager_params, browser_params

    def test_stealth_passes_all_detection_checks(self):
        """With stealth enabled, all detection checks should pass.

        This test will only pass once the stealth extension is
        properly integrated and rebased onto master.
        """
        manager_params, browser_params = self._get_stealth_config()
        results = _run_detection(manager_params, browser_params)

        assert results, "No detection results collected"

        # navigator.webdriver should be hidden
        assert (
            results.get("webdriver_flag") is True
        ), "navigator.webdriver was not hidden by stealth extension"

        # Canvas functions should still appear native (no prototype pollution)
        assert (
            results.get("canvas_functions_native") is True
        ), "Canvas functions are not native - stealth instrument should avoid prototype pollution"

        # Storage functions should still appear native
        assert (
            results.get("storage_functions_native") is True
        ), "Storage functions are not native - stealth instrument should avoid prototype pollution"

        # Navigator getters should appear native
        assert (
            results.get("navigator_native") is True
        ), "Navigator getters are not native - stealth instrument should avoid prototype pollution"

        # No OpenWPM globals should be exposed
        assert (
            results.get("no_global_leaks") is True
        ), "OpenWPM globals detected (jsInstruments, instrumentFingerprintingApis, etc.)"

        # Constructor properties should be preserved
        assert (
            results.get("constructors_present") is True
        ), "Constructor properties missing on instrumented objects"

        # Function.prototype.bind should not be tampered
        assert (
            results.get("bind_integrity") is True
        ), "Function.prototype.bind integrity check failed"

        # Error stacks should not contain extension URLs
        assert (
            results.get("clean_error_stacks") is True
        ), "Error stack traces contain moz-extension:// URLs"

        # No extra properties added to prototypes
        assert (
            results.get("no_extra_prototype_properties") is True
        ), "Extra instrumentation properties found on prototypes"

        # RTC functions should appear native
        assert (
            results.get("rtc_native") is True
        ), "RTCPeerConnection functions are not native"

    def test_legacy_instrument_is_detectable(self):
        """With legacy JS instrumentation, detection checks should catch it.

        This serves as a control test - proving the detection page
        actually works by showing the legacy instrument IS detectable.
        At minimum, the toString/native checks should fail.
        """
        manager_params, browser_params = self._get_legacy_config()
        results = _run_detection(manager_params, browser_params)

        assert results, "No detection results collected"

        # The legacy instrument SHOULD be detectable by at least one check.
        # The canvas functions should NOT appear native when legacy
        # instrumentation is active (because it wraps them).
        detectable = (
            not results.get("canvas_functions_native", True)
            or not results.get("storage_functions_native", True)
            or not results.get("no_global_leaks", True)
            or not results.get("constructors_present", True)
        )
        assert detectable, (
            "Legacy JS instrumentation was not detected by any check - "
            "the detection page may not be working correctly"
        )
