from os.path import isfile

from ..automation.utilities.platform_utils import get_firefox_binary_path
from .openwpmtest import OpenWPMTest


class TestDependencies(OpenWPMTest):
    def test_dependencies(self):
        firefox_binary_path = get_firefox_binary_path()
        assert isfile(firefox_binary_path)
