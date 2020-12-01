import pytest

from openwpm.config import (
    BrowserParams,
    ManagerParams,
    validate_browser_params,
    validate_manager_params,
)
from openwpm.errors import ConfigError

from .openwpmtest import OpenWPMTest


def get_config(data_dir=""):
    return ManagerParams(), [BrowserParams()]


def test_display_mode():
    _, browser_params = get_config()

    browser_params[0].display_mode = "something unsupported"
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params[0])

    browser_params[0].display_mode = []
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params[0])

    browser_params[0].display_mode = "native"
    validate_browser_params(browser_params[0])


def test_browser_type():
    _, browser_params = get_config()

    browser_params[0].browser = "something unsupported"
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params[0])

    browser_params[0].browser = "firefox"
    validate_browser_params(browser_params[0])


def test_tp_cookies_opt():
    _, browser_params = get_config()

    browser_params[0].tp_cookies = "something unsupported"
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params[0])

    browser_params[0].tp_cookies = "never"
    validate_browser_params(browser_params[0])


def test_save_content_type():
    _, browser_params = get_config()

    browser_params[0].save_content = []
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params[0])

    browser_params[0].save_content = "something unsupported"
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params[0])

    browser_params[0].save_content = False
    validate_browser_params(browser_params[0])

    browser_params[0].save_content = "script"
    validate_browser_params(browser_params[0])


def test_log_file_extension():
    manager_params, _ = get_config()

    manager_params.log_file = "something.unsupported"
    with pytest.raises(ConfigError):
        validate_manager_params(manager_params)

    manager_params.log_file = []
    with pytest.raises(ConfigError):
        validate_manager_params(manager_params)


def test_database_file_extension():
    manager_params, _ = get_config()

    manager_params.database_name = "something.unsupported"
    with pytest.raises(ConfigError):
        validate_manager_params(manager_params)


def test_failure_limit():
    manager_params, _ = get_config()

    manager_params.failure_limit = "not None and not int"
    with pytest.raises(ConfigError):
        validate_manager_params(manager_params)

    manager_params.failure_limit = None  # when failure_limit is set to None
    validate_manager_params(manager_params)

    manager_params.failure_limit = 2  # when failure_limit is set to int
    validate_manager_params(manager_params)


def test_output_format():
    manager_params, _ = get_config()

    manager_params.output_format = "not None and not int"
    with pytest.raises(ConfigError):
        validate_manager_params(manager_params)

    manager_params.output_format = "s3"
    validate_manager_params(manager_params)
