import os
from datetime import datetime
from pathlib import Path
from sqlite3 import Row
from typing import List, Tuple

import pytest

from openwpm.config import BrowserParams, ManagerParams
from openwpm.utilities import db_utils

from . import utilities
from .openwpmtest import OpenWPMTest

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
    "window.screen.colorDepth",
}

# Canvas Fingerprinting DB calls and property sets
CANVAS_TEST_URL = "%s/canvas_fingerprinting.html" % utilities.BASE_TEST_URL

CANVAS_CALLS = {
    (CANVAS_TEST_URL, "CanvasRenderingContext2D.fillStyle", "set", "#f60", None),
    (
        CANVAS_TEST_URL,
        "CanvasRenderingContext2D.textBaseline",
        "set",
        "alphabetic",
        None,
    ),
    (CANVAS_TEST_URL, "CanvasRenderingContext2D.textBaseline", "set", "top", None),
    (CANVAS_TEST_URL, "CanvasRenderingContext2D.font", "set", "14px 'Arial'", None),
    (CANVAS_TEST_URL, "CanvasRenderingContext2D.fillStyle", "set", "#069", None),
    (
        CANVAS_TEST_URL,
        "CanvasRenderingContext2D.fillStyle",
        "set",
        "rgba(102, 204, 0, 0.7)",
        None,
    ),
    (CANVAS_TEST_URL, "HTMLCanvasElement.getContext", "call", "", '["2d"]'),
    (
        CANVAS_TEST_URL,
        "CanvasRenderingContext2D.fillRect",
        "call",
        "",
        "[125,1,62,20]",
    ),
    (CANVAS_TEST_URL, "HTMLCanvasElement.toDataURL", "call", "", None),
    (
        CANVAS_TEST_URL,
        "CanvasRenderingContext2D.fillText",
        "call",
        "",
        '["BrowserLeaks,com <canvas> 1.0",4,17]',
    ),
    (
        CANVAS_TEST_URL,
        "CanvasRenderingContext2D.fillText",
        "call",
        "",
        '["BrowserLeaks,com <canvas> 1.0",2,15]',
    ),
}

WEBRTC_TEST_URL = "%s/webrtc_localip.html" % utilities.BASE_TEST_URL

WEBRTC_CALLS = {
    (
        WEBRTC_TEST_URL,
        "RTCPeerConnection.createOffer",
        "call",
        "",
        '["FUNCTION","FUNCTION"]',
    ),
    (WEBRTC_TEST_URL, "RTCPeerConnection.createDataChannel", "call", "", '[""]'),
    (
        WEBRTC_TEST_URL,
        "RTCPeerConnection.createDataChannel",
        "call",
        "",
        '["","{\\"reliable\\":false}"]',
    ),
    (WEBRTC_TEST_URL, "RTCPeerConnection.onicecandidate", "set", "FUNCTION", None),
}

# we expect these strings to be present in the WebRTC SDP
WEBRTC_SDP_OFFER_STRINGS = (
    "a=ice-options",
    "o=mozilla...THIS_IS_SDPARTA",
    "IN IP4",
    "a=fingerprint:sha-256",
    "a=ice-options:",
    "a=msid-semantic",
    "m=application",
    "a=sendrecv",
    "a=ice-pwd:",
    "a=ice-ufrag:",
    "a=mid:0",
    "a=sctp-port:",
    "a=setup:",
)

# AudioContext and AudioNode symbols we expect from our test script
AUDIO_SYMBOLS = {
    "AudioContext.createOscillator",
    "AudioContext.createAnalyser",
    "AudioContext.createGain",
    "AudioContext.createScriptProcessor",
    "GainNode.gain",
    "OscillatorNode.type",
    "OscillatorNode.connect",
    "AnalyserNode.connect",
    "ScriptProcessorNode.connect",
    "AudioContext.destination",
    "GainNode.connect",
    "ScriptProcessorNode.onaudioprocess",
    "OscillatorNode.start",
    "AnalyserNode.frequencyBinCount",
    "AnalyserNode.getFloatFrequencyData",
    "AnalyserNode.disconnect",
    "ScriptProcessorNode.disconnect",
    "GainNode.disconnect",
    "OscillatorNode.stop",
}

