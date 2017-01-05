import pytest
import os
import utilities
from openwpmtest import OpenWPMTest
from ..automation import TaskManager
from ..automation.utilities import db_utils
from datetime import datetime

# Expected Navigator and Screen properties
PROPERTIES = {
    "window.navigator.appCodeName",
    "window.navigator.appName",
    "window.navigator.appVersion",
    "window.navigator.buildID",
    "window.navigator.cookieEnabled",
    "window.navigator.doNotTrack",
    "window.navigator.geolocation",
    "window.navigator.language",
    "window.navigator.languages",
    "window.navigator.onLine",
    "window.navigator.oscpu",
    "window.navigator.platform",
    "window.navigator.product",
    "window.navigator.productSub",
    "window.navigator.userAgent",
    "window.navigator.vendorSub",
    "window.navigator.vendor",
    "window.screen.pixelDepth",
    "window.screen.colorDepth"
}

# Canvas Fingerprinting DB calls and property sets
CANVAS_TEST_URL = u"%s/canvas_fingerprinting.html" % utilities.BASE_TEST_URL

CANVAS_CALLS = {
    (CANVAS_TEST_URL, u"HTMLCanvasElement.getContext",
     u"get", u"FUNCTION", None, None),
    (CANVAS_TEST_URL,
     u"HTMLCanvasElement.getContext", u"call", u"", 0, u"2d"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.textBaseline",
     u"set", u"top", None, None),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.font", u"set",
     u"14px 'Arial'", None, None),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.textBaseline",
     u"set", u"alphabetic", None, None),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillStyle",
     u"set", u"#f60", None, None),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillRect",
     u"get", u"FUNCTION", None, None),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillRect",
     u"call", u"", 0, u"125"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillRect",
     u"call", u"", 1, u"1"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillRect",
     u"call", u"", 2, u"62"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillRect",
     u"call", u"", 3, u"20"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillStyle",
     u"set", u"#069", None, None),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillText",
     u"get", u"FUNCTION", None, None),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillText",
     u"call", u"", 0, u"BrowserLeaks,com <canvas> 1.0"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillText",
     u"call", u"", 1, u"2"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillText",
     u"call", u"", 2, u"15"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillStyle",
     u"set", u"rgba(102, 204, 0, 0.7)", None, None),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillText",
     u"call", u"", 0, u"BrowserLeaks,com <canvas> 1.0"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillText",
     u"call", u"", 1, u"4"),
    (CANVAS_TEST_URL, u"CanvasRenderingContext2D.fillText",
     u"call", u"", 2, u"17"),
    (CANVAS_TEST_URL, u"HTMLCanvasElement.toDataURL",
     u"get", u"FUNCTION", None, None),
    (CANVAS_TEST_URL, u"HTMLCanvasElement.toDataURL", u"call",
     u"", None, None)
}

WEBRTC_TEST_URL = u"%s/webrtc_localip.html" % utilities.BASE_TEST_URL

WEBRTC_CALLS = {
    (WEBRTC_TEST_URL, u'RTCPeerConnection.createDataChannel',
     u'get', u'FUNCTION', None, None),
    (WEBRTC_TEST_URL, u'RTCPeerConnection.createDataChannel',
     u'call', u'', 0, u''),
    (WEBRTC_TEST_URL, u'RTCPeerConnection.createDataChannel',
     u'call', u'', 1, u'{"reliable":false}'),
    (WEBRTC_TEST_URL, u'RTCPeerConnection.onicecandidate',
     u'set', u'FUNCTION', None, None),
    (WEBRTC_TEST_URL, u'RTCPeerConnection.createOffer',
     u'get', u'FUNCTION', None, None),
    (WEBRTC_TEST_URL, u'RTCPeerConnection.createOffer',
     u'call', u'', 0, u'FUNCTION'),
    (WEBRTC_TEST_URL, u'RTCPeerConnection.createOffer',
     u'call', u'', 1, u'FUNCTION'),
    (WEBRTC_TEST_URL, u'RTCPeerConnection.setLocalDescription',
     u'get', u'FUNCTION', None, None),
}

# we expect these strings to be present in the WebRTC SDP
WEBRTC_SDP_OFFER_STRINGS = ("a=ice-options",
                            "o=mozilla...THIS_IS_SDPARTA",
                            "IN IP4",
                            "a=fingerprint:sha-256",
                            "a=ice-options:",
                            "a=msid-semantic",
                            "m=application",
                            "a=sendrecv",
                            "a=ice-pwd:",
                            "a=ice-ufrag:",
                            "a=mid:sdparta",
                            "a=sctpmap:",
                            "a=setup:",
                            "a=ssrc:",
                            "cname:")

# AudioContext and AudioNode symbols we expect from our test script
AUDIO_SYMBOLS = {
    u"AudioContext.createOscillator",
    u"AudioContext.createAnalyser",
    u"AudioContext.createGain",
    u"AudioContext.createScriptProcessor",
    u"GainNode.gain",
    u"OscillatorNode.type",
    u"OscillatorNode.connect",
    u"AnalyserNode.connect",
    u"ScriptProcessorNode.connect",
    u"AudioContext.destination",
    u"GainNode.connect",
    u"ScriptProcessorNode.onaudioprocess",
    u"OscillatorNode.start",
    u"AnalyserNode.frequencyBinCount",
    u"AnalyserNode.getFloatFrequencyData",
    u"AnalyserNode.disconnect",
    u"ScriptProcessorNode.disconnect",
    u"GainNode.disconnect",
    u"OscillatorNode.stop"
}

