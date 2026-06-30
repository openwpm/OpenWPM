"""This file aims to demonstrate how to write custom commands in OpenWPM

Steps to have a custom command run as part of a CommandSequence

1. Create a class that derives from BaseCommand
2. Implement the execute method
3. Append it to the CommandSequence
4. Execute the CommandSequence

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

    # Have a look at openwpm.commands.types.BaseCommand.execute to see
    # an explanation of each parameter
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


def get_screen_resolution(webdriver: Firefox) -> tuple[int, int]:
    """Returns the available screen resolution (width, height) as seen by the page.

    Uses ``screen.availWidth``/``screen.availHeight``, which exclude OS chrome
    such as taskbars and docks, so it reflects the maximum window size the page
    can actually occupy.
    """
    width, height = webdriver.execute_script(
        "return [screen.availWidth, screen.availHeight];"
    )
    return int(width), int(height)


class SetResolution(BaseCommand):
    """Sets the browser window to a realistic resolution.

    Many crawls run headless or in a virtual framebuffer where the default
    window size is unusual and easy to fingerprint. Setting a common, realistic
    resolution makes the browser blend in better with ordinary visitors.
    """

    # A common desktop resolution; override per-crawl as needed.
    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        self.logger = logging.getLogger("openwpm")
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f"SetResolution({self.width}, {self.height})"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        self.logger.info(
            "Setting window resolution to %d x %d", self.width, self.height
        )
        webdriver.set_window_size(self.width, self.height)

        screen_width, screen_height = get_screen_resolution(webdriver)
        if self.width > screen_width or self.height > screen_height:
            self.logger.warning(
                "Requested window resolution (%d x %d) exceeds the available "
                "screen resolution (%d x %d); the window may be clamped",
                self.width,
                self.height,
                screen_width,
                screen_height,
            )
