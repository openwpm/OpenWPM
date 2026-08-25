//#region src/signals/webdriver.ts
function e() {
	return navigator.webdriver;
}
//#endregion
//#region src/signals/userAgent.ts
function t() {
	return navigator.userAgent;
}
//#endregion
//#region src/signals/platform.ts
function n() {
	return navigator.platform;
}
//#endregion
//#region src/signals/utils.ts
var r = "ERROR", i = "INIT", a = "SKIPPED", o = "high";
function s(e) {
	if (typeof e == "string" && e.length !== 0 && e !== "NA" && e !== "ERROR" && e !== "SKIPPED" && e !== "INIT") return e;
}
function c(...e) {
	return e.map(s).filter((e) => e !== void 0);
}
function l(e) {
	let t = 0;
	for (let n = 0, r = e.length; n < r; n++) {
		let r = e.charCodeAt(n);
		t = (t << 5) - t + r, t |= 0;
	}
	return t.toString(16).padStart(8, "0");
}
function u(e, t) {
	for (let n in e) e[n] = t;
}
function d() {
	return navigator.buildID === "20181001000000";
}
//#endregion
//#region src/signals/cdp.ts
function f() {
	try {
		let e = !1, t = Error.prepareStackTrace;
		return Error.prepareStackTrace = function() {
			return e = !0, t;
		}, console.log(/* @__PURE__ */ Error("")), e;
	} catch {
		return r;
	}
}
//#endregion
//#region src/signals/webGL.ts
function p() {
	let e = {
		vendor: i,
		renderer: i
	};
	if (d()) return u(e, "NA"), e;
	try {
		var t = document.createElement("canvas"), n = t.getContext("webgl") || t.getContext("experimental-webgl");
		n.getSupportedExtensions().indexOf("WEBGL_debug_renderer_info") >= 0 ? (e.vendor = n.getParameter(n.getExtension("WEBGL_debug_renderer_info").UNMASKED_VENDOR_WEBGL), e.renderer = n.getParameter(n.getExtension("WEBGL_debug_renderer_info").UNMASKED_RENDERER_WEBGL)) : u(e, "NA");
	} catch {
		u(e, r);
	}
	return e;
}
//#endregion
//#region src/signals/playwright.ts
function m() {
	return "__pwInitScripts" in window || "__playwright__binding__" in window;
}
//#endregion
//#region src/signals/cpuCount.ts
function h() {
	return navigator.hardwareConcurrency || "NA";
}
//#endregion
//#region src/signals/maths.ts
function g() {
	let e = [];
	return [
		"E",
		"LN10",
		"LN2",
		"LOG10E",
		"LOG2E",
		"PI",
		"SQRT1_2",
		"SQRT2"
	].forEach(function(t) {
		try {
			e.push(Math[t]);
		} catch {
			e.push(-1);
		}
	}), [
		"tan",
		"sin",
		"exp",
		"atan",
		"acosh",
		"asinh",
		"atanh",
		"expm1",
		"log1p",
		"sinh"
	].forEach(function(t) {
		try {
			e.push(Math[t](.123456789));
		} catch {
			e.push(-1);
		}
	}), "sumPrecise" in Math ? e.push(Math.sumPrecise([
		0x56bc75e2d63100000,
		.1,
		-0x56bc75e2d63100000
	])) : e.push(-1), l(e.map(String).join(","));
}
//#endregion
//#region src/signals/memory.ts
function _() {
	return navigator.deviceMemory || "NA";
}
//#endregion
//#region src/signals/etsl.ts
function v() {
	return eval.toString().length;
}
//#endregion
//#region src/signals/internationalization.ts
function ee() {
	let e = {
		timezone: i,
		localeLanguage: i
	};
	try {
		if (typeof Intl < "u" && Intl.DateTimeFormat !== void 0) {
			let t = Intl.DateTimeFormat().resolvedOptions();
			e.timezone = t.timeZone, e.localeLanguage = t.locale;
		} else e.timezone = "NA", e.localeLanguage = "NA";
	} catch {
		e.timezone = r, e.localeLanguage = r;
	}
	return e;
}
//#endregion
//#region src/signals/screenResolution.ts
function te() {
	return {
		width: window.screen.width,
		height: window.screen.height,
		pixelDepth: window.screen.pixelDepth,
		colorDepth: window.screen.colorDepth,
		availableWidth: window.screen.availWidth,
		availableHeight: window.screen.availHeight,
		innerWidth: window.innerWidth,
		innerHeight: window.innerHeight,
		hasMultipleDisplays: screen.isExtended === void 0 ? "NA" : screen.isExtended
	};
}
//#endregion
//#region src/signals/languages.ts
function ne() {
	return {
		languages: navigator.languages,
		language: navigator.language
	};
}
//#endregion
//#region src/signals/webgpu.ts
async function re() {
	let e = {
		vendor: i,
		architecture: i,
		device: i,
		description: i
	};
	if ("gpu" in navigator) try {
		let t = await navigator.gpu.requestAdapter();
		t && (e.vendor = t.info.vendor, e.architecture = t.info.architecture, e.device = t.info.device, e.description = t.info.description);
	} catch {
		u(e, r);
	}
	else u(e, "NA");
	return e;
}
//#endregion
//#region src/signals/seleniumProperties.ts
function ie() {
	let e = [
		"__driver_evaluate",
		"__webdriver_evaluate",
		"__selenium_evaluate",
		"__fxdriver_evaluate",
		"__driver_unwrapped",
		"__webdriver_unwrapped",
		"__selenium_unwrapped",
		"__fxdriver_unwrapped",
		"_Selenium_IDE_Recorder",
		"_selenium",
		"calledSelenium",
		"$cdc_asdjflasutopfhvcZLmcfl_",
		"$chrome_asyncScriptInfo",
		"__$webdriverAsyncExecutor",
		"webdriver",
		"__webdriverFunc",
		"domAutomation",
		"domAutomationController",
		"__lastWatirAlert",
		"__lastWatirConfirm",
		"__lastWatirPrompt",
		"__webdriver_script_fn",
		"_WEBDRIVER_ELEM_CACHE"
	], t = !1;
	for (let n = 0; n < e.length; n++) if (e[n] in window) {
		t = !0;
		break;
	}
	return t = t || !!document.__webdriver_script_fn || !!window.domAutomation || !!window.domAutomationController, t;
}
//#endregion
//#region src/signals/webdriverWritable.ts
function ae() {
	try {
		let e = "webdriver", t = window.navigator;
		if (!t[e] && !t.hasOwnProperty(e)) {
			t[e] = 1;
			let n = t[e] === 1;
			return delete t[e], n;
		}
		return !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/signals/highEntropyValues.ts
async function y() {
	let e = window.navigator, t = {
		architecture: i,
		bitness: i,
		brands: i,
		mobile: i,
		model: i,
		platform: i,
		platformVersion: i,
		uaFullVersion: i
	};
	if ("userAgentData" in e) try {
		let n = await e.userAgentData.getHighEntropyValues([
			"architecture",
			"bitness",
			"brands",
			"mobile",
			"model",
			"platform",
			"platformVersion",
			"uaFullVersion"
		]);
		t.architecture = n.architecture, t.bitness = n.bitness, t.brands = n.brands, t.mobile = n.mobile, t.model = n.model, t.platform = n.platform, t.platformVersion = n.platformVersion, t.uaFullVersion = n.uaFullVersion;
	} catch {
		u(t, r);
	}
	else u(t, "NA");
	return t;
}
//#endregion
//#region src/signals/plugins.ts
function b() {
	if (!navigator.plugins) return !1;
	let e = typeof navigator.plugins.toString == "function" ? navigator.plugins.toString() : navigator.plugins.constructor && typeof navigator.plugins.constructor.toString == "function" ? navigator.plugins.constructor.toString() : typeof navigator.plugins;
	return e === "[object PluginArray]" || e === "[object MSPluginsCollection]" || e === "[object HTMLPluginsCollection]";
}
function x() {
	if (!navigator.plugins) return "NA";
	let e = [];
	for (let t = 0; t < navigator.plugins.length; t++) e.push(navigator.plugins[t].name);
	return l(e.join(","));
}
function S() {
	return navigator.plugins ? navigator.plugins.length : "NA";
}
function C() {
	if (!navigator.plugins) return "NA";
	try {
		return navigator.plugins[0] === navigator.plugins[0][0].enabledPlugin;
	} catch {
		return r;
	}
}
function w() {
	if (!navigator.plugins) return "NA";
	try {
		return navigator.plugins.item(4294967296) !== navigator.plugins[0];
	} catch {
		return r;
	}
}
function T() {
	let e = {
		isValidPluginArray: i,
		pluginCount: i,
		pluginNamesHash: i,
		pluginConsistency1: i,
		pluginOverflow: i
	};
	try {
		e.isValidPluginArray = b(), e.pluginCount = S(), e.pluginNamesHash = x(), e.pluginConsistency1 = C(), e.pluginOverflow = w();
	} catch {
		u(e, r);
	}
	return e;
}
//#endregion
//#region src/signals/multimediaDevices.ts
async function E() {
	return new Promise(async function(e) {
		var t = {
			audiooutput: 0,
			audioinput: 0,
			videoinput: 0
		};
		if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
			let i = await navigator.mediaDevices.enumerateDevices();
			if (i !== void 0) {
				for (var n = 0; n < i.length; n++) {
					var r = i[n].kind;
					t[r] = t[r] + 1;
				}
				return e({
					speakers: t.audiooutput,
					microphones: t.audioinput,
					webcams: t.videoinput
				});
			}
			return u(t, "NA"), e(t);
		}
		return u(t, "NA"), e(t);
	});
}
//#endregion
//#region src/signals/iframe.ts
function D() {
	let e = {
		webdriver: i,
		userAgent: i,
		platform: i,
		memory: i,
		cpuCount: i,
		language: i
	}, t = document.createElement("iframe"), n = !1;
	try {
		t.style.display = "none", t.src = "about:blank", document.body.appendChild(t), n = !0;
		let r = t.contentWindow?.navigator;
		e.webdriver = r.webdriver ?? !1, e.userAgent = r.userAgent ?? "NA", e.platform = r.platform ?? "NA", e.memory = r.deviceMemory ?? "NA", e.cpuCount = r.hardwareConcurrency ?? "NA", e.language = r.language ?? "NA";
	} catch {
		u(e, r);
	} finally {
		if (n) try {
			document.body.removeChild(t);
		} catch {}
	}
	return e;
}
//#endregion
//#region src/signals/worker.ts
async function O() {
	return new Promise((e) => {
		let t = {
			vendor: i,
			renderer: i,
			userAgent: i,
			language: i,
			platform: i,
			memory: i,
			cpuCount: i
		}, n = null, a = null, o = null, s = () => {
			o && clearTimeout(o), n && n.terminate(), a && URL.revokeObjectURL(a);
		};
		try {
			let i = new Blob(["var fingerprintWorker = {\n                userAgent: 'NA',\n                language: 'NA',\n                cpuCount: 'NA',\n                platform: 'NA',\n                memory: 'NA',\n                vendor: 'NA',\n                renderer: 'NA'\n            };\n            try {\n                fingerprintWorker.userAgent = navigator.userAgent;\n                fingerprintWorker.language = navigator.language;\n                fingerprintWorker.cpuCount = navigator.hardwareConcurrency;\n                fingerprintWorker.platform = navigator.platform;\n                if (typeof navigator.deviceMemory !== 'undefined') {\n                    fingerprintWorker.memory = navigator.deviceMemory;\n                }\n\n                try {\n                    if (typeof OffscreenCanvas === 'undefined') {\n                        fingerprintWorker.vendor = 'NA';\n                        fingerprintWorker.renderer = 'NA';\n                    } else {\n                        var canvas = new OffscreenCanvas(1, 1);\n                        var gl = canvas.getContext('webgl');\n                        var isFirefox = navigator.userAgent.indexOf('Firefox') !== -1;\n                        if (gl && !isFirefox) {\n                            var glExt = gl.getExtension('WEBGL_debug_renderer_info');\n                            if (glExt) {\n                                fingerprintWorker.vendor = gl.getParameter(glExt.UNMASKED_VENDOR_WEBGL);\n                                fingerprintWorker.renderer = gl.getParameter(glExt.UNMASKED_RENDERER_WEBGL);\n                            } else {\n                                fingerprintWorker.vendor = 'NA';\n                                fingerprintWorker.renderer = 'NA';\n                            }\n                        } else {\n                            fingerprintWorker.vendor = 'NA';\n                            fingerprintWorker.renderer = 'NA';\n                        }\n                    }\n                } catch (_) {\n                    fingerprintWorker.vendor = 'ERROR';\n                    fingerprintWorker.renderer = 'ERROR';\n                }\n                self.postMessage(fingerprintWorker);\n            } catch (e) {\n                self.postMessage(fingerprintWorker);\n            }"], { type: "application/javascript" });
			a = URL.createObjectURL(i), n = new Worker(a), o = window.setTimeout(() => {
				s(), u(t, r), e(t);
			}, 2e3), n.onmessage = function(n) {
				try {
					let e = (e) => e === void 0 ? "NA" : e;
					t.vendor = e(n.data.vendor), t.renderer = e(n.data.renderer), t.userAgent = e(n.data.userAgent), t.language = e(n.data.language), t.platform = e(n.data.platform), t.memory = e(n.data.memory), t.cpuCount = e(n.data.cpuCount);
				} catch {
					u(t, r);
				} finally {
					s(), e(t);
				}
			}, n.onerror = function() {
				s(), u(t, r), e(t);
			};
		} catch {
			s(), u(t, r), e(t);
		}
	});
}
//#endregion
//#region src/signals/toSourceError.ts
function k() {
	let e = {
		toSourceError: i,
		hasToSource: !1
	};
	try {
		null.usdfsh;
	} catch (t) {
		e.toSourceError = t.toString();
	}
	try {
		throw "xyz";
	} catch (t) {
		try {
			t.toSource(), e.hasToSource = !0;
		} catch {
			e.hasToSource = !1;
		}
	}
	return e;
}
//#endregion
//#region src/signals/mediaCodecs.ts
var A = [
	"audio/mp4; codecs=\"mp4a.40.2\"",
	"audio/mpeg;",
	"audio/webm; codecs=\"vorbis\"",
	"audio/ogg; codecs=\"vorbis\"",
	"audio/wav; codecs=\"1\"",
	"audio/ogg; codecs=\"speex\"",
	"audio/ogg; codecs=\"flac\"",
	"audio/3gpp; codecs=\"samr\""
], j = [
	"video/mp4; codecs=\"avc1.42E01E, mp4a.40.2\"",
	"video/mp4; codecs=\"avc1.42E01E\"",
	"video/mp4; codecs=\"avc1.58A01E\"",
	"video/mp4; codecs=\"avc1.4D401E\"",
	"video/mp4; codecs=\"avc1.64001E\"",
	"video/mp4; codecs=\"mp4v.20.8\"",
	"video/mp4; codecs=\"mp4v.20.240\"",
	"video/webm; codecs=\"vp8\"",
	"video/ogg; codecs=\"theora\"",
	"video/ogg; codecs=\"dirac\"",
	"video/3gpp; codecs=\"mp4v.20.8\"",
	"video/x-matroska; codecs=\"theora\""
];
function M(e, t) {
	let n = {};
	try {
		let r = document.createElement(t);
		for (let t of e) try {
			n[t] = r.canPlayType(t) || null;
		} catch {
			n[t] = null;
		}
	} catch {
		for (let t of e) n[t] = null;
	}
	return n;
}
function N(e) {
	let t = {}, n = window.MediaSource;
	if (!n || typeof n.isTypeSupported != "function") {
		for (let n of e) t[n] = null;
		return t;
	}
	for (let r of e) try {
		t[r] = n.isTypeSupported(r);
	} catch {
		t[r] = null;
	}
	return t;
}
function P(e) {
	try {
		let t = window.RTCRtpReceiver;
		if (t && typeof t.getCapabilities == "function") {
			let n = t.getCapabilities(e);
			return l(JSON.stringify(n));
		}
		return "NA";
	} catch {
		return r;
	}
}
function F() {
	let e = {
		audioCanPlayTypeHash: "NA",
		videoCanPlayTypeHash: "NA",
		audioMediaSourceHash: "NA",
		videoMediaSourceHash: "NA",
		rtcAudioCapabilitiesHash: "NA",
		rtcVideoCapabilitiesHash: "NA",
		hasMediaSource: !1
	};
	try {
		e.hasMediaSource = !!window.MediaSource;
		let t = M(A, "audio"), n = M(j, "video");
		e.audioCanPlayTypeHash = l(JSON.stringify(t)), e.videoCanPlayTypeHash = l(JSON.stringify(n));
		let r = N(A), i = N(j);
		e.audioMediaSourceHash = l(JSON.stringify(r)), e.videoMediaSourceHash = l(JSON.stringify(i)), e.rtcAudioCapabilitiesHash = P("audio"), e.rtcVideoCapabilitiesHash = P("video");
	} catch {
		u(e, r);
	}
	return e;
}
//#endregion
//#region src/signals/canvas.ts
async function I() {
	return new Promise((e) => {
		try {
			let t = new Image(), n = document.createElement("canvas").getContext("2d");
			t.onload = () => {
				n.drawImage(t, 0, 0), e(n.getImageData(0, 0, 1, 1).data.filter((e) => e === 0).length != 4);
			}, t.onerror = () => {
				e(r);
			}, t.src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQYV2NgAAIAAAUAAarVyFEAAAAASUVORK5CYII=";
		} catch {
			e(r);
		}
	});
}
function L() {
	var e = document.createElement("canvas");
	e.width = 400, e.height = 200, e.style.display = "inline";
	var t = e.getContext("2d");
	try {
		return t.rect(0, 0, 10, 10), t.rect(2, 2, 6, 6), t.textBaseline = "alphabetic", t.fillStyle = "#f60", t.fillRect(125, 1, 62, 20), t.fillStyle = "#069", t.font = "11pt no-real-font-123", t.fillText("Cwm fjordbank glyphs vext quiz, 😃", 2, 15), t.fillStyle = "rgba(102, 204, 0, 0.2)", t.font = "18pt Arial", t.fillText("Cwm fjordbank glyphs vext quiz, 😃", 4, 45), t.globalCompositeOperation = "multiply", t.fillStyle = "rgb(255,0,255)", t.beginPath(), t.arc(50, 50, 50, 0, 2 * Math.PI, !0), t.closePath(), t.fill(), t.fillStyle = "rgb(0,255,255)", t.beginPath(), t.arc(100, 50, 50, 0, 2 * Math.PI, !0), t.closePath(), t.fill(), t.fillStyle = "rgb(255,255,0)", t.beginPath(), t.arc(75, 100, 50, 0, 2 * Math.PI, !0), t.closePath(), t.fill(), t.fillStyle = "rgb(255,0,255)", t.arc(75, 75, 75, 0, 2 * Math.PI, !0), t.arc(75, 75, 25, 0, 2 * Math.PI, !0), t.fill("evenodd"), l(e.toDataURL());
	} catch {
		return r;
	}
}
async function R() {
	let e = {
		hasModifiedCanvas: i,
		canvasFingerprint: i
	};
	return e.hasModifiedCanvas = await I(), e.canvasFingerprint = L(), e;
}
//#endregion
//#region src/signals/navigatorPropertyDescriptors.ts
function z() {
	let e = [
		"deviceMemory",
		"hardwareConcurrency",
		"language",
		"languages",
		"platform"
	], t = [];
	for (let n of e) {
		let e = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(navigator), n);
		e && e.value ? t.push("1") : t.push("0");
	}
	return t.join("");
}
//#endregion
//#region src/signals/nonce.ts
function B() {
	return Math.random().toString(36).substring(2, 15);
}
//#endregion
//#region src/signals/time.ts
function V() {
	return (/* @__PURE__ */ new Date()).getTime();
}
//#endregion
//#region src/signals/url.ts
function H() {
	return window.location.href;
}
//#endregion
//#region src/detections/hasContextMismatch.ts
function U(e, t) {
	let n = e.signals;
	return t === "iframe" ? n.contexts.iframe.webdriver !== n.automation.webdriver || n.contexts.iframe.userAgent !== n.browser.userAgent || n.contexts.iframe.platform !== n.device.platform || n.contexts.iframe.memory !== n.device.memory || n.contexts.iframe.cpuCount !== n.device.cpuCount : n.contexts.webWorker.webdriver !== n.automation.webdriver || n.contexts.webWorker.userAgent !== n.browser.userAgent || n.contexts.webWorker.platform !== n.device.platform || n.contexts.webWorker.memory !== n.device.memory || n.contexts.webWorker.cpuCount !== n.device.cpuCount;
}
//#endregion
//#region src/signals/browserExtensions.ts
function W() {
	let e = {
		bitmask: i,
		extensions: []
	}, t = document.body.hasAttribute("data-gr-ext-installed"), n = window.ethereum !== void 0, r = document.getElementById("coupon-birds-drop-div") !== null, a = document.querySelector("deepl-input-controller") !== null, o = document.getElementById("monica-content-root") !== null, s = document.querySelector("chatgpt-sidebar") !== null, c = window.__REQUESTLY__ !== void 0, l = Array.from(document.querySelectorAll("*")).filter((e) => e.tagName.toLowerCase().startsWith("veepn-")).length > 0;
	return e.bitmask = [
		t ? "1" : "0",
		n ? "1" : "0",
		r ? "1" : "0",
		a ? "1" : "0",
		o ? "1" : "0",
		s ? "1" : "0",
		c ? "1" : "0",
		l ? "1" : "0"
	].join(""), t && e.extensions.push("grammarly"), n && e.extensions.push("metamask"), r && e.extensions.push("coupon-birds"), a && e.extensions.push("deepl"), o && e.extensions.push("monica-ai"), s && e.extensions.push("sider-ai"), c && e.extensions.push("requestly"), l && e.extensions.push("veepn"), e;
}
//#endregion
//#region src/signals/browserFeatures.ts
function G(e) {
	try {
		return e();
	} catch {
		return !1;
	}
}
function K() {
	let e = {
		bitmask: i,
		chrome: G(() => "chrome" in window),
		brave: G(() => "brave" in navigator),
		applePaySupport: G(() => "ApplePaySetup" in window),
		opera: G(() => window.opr !== void 0 || typeof window.onoperadetachedviewchange == "object"),
		serial: G(() => window.navigator.serial !== void 0),
		attachShadow: G(() => !!Element.prototype.attachShadow),
		caches: G(() => !!window.caches),
		webAssembly: G(() => !!window.WebAssembly && !!window.WebAssembly.instantiate),
		buffer: G(() => "Buffer" in window),
		showModalDialog: G(() => "showModalDialog" in window),
		safari: G(() => "safari" in window),
		webkitPrefixedFunction: G(() => "webkitCancelAnimationFrame" in window),
		mozPrefixedFunction: G(() => "mozGetUserMedia" in navigator),
		usb: G(() => typeof window.USB == "function"),
		browserCapture: G(() => typeof window.BrowserCaptureMediaStreamTrack == "function"),
		paymentRequestUpdateEvent: G(() => typeof window.PaymentRequestUpdateEvent == "function"),
		pressureObserver: G(() => typeof window.PressureObserver == "function"),
		audioSession: G(() => "audioSession" in navigator),
		selectAudioOutput: G(() => typeof navigator < "u" && navigator.mediaDevices !== void 0 && typeof navigator.mediaDevices.selectAudioOutput == "function"),
		barcodeDetector: G(() => "BarcodeDetector" in window),
		battery: G(() => "getBattery" in navigator),
		devicePosture: G(() => "DevicePosture" in window),
		documentPictureInPicture: G(() => "documentPictureInPicture" in window),
		eyeDropper: G(() => "EyeDropper" in window),
		editContext: G(() => "EditContext" in window),
		fencedFrame: G(() => "FencedFrameConfig" in window),
		sanitizer: G(() => "Sanitizer" in window),
		otpCredential: G(() => "OTPCredential" in window),
		sumPrecise: G(() => "sumPrecise" in Math)
	};
	return e.bitmask = Object.keys(e).filter((e) => e !== "bitmask").map((t) => e[t] ? "1" : "0").join(""), e;
}
//#endregion
//#region src/signals/mediaQueries.ts
function q() {
	let e = {
		prefersColorScheme: i,
		prefersReducedMotion: i,
		prefersReducedTransparency: i,
		colorGamut: i,
		pointer: i,
		anyPointer: i,
		hover: i,
		anyHover: i,
		colorDepth: i
	};
	try {
		e.prefersColorScheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : null, e.prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches, e.prefersReducedTransparency = window.matchMedia("(prefers-reduced-transparency: reduce)").matches, e.colorGamut = window.matchMedia("(color-gamut: rec2020)").matches ? "rec2020" : window.matchMedia("(color-gamut: p3)").matches ? "p3" : window.matchMedia("(color-gamut: srgb)").matches ? "srgb" : null, e.pointer = window.matchMedia("(pointer: fine)").matches ? "fine" : window.matchMedia("(pointer: coarse)").matches ? "coarse" : window.matchMedia("(pointer: none)").matches ? "none" : null, e.anyPointer = window.matchMedia("(any-pointer: fine)").matches ? "fine" : window.matchMedia("(any-pointer: coarse)").matches ? "coarse" : window.matchMedia("(any-pointer: none)").matches ? "none" : null, e.hover = window.matchMedia("(hover: hover)").matches, e.anyHover = window.matchMedia("(any-hover: hover)").matches;
		let t = 0;
		for (let e = 0; e <= 16; e++) window.matchMedia(`(color: ${e})`).matches && (t = e);
		e.colorDepth = t;
	} catch {
		u(e, r);
	}
	return e;
}
//#endregion
//#region src/signals/keyboard.ts
async function J() {
	let e = {
		layout: i,
		layoutSize: i
	};
	if ("keyboard" in navigator && navigator.keyboard.getLayoutMap !== void 0) try {
		let t = await navigator.keyboard.getLayoutMap();
		e.layout = Array.from(t.entries()).map(([e, t]) => `${e},${t}`).join(" "), e.layoutSize = t.size;
	} catch {
		u(e, r);
	}
	else u(e, "NA");
	return e;
}
//#endregion
//#region src/signals/ai.ts
function oe() {
	return window.opr !== void 0;
}
async function se() {
	let e = {
		summarizerAvailability: i,
		summarizerLanguageAvailability: i
	};
	if ("Summarizer" in window && !oe()) try {
		e.summarizerAvailability = await window.Summarizer.availability(), e.summarizerLanguageAvailability = await window.Summarizer.availability({ expectedInputLanguages: [navigator.language] });
	} catch {
		u(e, r);
	}
	else u(e, "NA");
	return e;
}
//#endregion
//#region src/detections/hasHeadlessChromeScreenResolution.ts
function ce(e) {
	let t = e.signals.device.screenResolution;
	return t.width === 800 && t.height === 600 || t.availableWidth === 800 && t.availableHeight === 600 || t.innerWidth === 800 && t.innerHeight === 600;
}
//#endregion
//#region src/detections/hasWebdriver.ts
function le(e) {
	return e.signals.automation.webdriver === !0;
}
//#endregion
//#region src/detections/hasSeleniumProperty.ts
function ue(e) {
	return !!e.signals.automation.selenium;
}
//#endregion
//#region src/detections/hasCDP.ts
function de(e) {
	return e.signals.automation.cdp === !0;
}
//#endregion
//#region src/detections/hasPlaywright.ts
function fe(e) {
	return e.signals.automation.playwright === !0;
}
//#endregion
//#region src/detections/hasImpossibleDeviceMemory.ts
function pe(e) {
	return typeof e.signals.device.memory == "number" ? e.signals.device.memory > 32 || e.signals.device.memory < .25 : !1;
}
//#endregion
//#region src/detections/hasHighCPUCount.ts
function me(e) {
	return typeof e.signals.device.cpuCount == "number" && e.signals.device.cpuCount > 70;
}
//#endregion
//#region src/detections/environment.ts
var Y = /^(iPhone|iPad|iPod)/, he = /(iPhone|iPad|iPod)/, ge = /Android/, _e = /Windows NT/, ve = /Macintosh/, ye = /(Chrome|Chromium|CriOS)\//, be = /(Firefox|FxiOS)\//, xe = /Version\/[\d.]+( Mobile\/\S+)? Safari\//;
function X(e) {
	let t = s(e);
	return t !== void 0 && Y.test(t);
}
function Se(e) {
	let t = e.signals;
	return c(t.device.platform, t.contexts.iframe.platform, t.contexts.webWorker.platform).some((e) => Y.test(e)) ? !0 : c(t.browser.userAgent, t.contexts.iframe.userAgent, t.contexts.webWorker.userAgent).some((e) => he.test(e));
}
function Ce(e, t) {
	return Se(e) ? "ios" : t === void 0 ? "other" : ge.test(t) ? "android" : _e.test(t) ? "windows" : ve.test(t) ? "macos" : "other";
}
function we(e, t) {
	return e === "ios" ? "webkit" : t === void 0 ? "unknown" : ye.test(t) ? "v8" : be.test(t) ? "gecko" : xe.test(t) ? "webkit" : "unknown";
}
var Z = /* @__PURE__ */ new WeakMap();
function Q(e) {
	let t = Z.get(e);
	if (t !== void 0) return t;
	let n = s(e.signals.browser.userAgent), r = Ce(e, n), i = {
		userAgent: n,
		os: r,
		isDesktop: r === "windows" || r === "macos",
		engine: we(r, n)
	};
	return Z.set(e, i), i;
}
//#endregion
//#region src/detections/hasMissingChromeObject.ts
function Te(e) {
	let { os: t, engine: n } = Q(e);
	return n !== "v8" || t === "android" ? !1 : e.signals.browser.features.chrome === !1;
}
//#endregion
//#region src/detections/hasWebdriverIframe.ts
function Ee(e) {
	return e.signals.contexts.iframe.webdriver === !0;
}
//#endregion
//#region src/detections/hasWebdriverWorker.ts
function De(e) {
	return e.signals.contexts.webWorker.webdriver === !0;
}
//#endregion
//#region src/detections/hasMismatchWebGLInWorker.ts
function Oe(e) {
	let t = e.signals.contexts.webWorker, n = e.signals.graphics.webGL;
	return c(n.vendor, n.renderer, t.vendor, t.renderer).length === 4 ? t.vendor !== n.vendor || t.renderer !== n.renderer : !1;
}
//#endregion
//#region src/detections/hasMismatchPlatformWorker.ts
function ke(e, t) {
	if (X(e) === X(t)) return !1;
	let n = (e) => e === "MacIntel" || e === "MacPPC";
	return n(e) || n(t);
}
function Ae(e) {
	let t = s(e.signals.device.platform), n = s(e.signals.contexts.webWorker.platform);
	return !(t === void 0 || n === void 0 || t === n || ke(t, n));
}
//#endregion
//#region src/detections/hasMismatchPlatformIframe.ts
function je(e) {
	let t = s(e.signals.device.platform), n = s(e.signals.contexts.iframe.platform);
	return t === void 0 || n === void 0 ? !1 : t !== n;
}
//#endregion
//#region src/detections/hasWebdriverWritable.ts
function Me(e) {
	return e.signals.automation.webdriverWritable === !0;
}
//#endregion
//#region src/detections/hasSwiftshaderRenderer.ts
function Ne(e) {
	return e.signals.graphics.webGL.renderer.includes("SwiftShader");
}
//#endregion
//#region src/detections/hasUTCTimezone.ts
function Pe(e) {
	return e.signals.locale.internationalization.timezone === "UTC";
}
//#endregion
//#region src/detections/hasMismatchLanguages.ts
function $(e) {
	let t = e.signals.locale.languages.languages, n = e.signals.locale.languages.language;
	return n && t && Array.isArray(t) && t.length > 0 ? t[0] !== n : !1;
}
//#endregion
//#region src/detections/hasInconsistentEtsl.ts
var Fe = 33, Ie = 37;
function Le(e) {
	let t = e.signals.browser.etsl;
	if (typeof t != "number") return !1;
	let { engine: n, isDesktop: r } = Q(e);
	switch (n) {
		case "v8": return r && t !== Fe;
		case "gecko":
		case "webkit": return t !== Ie;
		default: return !1;
	}
}
//#endregion
//#region src/detections/hasBotUserAgent.ts
function Re(e) {
	return [
		e.signals.browser.userAgent,
		e.signals.contexts.iframe.userAgent,
		e.signals.contexts.webWorker.userAgent
	].some((e) => /bot|headless/i.test(e.toLowerCase()));
}
//#endregion
//#region src/detections/hasGPUMismatch.ts
function ze(e) {
	let t = e.signals.graphics.webgpu, n = e.signals.graphics.webGL, r = e.signals.browser.userAgent;
	return !!((n.vendor.includes("Apple") || n.renderer.includes("Apple")) && !r.includes("Mac") || t.vendor.includes("apple") && !r.includes("Mac") || t.vendor.includes("apple") && !n.renderer.includes("Apple"));
}
//#endregion
//#region src/detections/hasPlatformMismatch.ts
function Be(e) {
	let t = e.signals.device.platform, n = e.signals.browser.userAgent, r = e.signals.browser.highEntropyValues.platform;
	return !!(n.includes("Mac") && (t.includes("Win") || t.includes("Linux")) || n.includes("Windows") && (t.includes("Mac") || t.includes("Linux")) || n.includes("Linux") && (t.includes("Mac") || t.includes("Win")) || r !== "ERROR" && r !== "NA" && (r.includes("Mac") && (t.includes("Win") || t.includes("Linux")) || r.includes("Windows") && (t.includes("Mac") || t.includes("Linux")) || r.includes("Linux") && (t.includes("Mac") || t.includes("Win"))));
}
//#endregion
//#region src/crypto-helpers.ts
async function Ve(e, t) {
	let n = new TextEncoder().encode(t), r = new TextEncoder().encode(e), i = new Uint8Array(r.length);
	for (let e = 0; e < r.length; e++) i[e] = r[e] ^ n[e % n.length];
	let a = String.fromCharCode(...i);
	return btoa(a);
}
//#endregion
//#region src/index.ts
var He = class {
	constructor() {
		this.fingerprint = {
			signals: {
				automation: {
					webdriver: i,
					webdriverWritable: i,
					selenium: i,
					cdp: i,
					playwright: i,
					navigatorPropertyDescriptors: i
				},
				device: {
					cpuCount: i,
					memory: i,
					platform: i,
					screenResolution: {
						width: i,
						height: i,
						pixelDepth: i,
						colorDepth: i,
						availableWidth: i,
						availableHeight: i,
						innerWidth: i,
						innerHeight: i,
						hasMultipleDisplays: i
					},
					multimediaDevices: {
						speakers: i,
						microphones: i,
						webcams: i
					},
					mediaQueries: {
						prefersColorScheme: i,
						prefersReducedMotion: i,
						prefersReducedTransparency: i,
						colorGamut: i,
						pointer: i,
						anyPointer: i,
						hover: i,
						anyHover: i,
						colorDepth: i
					},
					keyboard: {
						layout: i,
						layoutSize: i
					}
				},
				browser: {
					userAgent: i,
					features: {
						bitmask: i,
						chrome: i,
						brave: i,
						applePaySupport: i,
						opera: i,
						serial: i,
						attachShadow: i,
						caches: i,
						webAssembly: i,
						buffer: i,
						showModalDialog: i,
						safari: i,
						webkitPrefixedFunction: i,
						mozPrefixedFunction: i,
						usb: i,
						browserCapture: i,
						paymentRequestUpdateEvent: i,
						pressureObserver: i,
						audioSession: i,
						selectAudioOutput: i,
						barcodeDetector: i,
						battery: i,
						devicePosture: i,
						documentPictureInPicture: i,
						eyeDropper: i,
						editContext: i,
						fencedFrame: i,
						sanitizer: i,
						otpCredential: i
					},
					plugins: {
						isValidPluginArray: i,
						pluginCount: i,
						pluginNamesHash: i,
						pluginConsistency1: i,
						pluginOverflow: i
					},
					extensions: {
						bitmask: i,
						extensions: i
					},
					highEntropyValues: {
						architecture: i,
						bitness: i,
						brands: i,
						mobile: i,
						model: i,
						platform: i,
						platformVersion: i,
						uaFullVersion: i
					},
					etsl: i,
					maths: i,
					toSourceError: {
						toSourceError: i,
						hasToSource: i
					},
					ai: {
						summarizerAvailability: i,
						summarizerLanguageAvailability: i
					}
				},
				graphics: {
					webGL: {
						vendor: i,
						renderer: i
					},
					webgpu: {
						vendor: i,
						architecture: i,
						device: i,
						description: i
					},
					canvas: {
						hasModifiedCanvas: i,
						canvasFingerprint: i
					}
				},
				codecs: {
					audioCanPlayTypeHash: i,
					videoCanPlayTypeHash: i,
					audioMediaSourceHash: i,
					videoMediaSourceHash: i,
					rtcAudioCapabilitiesHash: i,
					rtcVideoCapabilitiesHash: i,
					hasMediaSource: i
				},
				locale: {
					internationalization: {
						timezone: i,
						localeLanguage: i
					},
					languages: {
						languages: i,
						language: i
					}
				},
				contexts: {
					iframe: {
						webdriver: i,
						userAgent: i,
						platform: i,
						memory: i,
						cpuCount: i,
						language: i
					},
					webWorker: {
						webdriver: i,
						userAgent: i,
						platform: i,
						memory: i,
						cpuCount: i,
						language: i,
						vendor: i,
						renderer: i
					}
				}
			},
			fsid: i,
			nonce: i,
			time: i,
			url: i,
			fastBotDetection: !1,
			fastBotDetectionDetails: {
				headlessChromeScreenResolution: {
					detected: !1,
					severity: "high"
				},
				hasWebdriver: {
					detected: !1,
					severity: "high"
				},
				hasWebdriverWritable: {
					detected: !1,
					severity: "high"
				},
				hasSeleniumProperty: {
					detected: !1,
					severity: "high"
				},
				hasCDP: {
					detected: !1,
					severity: "high"
				},
				hasPlaywright: {
					detected: !1,
					severity: "high"
				},
				hasImpossibleDeviceMemory: {
					detected: !1,
					severity: "high"
				},
				hasHighCPUCount: {
					detected: !1,
					severity: "high"
				},
				hasMissingChromeObject: {
					detected: !1,
					severity: "high"
				},
				hasWebdriverIframe: {
					detected: !1,
					severity: "high"
				},
				hasWebdriverWorker: {
					detected: !1,
					severity: "high"
				},
				hasMismatchWebGLInWorker: {
					detected: !1,
					severity: "high"
				},
				hasMismatchPlatformIframe: {
					detected: !1,
					severity: "high"
				},
				hasMismatchPlatformWorker: {
					detected: !1,
					severity: "high"
				},
				hasSwiftshaderRenderer: {
					detected: !1,
					severity: "low"
				},
				hasUTCTimezone: {
					detected: !1,
					severity: "medium"
				},
				hasMismatchLanguages: {
					detected: !1,
					severity: "low"
				},
				hasInconsistentEtsl: {
					detected: !1,
					severity: "high"
				},
				hasBotUserAgent: {
					detected: !1,
					severity: "high"
				},
				hasGPUMismatch: {
					detected: !1,
					severity: "high"
				},
				hasPlatformMismatch: {
					detected: !1,
					severity: "high"
				}
			}
		};
	}
	async collectSignal(e) {
		try {
			return await e();
		} catch {
			return r;
		}
	}
	generateFingerprintScannerId() {
		try {
			let e = this.fingerprint.signals, t = this.fingerprint.fastBotDetectionDetails;
			return [
				"FS1",
				[
					t.headlessChromeScreenResolution.detected,
					t.hasWebdriver.detected,
					t.hasWebdriverWritable.detected,
					t.hasSeleniumProperty.detected,
					t.hasCDP.detected,
					t.hasPlaywright.detected,
					t.hasImpossibleDeviceMemory.detected,
					t.hasHighCPUCount.detected,
					t.hasMissingChromeObject.detected,
					t.hasWebdriverIframe.detected,
					t.hasWebdriverWorker.detected,
					t.hasMismatchWebGLInWorker.detected,
					t.hasMismatchPlatformIframe.detected,
					t.hasMismatchPlatformWorker.detected,
					t.hasSwiftshaderRenderer.detected,
					t.hasUTCTimezone.detected,
					t.hasMismatchLanguages.detected,
					t.hasInconsistentEtsl.detected,
					t.hasBotUserAgent.detected,
					t.hasGPUMismatch.detected,
					t.hasPlatformMismatch.detected
				].map((e) => e ? "1" : "0").join(""),
				`${[
					e.automation.webdriver === !0,
					e.automation.webdriverWritable === !0,
					e.automation.selenium === !0,
					e.automation.cdp === !0,
					e.automation.playwright === !0
				].map((e) => e ? "1" : "0").join("")}h${l(String(e.automation.navigatorPropertyDescriptors)).slice(0, 4)}`,
				`${typeof e.device.screenResolution.width == "number" ? e.device.screenResolution.width : 0}x${typeof e.device.screenResolution.height == "number" ? e.device.screenResolution.height : 0}c${typeof e.device.cpuCount == "number" ? String(e.device.cpuCount).padStart(2, "0") : "00"}m${typeof e.device.memory == "number" ? String(Math.round(e.device.memory)).padStart(2, "0") : "00"}b${[
					e.device.screenResolution.hasMultipleDisplays === !0,
					e.device.mediaQueries.prefersReducedMotion === !0,
					e.device.mediaQueries.prefersReducedTransparency === !0,
					e.device.mediaQueries.hover === !0,
					e.device.mediaQueries.anyHover === !0
				].map((e) => e ? "1" : "0").join("")}h${l([
					e.device.platform,
					e.device.screenResolution.pixelDepth,
					e.device.screenResolution.colorDepth,
					e.device.multimediaDevices.speakers,
					e.device.multimediaDevices.microphones,
					e.device.multimediaDevices.webcams,
					e.device.mediaQueries.prefersColorScheme,
					e.device.mediaQueries.colorGamut,
					e.device.mediaQueries.pointer,
					e.device.mediaQueries.anyPointer,
					e.device.mediaQueries.colorDepth,
					e.device.keyboard.layout,
					e.device.keyboard.layoutSize
				].map((e) => String(e)).join("|")).slice(0, 6)}`,
				`f${typeof e.browser.features.bitmask == "string" ? e.browser.features.bitmask : "0".repeat(29)}e${typeof e.browser.extensions.bitmask == "string" ? e.browser.extensions.bitmask : "0".repeat(8)}p${[
					e.browser.plugins.isValidPluginArray === !0,
					e.browser.plugins.pluginConsistency1 === !0,
					e.browser.plugins.pluginOverflow === !0,
					e.browser.toSourceError.hasToSource === !0
				].map((e) => e ? "1" : "0").join("")}h${l([
					e.browser.userAgent,
					e.browser.etsl,
					e.browser.maths,
					e.browser.plugins.pluginCount,
					e.browser.plugins.pluginNamesHash,
					e.browser.toSourceError.toSourceError,
					e.browser.highEntropyValues.architecture,
					e.browser.highEntropyValues.bitness,
					e.browser.highEntropyValues.platform,
					e.browser.highEntropyValues.platformVersion,
					e.browser.highEntropyValues.uaFullVersion,
					e.browser.highEntropyValues.mobile,
					e.browser.ai.summarizerAvailability,
					e.browser.ai.summarizerLanguageAvailability
				].map((e) => String(e)).join("|")).slice(0, 6)}`,
				`${[e.graphics.canvas.hasModifiedCanvas === !0].map((e) => e ? "1" : "0").join("")}h${l([
					e.graphics.webGL.vendor,
					e.graphics.webGL.renderer,
					e.graphics.webgpu.vendor,
					e.graphics.webgpu.architecture,
					e.graphics.webgpu.device,
					e.graphics.webgpu.description,
					e.graphics.canvas.canvasFingerprint
				].map((e) => String(e)).join("|")).slice(0, 6)}`,
				`${[e.codecs.hasMediaSource === !0].map((e) => e ? "1" : "0").join("")}h${l([
					e.codecs.audioCanPlayTypeHash,
					e.codecs.videoCanPlayTypeHash,
					e.codecs.audioMediaSourceHash,
					e.codecs.videoMediaSourceHash,
					e.codecs.rtcAudioCapabilitiesHash,
					e.codecs.rtcVideoCapabilitiesHash
				].map((e) => String(e)).join("|")).slice(0, 6)}`,
				`${typeof e.locale.languages.language == "string" ? e.locale.languages.language.slice(0, 2).toLowerCase() : "xx"}${Array.isArray(e.locale.languages.languages) ? e.locale.languages.languages.length : 0}t${(typeof e.locale.internationalization.timezone == "string" ? e.locale.internationalization.timezone : "unknown").replace(/[\/\s]/g, "-")}_h${l([
					e.locale.internationalization.timezone,
					e.locale.internationalization.localeLanguage,
					Array.isArray(e.locale.languages.languages) ? e.locale.languages.languages.join(",") : e.locale.languages.languages,
					e.locale.languages.language
				].map((e) => String(e)).join("|")).slice(0, 4)}`,
				`${[
					U(this.fingerprint, "iframe"),
					U(this.fingerprint, "worker"),
					e.contexts.iframe.webdriver === !0,
					e.contexts.webWorker.webdriver === !0
				].map((e) => e ? "1" : "0").join("")}h${l([
					e.contexts.iframe.userAgent,
					e.contexts.iframe.platform,
					e.contexts.iframe.memory,
					e.contexts.iframe.cpuCount,
					e.contexts.iframe.language,
					e.contexts.webWorker.userAgent,
					e.contexts.webWorker.platform,
					e.contexts.webWorker.memory,
					e.contexts.webWorker.cpuCount,
					e.contexts.webWorker.language,
					e.contexts.webWorker.vendor,
					e.contexts.webWorker.renderer
				].map((e) => String(e)).join("|")).slice(0, 6)}`
			].join("_");
		} catch (e) {
			return console.error("Error generating fingerprint scanner id", e), r;
		}
	}
	async encryptFingerprint(e) {
		let t = "__DEFAULT_FPSCANNER_KEY__";
		return t.indexOf("DEFAULT") > 0 && t.indexOf("FPSCANNER") > 0 && console.warn("[fpscanner] WARNING: Using default encryption key! Run \"npx fpscanner build --key=your-secret-key\" to inject your own key. See: https://github.com/antoinevastel/fpscanner#advanced-custom-builds"), await Ve(JSON.stringify(e), t);
	}
	getDetectionRules() {
		return [
			{
				name: "headlessChromeScreenResolution",
				severity: o,
				test: ce
			},
			{
				name: "hasWebdriver",
				severity: o,
				test: le
			},
			{
				name: "hasWebdriverWritable",
				severity: o,
				test: Me
			},
			{
				name: "hasSeleniumProperty",
				severity: o,
				test: ue
			},
			{
				name: "hasCDP",
				severity: o,
				test: de
			},
			{
				name: "hasPlaywright",
				severity: o,
				test: fe
			},
			{
				name: "hasImpossibleDeviceMemory",
				severity: o,
				test: pe
			},
			{
				name: "hasHighCPUCount",
				severity: o,
				test: me
			},
			{
				name: "hasMissingChromeObject",
				severity: o,
				test: Te
			},
			{
				name: "hasWebdriverIframe",
				severity: o,
				test: Ee
			},
			{
				name: "hasWebdriverWorker",
				severity: o,
				test: De
			},
			{
				name: "hasMismatchWebGLInWorker",
				severity: o,
				test: Oe
			},
			{
				name: "hasMismatchPlatformIframe",
				severity: o,
				test: je
			},
			{
				name: "hasMismatchPlatformWorker",
				severity: o,
				test: Ae
			},
			{
				name: "hasSwiftshaderRenderer",
				severity: "low",
				test: Ne
			},
			{
				name: "hasUTCTimezone",
				severity: "medium",
				test: Pe
			},
			{
				name: "hasMismatchLanguages",
				severity: "low",
				test: $
			},
			{
				name: "hasInconsistentEtsl",
				severity: o,
				test: Le
			},
			{
				name: "hasBotUserAgent",
				severity: o,
				test: Re
			},
			{
				name: "hasGPUMismatch",
				severity: o,
				test: ze
			},
			{
				name: "hasPlatformMismatch",
				severity: o,
				test: Be
			}
		];
	}
	runDetectionRules() {
		let e = this.getDetectionRules(), t = {
			headlessChromeScreenResolution: {
				detected: !1,
				severity: "high"
			},
			hasWebdriver: {
				detected: !1,
				severity: "high"
			},
			hasWebdriverWritable: {
				detected: !1,
				severity: "high"
			},
			hasSeleniumProperty: {
				detected: !1,
				severity: "high"
			},
			hasCDP: {
				detected: !1,
				severity: "high"
			},
			hasPlaywright: {
				detected: !1,
				severity: "high"
			},
			hasImpossibleDeviceMemory: {
				detected: !1,
				severity: "high"
			},
			hasHighCPUCount: {
				detected: !1,
				severity: "high"
			},
			hasMissingChromeObject: {
				detected: !1,
				severity: "high"
			},
			hasWebdriverIframe: {
				detected: !1,
				severity: "high"
			},
			hasWebdriverWorker: {
				detected: !1,
				severity: "high"
			},
			hasMismatchWebGLInWorker: {
				detected: !1,
				severity: "high"
			},
			hasMismatchPlatformIframe: {
				detected: !1,
				severity: "high"
			},
			hasMismatchPlatformWorker: {
				detected: !1,
				severity: "high"
			},
			hasSwiftshaderRenderer: {
				detected: !1,
				severity: "low"
			},
			hasUTCTimezone: {
				detected: !1,
				severity: "medium"
			},
			hasMismatchLanguages: {
				detected: !1,
				severity: "low"
			},
			hasInconsistentEtsl: {
				detected: !1,
				severity: "high"
			},
			hasBotUserAgent: {
				detected: !1,
				severity: "high"
			},
			hasGPUMismatch: {
				detected: !1,
				severity: "high"
			},
			hasPlatformMismatch: {
				detected: !1,
				severity: "high"
			}
		};
		for (let n of e) try {
			let e = n.test(this.fingerprint);
			t[n.name] = {
				detected: e,
				severity: n.severity
			};
		} catch {
			t[n.name] = {
				detected: !1,
				severity: n.severity
			};
		}
		return t;
	}
	async collectFingerprint(r = { encrypt: !0 }) {
		let { encrypt: i = !0, skipWorker: o = !1 } = r, s = this.fingerprint.signals, c = {
			webdriver: this.collectSignal(e),
			webdriverWritable: this.collectSignal(ae),
			selenium: this.collectSignal(ie),
			cdp: this.collectSignal(f),
			playwright: this.collectSignal(m),
			navigatorPropertyDescriptors: this.collectSignal(z),
			cpuCount: this.collectSignal(h),
			memory: this.collectSignal(_),
			platform: this.collectSignal(n),
			screenResolution: this.collectSignal(te),
			multimediaDevices: this.collectSignal(E),
			mediaQueries: this.collectSignal(q),
			keyboard: this.collectSignal(J),
			userAgent: this.collectSignal(t),
			browserFeatures: this.collectSignal(K),
			plugins: this.collectSignal(T),
			browserExtensions: this.collectSignal(W),
			highEntropyValues: this.collectSignal(y),
			etsl: this.collectSignal(v),
			maths: this.collectSignal(g),
			toSourceError: this.collectSignal(k),
			ai: this.collectSignal(se),
			webGL: this.collectSignal(p),
			webgpu: this.collectSignal(re),
			canvas: this.collectSignal(R),
			mediaCodecs: this.collectSignal(F),
			internationalization: this.collectSignal(ee),
			languages: this.collectSignal(ne),
			iframe: this.collectSignal(D),
			webWorker: o ? Promise.resolve({
				webdriver: a,
				userAgent: a,
				platform: a,
				memory: a,
				cpuCount: a,
				language: a,
				vendor: a,
				renderer: a
			}) : this.collectSignal(O),
			nonce: this.collectSignal(B),
			time: this.collectSignal(V),
			url: this.collectSignal(H)
		}, l = Object.keys(c), u = await Promise.all(Object.values(c)), d = Object.fromEntries(l.map((e, t) => [e, u[t]]));
		return s.automation.webdriver = d.webdriver, s.automation.webdriverWritable = d.webdriverWritable, s.automation.selenium = d.selenium, s.automation.cdp = d.cdp, s.automation.playwright = d.playwright, s.automation.navigatorPropertyDescriptors = d.navigatorPropertyDescriptors, s.device.cpuCount = d.cpuCount, s.device.memory = d.memory, s.device.platform = d.platform, s.device.screenResolution = d.screenResolution, s.device.multimediaDevices = d.multimediaDevices, s.device.mediaQueries = d.mediaQueries, s.device.keyboard = d.keyboard, s.browser.userAgent = d.userAgent, s.browser.features = d.browserFeatures, s.browser.plugins = d.plugins, s.browser.extensions = d.browserExtensions, s.browser.highEntropyValues = d.highEntropyValues, s.browser.etsl = d.etsl, s.browser.maths = d.maths, s.browser.toSourceError = d.toSourceError, s.browser.ai = d.ai, s.graphics.webGL = d.webGL, s.graphics.webgpu = d.webgpu, s.graphics.canvas = d.canvas, s.codecs = d.mediaCodecs, s.locale.internationalization = d.internationalization, s.locale.languages = d.languages, s.contexts.iframe = d.iframe, s.contexts.webWorker = d.webWorker, this.fingerprint.nonce = d.nonce, this.fingerprint.time = d.time, this.fingerprint.url = d.url, this.fingerprint.fastBotDetectionDetails = this.runDetectionRules(), this.fingerprint.fastBotDetection = Object.values(this.fingerprint.fastBotDetectionDetails).some((e) => e.detected), this.fingerprint.fsid = this.generateFingerprintScannerId(), i ? await this.encryptFingerprint(JSON.stringify(this.fingerprint)) : this.fingerprint;
	}
};
//#endregion
export { He as default };
