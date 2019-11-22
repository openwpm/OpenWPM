
import glob
import gzip
import json
import os
import re
from urllib.parse import urlparse

from PIL import Image

from ..automation import CommandSequence, TaskManager
from ..automation.utilities import db_utils
from . import utilities
from .openwpmtest import OpenWPMTest

url_a = utilities.BASE_TEST_URL + '/simple_a.html'
url_b = utilities.BASE_TEST_URL + '/simple_b.html'
url_c = utilities.BASE_TEST_URL + '/simple_c.html'
url_d = utilities.BASE_TEST_URL + '/simple_d.html'

rendered_js_url = utilities.BASE_TEST_URL + '/property_enumeration.html'

# Expected nested page source
NESTED_TEST_DIR = '/recursive_iframes/'
NESTED_FRAMES_URL = utilities.BASE_TEST_URL + NESTED_TEST_DIR + 'parent.html'
D1_BASE = 'http://d1.' + utilities.BASE_TEST_URL_NOSCHEME + NESTED_TEST_DIR
D2_BASE = 'http://d2.' + utilities.BASE_TEST_URL_NOSCHEME + NESTED_TEST_DIR
D3_BASE = 'http://d3.' + utilities.BASE_TEST_URL_NOSCHEME + NESTED_TEST_DIR
D4_BASE = 'http://d4.' + utilities.BASE_TEST_URL_NOSCHEME + NESTED_TEST_DIR
D5_BASE = 'http://d5.' + utilities.BASE_TEST_URL_NOSCHEME + NESTED_TEST_DIR
EXPECTED_PARENTS = {
    NESTED_FRAMES_URL: [],
    D1_BASE + 'child1a.html': [NESTED_FRAMES_URL],
    D1_BASE + 'child1b.html': [NESTED_FRAMES_URL],
    D1_BASE + 'child1c.html': [NESTED_FRAMES_URL],
    D2_BASE + 'child2a.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1a.html'],
    D2_BASE + 'child2b.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1a.html'],
    D2_BASE + 'child2c.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1c.html'],
    D3_BASE + 'child3a.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1a.html',
                               D2_BASE + 'child2a.html'],
    D3_BASE + 'child3b.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1c.html',
                               D2_BASE + 'child2c.html'],
    D3_BASE + 'child3c.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1c.html',
                               D2_BASE + 'child2c.html'],
    D3_BASE + 'child3d.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1c.html',
                               D2_BASE + 'child2c.html'],
    D4_BASE + 'child4a.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1a.html',
                               D2_BASE + 'child2a.html',
                               D3_BASE + 'child3a.html'],
    D5_BASE + 'child5a.html': [NESTED_FRAMES_URL,
                               D1_BASE + 'child1a.html',
                               D2_BASE + 'child2a.html',
                               D3_BASE + 'child3a.html',
                               D4_BASE + 'child4a.html']
}


