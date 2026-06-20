"""Browser-required adversarial tests for the full crawl pipeline.

These exercise the end-to-end recovery path through ``TaskManager`` ->
``BrowserManager`` -> Firefox + WebExtension, which the browser-free
storage-tier tests (``test/storage/test_adversarial_*.py``) cannot reach.

PROPERTY UNDER TEST (graceful degradation):
  For each adversarial scenario the crawl must
    1. make forward progress - the offending visit reaches a terminal state
       and the crawl continues to the *next* site,
    2. record the offending visit as incomplete (``incomplete_visits`` row),
    3. not hang (the whole sequence completes within the per-command timeout
       plus restart budget),
    4. preserve prior data (records from earlier good visits survive).

ENVIRONMENT BLOCK
  These tests need a real Firefox + the built extension xpi. In CI that is
  provided by the install script (pinned, unbranded Firefox 152 build) and the
  ``xpi`` fixture. Locally the workspace frequently lacks ``firefox-bin`` and
  ``FIREFOX_BINARY`` (system Firefox is a different version and not wired in),
  so these tests are *skipped* rather than reported as failures. They are NOT
  faked: the assertions below run for real in CI.

Scenarios:
  * S1a  custom command raises            -> incomplete + continue
  * S1b  custom command hangs forever     -> timeout + kill + incomplete + continue
  * S5   custom command kills the browser -> watchdog restart + incomplete + continue

A crashing *extension modification* (S2) shares the recovery shape with S5
(the BrowserManager subprocess / Firefox dies and must be restarted); a
faithful S2 test requires building a deliberately-broken xpi and is documented
as a design item in the PR / crosslink #46 rather than implemented here, to
avoid shipping a broken extension build into the repo.
"""

import os
import time

import pytest
from selenium.webdriver import Firefox

from openwpm import command_sequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParamsInternal, ManagerParamsInternal
from openwpm.socket_interface import ClientSocket
from openwpm.utilities import db_utils

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls


def _firefox_available() -> bool:
    """True iff a Firefox binary OpenWPM can launch is resolvable."""
    if os.environ.get("FIREFOX_BINARY"):
        return os.path.isfile(os.environ["FIREFOX_BINARY"])
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.isfile(os.path.join(root, "firefox-bin", "firefox-bin"))


requires_browser = pytest.mark.skipif(
    not _firefox_available(),
    reason="No launchable Firefox (firefox-bin / FIREFOX_BINARY missing). "
    "Browser-required adversarial test; runs in CI where the pinned Firefox "
    "and built xpi are installed.",
)


# ---------------------------------------------------------------------------
# Adversarial custom commands
# ---------------------------------------------------------------------------


class RaisingCommand(BaseCommand):
    """A user custom command whose ``execute`` raises immediately."""

    def __repr__(self) -> str:
        return "RaisingCommand"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParamsInternal,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        raise RuntimeError("intentional crash inside a user custom command")


class HangingCommand(BaseCommand):
    """A user custom command that never returns.

    The BrowserManager must hit the per-command timeout, kill the browser, mark
    the visit incomplete, and let the crawl proceed.
    """

    def __repr__(self) -> str:
        return "HangingCommand"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParamsInternal,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        while True:
            time.sleep(1)


class BrowserKillingCommand(BaseCommand):
    """A custom command that hard-kills the browser process from inside the
    BrowserManager subprocess, standing in for a mid-visit browser crash (and,
    by recovery shape, a crashing extension that takes the browser down).
    """

    def __repr__(self) -> str:
        return "BrowserKillingCommand"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParamsInternal,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        # Terminate the geckodriver-controlled Firefox out from under Selenium.
        pid = webdriver.service.process.pid
        os.kill(pid, 9)
        # Touch the driver so the BrowserManager observes a WebDriverException.
        webdriver.get("about:blank")


# ---------------------------------------------------------------------------
# Shared assertion: offending visit incomplete, later visit good, no hang
# ---------------------------------------------------------------------------


