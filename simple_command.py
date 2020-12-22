""" This file aims to demonstrate how to write custom commands in OpenWPM

Steps to have a custom command run as part of a CommandSequence

1. Create a class that derives from BaseCommand
2. Implement the execute method
3. Append it to the CommandSequence
4. Execute the CommandSequence

The following parameters get passed to the execute function:
1. webdriver: WebDriver is a Selenium class used to control
   browser. You can simulate arbitrary interactions and extract almost all browser state
   with the tools that Selenium gives you
2. browser_params: Configuration that might differ per browser
   OpenWPM allows you to run multiple browsers with different
   configurations in parallel and this parameter allows you
   to figure out which Browser your command is running on
3. manager_params: Configuration for the TaskManager
   This configuration will be the same for all browsers running on the same
   TaskManager. E.g. if your command writes out data to disk, it should do
   so by having a look at the data_directory in the manager_params
4. extension_socket: Communication channel to the storage provider
   TODO: Further document this once the StorageProvider PR has landed
   This allows you to send data to be persisted to storage.
"""
import logging

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By

from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket


class LinkCountingCommand(BaseCommand):
    """This command logs how many links it found on any given page"""

    def __init__(self) -> None:
        self.logger = logging.getLogger("openwpm")

    # While this is not strictly necessary, we use the repr of a command for logging
    # So not having a proper repr will make your logs a lot less useful
    def __repr__(self) -> str:
        return "LinkCountingCommand"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        current_url = webdriver.current_url
        link_count = len(webdriver.find_elements(By.TAG_NAME, "a"))
        self.logger.info("There are %d links on %s", link_count, current_url)
