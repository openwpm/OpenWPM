import pytest # NOQA
import os
from openwpmtest import OpenWPMTest
from ..automation import TaskManager
import utilities
import expected
# TODO: add test for setter instrumentation


class TestExtension(OpenWPMTest):
    NUM_BROWSERS = 1

    def get_config(self, data_dir):
        manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        browser_params[0]['headless'] = True
        browser_params[0]['extension']['enabled'] = True
        browser_params[0]['extension']['jsInstrument'] = True
        manager_params['db'] = os.path.join(manager_params['data_directory'],
                                            manager_params['database_name'])
        return manager_params, browser_params

    def test_property_enumeration(self, tmpdir):
        test_url = utilities.BASE_TEST_URL + '/property_enumeration.html'
        db = self.visit(test_url, str(tmpdir))
        rows = utilities.query_db(db,
                                  "SELECT script_url, symbol FROM javascript")
        observed_symbols = set()
        for script_url, symbol in rows:
            assert script_url == test_url
            observed_symbols.add(symbol)
        assert expected.properties == observed_symbols

    def test_canvas_fingerprinting(self, tmpdir):
        db = self.visit('/canvas_fingerprinting.html', str(tmpdir))
        # Check that all calls and methods are recorded
        rows = utilities.get_javascript_entries(db)
        observed_rows = set()
        for item in rows:
            observed_rows.add(item)
        assert expected.canvas == observed_rows

    def check_webrtc_sdp_offer(self, sdp_str):
        """Make sure the SDP offer includes expected fields/strings.

        SDP offer contains randomly generated strings (e.g. GUID). That's why
        we don't expect a fixed string but only check the presence of certain
        protocol fields.
        """
        for expected_str in expected.webrtc_sdp_offer_strings:
            assert expected_str in sdp_str

    def test_webrtc_localip(self, tmpdir):
        db = self.visit('/webrtc_localip.html', str(tmpdir))
        # Check that all calls and methods are recorded
        rows = utilities.get_javascript_entries(db)
        observed_rows = set()
        for item in rows:
            if item[1] == "RTCPeerConnection.setLocalDescription":
                assert item[2:5] == (u'call', u'', 0)
                sdp_offer = item[5]
                self.check_webrtc_sdp_offer(sdp_offer)
            else:
                observed_rows.add(item)
        assert set(expected.webrtc_calls) == observed_rows
