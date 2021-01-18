import os

from selenium.webdriver import Firefox

from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParamsInternal, ManagerParamsInternal
from openwpm.socket_interface import ClientSocket

from .utilities import BASE_TEST_URL


class ExceptionCommand(BaseCommand):
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParamsInternal,
        manager_params: ManagerParamsInternal,
        extension_socket: ClientSocket,
    ) -> None:
        raise RuntimeError("We simulate a Command failing")


def test_display_shutdown(task_manager_creator, default_params):
    """Test the XVFB display option to see if it runs and deletes the lockfile upon shutdown"""
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.display_mode = "xvfb"
    TEST_SITE = BASE_TEST_URL + "/test_pages/simple_a.html"
    manager, db = task_manager_creator((manager_params, browser_params))
    port = manager.browsers[0].display_port

    sequence = CommandSequence(TEST_SITE)
    sequence.get()
    sequence.append_command(ExceptionCommand())
    manager.execute_command_sequence(sequence)
    manager.close()
    assert not os.path.exists("/tmp/.X%s-lock" % port)
