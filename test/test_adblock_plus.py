import sqlite3
import pytest
import os

from ..automation import TaskManager
from ..automation.Errors import BrowserConfigError
from ..automation.platform_utils import fetch_adblockplus_list
import utilities
import expected

class TestABP():
    NUM_BROWSERS = 1
    server = None
    server_thread = None

    @classmethod
    def setup_class(cls):
        cls.server, cls.server_thread = utilities.start_server()

    @classmethod
    def teardown_class(cls):
        print "Closing server thread..."
        cls.server.shutdown()
        cls.server_thread.join()

    def get_config(self, data_dir):
        manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        browser_params[0]['headless'] = True
        browser_params[0]['adblock-plus'] = True
        return manager_params, browser_params

    def test_list_fetch(self, tmpdir):
        data_dir = str(tmpdir)
        fetch_adblockplus_list(data_dir)
        assert os.path.isfile(os.path.join(data_dir, 'patterns.ini'))
        assert os.path.isfile(os.path.join(data_dir, 'elemhide.css'))

    def test_blocks_includes(self, tmpdir):
        data_dir = str(tmpdir)
        list_loc = os.path.join(data_dir, 'adblock_plus')
        manager_params, browser_params = self.get_config(data_dir)
        fetch_adblockplus_list(list_loc)
        browser_params[0]['adblock-plus_list_location'] = list_loc
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get('http://localhost:8000/abp/adblock_plus_test.html')
        manager.close(post_process=False)

        db = os.path.join(data_dir,manager_params['database_name'])
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT url FROM http_requests")
        urls = set()
        for url, in cur.fetchall():
            urls.add(url)
        assert urls == expected.adblockplus

    def test_error_with_missing_option(self, tmpdir):
        manager_params, browser_params = self.get_config(str(tmpdir))
        with pytest.raises(BrowserConfigError):
            manager = TaskManager.TaskManager(manager_params, browser_params)
            manager.close(post_process=False)

    def test_error_with_missing_list(self, tmpdir):
        data_dir = str(tmpdir)
        list_loc = os.path.join(data_dir, 'adblock_plus')
        manager_params, browser_params = self.get_config(data_dir)
        browser_params[0]['adblock-plus_list_location'] = list_loc
        with pytest.raises(BrowserConfigError):
            manager = TaskManager.TaskManager(manager_params, browser_params)
            manager.close(post_process=False)
