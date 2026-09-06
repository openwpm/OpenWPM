"""Invariant guard for crosslink #53 / review item R16.

The legacy JS instrument is injected as an inline ``<script>`` element (see
``Extension/src/content/javascript-instrument-content-scope.ts``), so Firefox
attributes ALL of its frames -- including the wrapper closures -- to the page
document URL, never to ``moz-extension://``. Consequently a page that catches
an error thrown by an instrumented API sees only page-URL frames on
``error.stack``; no ``moz-extension://`` frame appears on this path.

This test asserts that end-to-end invariant. It is NOT a reproduction of a
fixed leak: with the current page-world injection the assertion holds by
construction -- there is nothing in ``js-instruments.ts`` that strips frames,
because none reach page code to strip. It DOES fail -- and earns its keep -- if
the injection model ever regresses to an extension-world script (or a
``//# sourceURL=moz-extension://...`` directive) that leaks extension frames.
Should that happen, this test flags it so the leak can be addressed.

Note: the genuine, inherent legacy tell -- the page-URL wrapper frame itself --
is not covered here and cannot be stripped without breaking script attribution.
"""

from pathlib import Path

from selenium.webdriver import Firefox

from openwpm.command_sequence import CommandSequence
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


def test_instrumented_error_stack_has_no_extension_frames(
    default_params, task_manager_creator, server
):
    """The page-observable stack of a thrown instrumented-API error must carry
    no moz-extension:// frame (holds by construction on the page-world injection
    path; guarded here against a regression of that injection model)."""
    manager_params, browser_params = default_params
    for bp in browser_params:
        bp.js_instrument = True
        # Instrument an API that we can make throw deterministically from page
        # code. atob() raises an InvalidCharacterError (a DOMException) when
        # given input outside the base64 alphabet.
        bp.js_instrument_settings = [{"window": ["atob"]}]

    tm, db = task_manager_creator((manager_params, browser_params))
    cs = CommandSequence(server.base + TEST_PAGE)
    cs.get(sleep=0)
    cs.append_command(CaptureStackCommand())
    tm.execute_command_sequence(cs)
    tm.close()

    capture_path: Path = manager_params.data_directory / CAPTURE_FILENAME
    assert capture_path.exists(), "custom command did not record the page title"
    captured = capture_path.read_text(encoding="utf-8")

    # Sanity: the instrumented call must actually have thrown and been caught in
    # page code (otherwise the assertion below would pass vacuously).
    assert captured.startswith("STACK:"), (
        "expected the instrumented atob() call to throw and the page to capture "
        f"its stack; got title: {captured!r}"
    )
    stack = captured[len("STACK:") :]

    # The core assertion: no extension frame must survive on the page-observable
    # stack. On the current inline page-world injection path this holds by
    # construction (all frames are page-URL attributed); it would fail if a
    # future change let extension frames reach page code without stripping them.
    assert "moz-extension://" not in stack, (
        "page-observable error stack leaked an extension frame:\n" + stack
    )
