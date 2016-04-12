""" Contains lists of expected data and or rows for tests """
from utilities import BASE_TEST_URL, BASE_TEST_URL_DOMAIN, BASE_TEST_URL_NOPATH

# Navigator and Screen properties
properties = {
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
    "window.screen.colorDepth"}

# Canvas Fingerprinting DB calls and property sets
CANVAS_TEST_URL = u"%s/canvas_fingerprinting.html" % BASE_TEST_URL

canvas = {(CANVAS_TEST_URL,
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
          (CANVAS_TEST_URL, u"HTMLCanvasElement.toDataURL", u"call",
           u"", None, None)
          }

adblockplus = {
    "%s/abp/adblock_plus_test.html" % BASE_TEST_URL,
    # favicon request is made to URL without a path
    "%s/favicon.ico" % BASE_TEST_URL_NOPATH}

js_cookie = (u'%s/js_cookie.html' % BASE_TEST_URL,
             u'%s' % BASE_TEST_URL_DOMAIN,
             u'test_cookie',
             u'Test-0123456789',
             u'%s' % BASE_TEST_URL_DOMAIN,
             u'/')

lso_content = [u'%s/lso/setlso.html?lso_test_key=test_key&lso_test_value=REPLACEME' % BASE_TEST_URL,  # noqa
               u'localtest.me',
               u'FlashCookie.sol',
               u'localtest.me/FlashCookie.sol',
               u'test_key',
               u'REPLACEME']

WEBRTC_TEST_URL = u"%s/webrtc_localip.html" % BASE_TEST_URL

webrtc_calls = ((WEBRTC_TEST_URL, u'RTCPeerConnection.createDataChannel',
                 u'call', u'', 0, u''),
                (WEBRTC_TEST_URL, u'RTCPeerConnection.createDataChannel',
                 u'call', u'', 1, u'{"reliable":false}'),
                (WEBRTC_TEST_URL, u'RTCPeerConnection.onicecandidate',
                 u'set', u'FUNCTION', None, None),
                (WEBRTC_TEST_URL, u'RTCPeerConnection.createDataChannel',
                 u'call', u'', 0, u''),
                (WEBRTC_TEST_URL, u'RTCPeerConnection.createOffer',
                 u'call', u'', 0, u'FUNCTION'),
                (WEBRTC_TEST_URL, u'RTCPeerConnection.createOffer',
                 u'call', u'', 1, u'FUNCTION'))

# we expect these strings to be present in the WebRTC SDP
webrtc_sdp_offer_strings = ("a=ice-options",
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

SET_PROP_TEST_PAGE = u'%s/set_property/set_property.js' % BASE_TEST_URL
set_property = [(SET_PROP_TEST_PAGE,
                 u'5', u'3',
                 u'set_window_name@%s:5:3\n'
                 '@%s:8:1\n' % (SET_PROP_TEST_PAGE, SET_PROP_TEST_PAGE),
                 u'window.HTMLFormElement.action',
                 u'set', u'TEST-ACTION', None, None)]