JS_STACK_TEST_URL = "%s/js_call_stack.html" % utilities.BASE_TEST_URL
JS_STACK_TEST_SCRIPT_URL = "%s/stack.js" % utilities.BASE_TEST_URL

JS_STACK_CALLS = {
    (
        JS_STACK_TEST_URL,
        "1",
        "1",
        "",
        "line 10 > eval",
        "",
        "window.navigator.appName",
        "get",
    ),
    (
        JS_STACK_TEST_SCRIPT_URL,
        "3",
        "5",
        "js_check_navigator",
        "",
        "",
        "window.navigator.userAgent",
        "get",
    ),
    (
        JS_STACK_TEST_SCRIPT_URL,
        "1",
        "1",
        "",
        "line 4 > eval",
        "",
        "window.navigator.platform",
        "get",
    ),
    (
        JS_STACK_TEST_SCRIPT_URL,
        "1",
        "1",
        "",
        "line 11 > eval",
        "",
        "window.navigator.buildID",
        "get",
    ),
    (
        JS_STACK_TEST_SCRIPT_URL,
        "3",
        "1",
        "anonymous",
        "line 14 > Function",
        "",
        "window.navigator.appVersion",
        "get",
    ),
    (
        JS_STACK_TEST_URL,
        "7",
        "9",
        "check_navigator",
        "",
        "",
        "window.navigator.userAgent",
        "get",
    ),
    (
        JS_STACK_TEST_URL,
        "1",
        "1",
        "",
        "line 8 > eval",
        "",
        "window.navigator.appCodeName",
        "get",
    ),
}

JS_COOKIE_TEST_URL = "%s/js_cookie.html" % utilities.BASE_TEST_URL

DOCUMENT_COOKIE_READ = (
    JS_COOKIE_TEST_URL,
    "8",
    "9",
    "set_cookie",
    "",
    "set_cookie@" + JS_COOKIE_TEST_URL + ":8:9"
    "\nonload@" + JS_COOKIE_TEST_URL + ":1:1",
    "window.document.cookie",
    "get",
    "test_cookie=Test-0123456789",
)

DOCUMENT_COOKIE_WRITE = (
    JS_COOKIE_TEST_URL,
    "7",
    "9",
    "set_cookie",
    "",
    "set_cookie@" + JS_COOKIE_TEST_URL + ":7:9"
    "\nonload@" + JS_COOKIE_TEST_URL + ":1:1",
    "window.document.cookie",
    "set",
    "test_cookie=Test-0123456789; " "expires=Tue, 31 Dec 2030 00:00:00 UTC; path=/",
)

DOCUMENT_COOKIE_READ_WRITE = {DOCUMENT_COOKIE_READ, DOCUMENT_COOKIE_WRITE}


