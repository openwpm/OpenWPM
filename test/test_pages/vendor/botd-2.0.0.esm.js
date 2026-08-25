/**
 * Fingerprint BotD v2.0.0 - Copyright (c) FingerprintJS, Inc, 2025 (https://fingerprint.com)
 * Licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) license.
 */

var version = "2.0.0";

/**
 * Enum for types of bots.
 * Specific types of bots come first, followed by automation technologies.
 *
 * @readonly
 * @enum {string}
 */
const BotKind = {
    // Object is used instead of Typescript enum to avoid emitting IIFE which might be affected by further tree-shaking.
    // See example of compiled enums https://stackoverflow.com/q/47363996)
    Awesomium: 'awesomium',
    Cef: 'cef',
    CefSharp: 'cefsharp',
    CoachJS: 'coachjs',
    Electron: 'electron',
    FMiner: 'fminer',
    Geb: 'geb',
    NightmareJS: 'nightmarejs',
    Phantomas: 'phantomas',
    PhantomJS: 'phantomjs',
    Rhino: 'rhino',
    Selenium: 'selenium',
    Sequentum: 'sequentum',
    SlimerJS: 'slimerjs',
    WebDriverIO: 'webdriverio',
    WebDriver: 'webdriver',
    HeadlessChrome: 'headless_chrome',
    Unknown: 'unknown',
};
/**
 * Bot detection error.
 */
class BotdError extends Error {
    /**
     * Creates a new BotdError.
     *
     * @class
     */
    constructor(state, message) {
        super(message);
        this.state = state;
        this.name = 'BotdError';
        Object.setPrototypeOf(this, BotdError.prototype);
    }
}

function detect(components, detectors) {
    const detections = {};
    let finalDetection = {
        bot: false,
    };
    for (const detectorName in detectors) {
        const detector = detectors[detectorName];
        const detectorRes = detector(components);
        let detection = { bot: false };
        if (typeof detectorRes === 'string') {
            detection = { bot: true, botKind: detectorRes };
        }
        else if (detectorRes) {
            detection = { bot: true, botKind: BotKind.Unknown };
        }
        detections[detectorName] = detection;
        if (detection.bot) {
            finalDetection = detection;
        }
    }
    return [detections, finalDetection];
}
async function collect(sources) {
    const components = {};
    const sourcesKeys = Object.keys(sources);
    await Promise.all(sourcesKeys.map(async (sourceKey) => {
        const res = sources[sourceKey];
        try {
            components[sourceKey] = {
                value: await res(),
                state: 0 /* State.Success */,
            };
        }
        catch (error) {
            if (error instanceof BotdError) {
                components[sourceKey] = {
                    state: error.state,
                    error: `${error.name}: ${error.message}`,
                };
            }
            else {
                components[sourceKey] = {
                    state: -3 /* State.UnexpectedBehaviour */,
                    error: error instanceof Error ? `${error.name}: ${error.message}` : String(error),
                };
            }
        }
    }));
    return components;
}

function detectAppVersion({ appVersion }) {
    if (appVersion.state !== 0 /* State.Success */)
        return false;
    if (/headless/i.test(appVersion.value))
        return BotKind.HeadlessChrome;
    if (/electron/i.test(appVersion.value))
        return BotKind.Electron;
    if (/slimerjs/i.test(appVersion.value))
        return BotKind.SlimerJS;
}

function arrayIncludes(arr, value) {
    return arr.indexOf(value) !== -1;
}
function strIncludes(str, value) {
    return str.indexOf(value) !== -1;
}
function arrayFind(array, callback) {
    if ('find' in array)
        return array.find(callback);
    for (let i = 0; i < array.length; i++) {
        if (callback(array[i], i, array))
            return array[i];
    }
    return undefined;
}

function getObjectProps(obj) {
    return Object.getOwnPropertyNames(obj);
}
function includes(arr, ...keys) {
    for (const key of keys) {
        if (typeof key === 'string') {
            if (arrayIncludes(arr, key))
                return true;
        }
        else {
            const match = arrayFind(arr, (value) => key.test(value));
            if (match != null)
                return true;
        }
    }
    return false;
}
function countTruthy(values) {
    return values.reduce((sum, value) => sum + (value ? 1 : 0), 0);
}

function detectDocumentAttributes({ documentElementKeys }) {
    if (documentElementKeys.state !== 0 /* State.Success */)
        return false;
    if (includes(documentElementKeys.value, 'selenium', 'webdriver', 'driver')) {
        return BotKind.Selenium;
    }
}

