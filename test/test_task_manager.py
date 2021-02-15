import pytest

from openwpm.errors import CommandExecutionError
from openwpm.task_manager import TaskManager

from .openwpmtest import OpenWPMTest
from .utilities import BASE_TEST_URL


class TestTaskManager(OpenWPMTest):
    """Test TaskManager functionality."""

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)

    def test_failure_limit_value(self):
        manager_params, _ = self.get_config()
        # The default value for failure_limit is 2 * num_browsers + 10
        assert manager_params.failure_limit == 12
        manager_params.failure_limit = 2
        # Test that the chosen value is not overwritten by the default
        assert manager_params.failure_limit == 2

    def test_failure_limit_exceeded(self):
        manager_params, browser_params = self.get_config()
        manager_params.failure_limit = 0
        manager = TaskManager(manager_params, browser_params)
        with pytest.raises(CommandExecutionError):
            manager.get("example.com")  # Selenium requires scheme prefix
            manager.get("example.com")  # Requires two commands to shut down

    def test_failure_limit_reset(self):
        """Test that failure_count is reset on command sequence completion."""
        manager_params, browser_params = self.get_config()
        manager_params.failure_limit = 1
        manager = TaskManager(manager_params, browser_params)
        manager.get("example.com")  # Selenium requires scheme prefix
        manager.get(BASE_TEST_URL)  # Successful command sequence
        # Now failure_count should be reset to 0 and the following command
        # failure should not raise a CommandExecutionError
        manager.get("example.com")  # Selenium requires scheme prefix
        manager.get(BASE_TEST_URL)  # Requires two commands to shut down
        manager.close()
