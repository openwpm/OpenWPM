import os
from functools import partial
from typing import List

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.task_manager import TaskManager

from .openwpmtest import OpenWPMTest
from .utilities import BASE_TEST_URL


class ExceptionCommand(BaseCommand):
    def execute(self):
        raise Exception


class TestXVFBDisplay(OpenWPMTest):
    """Test the XVFB display option to see if it runs and deletes the lockfile upon shutdown"""

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir, display_mode="xvfb")

    def test_display_shutdown(self):
        manager_params, browser_params = self.get_config()
        TEST_SITE = BASE_TEST_URL + "/test_pages/simple_a.html"
        manager = TaskManager(manager_params, browser_params)
        port = manager.browsers[0].display_port

        sequence = CommandSequence(TEST_SITE)
        sequence.get()
        sequence.append_command(ExceptionCommand)
        manager.execute_command_sequence(sequence)
        manager.close()
        assert not os.path.exists("/tmp/.X%s-lock" % port)