class TestExtension(OpenWPMTest):
    def get_config(
        self, data_dir: Path = None
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0].js_instrument = True
        return manager_params, browser_params

    def test_property_enumeration(self) -> None:
        test_url = utilities.BASE_TEST_URL + "/property_enumeration.html"
        db = self.visit(test_url)
        rows = db_utils.query_db(db, "SELECT script_url, symbol FROM javascript")
        observed_symbols = set()
        for script_url, symbol in rows:
            assert script_url == test_url
            observed_symbols.add(symbol)
        assert PROPERTIES == observed_symbols

    def test_canvas_fingerprinting(self) -> None:
        db = self.visit("/canvas_fingerprinting.html")
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_rows = set()
        for row in rows:
            assert isinstance(row, Row)
            item = (
                row["script_url"],
                row["symbol"],
                row["operation"],
                row["value"],
                row["arguments"],
            )
            observed_rows.add(item)
        assert CANVAS_CALLS == observed_rows

    def test_extension_gets_correct_visit_id(self) -> None:
        url_a = utilities.BASE_TEST_URL + "/simple_a.html"
        url_b = utilities.BASE_TEST_URL + "/simple_b.html"
        self.visit(url_a)
        db = self.visit(url_b)

        qry_res = db_utils.query_db(db, "SELECT visit_id, site_url FROM site_visits")

        # Construct dict mapping site_url to visit_id
        visit_ids = dict()
        for row in qry_res:
            visit_ids[row[1]] = row[0]

        simple_a_visit_id = db_utils.query_db(
            db,
            "SELECT visit_id FROM javascript WHERE symbol=?",
            ("window.navigator.userAgent",),
        )

        simple_b_visit_id = db_utils.query_db(
            db,
            "SELECT visit_id FROM javascript WHERE symbol=?",
            ("window.navigator.platform",),
        )

        assert visit_ids[url_a] == simple_a_visit_id[0][0]
        assert visit_ids[url_b] == simple_b_visit_id[0][0]

    def check_webrtc_sdp_offer(self, sdp_str: str) -> None:
        """Make sure the SDP offer includes expected fields/strings.

        SDP offer contains randomly generated strings (e.g. GUID). That's why
        we don't expect a fixed string but only check the presence of certain
        protocol fields.
        """
        for expected_str in WEBRTC_SDP_OFFER_STRINGS:
            assert expected_str in sdp_str

    def test_webrtc_localip(self) -> None:
        db = self.visit("/webrtc_localip.html")
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_rows = set()
        for row in rows:
            assert isinstance(row, Row)
            if row["symbol"] == "RTCPeerConnection.setLocalDescription" and (
                row["operation"] == "call"
            ):
                sdp_offer = row["arguments"]
                self.check_webrtc_sdp_offer(sdp_offer)
            else:
                item = (
                    row["script_url"],
                    row["symbol"],
                    row["operation"],
                    row["value"],
                    row["arguments"],
                )
                observed_rows.add(item)
        assert WEBRTC_CALLS == observed_rows

    @pytest.mark.skipif(
        "CI" in os.environ and os.environ["CI"] == "true",
        reason="Flaky on CI",
    )
    def test_audio_fingerprinting(self):
        db = self.visit("/audio_fingerprinting.html")
        # Check that all calls and methods are recorded
        rows = db_utils.get_javascript_entries(db)
        observed_symbols = set()
        for item in rows:
            observed_symbols.add(item[1])
        assert AUDIO_SYMBOLS == observed_symbols

    def test_js_call_stack(self):
        db = self.visit("/js_call_stack.html")
        # Check that all stack info are recorded
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        observed_rows = set()
        for row in rows:
            item = (
                row["script_url"],
                row["script_line"],
                row["script_col"],
                row["func_name"],
                row["script_loc_eval"],
                row["call_stack"],
                row["symbol"],
                row["operation"],
            )
            observed_rows.add(item)
        assert JS_STACK_CALLS == observed_rows

    def test_js_time_stamp(self):
        # Check that timestamp is recorded correctly for the javascript table
        MAX_TIMEDELTA = 60  # max time diff in seconds
        db = self.visit("/js_call_stack.html")
        utc_now = datetime.utcnow()  # OpenWPM stores timestamp in UTC time
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        assert len(rows)  # make sure we have some JS events captured
        for row in rows:
            js_time = datetime.strptime(row["time_stamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
            # compare UTC now and the timestamp recorded at the visit
            assert (utc_now - js_time).seconds < MAX_TIMEDELTA
        assert not db_utils.any_command_failed(db)

    def test_document_cookie_instrumentation(self):
        db = self.visit(utilities.BASE_TEST_URL + "/js_cookie.html")
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        captured_cookie_calls = set()
        for row in rows:
            item = (
                row["script_url"],
                row["script_line"],
                row["script_col"],
                row["func_name"],
                row["script_loc_eval"],
                row["call_stack"],
                row["symbol"],
                row["operation"],
                row["value"],
            )
            captured_cookie_calls.add(item)
        assert captured_cookie_calls == DOCUMENT_COOKIE_READ_WRITE