function detectErrorTrace({ errorTrace }) {
    if (errorTrace.state !== 0 /* State.Success */)
        return false;
    if (/PhantomJS/i.test(errorTrace.value))
        return BotKind.PhantomJS;
}

function detectEvalLengthInconsistency({ evalLength, browserKind, browserEngineKind, }) {
    if (evalLength.state !== 0 /* State.Success */ ||
        browserKind.state !== 0 /* State.Success */ ||
        browserEngineKind.state !== 0 /* State.Success */)
        return;
    const length = evalLength.value;
    if (browserEngineKind.value === "unknown" /* BrowserEngineKind.Unknown */)
        return false;
    return ((length === 37 && !arrayIncludes(["webkit" /* BrowserEngineKind.Webkit */, "gecko" /* BrowserEngineKind.Gecko */], browserEngineKind.value)) ||
        (length === 39 && !arrayIncludes(["internet_explorer" /* BrowserKind.IE */], browserKind.value)) ||
        (length === 33 && !arrayIncludes(["chromium" /* BrowserEngineKind.Chromium */], browserEngineKind.value)));
}

function detectFunctionBind({ functionBind }) {
    if (functionBind.state === -2 /* State.NotFunction */)
        return BotKind.PhantomJS;
}

function detectLanguagesLengthInconsistency({ languages }) {
    if (languages.state === 0 /* State.Success */ && languages.value.length === 0) {
        return BotKind.HeadlessChrome;
    }
}

function detectMimeTypesConsistent({ mimeTypesConsistent }) {
    if (mimeTypesConsistent.state === 0 /* State.Success */ && !mimeTypesConsistent.value) {
        return BotKind.Unknown;
    }
}

function detectNotificationPermissions({ notificationPermissions, browserKind, }) {
    if (browserKind.state !== 0 /* State.Success */ || browserKind.value !== "chrome" /* BrowserKind.Chrome */)
        return false;
    if (notificationPermissions.state === 0 /* State.Success */ && notificationPermissions.value) {
        return BotKind.HeadlessChrome;
    }
}

function detectPluginsArray({ pluginsArray }) {
    if (pluginsArray.state === 0 /* State.Success */ && !pluginsArray.value)
        return BotKind.HeadlessChrome;
}

function detectPluginsLengthInconsistency({ pluginsLength, android, browserKind, browserEngineKind, }) {
    if (pluginsLength.state !== 0 /* State.Success */ ||
        android.state !== 0 /* State.Success */ ||
        browserKind.state !== 0 /* State.Success */ ||
        browserEngineKind.state !== 0 /* State.Success */)
        return;
    if (browserKind.value !== "chrome" /* BrowserKind.Chrome */ ||
        android.value ||
        browserEngineKind.value !== "chromium" /* BrowserEngineKind.Chromium */)
        return;
    if (pluginsLength.value === 0)
        return BotKind.HeadlessChrome;
}

function detectProcess({ process }) {
    var _a;
    if (process.state !== 0 /* State.Success */)
        return false;
    if (process.value.type === 'renderer' || ((_a = process.value.versions) === null || _a === void 0 ? void 0 : _a.electron) != null)
        return BotKind.Electron;
}

function detectProductSub({ productSub, browserKind }) {
    if (productSub.state !== 0 /* State.Success */ || browserKind.state !== 0 /* State.Success */)
        return false;
    if ((browserKind.value === "chrome" /* BrowserKind.Chrome */ ||
        browserKind.value === "safari" /* BrowserKind.Safari */ ||
        browserKind.value === "opera" /* BrowserKind.Opera */ ||
        browserKind.value === "wechat" /* BrowserKind.WeChat */) &&
        productSub.value !== '20030107')
        return BotKind.Unknown;
}

function detectUserAgent({ userAgent }) {
    if (userAgent.state !== 0 /* State.Success */)
        return false;
    if (/PhantomJS/i.test(userAgent.value))
        return BotKind.PhantomJS;
    if (/Headless/i.test(userAgent.value))
        return BotKind.HeadlessChrome;
    if (/Electron/i.test(userAgent.value))
        return BotKind.Electron;
    if (/slimerjs/i.test(userAgent.value))
        return BotKind.SlimerJS;
}

function detectWebDriver({ webDriver }) {
    if (webDriver.state === 0 /* State.Success */ && webDriver.value)
        return BotKind.HeadlessChrome;
}

