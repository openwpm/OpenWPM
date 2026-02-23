from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from selenium.webdriver import Firefox

from ..config import BrowserParamsInternal, ManagerParamsInternal


@runtime_checkable
class ExtensionSocket(Protocol):
    """Protocol for the extension communication socket.

    Both the legacy ClientSocket and the new ExtensionSocketAdapter
    satisfy this interface.
    """

    def send(self, msg: Any) -> None: ...
    def close(self) -> None: ...


class BaseCommand(ABC):
    """
    Base class for all Commands in OpenWPM

    See `custom_command.py` for instructions on how
    to implement your own and `openwpm/commands` for
    all commands that are already implemented
    """

    def set_visit_browser_id(self, visit_id, browser_id):
        self.visit_id = visit_id
        self.browser_id = browser_id

    def set_start_time(self, start_time):
        self.start_time = start_time

    @abstractmethod
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParamsInternal,
        manager_params: ManagerParamsInternal,
        extension_socket: ExtensionSocket,
    ) -> None:
        """This method gets called in the Browser process

        :parameter webdriver: WebDriver is a Selenium class used to control
            browser. You can simulate arbitrary interactions and extract almost
            all browser state with the tools that Selenium gives you
        :parameter browser_params: Contains the per browser configuration
            E.g. which instruments are enabled
        :parameter manager_params: Per crawl parameters E.g. where to store files
        :parameter extension_socket: Communication channel to the extension.
            Supports send() to push commands to the extension.
        """
        pass


class ShutdownSignal:
    def __repr__(self):
        return "ShutdownSignal()"
