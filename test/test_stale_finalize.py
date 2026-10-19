"""A Finalize still parked in the extension's grace wait must not clear the
visit_id of the visit that started in the meantime."""

import time

from selenium.webdriver import Firefox

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParamsInternal
from openwpm.socket_interface import ClientSocket
from openwpm.utilities import db_utils

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls

STALE_GRACE = 8


class StaleFinalizeCommand(BaseCommand):
    """Sends a second Finalize for this visit with a long grace, standing in
    for one the extension was too busy to finish in time."""

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        extension_socket.send(
            {
                "action": "Finalize",
                "visit_id": self.visit_id,
                "finalize_grace_seconds": STALE_GRACE,
            }
        )


class SleepCommand(BaseCommand):
    def __init__(self, seconds: float) -> None:
        self.seconds = seconds

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        time.sleep(self.seconds)


class FetchCommand(BaseCommand):
    """Issues a request without a GetCommand, which would re-send the
    visit_id to the extension."""

    def __init__(self, url: str) -> None:
        self.url = url

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        webdriver.execute_script(
            "return fetch(arguments[0]).then(r => r.text());", self.url
        )
        time.sleep(1)


def test_stale_finalize_keeps_next_visit_id(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    browser_params[0].http_instrument = True
    manager, db = task_manager_creator((manager_params, browser_params[:1]))
    first_url = server.base + "/simple_c.html"
    second_url = server.base + "/simple_a.html"
    late_url = server.base + "/simple_d.html"

    cs = CommandSequence(first_url, blocking=True)
    cs.append_command(StaleFinalizeCommand(), timeout=10)
    manager.execute_command_sequence(cs)

    cs = CommandSequence(second_url, blocking=True)
    cs.get(sleep=0, timeout=60)
    # Let the stale Finalize resume while this visit is active.
    cs.append_command(SleepCommand(STALE_GRACE), timeout=STALE_GRACE + 10)
    cs.append_command(FetchCommand(late_url), timeout=30)
    manager.execute_command_sequence(cs)
    manager.close()

    ((second_visit_id,),) = db_utils.query_db(
        db,
        "SELECT visit_id FROM site_visits WHERE site_url = ?",
        (second_url,),
        as_tuple=True,
    )
    visit_ids = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_requests WHERE url = ?",
        (late_url,),
        as_tuple=True,
    )
    assert visit_ids == [(second_visit_id,)]
