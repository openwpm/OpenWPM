from functools import partial
from typing import List

from openwpm.command_sequence import CommandSequence
from openwpm.task_manager import TaskManager

from .openwpmtest import OpenWPMTest
from .utilities import BASE_TEST_URL


class TestXVFBDisplay(OpenWPMTest):
    """Test the XVFB display option to see if it runs and shuts down properly after a command is given"""

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir, display_mode="xvfb")

    def test_display_shutdown(self):
        manager_params, browser_params = self.get_config()
        TEST_SITE = BASE_TEST_URL + "/test_pages/simple_a.html"
        manager = TaskManager(manager_params, browser_params)

        sequence = CommandSequence(TEST_SITE)
        sequence.get()
        sequence.save_screenshot()
        manager.execute_command_sequence(sequence)
        manager.close()