function detectWebGL({ webGL }) {
    if (webGL.state === 0 /* State.Success */) {
        const { vendor, renderer } = webGL.value;
        if (vendor == 'Brian Paul' && renderer == 'Mesa OffScreen') {
            return BotKind.HeadlessChrome;
        }
    }
}

function detectWindowExternal({ windowExternal }) {
    if (windowExternal.state !== 0 /* State.Success */)
        return false;
    if (/Sequentum/i.test(windowExternal.value))
        return BotKind.Sequentum;
}

function detectWindowSize({ windowSize, documentFocus }) {
    if (windowSize.state !== 0 /* State.Success */ || documentFocus.state !== 0 /* State.Success */)
        return false;
    const { outerWidth, outerHeight } = windowSize.value;
    // When a page is opened in a new tab without focusing it right away, the window outer size is 0x0
    if (!documentFocus.value)
        return;
    if (outerWidth === 0 && outerHeight === 0)
        return BotKind.HeadlessChrome;
}

function detectDistinctiveProperties({ distinctiveProps }) {
    if (distinctiveProps.state !== 0 /* State.Success */)
        return false;
    const value = distinctiveProps.value;
    let bot;
    for (bot in value)
        if (value[bot])
            return bot;
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
const detectors = {
    detectAppVersion,
    detectDocumentAttributes,
    detectErrorTrace,
    detectEvalLengthInconsistency,
    detectFunctionBind,
    detectLanguagesLengthInconsistency,
    detectNotificationPermissions,
    detectPluginsArray,
    detectPluginsLengthInconsistency,
    detectProcess,
    detectUserAgent,
    detectWebDriver,
    detectWebGL,
    detectWindowExternal,
    detectWindowSize,
    detectMimeTypesConsistent,
    detectProductSub,
    detectDistinctiveProperties,
};

function getAppVersion() {
    const appVersion = navigator.appVersion;
    if (appVersion == undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.appVersion is undefined');
    }
    return appVersion;
}

function getDocumentElementKeys() {
    if (document.documentElement === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'document.documentElement is undefined');
    }
    const { documentElement } = document;
    if (typeof documentElement.getAttributeNames !== 'function') {
        throw new BotdError(-2 /* State.NotFunction */, 'document.documentElement.getAttributeNames is not a function');
    }
    return documentElement.getAttributeNames();
}

function getErrorTrace() {
    try {
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        null[0]();
    }
    catch (error) {
        if (error instanceof Error && error['stack'] != null) {
            return error.stack.toString();
        }
    }
    throw new BotdError(-3 /* State.UnexpectedBehaviour */, 'errorTrace signal unexpected behaviour');
}

function getEvalLength() {
    return eval.toString().length;
}

function getFunctionBind() {
    if (Function.prototype.bind === undefined) {
        throw new BotdError(-2 /* State.NotFunction */, 'Function.prototype.bind is undefined');
    }
    return Function.prototype.bind.toString();
}

