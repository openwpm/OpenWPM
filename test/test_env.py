import pytest
from openwpmtest import OpenWPMTest


class TestDependencies(OpenWPMTest):
    # TODO: add tests for firefox-bin directory and Alexa list
    def test_dependencies(self, tmpdir):
        self.assert_is_installed("npm")
        self.assert_is_installed("jpm")
        self.assert_is_installed('mitmdump')
        self.assert_is_installed('firefox')

    def test_py_pkgs(self):
        # TODO: move python module names from install.sh to requirements.txt.
        # use  requirements.txt to test the dependencies
        py_pkgs = ["setuptools", "pyvirtualdisplay", "beautifulsoup4",
                   "pyasn1", "pyOpenSSL", "python-dateutil", "tld", "pyamf",
                   "psutil", "mmh3", "plyvel", "tblib", "tabulate",
                   "pytest", "publicsuffix"]

        for pkg in py_pkgs:
            self.assert_py_pkg_installed(pkg)
