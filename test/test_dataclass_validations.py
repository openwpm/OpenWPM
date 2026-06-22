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


def test_specific_config_error_surfaces():
    browser_params = BrowserParams()
    browser_params.display_mode = "not_a_mode"
    with pytest.raises(ConfigError) as exc_info:
        validate_browser_params(browser_params)
    message = str(exc_info.value)
    assert "display_mode" in message
    assert "Something went wrong" not in message


def test_unexpected_type_is_wrapped():
    browser_params = BrowserParams()
    # An int has no .lower(), triggering an unexpected AttributeError that
    # should be wrapped in the generic ConfigError.
    browser_params.display_mode = 123
    with pytest.raises(ConfigError) as exc_info:
        validate_browser_params(browser_params)
    assert "Something went wrong" in str(exc_info.value)


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


@pytest.mark.parametrize(
    "prefs",
    [
        # startupScanScopes omits the SCOPE_PROFILE bit (value 1)
        {"extensions.startupScanScopes": 0},
        {"extensions.startupScanScopes": 4},  # SCOPE_SYSTEM only
        {"extensions.startupScanScopes": "0"},
        {"extensions.startupScanScopes": "not an int"},
        # autoDisableScopes includes the SCOPE_PROFILE bit (value 1)
        {"extensions.autoDisableScopes": 1},
        {"extensions.autoDisableScopes": 15},  # all scopes
        {"extensions.autoDisableScopes": "1"},
        {"extensions.autoDisableScopes": "not an int"},
        # signatures required is truthy
        {"xpinstall.signatures.required": True},
        {"xpinstall.signatures.required": 1},
        {"xpinstall.signatures.required": "true"},
    ],
)
def test_extension_incompatible_prefs_raise(prefs):
    browser_params = BrowserParams()
    browser_params.prefs = prefs
    with pytest.raises(ConfigError):
        validate_browser_params(browser_params)


@pytest.mark.parametrize(
    "prefs",
    [
        {},  # no extension-critical prefs
        {"some.unrelated.pref": True},
        # startupScanScopes includes the SCOPE_PROFILE bit (value 1)
        {"extensions.startupScanScopes": 1},
        {"extensions.startupScanScopes": 5},  # SCOPE_PROFILE | SCOPE_SYSTEM
        {"extensions.startupScanScopes": "1"},
        # autoDisableScopes omits the SCOPE_PROFILE bit (value 1)
        {"extensions.autoDisableScopes": 0},
        {"extensions.autoDisableScopes": 4},  # SCOPE_SYSTEM only
        {"extensions.autoDisableScopes": "0"},
        # signatures required is falsy
        {"xpinstall.signatures.required": False},
        {"xpinstall.signatures.required": 0},
        {"xpinstall.signatures.required": "false"},
    ],
)
def test_extension_compatible_prefs_pass(prefs):
    browser_params = BrowserParams()
    browser_params.prefs = prefs
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
