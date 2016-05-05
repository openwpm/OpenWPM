import pytest
import time
import os
import utilities
from ..automation import CommandSequence
from ..automation import TaskManager

url_a = utilities.BASE_TEST_URL + '/simple_a.html'
url_b = utilities.BASE_TEST_URL + '/simple_b.html'
url_c = utilities.BASE_TEST_URL + '/simple_c.html'

class TestSimpleCommands():
    """Test correctness of simple commands and check
    that resulting data is properly keyed.
    """
    NUM_BROWSERS = 1

    def get_config(self, data_dir):
        manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        manager_params['db'] = os.path.join(manager_params['data_directory'],
                                            manager_params['database_name'])
        browser_params[0]['headless'] = True
        return manager_params, browser_params

    def test_get_site_visits_table_valid(self, tmpdir):
        """Check that get works and populates db correctly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential get commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a)
        cs_a.get(sleep=1)
        cs_b = CommandSequence.CommandSequence(url_b)
        cs_b.get(sleep=1)

        # Perform the get commands
        manager.execute_command_sequence(cs_a)
        manager.execute_command_sequence(cs_b)
        manager.close(post_process=False)

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT site_url FROM site_visits")

        # We had two separate page visits
        assert len(qry_res) == 2

        assert qry_res[0][0] == url_a
        assert qry_res[1][0] == url_b

    def test_get_http_tables_valid(self, tmpdir):
        """Check that get works and populates http tables correctly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential get commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a)
        cs_a.get(sleep=1)
        cs_b = CommandSequence.CommandSequence(url_b)
        cs_b.get(sleep=1)

        manager.execute_command_sequence(cs_a)
        manager.execute_command_sequence(cs_b)
        manager.close(post_process=False)

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id, site_url FROM site_visits")

        # Construct dict mapping site_url to visit_id
        visit_ids = dict()
        for row in qry_res:
            visit_ids[row[1]] = row[0]

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_requests"
                                     " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_requests"
                                     " WHERE url = ?", (url_b,))
        assert qry_res[0][0] == visit_ids[url_b]

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_responses"
                                     " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_responses"
                                     " WHERE url = ?", (url_b,))
        assert qry_res[0][0] == visit_ids[url_b]

    def test_browse_site_visits_table_valid(self, tmpdir):
        """Check that 'browse' works and populates db correctly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential browse commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a)
        cs_a.browse(num_links=1, sleep=1)
        cs_b = CommandSequence.CommandSequence(url_b)
        cs_b.browse(num_links=1, sleep=1)

        manager.execute_command_sequence(cs_a)
        manager.execute_command_sequence(cs_b)
        manager.close(post_process=False)

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT site_url FROM site_visits")

        # We had two separate page visits
        assert len(qry_res) == 2

        assert qry_res[0][0] == url_a
        assert qry_res[1][0] == url_b

    def test_browse_http_table_valid(self, tmpdir):
        """Check that 'browse' works and populates http tables correctly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential browse commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a)
        cs_a.browse(num_links=1, sleep=1)
        cs_b = CommandSequence.CommandSequence(url_b)
        cs_b.browse(num_links=1, sleep=1)

        manager.execute_command_sequence(cs_a)
        manager.execute_command_sequence(cs_b)
        manager.close(post_process=False)

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id, site_url FROM site_visits")

        # Construct dict mapping site_url to visit_id
        visit_ids = dict()
        for row in qry_res:
            visit_ids[row[1]] = row[0]

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_requests"
                                     " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_requests"
                                     " WHERE url = ?", (url_b,))
        assert qry_res[0][0] == visit_ids[url_b]

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_responses"
                                     " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_responses"
                                     " WHERE url = ?", (url_b,))
        assert qry_res[0][0] == visit_ids[url_b]

        # Page simple_a.html has a link to simple_c.html. This request should
        # be keyed to the site visit for simple_a.html
        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_responses"
                                     " WHERE url = ?", (url_c,))
        assert len(qry_res) == 1
        assert qry_res[0][0] == visit_ids[url_a]

