from functools import partial
from typing import List

from openwpm.command_sequence import CommandSequence

from .utilities import BASE_TEST_URL


def test_local_callbacks(default_params, task_manager_creator):
    """Test the storage controller as well as the entire callback machinery
    to see if all callbacks get correctly called"""
    manager, _ = task_manager_creator(default_params)
    TEST_SITE = BASE_TEST_URL + "/test_pages/simple_a.html"

    def callback(argument: List[int], success: bool) -> None:
        argument.extend([1, 2, 3])

    my_list: List[int] = []
    sequence = CommandSequence(
        TEST_SITE, blocking=True, callback=partial(callback, my_list)
    )
    sequence.get()

    manager.execute_command_sequence(sequence)
    manager.close()
    assert my_list == [1, 2, 3]
