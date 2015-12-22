import sqlite3
import tarfile
import pytest
import os

from ..automation import TaskManager
from ..automation.Errors import CommandExecutionError, ProfileLoadError
import utilities

class TestExtension():
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
        browser_params[0]['extension']['enabled'] = True
        browser_params[0]['extension']['jsInstrument'] = True
        return manager_params, browser_params

    def test_property_enumeration(self, tmpdir):
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get('http://localhost:8000/test_pages/property_enumeration.html')
        manager.close(post_process=False)
        
        # Check that all property access was recorded
        db = os.path.join(manager_params['data_directory'], manager_params['database_name'])
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT script_url, symbol FROM javascript")
        expected_symbols= {
            "window.navigator.appCodeName",
            "window.navigator.appMinorVersion",
            "window.navigator.appName",
            "window.navigator.appVersion",
            "window.navigator.buildID",
            "window.navigator.cookieEnabled",
            "window.navigator.cpuClass",
            "window.navigator.doNotTrack",
            "window.navigator.geolocation",
            "window.navigator.language",
            "window.navigator.languages",
            "window.navigator.onLine",
            "window.navigator.opsProfile",
            "window.navigator.oscpu",
            "window.navigator.platform",
            "window.navigator.product",
            "window.navigator.productSub",
            "window.navigator.systemLanguage",
            "window.navigator.userAgent",
            "window.navigator.userLanguage",
            "window.navigator.userProfile",
            "window.navigator.vendorSub",
            "window.navigator.vendor",
            "window.screen.pixelDepth",
            "window.screen.colorDepth"}
        observed_symbols = set()
        for script_url, symbol in cur.fetchall():
            assert script_url == 'http://localhost:8000/test_pages/property_enumeration.html'
            observed_symbols.add(symbol)
        con.close()
        assert expected_symbols == observed_symbols
