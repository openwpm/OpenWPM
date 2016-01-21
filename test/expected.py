""" Contains lists of expected data and or rows for tests """

# Navigator and Screen properties
properties = {
    "window.navigator.appCodeName",
    "window.navigator.appMinorVersion",
    "window.navigator.appName",
    "window.navigator.appVersion",
    "window.navigator.buildID",
    "window.navigator.cookieEnabled",
    "window.navigator.cpuClass",
    "window.navigator.doNotTrack",
    "window.navigator.geolocation",
    "window.navigator.language",
    "window.navigator.languages",
    "window.navigator.onLine",
    "window.navigator.opsProfile",
    "window.navigator.oscpu",
    "window.navigator.platform",
    "window.navigator.product",
    "window.navigator.productSub",
    "window.navigator.systemLanguage",
    "window.navigator.userAgent",
    "window.navigator.userLanguage",
    "window.navigator.userProfile",
    "window.navigator.vendorSub",
    "window.navigator.vendor",
    "window.screen.pixelDepth",
    "window.screen.colorDepth"}

# Canvas Fingerprinting DB calls and property sets
canvas = {
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"HTMLCanvasElement.getContext",u"call",u"",0,u"2d"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.textBaseline",u"set",u"top", None, None),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.font",u"set",u"14px 'Arial'", None, None),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.textBaseline",u"set",u"alphabetic", None, None),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillStyle",u"set",u"#f60", None, None),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillRect",u"call",u"",0,u"125"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillRect",u"call",u"",1,u"1"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillRect",u"call",u"",2,u"62"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillRect",u"call",u"",3,u"20"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillStyle",u"set",u"#069", None, None),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillText",u"call",u"",0,u"BrowserLeaks,com <canvas> 1.0"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillText",u"call",u"",1,u"2"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillText",u"call",u"",2,u"15"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillStyle",u"set",u"rgba(102, 204, 0, 0.7)", None, None),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillText",u"call",u"",0,u"BrowserLeaks,com <canvas> 1.0"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillText",u"call",u"",1,u"4"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"CanvasRenderingContext2D.fillText",u"call",u"",2,u"17"),
    (u"http://localhost:8000/test_pages/canvas_fingerprinting.html",u"HTMLCanvasElement.toDataURL",u"call",u"", None, None)
}

adblockplus = {
        "http://localhost:8000/abp/adblock_plus_test.html",
        "http://localhost:8000/favicon.ico"}
