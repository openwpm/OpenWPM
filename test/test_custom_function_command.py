import sqlite3

from selenium.webdriver import Firefox

from openwpm import command_sequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParamsInternal
from openwpm.socket_interface import ClientSocket
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_providers import TableName
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils

from . import utilities

url_a = utilities.BASE_TEST_URL + "/simple_a.html"

PAGE_LINKS = {
    (
        f"{utilities.BASE_TEST_URL}/simple_a.html",
        f"{utilities.BASE_TEST_URL}/simple_c.html",
    ),
    (
        f"{utilities.BASE_TEST_URL}/simple_a.html",
        f"{utilities.BASE_TEST_URL}/simple_d.html",
    ),
    (
        f"{utilities.BASE_TEST_URL}/simple_a.html",
        "http://example.com/test.html?localhost",
    ),
}


class CollectLinksCommand(BaseCommand):
    """Collect links with `scheme` and save in table `table_name`"""

    def __init__(self, table_name: TableName, scheme: str) -> None:
        self.scheme = scheme
        self.table_name = table_name

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        browser_id = self.browser_id
        visit_id = self.visit_id
        link_urls = [
            x
            for x in (
                element.get_attribute("href")
                for element in webdriver.find_elements_by_tag_name("a")
            )
            if x.startswith(self.scheme + "://")
        ]
        current_url = webdriver.current_url

        sock = ClientSocket()
        assert manager_params.storage_controller_address is not None
        sock.connect(*manager_params.storage_controller_address)

        for link in link_urls:
            query = (
                self.table_name,
                {
                    "top_url": current_url,
                    "link": link,
                    "visit_id": visit_id,
                    "browser_id": browser_id,
                },
            )
            sock.send(query)
        sock.close()


def test_custom_function(default_params, xpi, server):
    """Test `custom_function` with an inline func that collects links"""
    table_name = TableName("page_links")

    manager_params, browser_params = default_params
    path = manager_params.data_directory / "crawl-data.sqlite"
    db = sqlite3.connect(path)
    cur = db.cursor()

    cur.execute(
        """CREATE TABLE IF NOT EXISTS %s (
            top_url TEXT, link TEXT,
            visit_id INTEGER, browser_id INTEGER);"""
        % table_name
    )
    cur.close()
    db.close()

    storage_provider = SQLiteStorageProvider(path)
    manager = TaskManager(manager_params, browser_params, storage_provider, None)
    cs = command_sequence.CommandSequence(url_a)
    cs.get(sleep=0, timeout=60)
    cs.append_command(CollectLinksCommand(table_name, "http"))
    manager.execute_command_sequence(cs)
    manager.close()
    query_result = db_utils.query_db(
        path,
        "SELECT top_url, link FROM page_links;",
        as_tuple=True,
    )
    assert PAGE_LINKS == set(query_result)