function getBrowserEngineKind() {
    var _a, _b;
    // Based on research in October 2020. Tested to detect Chromium 42-86.
    const w = window;
    const n = navigator;
    if (countTruthy([
        'webkitPersistentStorage' in n,
        'webkitTemporaryStorage' in n,
        n.vendor.indexOf('Google') === 0,
        'webkitResolveLocalFileSystemURL' in w,
        'BatteryManager' in w,
        'webkitMediaStream' in w,
        'webkitSpeechGrammar' in w,
    ]) >= 5) {
        return "chromium" /* BrowserEngineKind.Chromium */;
    }
    if (countTruthy([
        'ApplePayError' in w,
        'CSSPrimitiveValue' in w,
        'Counter' in w,
        n.vendor.indexOf('Apple') === 0,
        'getStorageUpdates' in n,
        'WebKitMediaKeys' in w,
    ]) >= 4) {
        return "webkit" /* BrowserEngineKind.Webkit */;
    }
    if (countTruthy([
        'buildID' in navigator,
        'MozAppearance' in ((_b = (_a = document.documentElement) === null || _a === void 0 ? void 0 : _a.style) !== null && _b !== void 0 ? _b : {}),
        'onmozfullscreenchange' in w,
        'mozInnerScreenX' in w,
        'CSSMozDocumentRule' in w,
        'CanvasCaptureMediaStream' in w,
    ]) >= 4) {
        return "gecko" /* BrowserEngineKind.Gecko */;
    }
    return "unknown" /* BrowserEngineKind.Unknown */;
}
function getBrowserKind() {
    var _a;
    const userAgent = (_a = navigator.userAgent) === null || _a === void 0 ? void 0 : _a.toLowerCase();
    if (strIncludes(userAgent, 'edg/')) {
        return "edge" /* BrowserKind.Edge */;
    }
    else if (strIncludes(userAgent, 'trident') || strIncludes(userAgent, 'msie')) {
        return "internet_explorer" /* BrowserKind.IE */;
    }
    else if (strIncludes(userAgent, 'wechat')) {
        return "wechat" /* BrowserKind.WeChat */;
    }
    else if (strIncludes(userAgent, 'firefox')) {
        return "firefox" /* BrowserKind.Firefox */;
    }
    else if (strIncludes(userAgent, 'opera') || strIncludes(userAgent, 'opr')) {
        return "opera" /* BrowserKind.Opera */;
    }
    else if (strIncludes(userAgent, 'chrome')) {
        return "chrome" /* BrowserKind.Chrome */;
    }
    else if (strIncludes(userAgent, 'safari')) {
        return "safari" /* BrowserKind.Safari */;
    }
    else {
        return "unknown" /* BrowserKind.Unknown */;
    }
}
// Source: https://github.com/fingerprintjs/fingerprintjs/blob/master/src/utils/browser.ts#L223
function isAndroid() {
    const browserEngineKind = getBrowserEngineKind();
    const isItChromium = browserEngineKind === "chromium" /* BrowserEngineKind.Chromium */;
    const isItGecko = browserEngineKind === "gecko" /* BrowserEngineKind.Gecko */;
    const w = window;
    const n = navigator;
    const c = 'connection';
    // Chrome removes all words "Android" from `navigator` when desktop version is requested
    // Firefox keeps "Android" in `navigator.appVersion` when desktop version is requested
    if (isItChromium) {
        return (countTruthy([
            !('SharedWorker' in w),
            // `typechange` is deprecated, but it's still present on Android (tested on Chrome Mobile 117)
            // Removal proposal https://bugs.chromium.org/p/chromium/issues/detail?id=699892
            // Note: this expression returns true on ChromeOS, so additional detectors are required to avoid false-positives
            n[c] && 'ontypechange' in n[c],
            !('sinkId' in new Audio()),
        ]) >= 2);
    }
    else if (isItGecko) {
        return countTruthy(['onorientationchange' in w, 'orientation' in w, /android/i.test(n.appVersion)]) >= 2;
    }
    else {
        // Only 2 browser engines are presented on Android.
        // Actually, there is also Android 4.1 browser, but it's not worth detecting it at the moment.
        return false;
    }
}
function getDocumentFocus() {
    if (document.hasFocus === undefined) {
        return false;
    }
    return document.hasFocus();
}
function isChromium86OrNewer() {
    // Checked in Chrome 85 vs Chrome 86 both on desktop and Android. Checked in macOS Chrome 128, Android Chrome 127.
    const w = window;
    return (countTruthy([
        !('MediaSettingsRange' in w),
        'RTCEncodedAudioFrame' in w,
        '' + w.Intl === '[object Intl]',
        '' + w.Reflect === '[object Reflect]',
    ]) >= 3);
}

function getLanguages() {
    const n = navigator;
    const result = [];
    const language = n.language || n.userLanguage || n.browserLanguage || n.systemLanguage;
    if (language !== undefined) {
        result.push([language]);
    }
    if (Array.isArray(n.languages)) {
        const browserEngine = getBrowserEngineKind();
        // Starting from Chromium 86, there is only a single value in `navigator.language` in Incognito mode:
        // the value of `navigator.language`. Therefore, the value is ignored in this browser.
        if (!(browserEngine === "chromium" /* BrowserEngineKind.Chromium */ && isChromium86OrNewer())) {
            result.push(n.languages);
        }
    }
    else if (typeof n.languages === 'string') {
        const languages = n.languages;
        if (languages) {
            result.push(languages.split(','));
        }
    }
    return result;
}

function areMimeTypesConsistent() {
    if (navigator.mimeTypes === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.mimeTypes is undefined');
    }
    const { mimeTypes } = navigator;
    let isConsistent = Object.getPrototypeOf(mimeTypes) === MimeTypeArray.prototype;
    for (let i = 0; i < mimeTypes.length; i++) {
        isConsistent && (isConsistent = Object.getPrototypeOf(mimeTypes[i]) === MimeType.prototype);
    }
    return isConsistent;
}

