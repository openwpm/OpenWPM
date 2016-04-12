import pytest
import time
import os
import utilities
import expected
from ..automation import TaskManager


class TestStorageVectors():
    """ Runs some basic tests to check that the saving of
    storage vectors (i.e. Flash LSOs, profile cookies) works.

    NOTE: These tests are very basic and should be expanded
    on to check for completeness and correctness.
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

    def test_flash_cookies(self, tmpdir):
        """ Check that some Flash LSOs are saved """
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        browser_params[0]['disable_flash'] = False
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Get a site we know sets Flash cookies
        lso_value = utilities.rand_str(8)
        expected.lso_content[5] = lso_value  # we'll expect this to be present
        expected.lso_content[0] = expected.lso_content[0].replace("REPLACEME",
                                                                  lso_value)
        qry_str = '?lso_test_key=%s&lso_test_value=%s' % ("test_key",
                                                          lso_value)
        test_url = utilities.BASE_TEST_URL + '/lso/setlso.html' + qry_str
        start_time = time.time()
        manager.get(test_url)
        time.sleep(5)
        manager.dump_flash_cookies(test_url, start_time)
        manager.close(post_process=False)

        #  Check that some flash cookies are recorded
        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT * FROM flash_cookies")
        lso_count = len(qry_res)
        assert lso_count == 1
        lso_content = list(qry_res[0][2:])  # Remove first two items
        # remove randomly generated LSO directory name
        # e.g. TY2FOJUG/localtest.me/Flash.sol -> localtest.me/Flash.sol
        lso_content[3] = lso_content[3].split("/", 1)[-1]  # remove LSO dirname
        assert lso_content == expected.lso_content

    def test_profile_cookies(self, tmpdir):
        """ Check that some profile cookies are saved """
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        # TODO update this to local test site
        url = 'http://www.yahoo.com'
        start_time = time.time()
        manager.get(url)
        time.sleep(5)
        manager.dump_profile_cookies(url, start_time)
        manager.close(post_process=False)

        # Check that some flash cookies are recorded
        qry_res = utilities.query_db(manager_params['db'],
                                     "SELECT COUNT(*) FROM profile_cookies")
        prof_cookie_count = qry_res[0]
        assert prof_cookie_count > 0

    def test_js_profile_cookies(self, tmpdir):
        """ Check that profile cookies set by JS are saved """
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        url = utilities.BASE_TEST_URL + "/js_cookie.html"
        start_time = time.time()
        manager.get(url)
        time.sleep(5)
        manager.dump_profile_cookies(url, start_time)
        manager.close(post_process=False)
        # Check that the JS cookie we stored is recorded
        qry_res = utilities.query_db(manager_params['db'], "SELECT * FROM profile_cookies")
        assert len(qry_res) == 1  # we store only one cookie
        cookies = qry_res[0]  # take the first cookie
        # compare URL, domain, name, value, origin, path
        assert cookies[2:8] == expected.js_cookie
