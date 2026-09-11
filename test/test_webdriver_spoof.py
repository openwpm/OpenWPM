"""Tests for `BrowserParams.spoof_webdriver`.

The point of the spoof is that the *page* cannot tell it happened, so every
assertion here compares a spoofed run against a `spoof_webdriver=False`
baseline: the value flips, and nothing else about the property does.
"""

import json
from pathlib import Path

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParamsInternal, ManagerParamsInternal
from openwpm.socket_interface import ClientSocket

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls

PROBE_FILE = "webdriver_probe.json"


class DumpWebdriverProbeCommand(BaseCommand):
    """Copy the probe the test page wrote into the DOM out to a file.

    The page has to run the probe itself: `execute_script` sees the page through
    Xray vision, where `navigator.webdriver` is still the untouched native
    getter and the page's own expandos are invisible.
    """

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParamsInternal,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        # Some probes are deliberately asynchronous (a frame's load event, a
        # macrotask), so wait for the page to say it is finished rather than
        # guessing how long that takes.
        WebDriverWait(webdriver, 30).until(
            lambda d: d.find_element(By.TAG_NAME, "html").get_attribute(
                "data-probe-complete"
            )
        )
        probe = webdriver.find_element(By.ID, "probe").get_attribute("textContent")
        assert probe is not None
        (manager_params.data_directory / PROBE_FILE).write_text(probe)


def _probe(
    task_manager_creator: TaskManagerCreator,
    params: FullConfig,
    server: ServerUrls,
    data_directory: Path,
    spoof_webdriver: bool,
    page: str = "/webdriver_spoof.html",
) -> dict:
    """Visit a probe page in a single browser and return what the page saw."""
    manager_params, browser_params = params
    data_directory.mkdir(parents=True, exist_ok=True)
    manager_params.data_directory = data_directory
    manager_params.log_path = data_directory / "openwpm.log"
    manager_params.num_browsers = 1
    browser_params = browser_params[:1]
    browser_params[0].spoof_webdriver = spoof_webdriver

    manager, _ = task_manager_creator((manager_params, browser_params))
    sequence = CommandSequence(server.base + page)
    sequence.get()
    sequence.append_command(DumpWebdriverProbeCommand())
    manager.execute_command_sequence(sequence)
    manager.close()
    return json.loads((data_directory / PROBE_FILE).read_text())


def test_spoof_webdriver_is_invisible_to_the_page(
    task_manager_creator: TaskManagerCreator,
    default_params: FullConfig,
    server: ServerUrls,
    tmp_path: Path,
) -> None:
    baseline = _probe(
        task_manager_creator,
        default_params,
        server,
        tmp_path / "baseline",
        spoof_webdriver=False,
    )
    spoofed = _probe(
        task_manager_creator,
        default_params,
        server,
        tmp_path / "spoofed",
        spoof_webdriver=True,
    )

    # Selenium's tell, and the one thing the spoof is allowed to change.
    assert baseline["value"] is True
    assert baseline["staticFrameValue"] is True
    assert spoofed["value"] is False
    assert spoofed["staticFrameValue"] is False

    # Everything else about the property is indistinguishable from native: the
    # accessor still stringifies as native code under its native name, carries
    # no setter, keeps its descriptor flags, and stays in place in the
    # prototype's property order. The `navigator` instance gains no own
    # property, which is what rules out the `Object.defineProperty(navigator,
    # ...)` approach (see https://github.com/openwpm/OpenWPM/pull/526).
    assert baseline["getterName"] == "get webdriver"
    assert "[native code]" in baseline["getterSource"]
    assert baseline["ownOnInstance"] is False
    assert baseline["hasSetter"] is False

    for key in (
        "getterName",
        "getterSource",
        "ownOnInstance",
        "hasSetter",
        "enumerable",
        "configurable",
        "prototypeKeys",
        # A replaced accessor diverges from native on both of these, so they
        # are the probes that would catch a regression back to patching the
        # page rather than the automation flag.
        "getterOnWrongReceiver",
        "getterOwnKeys",
    ):
        assert spoofed[key] == baseline[key], key


# Realms the page can reach other than the top-level document. Every one is
# spoofed, including the two that #526 and the stealth instrument's D10 notes
# describe as escapes: on Firefox 155 a pop-up opened with `window.open("")` and
# a frame appended and read in the same task are both covered.
REACHED_REALMS = [
    "syncAppendedIframe",
    "syncAppendedIframeAboutBlank",
    "indexedFrameAccess",
    "popupEmpty",
    "popupAboutBlank",
    "frameNavigatorPrototypeGetter",
    "srcdocOnLoad",
    "srcdocAfterTimeout",
]


def test_spoof_webdriver_reaches_other_realms(
    task_manager_creator: TaskManagerCreator,
    default_params: FullConfig,
    server: ServerUrls,
    tmp_path: Path,
) -> None:
    """Every realm the page can reach is patched, including ones no content
    script can cover.

    The hard case is a srcdoc frame read in the same task as the appendChild
    that created it. That read does not reach the srcdoc document; it reaches
    the frame's uncommitted initial about:blank, which Firefox deliberately
    never injects content scripts into (bug 1415539). It is observable from the
    parent regardless, which is why the spoof is installed from a privileged
    actor observing content-document-global-created rather than from a content
    script.
    """
    page = "/webdriver_spoof_escapes.html"
    baseline = _probe(
        task_manager_creator,
        default_params,
        server,
        tmp_path / "escapes-baseline",
        spoof_webdriver=False,
        page=page,
    )
    spoofed = _probe(
        task_manager_creator,
        default_params,
        server,
        tmp_path / "escapes-spoofed",
        spoof_webdriver=True,
        page=page,
    )

    # Every probe must actually have reached a realm, or it proves nothing.
    for key in REACHED_REALMS + ["srcdocSyncAfterAppend"]:
        assert baseline[key] is True, (key, baseline[key])

    for key in REACHED_REALMS:
        assert spoofed[key] is False, (key, spoofed[key])

    # The case no content script can reach: this read lands on the frame's
    # uncommitted initial about:blank (bug 1415539), not on the srcdoc
    # document. The actor covers it because it observes every window global.
    assert spoofed["srcdocSyncAfterAppend"] is False