class TestSimpleCommands(OpenWPMTest):
    """Test correctness of simple commands and check
    that resulting data is properly keyed.
    """

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0]['http_instrument'] = True
        return manager_params, browser_params

    def test_get_site_visits_table_valid(self):
        """Check that get works and populates db correctly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential get commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a)
        cs_a.get(sleep=1)
        cs_b = CommandSequence.CommandSequence(url_b)
        cs_b.get(sleep=1)

        # Perform the get commands
        manager.execute_command_sequence(cs_a)
        manager.execute_command_sequence(cs_b)
        manager.close()

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT site_url FROM site_visits")

        # We had two separate page visits
        assert len(qry_res) == 2

        assert qry_res[0][0] == url_a
        assert qry_res[1][0] == url_b

    def test_get_http_tables_valid(self):
        """Check that get works and populates http tables correctly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential get commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a)
        cs_a.get(sleep=1)
        cs_b = CommandSequence.CommandSequence(url_b)
        cs_b.get(sleep=1)

        manager.execute_command_sequence(cs_a)
        manager.execute_command_sequence(cs_b)
        manager.close()

        qry_res = db_utils.query_db(
            manager_params['db'],
            "SELECT visit_id, site_url FROM site_visits")

        # Construct dict mapping site_url to visit_id
        visit_ids = dict()
        for row in qry_res:
            visit_ids[row[1]] = row[0]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_requests"
                                    " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_requests"
                                    " WHERE url = ?", (url_b,))
        assert qry_res[0][0] == visit_ids[url_b]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_responses"
                                    " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_responses"
                                    " WHERE url = ?", (url_b,))
        assert qry_res[0][0] == visit_ids[url_b]

    def test_browse_site_visits_table_valid(self):
        """Check that CommandSequence.browse() populates db correctly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential browse commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a, site_rank=0)
        cs_a.browse(num_links=1, sleep=1)
        cs_b = CommandSequence.CommandSequence(url_b, site_rank=1)
        cs_b.browse(num_links=1, sleep=1)

        manager.execute_command_sequence(cs_a)
        manager.execute_command_sequence(cs_b)
        manager.close()

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT site_url, site_rank"
                                    " FROM site_visits")

        # We had two separate page visits
        assert len(qry_res) == 2

        assert qry_res[0][0] == url_a
        assert qry_res[0][1] == 0
        assert qry_res[1][0] == url_b
        assert qry_res[1][1] == 1

    def test_browse_http_table_valid(self):
        """Check CommandSequence.browse() works and populates http tables correctly.

        NOTE: Since the browse command is choosing links randomly, there is a
              (very small -- 2*0.5^20) chance this test will fail with valid
              code.
        """
        # Run the test crawl
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential browse commands to two URLS
        cs_a = CommandSequence.CommandSequence(url_a)
        cs_a.browse(num_links=20, sleep=1)
        cs_b = CommandSequence.CommandSequence(url_b)
        cs_b.browse(num_links=1, sleep=1)

        manager.execute_command_sequence(cs_a)
        manager.execute_command_sequence(cs_b)
        manager.close()

        qry_res = db_utils.query_db(
            manager_params['db'],
            "SELECT visit_id, site_url FROM site_visits")

        # Construct dict mapping site_url to visit_id
        visit_ids = dict()
        for row in qry_res:
            visit_ids[row[1]] = row[0]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_requests"
                                    " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_requests"
                                    " WHERE url = ?", (url_b,))
        assert qry_res[0][0] == visit_ids[url_b]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_responses"
                                    " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = db_utils.query_db(manager_params['db'],
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
        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_responses"
                                    " WHERE url = ?", (url_c,))
        assert qry_res[0][0] == visit_ids[url_a]
        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_responses"
                                    " WHERE url = ?", (url_d,))
        assert qry_res[0][0] == visit_ids[url_a]

        # We expect 4 urls: a,c,d and a favicon request
        qry_res = db_utils.query_db(
            manager_params['db'],
            "SELECT COUNT(DISTINCT url) FROM http_responses"
            " WHERE visit_id = ?", (visit_ids[url_a],)
        )
        assert qry_res[0][0] == 4

    def test_browse_wrapper_http_table_valid(self):
        """Check that TaskManager.browse() wrapper works and populates
        http tables correctly.

        NOTE: Since the browse command is choosing links randomly, there is a
              (very small -- 2*0.5^20) chance this test will fail with valid
              code.
        """
        # Run the test crawl
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential browse commands to two URLS
        manager.browse(url_a, num_links=20, sleep=1)
        manager.browse(url_b, num_links=1, sleep=1)
        manager.close()

        qry_res = db_utils.query_db(
            manager_params['db'],
            "SELECT visit_id, site_url FROM site_visits"
        )

        # Construct dict mapping site_url to visit_id
        visit_ids = dict()
        for row in qry_res:
            visit_ids[row[1]] = row[0]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_requests"
                                    " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_requests"
                                    " WHERE url = ?", (url_b,))
        assert qry_res[0][0] == visit_ids[url_b]

        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_responses"
                                    " WHERE url = ?", (url_a,))
        assert qry_res[0][0] == visit_ids[url_a]

        qry_res = db_utils.query_db(manager_params['db'],
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
        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_responses"
                                    " WHERE url = ?", (url_c,))
        assert qry_res[0][0] == visit_ids[url_a]
        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT visit_id FROM http_responses"
                                    " WHERE url = ?", (url_d,))
        assert qry_res[0][0] == visit_ids[url_a]

        # We expect 4 urls: a,c,d and a favicon request
        qry_res = db_utils.query_db(
            manager_params['db'],
            "SELECT COUNT(DISTINCT url) FROM http_responses"
            " WHERE visit_id = ?", (visit_ids[url_a],))
        assert qry_res[0][0] == 4

    def test_save_screenshot_valid(self, tmpdir):
        """Check that 'save_screenshot' works"""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        cs = CommandSequence.CommandSequence(url_a)
        cs.get(sleep=1)
        cs.save_screenshot('test')
        cs.screenshot_full_page('test_full')
        manager.execute_command_sequence(cs)
        manager.close()

        # Check that viewport image is not blank
        pattern = os.path.join(str(tmpdir), 'screenshots', '1-*-test.png')
        screenshot = glob.glob(pattern)[0]
        im = Image.open(screenshot)
        bands = im.split()
        is_blank = all(band.getextrema() == (255, 255) for band in bands)
        assert not is_blank

        # Check that full page screenshot is not blank
        pattern = os.path.join(str(tmpdir), 'screenshots', '1-*-test_full.png')
        screenshot = glob.glob(pattern)[0]
        im = Image.open(screenshot)
        bands = im.split()
        is_blank = all(band.getextrema() == (255, 255) for band in bands)
        assert not is_blank

    def test_dump_page_source_valid(self, tmpdir):
        """Check that 'dump_page_source' works and source is saved properly."""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        cs = CommandSequence.CommandSequence(url_a)
        cs.get(sleep=1)
        cs.dump_page_source(suffix='test')
        manager.execute_command_sequence(cs)
        manager.close()

        # Source filename is of the follow structure:
        # `sources/<visit_id>-<md5_of_url>(-suffix).html`
        # thus for this test we expect `sources/1-<md5_of_test_url>-test.html`.
        outfile = os.path.join(str(tmpdir), 'sources', '1-*-test.html')
        source_file = glob.glob(outfile)[0]
        with open(source_file, 'rb') as f:
            actual_source = f.read()
        with open('./test_pages/expected_source.html', 'rb') as f:
            expected_source = f.read()

        assert actual_source == expected_source

    def test_recursive_dump_page_source_valid(self, tmpdir):
        """Check that 'recursive_dump_page_source' works"""
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        cs = CommandSequence.CommandSequence(NESTED_FRAMES_URL)
        cs.get(sleep=1)
        cs.recursive_dump_page_source()
        manager.execute_command_sequence(cs)
        manager.close()

        outfile = os.path.join(str(tmpdir), 'sources', '1-*.json.gz')
        src_file = glob.glob(outfile)[0]
        with gzip.GzipFile(src_file, 'rb') as f:
            visit_source = json.loads(f.read().decode('utf-8'))

        observed_parents = dict()

        def verify_frame(frame, parent_frames=[]):
            # Verify structure
            observed_parents[frame['doc_url']] = list(parent_frames)  # copy

            # Verify source
            path = urlparse(frame['doc_url']).path
            expected_source = ''
            with open('.' + path, 'r') as f:
                expected_source = re.sub(r'\s', '', f.read().lower())
                if expected_source.startswith('<!doctypehtml>'):
                    expected_source = expected_source[14:]
            observed_source = re.sub(r'\s', '', frame['source'].lower())
            if observed_source.startswith('<!doctypehtml>'):
                observed_source = observed_source[14:]
            assert observed_source == expected_source

            # Verify children
            parent_frames.append(frame['doc_url'])
            for key, child_frame in frame['iframes'].items():
                verify_frame(child_frame, parent_frames)
            parent_frames.pop()

        verify_frame(visit_source)
        assert EXPECTED_PARENTS == observed_parents
