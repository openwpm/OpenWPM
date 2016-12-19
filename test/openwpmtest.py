from os.path import join
import utilities
import pytest
import commands
from ..automation import TaskManager


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

    def is_installed(self, pkg_name):
        """Check if a Linux package is installed."""
        cmd = 'which %s' % pkg_name
        status, _ = commands.getstatusoutput(cmd)
        return False if status else True

    def assert_is_installed(self, pkg):
        assert self.is_installed(pkg), 'Cannot find %s in your system' % pkg

    def assert_py_pkg_installed(self, pkg):
        # some modules are imported using a different name than the ones used
        # at the installation.
        pkg_name_mapping = {"pyopenssl": "OpenSSL",
                            "mitmproxy": "libmproxy",
                            "beautifulsoup4": "bs4",
                            "python-dateutil": "dateutil"
                            }
        # get the mapped name if it exists.
        pkg_importable = pkg_name_mapping.get(pkg.lower(), pkg)
        try:
            __import__(pkg_importable)
        except ImportError:
            pytest.fail("Cannot find python package %s in your system" % pkg)