async function getNotificationPermissions() {
    if (window.Notification === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'window.Notification is undefined');
    }
    if (navigator.permissions === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.permissions is undefined');
    }
    const { permissions } = navigator;
    if (typeof permissions.query !== 'function') {
        throw new BotdError(-2 /* State.NotFunction */, 'navigator.permissions.query is not a function');
    }
    try {
        const permissionStatus = await permissions.query({ name: 'notifications' });
        return window.Notification.permission === 'denied' && permissionStatus.state === 'prompt';
    }
    catch (e) {
        throw new BotdError(-3 /* State.UnexpectedBehaviour */, 'notificationPermissions signal unexpected behaviour');
    }
}

function getPluginsArray() {
    if (navigator.plugins === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.plugins is undefined');
    }
    if (window.PluginArray === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'window.PluginArray is undefined');
    }
    return navigator.plugins instanceof PluginArray;
}

function getPluginsLength() {
    if (navigator.plugins === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.plugins is undefined');
    }
    if (navigator.plugins.length === undefined) {
        throw new BotdError(-3 /* State.UnexpectedBehaviour */, 'navigator.plugins.length is undefined');
    }
    return navigator.plugins.length;
}

function getProcess() {
    const { process } = window;
    const errorPrefix = 'window.process is';
    if (process === undefined) {
        throw new BotdError(-1 /* State.Undefined */, `${errorPrefix} undefined`);
    }
    if (process && typeof process !== 'object') {
        throw new BotdError(-3 /* State.UnexpectedBehaviour */, `${errorPrefix} not an object`);
    }
    return process;
}

function getProductSub() {
    const { productSub } = navigator;
    if (productSub === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.productSub is undefined');
    }
    return productSub;
}

function getRTT() {
    if (navigator.connection === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.connection is undefined');
    }
    if (navigator.connection.rtt === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.connection.rtt is undefined');
    }
    return navigator.connection.rtt;
}

function getUserAgent() {
    return navigator.userAgent;
}

function getWebDriver() {
    if (navigator.webdriver == undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'navigator.webdriver is undefined');
    }
    return navigator.webdriver;
}

function getWebGL() {
    const canvasElement = document.createElement('canvas');
    if (typeof canvasElement.getContext !== 'function') {
        throw new BotdError(-2 /* State.NotFunction */, 'HTMLCanvasElement.getContext is not a function');
    }
    const webGLContext = canvasElement.getContext('webgl');
    if (webGLContext === null) {
        throw new BotdError(-4 /* State.Null */, 'WebGLRenderingContext is null');
    }
    if (typeof webGLContext.getParameter !== 'function') {
        throw new BotdError(-2 /* State.NotFunction */, 'WebGLRenderingContext.getParameter is not a function');
    }
    const vendor = webGLContext.getParameter(webGLContext.VENDOR);
    const renderer = webGLContext.getParameter(webGLContext.RENDERER);
    return { vendor: vendor, renderer: renderer };
}

function getWindowExternal() {
    if (window.external === undefined) {
        throw new BotdError(-1 /* State.Undefined */, 'window.external is undefined');
    }
    const { external } = window;
    if (typeof external.toString !== 'function') {
        throw new BotdError(-2 /* State.NotFunction */, 'window.external.toString is not a function');
    }
    return external.toString();
}

function getWindowSize() {
    return {
        outerWidth: window.outerWidth,
        outerHeight: window.outerHeight,
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
    };
}