JS_STACK_TEST_URL = u"%s/js_call_stack.html" % utilities.BASE_TEST_URL
JS_STACK_TEST_SCRIPT_URL = u"%s/stack.js" % utilities.BASE_TEST_URL

JS_STACK_CALLS = {
    (JS_STACK_TEST_URL, u'1', u'1', u'', u'line 10 > eval', u'',
     u'window.navigator.appName', u'get'),
    (JS_STACK_TEST_SCRIPT_URL, u'3', u'5', u'js_check_navigator', u'', u'',
     u'window.navigator.userAgent', u'get'),
    (JS_STACK_TEST_SCRIPT_URL, u'1', u'1', u'', u'line 4 > eval', u'',
     u'window.navigator.platform', u'get'),
    (JS_STACK_TEST_SCRIPT_URL, u'1', u'1', u'', u'line 11 > eval', u'',
     u'window.navigator.buildID', u'get'),
    (JS_STACK_TEST_SCRIPT_URL, u'1', u'1', u'anonymous', u'line 14 > Function',
     u'', u'window.navigator.appVersion', u'get'),
    (JS_STACK_TEST_URL, u'7', u'9', u'check_navigator', u'', u'',
     u'window.navigator.userAgent', u'get'),
    (JS_STACK_TEST_URL, u'1', u'1', u'', u'line 8 > eval', u'',
     u'window.navigator.appCodeName', u'get')
}

JS_COOKIE_TEST_URL = u'%s/js_cookie.html' % utilities.BASE_TEST_URL

DOCUMENT_COOKIE_READ = (
    JS_COOKIE_TEST_URL,
    u'8',
    u'9',
    u'set_cookie',
    u'',
    u'set_cookie@' + JS_COOKIE_TEST_URL + ':8:9'
    '\nonload@' + JS_COOKIE_TEST_URL + ':1:1',
    u'window.document.cookie', u'get',
    u'test_cookie=Test-0123456789')

DOCUMENT_COOKIE_WRITE = (
    JS_COOKIE_TEST_URL,
    u'7',
    u'9',
    u'set_cookie',
    u'',
    u'set_cookie@' + JS_COOKIE_TEST_URL + ':7:9'
    '\nonload@' + JS_COOKIE_TEST_URL + ':1:1',
    u'window.document.cookie', u'set',
    u'test_cookie=Test-0123456789; '
    'expires=Tue, 31 Dec 2030 00:00:00 UTC; path=/')

DOCUMENT_COOKIE_READ_WRITE = set([DOCUMENT_COOKIE_READ,
                                  DOCUMENT_COOKIE_WRITE])


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
        assert PROPERTIES == observed_symbols

    def test_canvas_fingerprinting(self):
        db = self.visit('/canvas_fingerprinting.html')
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_rows = set()
        for item in rows:
            observed_rows.add(item)
        assert CANVAS_CALLS == observed_rows

    def test_extension_gets_correct_visit_id(self):
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)

        url_a = utilities.BASE_TEST_URL + '/simple_a.html'
        url_b = utilities.BASE_TEST_URL + '/simple_b.html'

        manager.get(url_a)
        manager.get(url_b)
        manager.close()
        qry_res = db_utils.query_db(
            manager_params['db'],
            "SELECT visit_id, site_url FROM site_visits"
        )

        # Construct dict mapping site_url to visit_id
        visit_ids = dict()
        for row in qry_res:
            visit_ids[row[1]] = row[0]

        simple_a_visit_id = db_utils.query_db(
            manager_params['db'],
            "SELECT visit_id FROM javascript WHERE "
            "symbol=?", ("window.navigator.userAgent",)
        )

        simple_b_visit_id = db_utils.query_db(
            manager_params['db'],
            "SELECT visit_id FROM javascript WHERE "
            "symbol=?", ("window.navigator.platform",)
        )

        assert visit_ids[url_a] == simple_a_visit_id[0][0]
        assert visit_ids[url_b] == simple_b_visit_id[0][0]

    def check_webrtc_sdp_offer(self, sdp_str):
        """Make sure the SDP offer includes expected fields/strings.

        SDP offer contains randomly generated strings (e.g. GUID). That's why
        we don't expect a fixed string but only check the presence of certain
        protocol fields.
        """
        for expected_str in WEBRTC_SDP_OFFER_STRINGS:
            assert expected_str in sdp_str

    def test_webrtc_localip(self):
        db = self.visit('/webrtc_localip.html')
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_rows = set()
        for item in rows:
            if (item[1] == "RTCPeerConnection.setLocalDescription" and
                    item[2] == 'call' and item[4] == 0):
                sdp_offer = item[5]
                self.check_webrtc_sdp_offer(sdp_offer)
            else:
                observed_rows.add(item)
        assert WEBRTC_CALLS == observed_rows

    @pytest.mark.skipif(
        "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        reason='Flaky on Travis CI')
    def test_audio_fingerprinting(self):
        db = self.visit('/audio_fingerprinting.html')
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_symbols = set()
        for item in rows:
            observed_symbols.add(item[1])
        assert AUDIO_SYMBOLS == observed_symbols

    def test_js_call_stack(self):
        db = self.visit('/js_call_stack.html')
        # Check that all stack info are recorded
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        observed_rows = set()
        for item in rows:
            observed_rows.add(item[3:11])
        assert JS_STACK_CALLS == observed_rows

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
        assert captured_cookie_calls == DOCUMENT_COOKIE_READ_WRITE
