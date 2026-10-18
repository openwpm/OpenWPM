"""Tests for `BrowserParams.spoof_webdriver`.

The point of the spoof is that the *page* cannot tell it happened, so the
invisibility tests compare a spoofed run against a `spoof_webdriver=False`
baseline: the value flips, and nothing else about the property does.
"""

import json
from pathlib import Path
from typing import Optional

import pytest
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from openwpm import task_manager
from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParamsInternal, ManagerParamsInternal
from openwpm.errors import BrowserConfigError
from openwpm.socket_interface import ClientSocket
from openwpm.utilities import db_utils

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
    js_instrument_settings: Optional[list] = None,
) -> dict:
    """Visit a probe page in a single browser and return what the page saw."""
    manager_params, browser_params = params
    data_directory.mkdir(parents=True, exist_ok=True)
    manager_params.data_directory = data_directory
    manager_params.log_path = data_directory / "openwpm.log"
    manager_params.num_browsers = 1
    browser_params = browser_params[:1]
    browser_params[0].spoof_webdriver = spoof_webdriver
    if js_instrument_settings is not None:
        browser_params[0].js_instrument = True
        browser_params[0].js_instrument_settings = js_instrument_settings

    manager, _ = task_manager_creator((manager_params, browser_params))
    try:
        sequence = CommandSequence(server.base + page)
        sequence.get()
        sequence.append_command(DumpWebdriverProbeCommand())
        manager.execute_command_sequence(sequence)
    finally:
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

    # Everything else about the property matches native, timing aside (see
    # docs/Configuration.md): the accessor still stringifies as native code
    # under its native name, carries no setter, is not a constructor, keeps its
    # descriptor flags, and stays in place in the prototype's property order,
    # and reading it never reaches the page's builtins. The `navigator`
    # instance gains no own property, which is what rules out the
    # `Object.defineProperty(navigator, ...)` approach (see
    # https://github.com/openwpm/OpenWPM/pull/526).
    assert baseline["getterName"] == "get webdriver"
    assert "[native code]" in baseline["getterSource"]
    assert baseline["ownOnInstance"] is False
    assert baseline["hasSetter"] is False
    assert baseline["getterConstructed"].startswith("TypeError: ")
    assert baseline["ownReadWithHookedBuiltins"] == "value:true,hits:0"
    assert spoofed["ownReadWithHookedBuiltins"] == "value:false,hits:0"
    # Another realm's navigator, and a non-navigator, skip the forwarder's
    # own-navigator shortcut and reach the native getter.
    assert baseline["crossRealmWithHookedBuiltins"] == "value:true,hits:0"
    assert spoofed["crossRealmWithHookedBuiltins"] == "value:false,hits:0"
    assert baseline["wrongReceiverWithHookedBuiltins"].startswith("threw:TypeError: ")
    assert baseline["wrongReceiverWithHookedBuiltins"].endswith(",hits:0")
    # Writes to a getter-only accessor: ignored in sloppy mode, a TypeError in
    # strict mode, and never an own property on the instance.
    assert baseline["sloppyAssign"] is True
    assert spoofed["sloppyAssign"] is False
    assert baseline["strictAssign"].startswith("TypeError: ")
    assert baseline["ownDescriptorAfterAssign"] == "undefined"
    assert spoofed["fpscannerWebdriverWritable"] is False

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
        "getterConstructed",
        "wrongReceiverWithHookedBuiltins",
        "strictAssign",
        "ownDescriptorAfterAssign",
    ):
        assert spoofed[key] == baseline[key], key


def test_spoof_webdriver_survives_js_instrument(
    task_manager_creator: TaskManagerCreator,
    default_params: FullConfig,
    server: ServerUrls,
    tmp_path: Path,
) -> None:
    """With the legacy instrument on, the page still reads `false` everywhere
    and the reads are recorded.

    The instrument's own-property tell (fpscanner `webdriverWritable`) is a
    known cost of the legacy instrument, so it is not asserted on here.
    """
    data_directory = tmp_path / "instrumented"
    probe = _probe(
        task_manager_creator,
        default_params,
        server,
        data_directory,
        spoof_webdriver=True,
        js_instrument_settings=["collection_fingerprinting"],
    )
    assert probe["value"] is False
    assert probe["staticFrameValue"] is False

    escapes_directory = tmp_path / "instrumented-escapes"
    escapes = _probe(
        task_manager_creator,
        default_params,
        server,
        escapes_directory,
        spoof_webdriver=True,
        page="/webdriver_spoof_escapes.html",
        js_instrument_settings=["collection_fingerprinting"],
    )
    for key in REACHED_REALMS + ["srcdocSyncAfterAppend"]:
        assert escapes[key] is False, (key, escapes[key])

    for directory in (data_directory, escapes_directory):
        reads = {
            row[0]
            for row in db_utils.query_db(
                directory / "crawl-data.sqlite",
                "SELECT value FROM javascript WHERE symbol = ? AND operation = ?",
                ("window.navigator.webdriver", "get"),
            )
        }
        assert reads == {"false"}, (directory.name, reads)


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


def test_spoof_webdriver_failure_fails_startup(
    task_manager_creator: TaskManagerCreator,
    default_params: FullConfig,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A spoof that cannot be enabled aborts the launch rather than crawling
    unspoofed.

    Config validation already refuses the one known trigger, so bypass it: the
    pref could equally arrive from a seed profile, which validation never sees.
    """
    manager_params, browser_params = default_params
    manager_params.data_directory = tmp_path
    manager_params.log_path = tmp_path / "openwpm.log"
    manager_params.num_browsers = 1
    browser_params = browser_params[:1]
    browser_params[0].spoof_webdriver = True
    browser_params[0].prefs = {"dom.ipc.processPrelaunch.enabled": False}
    monkeypatch.setattr(task_manager, "validate_crawl_configs", lambda *_: None)

    try:
        manager, _ = task_manager_creator((manager_params, browser_params))
    except BrowserConfigError as e:
        assert "did not boot up" in str(e)
    else:
        manager.close()
        pytest.fail("browser started without the spoof")
    assert "webdriverSpoof requires dom.ipc.processPrelaunch.enabled" in (
        manager_params.log_path.read_text()
    )
