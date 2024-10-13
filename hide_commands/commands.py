""" This file aims to demonstrate how to write custom commands in OpenWPM

Steps to have a custom command run as part of a CommandSequence

1. Create a class that derives from BaseCommand
2. Implement the execute method
3. Append it to the CommandSequence
4. Execute the CommandSequence

"""
import logging
from tkinter import ttk

from selenium.webdriver import Firefox

from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket


def get_screen_resolution(driver: Firefox) -> list[int]:
    return driver.execute_script("return [screen.width, screen.height];")


class SetResolution(BaseCommand):
    """Sets the browser window resolution"""

    def __init__(self, width: int, height: int) -> None:
        self.logger = logging.getLogger("openwpm")
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return "SetResolution"

    def execute(
        self,
        driver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        self.logger.info(f"Setting window resolution to {self.width} x {self.height} ")
        driver.set_window_size(self.width, self.height)

        resolution = get_screen_resolution(driver)
        if resolution[0] <= self.width or resolution[1] <= self.height:
            self.logger.warn(
                f"Browser window resolution ({self.width} x {self.height}) exceeds "
                + f"screen resolution ({resolution[0]} x {resolution[1]})"
            )


class SetPosition(BaseCommand):
    """Sets the browser window position"""

    def __init__(self, x: int, y: int) -> None:
        self.logger = logging.getLogger("openwpm")
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return "SetPosition"

    def execute(
        self,
        driver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        driver.set_window_position(self.x, self.y, windowHandle="current")
