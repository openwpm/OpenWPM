import pytest # noqa

from PIL import Image
import filecmp
import os
import utilities
from ..automation import CommandSequence
from ..automation import TaskManager

url_a = utilities.BASE_TEST_URL + '/simple_a.html'
url_b = utilities.BASE_TEST_URL + '/simple_b.html'
url_c = utilities.BASE_TEST_URL + '/simple_c.html'
url_d = utilities.BASE_TEST_URL + '/simple_d.html'

rendered_js_url = utilities.BASE_TEST_URL + '/property_enumeration.html'

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
        """Check that 'browse' works and populates http tables correctly.

        NOTE: Since the browse command is choosing links randomly, there is a
              (very small -- 2*0.5^20) chance this test will fail with valid
              code.
        """
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential browse commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a)
        cs_a.browse(num_links=20, sleep=1)
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

        # Page simple_a.html has three links:
        # 1) An absolute link to simple_c.html
        # 2) A relative link to simple_d.html
        # 3) A javascript: link
        # 4) A link to www.google.com
        # 5) A link to example.com?localtest.me
        # We should see page visits for 1 and 2, but not 3-5.
        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_responses"
                                     " WHERE url = ?", (url_c,))
        assert qry_res[0][0] == visit_ids[url_a]
        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT visit_id FROM http_responses"
                                     " WHERE url = ?", (url_d,))
        assert qry_res[0][0] == visit_ids[url_a]

        # We expect 4 urls: a,c,d and a favicon request
        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT COUNT(DISTINCT url) FROM http_responses"
                                     " WHERE visit_id = ?", (visit_ids[url_a],))
        assert qry_res[0][0] == 4


    def test_save_screenshot_valid(self, tmpdir):
        """Check that 'save_screenshot' works and screenshot is created properly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        cs = CommandSequence.CommandSequence(url_a)
        cs.get(sleep=1)
        cs.save_screenshot('test_screenshot')
        manager.execute_command_sequence(cs)
        manager.close(post_process=False)


        # Check that image is not blank
        im = Image.open(os.path.join(str(tmpdir), 'screenshots', 'test_screenshot.png'))
        bands = im.split()

        isBlank = all(band.getextrema() == (255, 255) for band in bands)

        assert not isBlank


    def test_dump_page_source_valid(self, tmpdir):
        """Check that 'dump_page_source' works and source is saved properly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        cs = CommandSequence.CommandSequence(url_a)
        cs.get(sleep=1)
        cs.dump_page_source('test_source')
        manager.execute_command_sequence(cs)
        manager.close(post_process=False)

        with open(os.path.join(str(tmpdir), 'sources', 'test_source.html'), 'rb') as f:
            actual_source = f.read()
        with open('./test_pages/expected_source.html', 'rb') as f:
            expected_source = f.read()

        assert actual_source == expected_source
