from __future__ import absolute_import

import os
from os.path import isfile, join

import pytest

from ..automation import TaskManager
from . import utilities


class OpenWPMTest(object):
    NUM_BROWSERS = 1

    @pytest.fixture(autouse=True)
    def set_tmpdir(self, tmpdir):
        """Create a tmpdir fixture to be used in `get_test_config`.

        Based on:
        https://mail.python.org/pipermail/pytest-dev/2014-April/002484.html
        """
        self.tmpdir = str(tmpdir)

    def visit(self, page_url, data_dir="", sleep_after=0):
        """Visit a test page with the given parameters."""
        manager_params, browser_params = self.get_config(data_dir)
        manager = TaskManager.TaskManager(manager_params, browser_params)
        if not page_url.startswith("http"):
            page_url = utilities.BASE_TEST_URL + page_url
        manager.get(url=page_url, sleep=sleep_after)
        manager.close()
        return manager_params['db']

    def get_test_config(self, data_dir="",
                        num_browsers=NUM_BROWSERS):
        """Load and return the default test parameters."""
        if not data_dir:
            data_dir = self.tmpdir
        manager_params, browser_params = TaskManager.\
            load_default_params(num_browsers)
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        browser_params[0]['headless'] = True
        manager_params['db'] = join(manager_params['data_directory'],
                                    manager_params['database_name'])
        return manager_params, browser_params

    def is_installed(self, cmd):
        """Check if a program is available via the standard PATH lookup."""
        path = os.environ["PATH"].split(os.pathsep)
        for d in path:
            candidate = join(d, cmd)
            if isfile(candidate) and os.access(candidate, os.X_OK):
                return True
        return False

    def assert_is_installed(self, cmd):
        assert self.is_installed(cmd), 'Cannot find %s in your system' % cmd

    def assert_py_pkg_installed(self, pkg):
        # some modules are imported using a different name than the ones used
        # at the installation.
        pkg_name_mapping = {"pyopenssl": "OpenSSL",
                            "beautifulsoup4": "bs4",
                            "python-dateutil": "dateutil",
                            "flake8-isort": "flake8_isort",
                            "mini-amf": "miniamf",
                            "pillow": "PIL"
                            }
        # get the mapped name if it exists.
        pkg_importable = pkg_name_mapping.get(pkg.lower(), pkg)
        try:
            __import__(pkg_importable)
        except ImportError:
            pytest.fail("Cannot find python package %s in your system" % pkg)
