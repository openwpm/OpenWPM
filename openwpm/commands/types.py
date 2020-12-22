from abc import ABC, abstractmethod

from selenium.webdriver import Firefox

from ..config import BrowserParams, ManagerParams
from ..socket_interface import ClientSocket


class BaseCommand(ABC):
    def set_visit_browser_id(self, visit_id, browser_id):
        self.visit_id = visit_id
        self.browser_id = browser_id

    def set_start_time(self, start_time):
        self.start_time = start_time

    @abstractmethod
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        pass


class ShutdownSignal:
    def __repr__(self):
        return "ShutdownSignal()"
