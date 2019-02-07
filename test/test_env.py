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
        geckodriver_executable_path = get_geckodriver_exec_path()
        assert isfile(firefox_binary_path)
        assert isfile(geckodriver_executable_path)

    def test_py_pkgs(self):
        PY_REQUIREMENTS_TXT = join(self.BASE_DIR, "requirements.txt")
        assert isfile(PY_REQUIREMENTS_TXT)
        for line in open(PY_REQUIREMENTS_TXT):
            line = line.strip()
            if line == "" or line[0] == "#":
                continue
            pkg = re.split(r'[>=<]', line)[0]
            print("Checking Python package", pkg)
            self.assert_py_pkg_installed(pkg)
