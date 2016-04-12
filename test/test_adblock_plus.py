from urlparse import urlparse
import pytest
import os

from ..automation import TaskManager
from ..automation.Errors import BrowserConfigError
from ..automation.platform_utils import fetch_adblockplus_list
import utilities
import expected

psl = utilities.get_psl()


class TestABP():
    NUM_BROWSERS = 1

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
        manager.get(utilities.BASE_TEST_URL + '/abp/adblock_plus_test.html')
        manager.close(post_process=False)

        db = os.path.join(data_dir, manager_params['database_name'])
        rows = utilities.query_db(db, "SELECT url FROM http_requests")
        urls = set()
        for url, in rows:
            ps1 = psl.get_public_suffix(urlparse(url).hostname)
            # exclude requests to safebrowsing and tracking protection backends
            if ps1 not in ("mozilla.com", "mozilla.net"):
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
