import os
import time
from datetime import datetime
from pathlib import Path
from sqlite3 import Row
from typing import List, Optional, Tuple

import pytest
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By

from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket
from openwpm.utilities import db_utils

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


def expected_canvas_calls(canvas_test_url: str) -> set:
    return {
        (canvas_test_url, "CanvasRenderingContext2D.fillStyle", "set", "#f60", None),
        (
            canvas_test_url,
            "CanvasRenderingContext2D.textBaseline",
            "set",
            "alphabetic",
            None,
        ),
        (canvas_test_url, "CanvasRenderingContext2D.textBaseline", "set", "top", None),
        (
            canvas_test_url,
            "CanvasRenderingContext2D.font",
            "set",
            "14px 'Arial'",
            None,
        ),
        (canvas_test_url, "CanvasRenderingContext2D.fillStyle", "set", "#069", None),
        (
            canvas_test_url,
            "CanvasRenderingContext2D.fillStyle",
            "set",
            "rgba(102, 204, 0, 0.7)",
            None,
        ),
        (canvas_test_url, "HTMLCanvasElement.getContext", "call", "", '["2d"]'),
        (
            canvas_test_url,
            "CanvasRenderingContext2D.fillRect",
            "call",
            "",
            "[125,1,62,20]",
        ),
        (canvas_test_url, "HTMLCanvasElement.toDataURL", "call", "", None),
        (
            canvas_test_url,
            "CanvasRenderingContext2D.fillText",
            "call",
            "",
            '["BrowserLeaks,com <canvas> 1.0",4,17]',
        ),
        (
            canvas_test_url,
            "CanvasRenderingContext2D.fillText",
            "call",
            "",
            '["BrowserLeaks,com <canvas> 1.0",2,15]',
        ),
    }


def expected_webrtc_calls(webrtc_test_url: str) -> set:
    return {
        (
            webrtc_test_url,
            "RTCPeerConnection.createOffer",
            "call",
            "",
            '["FUNCTION","FUNCTION"]',
        ),
        (webrtc_test_url, "RTCPeerConnection.createDataChannel", "call", "", '[""]'),
        (
            webrtc_test_url,
            "RTCPeerConnection.createDataChannel",
            "call",
            "",
            '["","{\\"reliable\\":false}"]',
        ),
        (webrtc_test_url, "RTCPeerConnection.onicecandidate", "set", "FUNCTION", None),
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


def expected_js_stack_calls(base_url: str) -> set:
    js_stack_test_url = base_url + "/js_call_stack.html"
    js_stack_test_script_url = base_url + "/stack.js"
    return {
        (
            js_stack_test_url,
            "1",
            "1",
            "",
            "line 10 > eval",
            "",
            "window.navigator.appName",
            "get",
        ),
        (
            js_stack_test_script_url,
            "3",
            "17",
            "js_check_navigator",
            "",
            "",
            "window.navigator.userAgent",
            "get",
        ),
        (
            js_stack_test_script_url,
            "1",
            "1",
            "",
            "line 4 > eval",
            "",
            "window.navigator.platform",
            "get",
        ),
        (
            js_stack_test_script_url,
            "1",
            "1",
            "",
            "line 11 > eval",
            "",
            "window.navigator.buildID",
            "get",
        ),
        (
            js_stack_test_script_url,
            "3",
            "1",
            "anonymous",
            "line 14 > Function",
            "",
            "window.navigator.appVersion",
            "get",
        ),
        (
            js_stack_test_url,
            "7",
            "21",
            "check_navigator",
            "",
            "",
            "window.navigator.userAgent",
            "get",
        ),
        (
            js_stack_test_url,
            "1",
            "1",
            "",
            "line 8 > eval",
            "",
            "window.navigator.appCodeName",
            "get",
        ),
    }


def expected_document_cookie_read_write(base_url: str) -> set:
    js_cookie_test_url = base_url + "/js_cookie.html"
    document_cookie_read = (
        js_cookie_test_url,
        "8",
        "21",
        "set_cookie",
        "",
        "set_cookie@" + js_cookie_test_url + ":8:21"
        "\nonload@" + js_cookie_test_url + ":1:1",
        "window.document.cookie",
        "get",
        "test_cookie=Test-0123456789",
    )
    document_cookie_write = (
        js_cookie_test_url,
        "7",
        "9",
        "set_cookie",
        "",
        "set_cookie@" + js_cookie_test_url + ":7:9"
        "\nonload@" + js_cookie_test_url + ":1:1",
        "window.document.cookie",
        "set",
        "test_cookie=Test-0123456789; " "expires=Tue, 31 Dec 2030 00:00:00 UTC; path=/",
    )
    return {document_cookie_read, document_cookie_write}


class TestExtension(OpenWPMTest):
    def get_config(
        self, data_dir: Optional[Path] = None
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0].js_instrument = True
        return manager_params, browser_params

    def test_property_enumeration(self) -> None:
        test_url = self.server.base + "/property_enumeration.html"
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
        canvas_test_url = self.server.base + "/canvas_fingerprinting.html"
        assert expected_canvas_calls(canvas_test_url) == observed_rows

    def test_extension_gets_correct_visit_id(self) -> None:
        url_a = self.server.base + "/simple_a.html"
        url_b = self.server.base + "/simple_b.html"
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
        webrtc_test_url = self.server.base + "/webrtc_localip.html"
        assert expected_webrtc_calls(webrtc_test_url) == observed_rows

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
        assert expected_js_stack_calls(self.server.base) == observed_rows

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
        db = self.visit(self.server.base + "/js_cookie.html")
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
        assert captured_cookie_calls == expected_document_cookie_read_write(
            self.server.base
        )


class ClickButtonCommand(BaseCommand):
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        button = webdriver.find_element(By.ID, "play")
        button.click()
        time.sleep(5)


@pytest.mark.skipif(
    "CI" in os.environ and os.environ["CI"] == "true",
    reason="Flaky on CI",
)
def test_audio_fingerprinting(default_params, task_manager_creator, server):
    for browser_params in default_params[1]:
        browser_params.js_instrument = True

    tm, db = task_manager_creator(default_params)
    cs = CommandSequence("/audio_fingerprinting.html")
    cs.append_command(GetCommand(server.base + "/audio_fingerprinting.html", 0))
    cs.append_command(ClickButtonCommand())
    tm.execute_command_sequence(cs)

    tm.close()
    # Check that all calls and methods are recorded
    rows = db_utils.get_javascript_entries(db)
    observed_symbols = set()
    for item in rows:
        observed_symbols.add(item[1])
    assert AUDIO_SYMBOLS == observed_symbols
