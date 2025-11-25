import logging
from tkinter import ttk

from selenium.webdriver import Firefox

from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket

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