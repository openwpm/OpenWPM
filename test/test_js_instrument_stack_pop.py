"""INVESTIGATION / DO-NOT-MERGE: can "popping the top frame off stack traces"
hide the legacy instrument's page-observable wrapper frame?

Companion to ``test_js_instrument_error_stack.py`` (#1212), which surfaced the
real leak: when an instrumented native throws, the page-observable ``error.stack``
shows the legacy wrapper (``getInstrumentJS/instrumentFunction/<``) as the TOP
frame. The user's hypothesis: have the page-world instrument "pop the top frame"
off any stack a page reads, hiding the wrapper.

This test empirically answers that with a self-contained page
(``instrument_stack_pop.html``) that models the wrapper frame, installs an
``Error.prototype.stack`` getter patch in two variants -- ``crude`` (drop the top
frame unconditionally) and ``targeted`` (drop only instrument-attributed frames)
-- and measures, for each, whether the wrapper is hidden and at what cost.

The empirical verdict (Firefox 152, also reproduced direct-selenium with the REAL
inlined ``getInstrumentJS`` under ``datadir/stack-pop/``):

* ``Error.prototype.stack`` is a native accessor; instances have no own ``stack``
  data property, so a patch must redefine that accessor.
* The #1207/#1212 throw cases (``atob``, ``getImageData``) raise a **DOMException**,
  whose ``.stack`` comes from ``DOMException.prototype`` -- a SEPARATE accessor. An
  ``Error.prototype.stack`` patch is therefore **inert** for exactly those cases.
* Where the patch applies (a real ``Error``), **crude over-pops** every legitimate
  page Error's top frame; targeted avoids that but...
* ...both leave the stack getter **non-native** (page-detectable, same toString
  wall as #57), and both are **defeated cross-realm**: a pristine ``Error.prototype``
  stack getter from a fresh ``<iframe>`` realm re-derives the unfiltered stack,
  wrapper and all.

Conclusion: popping the top frame is NOT a viable cheap win -- it is another
instance of the page-world cross-realm ceiling (#56/#57 family). This test asserts
that ceiling, then dumps the full measured evidence via ``pytest.fail`` so the
literal stacks appear in the CI log. EXPECTED TO FAIL by design (do-not-merge).
"""

import json
from pathlib import Path

import pytest
from selenium.webdriver import Firefox

from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket

TEST_PAGE = "/js_instrument/instrument_stack_pop.html"
CAPTURE_FILENAME = "captured_stack_pop.txt"


class CapturePopCommand(BaseCommand):
    """Reads the JSON measurement the test page stored in ``document.title``."""

    def __repr__(self) -> str:
        return "CapturePopCommand"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        out_path = manager_params.data_directory / CAPTURE_FILENAME
        out_path.write_text(webdriver.title, encoding="utf-8")


def test_pop_top_frame_is_a_ceiling(default_params, task_manager_creator, server):
    """DO-NOT-MERGE demonstration: popping the top frame cannot hide the wrapper
    without unacceptable cost (inert for DOMExceptions, over-pop, non-native
    detectability, cross-realm bypass)."""
    manager_params, browser_params = default_params
    tm, db = task_manager_creator((manager_params, browser_params))
    cs = CommandSequence(server.base + TEST_PAGE)
    cs.append_command(GetCommand(server.base + TEST_PAGE, 0))
    cs.append_command(CapturePopCommand())
    tm.execute_command_sequence(cs)
    tm.close()

    capture_path: Path = manager_params.data_directory / CAPTURE_FILENAME
    assert capture_path.exists(), "custom command did not record the page title"
    title = capture_path.read_text(encoding="utf-8")
    assert title.startswith("POP:"), f"page did not run; got title: {title!r}"
    r = json.loads(title[len("POP:") :])

    # Mechanism sanity: the patch target is a native accessor and DOMException has
    # its own, separate stack accessor.
    assert r["errProtoIsNativeAccessor"] is True
    assert r["domExceptionHasSeparateStack"] is True
    assert r["before"]["dom_type"] == "DOMException"

    crude, targeted = r["crude"], r["targeted"]

    # 1. Inert for the #1207/#1212 DOMException throws -- both variants.
    assert crude["dom_hidesWrapper"] is False
    assert targeted["dom_hidesWrapper"] is False

    # 2. Crude over-pops a legitimate page Error's top frame; targeted does not.
    assert crude["legit_overPops"] is True
    assert targeted["legit_overPops"] is False

    # 3. The patched getter is page-observably non-native for both.
    assert crude["patchDetectable_getterNonNative"] is True
    assert targeted["patchDetectable_getterNonNative"] is True

    # 4. Both are defeated cross-realm: a pristine iframe-realm getter reveals the
    #    wrapper that the main-realm patch hid.
    assert crude["crossRealm_revealsWrapper"] is True
    assert targeted["crossRealm_revealsWrapper"] is True

    pytest.fail(
        "DEMONSTRATION (do-not-merge): popping the top frame is a ceiling, not a "
        "cheap win.\n" + json.dumps(r, indent=2)
    )
