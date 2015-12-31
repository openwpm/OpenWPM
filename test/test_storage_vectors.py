import sqlite3
import pytest
import time
import os

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
        browser_params[0]['headless'] = True
        return manager_params, browser_params

    def test_flash_cookies(self, tmpdir):
        """ Check that some Flash LSOs are saved """
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        browser_params[0]['disable_flash'] = False
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Get a site we know sets Flash cookies
        url = 'http://yandex.ru'# TODO update this to local test site
        start_time = time.time()
        manager.get(url, timeout=120)
        time.sleep(10)
        manager.dump_flash_cookies(url, start_time)
        manager.close(post_process=False)

        # Check that some flash cookies are recorded
        db = os.path.join(manager_params['data_directory'], manager_params['database_name'])
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM flash_cookies")
        count = cur.fetchone()[0]
        con.close()
        assert count > 0


    def test_profile_cookies(self, tmpdir):
        """ Check that some profile cookies are saved """
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Get a site we know sets Flash cookies
        url = 'http://www.yahoo.com'# TODO update this to local test site
        start_time = time.time()
        manager.get(url)
        time.sleep(5)
        manager.dump_profile_cookies(url, start_time)
        manager.close(post_process=False)

        # Check that some flash cookies are recorded
        db = os.path.join(manager_params['data_directory'], manager_params['database_name'])
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM profile_cookies")
        count = cur.fetchone()[0]
        con.close()
        assert count > 0
