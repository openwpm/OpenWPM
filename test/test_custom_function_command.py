import pytest # noqa
import os

import expected
import utilities
from ..automation import CommandSequence
from ..automation import TaskManager

url_a = utilities.BASE_TEST_URL + '/simple_a.html'

class TestCustomFunctionCommand():
    """Test `custom_function` command's ability to handle various inline functions"""
    NUM_BROWSERS = 1

    def get_config(self, data_dir):
        manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        manager_params['db'] = os.path.join(manager_params['data_directory'],
                                            manager_params['database_name'])
        browser_params[0]['headless'] = True
        return manager_params, browser_params

    def test_custom_function(self, tmpdir):
        """ Test `custom_function` with an inline function that collects links """

        from ..automation.SocketInterface import clientsocket
        def collect_links(table_name, scheme, **kwargs):
            """ Collect links with matching `scheme` and save in table `table_name` """
            driver = kwargs['driver']
            manager_params = kwargs['manager_params']
            link_elements = driver.find_elements_by_tag_name('a')
            link_urls = [element.get_attribute("href") for element in link_elements]
            link_urls = filter(lambda x: x.startswith(scheme+'://'), link_urls)
            current_url = driver.current_url

            sock = clientsocket()
            sock.connect(*manager_params['aggregator_address'])

            query = ("CREATE TABLE IF NOT EXISTS %s ("
                    "top_url TEXT, link TEXT);" % table_name)
            sock.send((query, ()))

            for link in link_urls:
                query = ("INSERT INTO %s (top_url, link) "
                         "VALUES (?, ?)" % table_name)
                sock.send((query, (current_url, link)))
            sock.close()

        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        cs = CommandSequence.CommandSequence(url_a)
        cs.get(sleep=0, timeout=60)
        cs.run_custom_function(collect_links, ('page_links', 'http'))
        manager.execute_command_sequence(cs)
        manager.close()
        query_result = utilities.query_db(manager_params['db'],
                                     "SELECT top_url, link FROM page_links;")
        assert expected.page_links == set(query_result)
