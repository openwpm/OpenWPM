import traceback
from typing import Optional

""" The OpenWPM Status Object. Used for TaskManager, and BrowserManager"""


class Status:
    def __init__(
        self,
        name: str = None,
        error_class: Optional[type] = None,
        error_text: Optional[type] = None,
        tb: Optional[type] = None,
    ):

        self.name = name
        self.error_class = error_class
        self.error_text = error_text
        self.tb = tb
        self.raw_tuple = None

    def set_name(self, s):
        self.name = str(s)

    def raw_tuple(self, tup):
        self.raw_tuple = tup
        if len(tup) == 1:
            self.name = tup
        else:
            self.name = tup[0]
            self.error_class = tup[1]
