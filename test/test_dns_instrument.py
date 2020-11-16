from openwpm.utilities import db_utils

from .openwpmtest import OpenWPMTest


class TestDNSInstrument(OpenWPMTest):
    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        for browser_param in browser_params:
            browser_param["dns_instrument"] = True
        return manager_params, browser_params

    def test_name_resolution(self):
        db = self.visit("http://localtest.me:8000")
        result = db_utils.query_db(db, "SELECT * FROM dns_responses")
        result = result[0]
        print(result.keys())
        assert result["used_address"] == "127.0.0.1"
        assert result["addresses"] == "127.0.0.1"
        assert result["hostname"] == "localtest.me"
        assert result["canonical_name"] == "localtest.me"
