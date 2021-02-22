"""Test TaskManager functionality."""
import pytest

from openwpm.errors import CommandExecutionError

from .utilities import BASE_TEST_URL


def test_failure_limit_value(default_params):
    manager_params, _ = default_params
    manager_params.num_browsers = 1
    # The default value for failure_limit is 2 * num_browsers + 10
    assert manager_params.failure_limit == 12
    manager_params.failure_limit = 2
    # Test that the chosen value is not overwritten by the default
    assert manager_params.failure_limit == 2


def test_failure_limit_exceeded(task_manager_creator, default_params):
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager_params.failure_limit = 0
    manager, _ = task_manager_creator((manager_params, browser_params[:1]))

    with pytest.raises(CommandExecutionError):
        manager.get("example.com")  # Selenium requires scheme prefix
        manager.get("example.com")  # Requires two commands to shut down
    manager.close()


def test_failure_limit_reset(task_manager_creator, default_params):
    """Test that failure_count is reset on command sequence completion."""
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager_params.failure_limit = 1
    manager, _ = task_manager_creator((manager_params, browser_params[:1]))
    manager.get("example.com")  # Selenium requires scheme prefix
    manager.get(BASE_TEST_URL)  # Successful command sequence
    # Now failure_count should be reset to 0 and the following command
    # failure should not raise a CommandExecutionError
    manager.get("example.com")  # Selenium requires scheme prefix
    manager.get(BASE_TEST_URL)  # Requires two commands to shut down
    manager.close()
