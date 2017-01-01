import pytest
import os
import utilities
import expected
from openwpmtest import OpenWPMTest
from ..automation import TaskManager
from ..automation.utilities import db_utils
from datetime import datetime
# TODO: add test for setter instrumentation


class TestExtension(OpenWPMTest):

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0]['js_instrument'] = True
        return manager_params, browser_params

    def test_property_enumeration(self):
        test_url = utilities.BASE_TEST_URL + '/property_enumeration.html'
        db = self.visit(test_url)
        rows = db_utils.query_db(db,
                                  "SELECT script_url, symbol FROM javascript")
        observed_symbols = set()
        for script_url, symbol in rows:
            assert script_url == test_url
            observed_symbols.add(symbol)
        assert expected.properties == observed_symbols

    def test_canvas_fingerprinting(self):
        db = self.visit('/canvas_fingerprinting.html')
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_rows = set()
        for item in rows:
            observed_rows.add(item)
        assert expected.canvas == observed_rows

    def test_extension_gets_correct_visit_id(self):
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)

        url_a = utilities.BASE_TEST_URL + '/simple_a.html'
        url_b = utilities.BASE_TEST_URL + '/simple_b.html'

        manager.get(url_a)
        manager.get(url_b)
        manager.close()
        qry_res = db_utils.query_db(manager_params['db'],
                                     "SELECT visit_id, site_url FROM site_visits")

        # Construct dict mapping site_url to visit_id
        visit_ids = dict()
        for row in qry_res:
            visit_ids[row[1]] = row[0]

        simple_a_visit_id = db_utils.query_db(
                                    manager_params['db'],
                                    "SELECT visit_id FROM javascript WHERE "
                                    "symbol=?", ("window.navigator.userAgent",))

        simple_b_visit_id = db_utils.query_db(
                                    manager_params['db'],
                                    "SELECT visit_id FROM javascript WHERE "
                                    "symbol=?", ("window.navigator.platform",))

        assert visit_ids[url_a] == simple_a_visit_id[0][0]
        assert visit_ids[url_b] == simple_b_visit_id[0][0]

    def check_webrtc_sdp_offer(self, sdp_str):
        """Make sure the SDP offer includes expected fields/strings.

        SDP offer contains randomly generated strings (e.g. GUID). That's why
        we don't expect a fixed string but only check the presence of certain
        protocol fields.
        """
        for expected_str in expected.webrtc_sdp_offer_strings:
            assert expected_str in sdp_str

    def test_webrtc_localip(self):
        db = self.visit('/webrtc_localip.html')
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_rows = set()
        for item in rows:
            if item[1] == "RTCPeerConnection.setLocalDescription":
                assert item[2:5] == (u'call', u'', 0)
                sdp_offer = item[5]
                self.check_webrtc_sdp_offer(sdp_offer)
            else:
                observed_rows.add(item)
        assert set(expected.webrtc_calls) == observed_rows

    @pytest.mark.skipif("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", reason='Flaky on Travis CI')
    def test_audio_fingerprinting(self):
        db = self.visit('/audio_fingerprinting.html')
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_symbols = set()
        for item in rows:
            observed_symbols.add(item[1])
        assert expected.audio == observed_symbols

    def test_js_call_stack(self):
        db = self.visit('/js_call_stack.html')
        # Check that all stack info are recorded
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        observed_rows = set()
        for item in rows:
            observed_rows.add(item[3:11])
        assert set(expected.js_stack_calls) == observed_rows

    def test_js_time_stamp(self):
        # Check that timestamp is recorded correctly for the javascript table
        MAX_TIMEDELTA = 30  # max time diff in seconds
        db = self.visit('/canvas_fingerprinting.html')
        utc_now = datetime.utcnow()  # OpenWPM stores timestamp in UTC time
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        assert len(rows)  # make sure we have some JS events captured
        for row in rows:
            js_time = datetime.strptime(row[14], "%Y-%m-%dT%H:%M:%S.%fZ")
            # compare UTC now and the timestamp recorded at the visit
            assert (utc_now - js_time).seconds < MAX_TIMEDELTA
        assert not db_utils.any_command_failed(db)

    def test_document_cookie_instrumentation(self):
        db = self.visit(utilities.BASE_TEST_URL + "/js_cookie.html")
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        # [3:12] exclude id and empty columns
        captured_cookie_calls = set([row[3:12] for row in rows])
        assert captured_cookie_calls == expected.document_cookie_read_write
