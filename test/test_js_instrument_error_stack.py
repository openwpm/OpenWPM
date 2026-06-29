"""INVESTIGATION / DO-NOT-MERGE: surface the page-observable error.stack of a
thrown instrumented call so the literal trace shows up in the CI log.

This reproduces PR #1207's (``harden/legacy-error-stacks``) setup faithfully:
it instruments ``window.atob``, has page code call it with invalid base64 so it
throws an ``InvalidCharacterError``, catches the error in page code, stashes
``e.stack`` into ``document.title`` (prefixed ``STACK:``), and a custom command
reads the title back to a file across the process boundary.

The ONE difference from #1207: instead of asserting
``"moz-extension://" not in stack`` -- which is a NO-OP because the legacy
instrument runs in the page world and never produces a moz-extension frame --
this test DUMPS the exact captured stack via ``pytest.fail(...)``. ``pytest.fail``
is used deliberately: it guarantees the full stack prints in the CI log
regardless of content (a passing assertion would hide it). This lets us read the
literal ``error.stack`` value and check #1207's "no moz-extension:// frame" claim
against ground truth.

Expectation (per an earlier empirical repro under ``datadir/stack-leak/``): no
moz-extension:// frame is present, BUT a page-attributed legacy-instrument
wrapper frame (``getInstrumentJS`` / ``instrumentFunction``) at the document URL
IS present -- which is the real page-observable leak that #1207's no-op
assertion misses.

This test is EXPECTED TO FAIL in CI by design (it ends in ``pytest.fail``). That
is not a regression; the failure message carries the captured trace.
"""

from pathlib import Path

import pytest
from selenium.webdriver import Firefox

from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket

TEST_PAGE = "/js_instrument/instrument_error_stack.html"

# The custom command writes the page-captured stack here, relative to the
# manager's data directory, so the test can read it back across the process
# boundary (commands run in a subprocess and can't return values directly).
CAPTURE_FILENAME = "captured_error_stack.txt"


class CaptureStackCommand(BaseCommand):
    """Reads the error stack the test page stored in ``document.title``.

    The page runs an instrumented API that throws, catches the error, and writes
    its ``.stack`` into the document title (prefixed with ``STACK:``). We read it
    back via Selenium and persist it to a file in the data directory.
    """

    def __repr__(self) -> str:
        return "CaptureStackCommand"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        title = webdriver.title
        out_path = manager_params.data_directory / CAPTURE_FILENAME
        out_path.write_text(title, encoding="utf-8")


def test_instrumented_error_stack_demonstration(
    default_params, task_manager_creator, server
):
    """DO-NOT-MERGE demonstration: surface the page-observable error.stack.

    Reproduces #1207's flow, then prints the literal captured stack via
    ``pytest.fail`` so Stefan can read it in CI and check the "no
    moz-extension:// frame" claim against ground truth.
    """
    manager_params, browser_params = default_params
    for bp in browser_params:
        bp.js_instrument = True
        # Instrument an API that we can make throw deterministically from page
        # code. atob() raises an InvalidCharacterError (a DOMException) when
        # given input outside the base64 alphabet.
        bp.js_instrument_settings = [{"window": ["atob"]}]

    tm, db = task_manager_creator((manager_params, browser_params))
    cs = CommandSequence(server.base + TEST_PAGE)
    cs.append_command(GetCommand(server.base + TEST_PAGE, 0))
    cs.append_command(CaptureStackCommand())
    tm.execute_command_sequence(cs)
    tm.close()

    capture_path: Path = manager_params.data_directory / CAPTURE_FILENAME
    assert capture_path.exists(), "custom command did not record the page title"
    captured = capture_path.read_text(encoding="utf-8")

    # Sanity: the instrumented call must actually have thrown and been caught in
    # page code (otherwise the demonstration below would be vacuous).
    assert captured.startswith("STACK:"), (
        "expected the instrumented atob() call to throw and the page to capture "
        f"its stack; got title: {captured!r}"
    )
    stack = captured[len("STACK:") :]

    # DEMONSTRATION: dump the exact captured stack into the CI log. pytest.fail
    # guarantees the full message prints regardless of content (unlike a passing
    # assertion, which would hide it). This test is EXPECTED TO FAIL by design.
    has_mozext = "moz-extension://" in stack
    has_wrapper = ("instrumentFunction" in stack) or ("getInstrumentJS" in stack)
    pytest.fail(
        "DEMONSTRATION (do-not-merge): page-observable error.stack of a thrown "
        "instrumented atob() call.\n"
        f"  moz-extension:// frame present? {has_mozext}\n"
        f"  legacy instrument wrapper frame present? {has_wrapper}\n"
        "--- full captured stack ---\n" + stack
    )