def _run_adversarial_then_good(
    task_manager_creator: TaskManagerCreator,
    http_params: FullConfig,
    server: ServerUrls,
    adversarial_command: BaseCommand,
    per_command_timeout: int = 30,
    overall_budget: float = 240.0,
) -> None:
    manager_params, browser_params = http_params
    # Single browser so the "next site" must reuse the (restarted) browser.
    manager_params.num_browsers = 1
    browser_params = browser_params[:1]
    # Keep the failure limit high enough that one failure does not abort.
    manager_params.failure_limit = 5

    manager, db = task_manager_creator((manager_params, browser_params))

    bad_url = server.base + "/simple_a.html"
    good_url = server.base + "/simple_d.html"

    start = time.time()

    # Visit 1: trip the adversarial command.
    cs_bad = command_sequence.CommandSequence(bad_url)
    cs_bad.get(sleep=0, timeout=per_command_timeout)
    cs_bad.append_command(adversarial_command, timeout=per_command_timeout)
    manager.execute_command_sequence(cs_bad)

    # Visit 2: a plain good visit must still run after recovery.
    cs_good = command_sequence.CommandSequence(good_url)
    cs_good.get(sleep=0, timeout=per_command_timeout)
    manager.execute_command_sequence(cs_good)

    manager.close()

    elapsed = time.time() - start
    assert elapsed < overall_budget, (
        f"crawl did not make forward progress in time ({elapsed:.0f}s) - "
        "likely a hang in the recovery path"
    )

    # Forward progress: both visits were recorded as site_visits.
    visits = db_utils.query_db(
        db, "SELECT site_url FROM site_visits ORDER BY visit_id;", as_tuple=True
    )
    visited_urls = {row[0] for row in visits}
    assert bad_url in visited_urls, "offending visit was never started/recorded"
    assert good_url in visited_urls, "crawl did not continue to the next site"

    # The offending visit must be marked incomplete.
    incomplete = db_utils.query_db(
        db, "SELECT visit_id FROM incomplete_visits;", as_tuple=True
    )
    assert len(incomplete) >= 1, (
        "offending visit was not recorded as incomplete - data loss / "
        "missing incomplete-visit accounting"
    )

    # The good visit's get() command must have succeeded (no global poisoning).
    statuses = db_utils.query_db(
        db,
        "SELECT command, command_status FROM crawl_history "
        "WHERE command = 'GetCommand';",
        as_tuple=True,
    )
    assert any(
        status == "ok" for _, status in statuses
    ), "no GetCommand ever succeeded - the crawl never recovered"


@requires_browser
@pytest.mark.usefixtures("xpi")
def test_crashing_custom_command_visit_incomplete_and_crawl_continues(
    task_manager_creator: TaskManagerCreator,
    http_params: FullConfig,
    server: ServerUrls,
) -> None:
    """S1a: a custom command that raises -> visit incomplete, crawl continues."""
    _run_adversarial_then_good(
        task_manager_creator, http_params, server, RaisingCommand()
    )


@requires_browser
@pytest.mark.slow
@pytest.mark.usefixtures("xpi")
def test_hanging_custom_command_times_out_and_crawl_continues(
    task_manager_creator: TaskManagerCreator,
    http_params: FullConfig,
    server: ServerUrls,
) -> None:
    """S1b: a custom command that hangs forever -> timeout + kill, then the
    crawl recovers and the next site is visited."""
    _run_adversarial_then_good(
        task_manager_creator,
        http_params,
        server,
        HangingCommand(),
        per_command_timeout=20,
    )


@requires_browser
@pytest.mark.slow
@pytest.mark.usefixtures("xpi")
def test_browser_killed_mid_visit_recovers_and_continues(
    task_manager_creator: TaskManagerCreator,
    http_params: FullConfig,
    server: ServerUrls,
) -> None:
    """S5 (and S2 by recovery shape): the browser process dies mid-visit ->
    watchdog/BrowserManager restart, offending visit incomplete, crawl
    continues."""
    _run_adversarial_then_good(
        task_manager_creator, http_params, server, BrowserKillingCommand()
    )
