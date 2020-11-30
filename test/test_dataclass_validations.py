import pytest

from openwpm.config import validate_browser_params, validate_manager_params
from openwpm.errors import ConfigError

from .openwpmtest import OpenWPMTest


class TestDataclassValidations(OpenWPMTest):
    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)


class TestBrowserParams(TestDataclassValidations):
    def test_display_mode(self):
        _, browser_params = self.get_config()
        browser_params[0].display_mode = "something unsupported"
        with pytest.raises(ConfigError):
            validate_browser_params(browser_params[0])
        browser_params[0].display_mode = []
        with pytest.raises(ConfigError):
            validate_browser_params(browser_params[0])
        browser_params[0].display_mode = "native"
        try:
            validate_browser_params(browser_params[0])
        except:
            pytest.fail("Unexpected error raised")

    def test_browser_type(self):
        _, browser_params = self.get_config()
        browser_params[0].browser = "something unsupported"
        with pytest.raises(ConfigError):
            validate_browser_params(browser_params[0])
        browser_params[0].browser = "firefox"
        try:
            validate_browser_params(browser_params[0])
        except:
            pytest.fail("Unexpected error raised")

    def test_tp_cookies_opt(self):
        _, browser_params = self.get_config()
        browser_params[0].tp_cookies = "something unsupported"
        with pytest.raises(ConfigError):
            validate_browser_params(browser_params[0])
        browser_params[0].tp_cookies = "never"
        try:
            validate_browser_params(browser_params[0])
        except:
            pytest.fail("Unexpected error raised")

    def test_save_content_type(self):
        _, browser_params = self.get_config()
        browser_params[0].save_content = []
        with pytest.raises(ConfigError):
            validate_browser_params(browser_params[0])
        browser_params[0].save_content = "something unsupported"
        with pytest.raises(ConfigError):
            validate_browser_params(browser_params[0])
        browser_params[0].save_content = False
        try:
            validate_browser_params(browser_params[0])
        except:
            pytest.fail("Unexpected error raised")
        browser_params[0].save_content = "script"
        try:
            validate_browser_params(browser_params[0])
        except:
            pytest.fail("Unexpected error raised")


class TestManagerParams(TestDataclassValidations):
    def test_log_file_extension(self):
        manager_params, _ = self.get_config()
        manager_params.log_file = "something.unsupported"
        with pytest.raises(ConfigError):
            validate_manager_params(manager_params)
        manager_params.log_file = []
        with pytest.raises(ConfigError):
            validate_manager_params(manager_params)

    def test_database_file_extension(self):
        manager_params, _ = self.get_config()
        manager_params.database_name = "something.unsupported"
        with pytest.raises(ConfigError):
            validate_manager_params(manager_params)

    def test_failure_limit(self):
        manager_params, _ = self.get_config()
        manager_params.failure_limit = "not None and not int"
        with pytest.raises(ConfigError):
            validate_manager_params(manager_params)
        manager_params.failure_limit = None  # when failure_limit is set to None
        try:
            validate_manager_params(manager_params)
        except:
            pytest.fail("Unexpected error raised")
        manager_params.failure_limit = 2  # when failure_limit is set to int
        try:
            validate_manager_params(manager_params)
        except:
            pytest.fail("Unexpected error raised")

    def test_output_format(self):
        manager_params, _ = self.get_config()
        manager_params.output_format = "not None and not int"
        with pytest.raises(ConfigError):
            validate_manager_params(manager_params)
        manager_params.output_format = "s3"
        try:
            validate_manager_params(manager_params)
        except:
            pytest.fail("Unexpected error raised")
