"""Guard that a page catching an error thrown through a legacy instrument
wrapper sees no ``moz-extension://`` frame on ``error.stack``.

The legacy instrument is injected as an inline page ``<script>``, so Firefox
attributes its frames to the page URL. The test fails if the instrument is
ever loaded from a ``moz-extension://`` URL instead.

The page-URL wrapper frame itself is still visible and is out of scope:
rewriting ``.stack`` on the caught error would leave an own data property
where native errors only have the prototype accessor, which is itself a tell.
"""

from pathlib import Path

from selenium.webdriver import Firefox

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket
from openwpm.utilities import db_utils

TEST_PAGE = "/js_instrument/instrument_error_stack.html"

# Commands run in the browser process, so the stack is handed back via a file.
CAPTURE_FILENAME = "captured_error_stack.txt"


class CaptureStackCommand(BaseCommand):
    """Saves the page title, where the test page stores the caught stack."""

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
    manager_params, browser_params = default_params
    for bp in browser_params:
        bp.js_instrument = True
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

    # Without these the assertion below would pass vacuously.
    calls = [
        row
        for row in db_utils.get_javascript_entries(db)
        if row["symbol"] == "window.atob" and row["operation"] == "call"
    ]
    assert len(calls) == 1, "atob was not called through the instrument wrapper"
    assert captured.startswith("STACK:"), (
        "expected the instrumented atob() call to throw and the page to capture "
        f"its stack; got title: {captured!r}"
    )
    stack = captured[len("STACK:") :]

    assert "moz-extension://" not in stack, (
        "page-observable error stack leaked an extension frame:\n" + stack
    )
