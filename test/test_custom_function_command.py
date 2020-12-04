from typing import Any, Dict

from selenium.webdriver import Firefox

from openwpm import command_sequence, task_manager
from openwpm.commands.types import BaseCommand
from openwpm.config import (
    BrowserParams,
    BrowserParamsInternal,
    ManagerParams,
    ManagerParamsInternal,
)
from openwpm.socket_interface import ClientSocket
from openwpm.utilities import db_utils

from . import utilities
from .openwpmtest import OpenWPMTest

url_a = utilities.BASE_TEST_URL + "/simple_a.html"

PAGE_LINKS = {
    (
        u"http://localtest.me:8000/test_pages/simple_a.html",
        u"http://localtest.me:8000/test_pages/simple_c.html",
    ),
    (
        u"http://localtest.me:8000/test_pages/simple_a.html",
        u"http://localtest.me:8000/test_pages/simple_d.html",
    ),
    (
        u"http://localtest.me:8000/test_pages/simple_a.html",
        u"http://example.com/test.html?localtest.me",
    ),
}


class CollectLinksCommand(BaseCommand):
    """ Collect links with `scheme` and save in table `table_name` """

    def __init__(self, scheme, table_name) -> None:
        self.scheme = scheme
        self.table_name = table_name

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParamsInternal,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
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
        sock.connect(*manager_params.aggregator_address)

        query = (
            "CREATE TABLE IF NOT EXISTS %s ("
            "top_url TEXT, link TEXT, "
            "visit_id INTEGER, browser_id INTEGER);" % self.table_name
        )
        sock.send(("create_table", query))

        for link in link_urls:
            query = (
                self.table_name,
                {
                    "top_url": current_url,
                    "link": link,
                    "visit_id": self.visit_id,
                    "browser_id": self.browser_id,
                },
            )
            sock.send(query)
        sock.close()


class TestCustomFunctionCommand(OpenWPMTest):
    """Test `custom_function` command's ability to handle inline functions"""

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)

    def test_custom_function(self):
        """ Test `custom_function` with an inline func that collects links """

        manager_params, browser_params = self.get_config()
        manager = task_manager.TaskManager(manager_params, browser_params)
        cs = command_sequence.CommandSequence(url_a)
        cs.get(sleep=0, timeout=60)
        cs.append_command(CollectLinksCommand("http", "page_links"))
        manager.execute_command_sequence(cs)
        manager.close()
        query_result = db_utils.query_db(
            manager_params.database_name,
            "SELECT top_url, link FROM page_links;",
            as_tuple=True,
        )
        assert PAGE_LINKS == set(query_result)
