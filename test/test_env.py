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

    def check_py_pkgs(self, requirements_file):
        assert isfile(requirements_file)
        for line in open(requirements_file):
            line = line.strip()
            if line == "" or line[0] == "#":
                continue
            # Extract the package name by stripping requirement specifiers
            pkg = re.split(r'[>=<\[]', line)[0]
            print("Checking Python package", pkg)
            self.assert_py_pkg_installed(pkg)

    def test_py_pkgs(self):
        self.check_py_pkgs(join(self.BASE_DIR, "requirements.txt"))
        self.check_py_pkgs(join(self.BASE_DIR, "requirements-dev.txt"))
