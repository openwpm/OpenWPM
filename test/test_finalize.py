from ..automation.utilities import db_utils
from .openwpmtest import OpenWPMTest


class TestExtension(OpenWPMTest):
    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0]["prefs"] = {"dom.disable_open_during_load": True}
        return manager_params, browser_params

    def test_finalize_with_no_popup(self):
        self.visit("https://example.com")
        assert not db_utils.any_command_failed()
