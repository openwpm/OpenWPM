from functools import partial
from typing import List

from ..automation.CommandSequence import CommandSequence
from ..automation.TaskManager import TaskManager
from .openwpmtest import OpenWPMTest
from .utilities import BASE_TEST_URL


class TestCallbackCommand(OpenWPMTest):
    """Test test the Aggregators as well as the entire callback machinery
    to see if all callbacks get correctly called"""

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)

    def test_local_callbacks(self):
        manager_params, browser_params = self.get_config()
        TEST_SITE = BASE_TEST_URL + "/test_pages/simple_a.html"
        manager = TaskManager(manager_params, browser_params)

        def callback(argument: List[int], success: bool):
            argument.extend([1, 2, 3])

        my_list = []
        sequence = CommandSequence(
            TEST_SITE, reset=True, blocking=True, callback=partial(callback, my_list)
        )
        sequence.get()

        manager.execute_command_sequence(sequence)
        manager.close()
        assert my_list == [1, 2, 3]
