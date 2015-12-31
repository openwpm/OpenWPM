import sqlite3
import tarfile
import pytest
import os

from ..automation import TaskManager
from ..automation.Errors import CommandExecutionError, ProfileLoadError
import utilities
import expected

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
        observed_symbols = set()
        for script_url, symbol in cur.fetchall():
            assert script_url == 'http://localhost:8000/test_pages/property_enumeration.html'
            observed_symbols.add(symbol)
        con.close()
        assert expected.properties == observed_symbols

    def test_canvas_fingerprinting(self, tmpdir):
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get('http://localhost:8000/test_pages/canvas_fingerprinting.html')
        manager.close(post_process=False)

        # Check that all calls and methods are recorded
        db = os.path.join(manager_params['data_directory'], manager_params['database_name'])
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT script_url, symbol, operation, value, parameter_index, parameter_value FROM javascript")
        observed_rows = set()
        for item in cur.fetchall():
            observed_rows.add(item)
        con.close()
        assert expected.canvas == observed_rows
