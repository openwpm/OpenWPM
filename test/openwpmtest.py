import utilities
import pytest
from time import sleep
import commands
from ..automation import TaskManager


class OpenWPMTest(object):

    def visit(self, page_url, data_dir, sleep_after=0, post_process=False):
        """Visits a given test page according to given parameters."""
        manager_params, browser_params = self.get_config(data_dir)
        manager = TaskManager.TaskManager(manager_params, browser_params)
        if not page_url.startswith("http"):
            page_url = utilities.BASE_TEST_URL + page_url
        manager.get(url=page_url, sleep=sleep_after)
        manager.close(post_process)
        return manager_params['db']

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
