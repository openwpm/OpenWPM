import sqlite3

from openwpm import command_sequence, task_manager
from openwpm.socket_interface import ClientSocket
from openwpm.storage.sql_provider import SqlLiteStorageProvider
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils

from . import utilities

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


def test_custom_function(default_params, xpi, server):
    """ Test `custom_function` with an inline func that collects links """
    table_name = "page_links"

    def collect_links(table_name, scheme, **kwargs):
        """ Collect links with `scheme` and save in table `table_name` """
        driver = kwargs["driver"]
        manager_params = kwargs["manager_params"]
        browser_id = kwargs["command"].browser_id
        visit_id = kwargs["command"].visit_id
        link_urls = [
            x
            for x in (
                element.get_attribute("href")
                for element in driver.find_elements_by_tag_name("a")
            )
            if x.startswith(scheme + "://")
        ]
        current_url = driver.current_url

        sock = ClientSocket()
        sock.connect(*manager_params["aggregator_address"])

        for link in link_urls:
            query = (
                table_name,
                {
                    "top_url": current_url,
                    "link": link,
                    "visit_id": visit_id,
                    "browser_id": browser_id,
                },
            )
            sock.send(query)
        sock.close()

    manager_params, browser_params = default_params

    db = sqlite3.connect(manager_params["db"])
    cur = db.cursor()

    cur.execute(
        """CREATE TABLE IF NOT EXISTS %s (
            top_url TEXT, link TEXT, 
            visit_id INTEGER, browser_id INTEGER);"""
        % table_name
    )
    cur.close()
    db.close()

    storage_provider = SqlLiteStorageProvider(manager_params["db"])
    manager = TaskManager(manager_params, browser_params, storage_provider, None)
    cs = command_sequence.CommandSequence(url_a)
    cs.get(sleep=0, timeout=60)
    cs.run_custom_function(collect_links, (table_name, "http"))
    manager.execute_command_sequence(cs)
    manager.close()
    query_result = db_utils.query_db(
        manager_params["db"], "SELECT top_url, link FROM page_links;", as_tuple=True
    )
    assert PAGE_LINKS == set(query_result)
