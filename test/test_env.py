from __future__ import absolute_import, print_function

import re
from os.path import dirname, isfile, join, realpath

from ..automation.utilities.platform_utils import (get_firefox_binary_path,
                                                   get_geckodriver_exec_path)
from .openwpmtest import OpenWPMTest


class TestDependencies(OpenWPMTest):

    BASE_DIR = dirname(dirname(realpath(__file__)))

    def test_dependencies(self):
        self.assert_is_installed("npm")
        firefox_binary_path = get_firefox_binary_path()
        assert isfile(firefox_binary_path)