function checkDistinctiveProperties() {
    // The order in the following list matters, because specific types of bots come first, followed by automation technologies.
    const distinctivePropsList = {
        [BotKind.Awesomium]: {
            window: ['awesomium'],
        },
        [BotKind.Cef]: {
            window: ['RunPerfTest'],
        },
        [BotKind.CefSharp]: {
            window: ['CefSharp'],
        },
        [BotKind.CoachJS]: {
            window: ['emit'],
        },
        [BotKind.FMiner]: {
            window: ['fmget_targets'],
        },
        [BotKind.Geb]: {
            window: ['geb'],
        },
        [BotKind.NightmareJS]: {
            window: ['__nightmare', 'nightmare'],
        },
        [BotKind.Phantomas]: {
            window: ['__phantomas'],
        },
        [BotKind.PhantomJS]: {
            window: ['callPhantom', '_phantom'],
        },
        [BotKind.Rhino]: {
            window: ['spawn'],
        },
        [BotKind.Selenium]: {
            window: ['_Selenium_IDE_Recorder', '_selenium', 'calledSelenium', /^([a-z]){3}_.*_(Array|Promise|Symbol)$/],
            document: ['__selenium_evaluate', 'selenium-evaluate', '__selenium_unwrapped'],
        },
        [BotKind.WebDriverIO]: {
            window: ['wdioElectron'],
        },
        [BotKind.WebDriver]: {
            window: [
                'webdriver',
                '__webdriverFunc',
                '__lastWatirAlert',
                '__lastWatirConfirm',
                '__lastWatirPrompt',
                '_WEBDRIVER_ELEM_CACHE',
                'ChromeDriverw',
            ],
            document: [
                '__webdriver_script_fn',
                '__driver_evaluate',
                '__webdriver_evaluate',
                '__fxdriver_evaluate',
                '__driver_unwrapped',
                '__webdriver_unwrapped',
                '__fxdriver_unwrapped',
                '__webdriver_script_fn',
                '__webdriver_script_func',
                '__webdriver_script_function',
                '$cdc_asdjflasutopfhvcZLmcf',
                '$cdc_asdjflasutopfhvcZLmcfl_',
                '$chrome_asyncScriptInfo',
                '__$webdriverAsyncExecutor',
            ],
        },
        [BotKind.HeadlessChrome]: {
            window: ['domAutomation', 'domAutomationController'],
        },
    };
    let botName;
    const result = {};
    const windowProps = getObjectProps(window);
    let documentProps = [];
    if (window.document !== undefined)
        documentProps = getObjectProps(window.document);
    for (botName in distinctivePropsList) {
        const props = distinctivePropsList[botName];
        if (props !== undefined) {
            const windowContains = props.window === undefined ? false : includes(windowProps, ...props.window);
            const documentContains = props.document === undefined || !documentProps.length ? false : includes(documentProps, ...props.document);
            result[botName] = windowContains || documentContains;
        }
    }
    return result;
}

const sources = {
    android: isAndroid,
    browserKind: getBrowserKind,
    browserEngineKind: getBrowserEngineKind,
    documentFocus: getDocumentFocus,
    userAgent: getUserAgent,
    appVersion: getAppVersion,
    rtt: getRTT,
    windowSize: getWindowSize,
    pluginsLength: getPluginsLength,
    pluginsArray: getPluginsArray,
    errorTrace: getErrorTrace,
    productSub: getProductSub,
    windowExternal: getWindowExternal,
    mimeTypesConsistent: areMimeTypesConsistent,
    evalLength: getEvalLength,
    webGL: getWebGL,
    webDriver: getWebDriver,
    languages: getLanguages,
    notificationPermissions: getNotificationPermissions,
    documentElementKeys: getDocumentElementKeys,
    functionBind: getFunctionBind,
    process: getProcess,
    distinctiveProps: checkDistinctiveProperties,
};

/**
 * Class representing a bot detector.
 *
 * @class
 * @implements {BotDetectorInterface}
 */
class BotDetector {
    constructor() {
        this.components = undefined;
        this.detections = undefined;
    }
    getComponents() {
        return this.components;
    }
    getDetections() {
        return this.detections;
    }
    /**
     * @inheritdoc
     */
    detect() {
        if (this.components === undefined) {
            throw new Error("BotDetector.detect can't be called before BotDetector.collect");
        }
        const [detections, finalDetection] = detect(this.components, detectors);
        this.detections = detections;
        return finalDetection;
    }
    /**
     * @inheritdoc
     */
    async collect() {
        this.components = await collect(sources);
        return this.components;
    }
}

/**
 * Sends an unpersonalized AJAX request to collect installation statistics
 */
function monitor() {
    // The FingerprintJS CDN (https://github.com/fingerprintjs/cdn) replaces `window.__fpjs_d_m` with `true`
    if (window.__fpjs_d_m || Math.random() >= 0.001) {
        return;
    }
    try {
        const request = new XMLHttpRequest();
        request.open('get', `https://m1.openfpcdn.io/botd/v${version}/npm-monitoring`, true);
        request.send();
    }
    catch (error) {
        // console.error is ok here because it's an unexpected error handler
        // eslint-disable-next-line no-console
        console.error(error);
    }
}
async function load({ monitoring = true } = {}) {
    if (monitoring) {
        monitor();
    }
    const detector = new BotDetector();
    await detector.collect();
    return detector;
}
var index = { load };

export { BotKind, BotdError, collect, index as default, detect, detectors, load, sources };
