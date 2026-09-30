import pytest

from openwpm.config import (
    BrowserParams,
    ManagerParams,
    validate_browser_params,
    validate_crawl_configs,
    validate_manager_params,
)
from openwpm.errors import ConfigError


def test_display_mode():
    browser_params = BrowserParams()

    browser_params.display_mode = "something unsupported"
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params)

    browser_params.display_mode = []
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params)

    browser_params.display_mode = "native"
    validate_browser_params(browser_params)


def test_browser_type():
    browser_params = BrowserParams()

    browser_params.browser = "something unsupported"
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params)

    browser_params.browser = "firefox"
    validate_browser_params(browser_params)


def test_tp_cookies_opt():
    browser_params = BrowserParams()

    browser_params.tp_cookies = "something unsupported"
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params)

    browser_params.tp_cookies = "never"
    validate_browser_params(browser_params)


def test_save_content_type():
    browser_params = BrowserParams()

    browser_params.save_content = []
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params)

    browser_params.save_content = "something unsupported"
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params)

    browser_params.save_content = False
    validate_browser_params(browser_params)

    browser_params.save_content = "script"
    validate_browser_params(browser_params)


def test_log_file_extension():
    manager_params = ManagerParams()

    manager_params.log_path = "something.unsupported"
    with pytest.raises(ConfigError):
        validate_manager_params(manager_params)

    manager_params.log_path = []
    with pytest.raises(ConfigError):
        validate_manager_params(manager_params)


def test_failure_limit():
    manager_params = ManagerParams()

    manager_params.failure_limit = "not None and not int"
    with pytest.raises(ConfigError):
        validate_manager_params(manager_params)

    manager_params.failure_limit = None  # when failure_limit is set to None
    validate_manager_params(manager_params)

    manager_params.failure_limit = 2  # when failure_limit is set to int
    validate_manager_params(manager_params)


def test_num_browser_crawl_config():
    manager_params = ManagerParams(num_browsers=2)
    browser_params = [BrowserParams()]

    with pytest.raises(ConfigError):
        validate_crawl_configs(manager_params, browser_params)

    browser_params.append(BrowserParams())
    validate_crawl_configs(manager_params, browser_params)
