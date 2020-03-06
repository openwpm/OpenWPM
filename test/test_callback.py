from .openwpmtest import OpenWPMTest
from . import utilities
from typing import List
from functools import partial


from ..automation.TaskManager import TaskManager
from ..automation.CommandSequence import CommandSequence


class TestCallbackCommand(OpenWPMTest):
    """Test `custom_function` command's ability to handle inline functions"""

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)

    def test_callbacks(self):
        manager_params, browser_params = self.get_config()
        url = utilities.BASE_TEST_URL + "/test_pages/simple_a.html"
        manager = TaskManager(manager_params, browser_params)

        def callback(argument: List[int]):
            argument.extend([4, 5, 6])
            print("Running callback")

        my_list = []
        sequence = CommandSequence(url, reset=True,
                                   blocking=True,
                                   callback=partial(callback, my_list))
        sequence.get()

        def custom_func(argument: List[int], **kwargs):
            list.extend([1, 2, 3])
            print("Running custom_func")

        sequence.run_custom_function(custom_func, (my_list,))
        manager.execute_command_sequence(sequence)
        assert my_list == [1, 2, 3, 4, 5, 6]
