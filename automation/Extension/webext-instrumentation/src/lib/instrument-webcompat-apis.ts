interface PropertyToInstrumentConfiguration {
  className: string;
  property: string;
  objectMissingOnWindow: boolean;
}

declare global {
  interface Window {
    [k: string]: any;
  }
}

export function instrumentWebcompatApis({ instrumentObject }) {
  const nonExistingPropertiesToInstrumentData: any[] = [
    {
      className: "AudioContext",
      property: "baseLatency",
    },
    {
      className: "AudioContext",
      property: "getOutputTimestamp",
    },
    {
      className: "AudioContext",
      property: "resume",
    },
    {
      className: "AudioListener",
      property: "forwardX",
    },
    {
      className: "AudioListener",
      property: "forwardY",
    },
    {
      className: "AudioListener",
      property: "forwardZ",
    },
    {
      className: "AudioListener",
      property: "positionX",
    },
    {
      className: "AudioListener",
      property: "positionY",
    },
    {
      className: "AudioListener",
      property: "positionZ",
    },
    {
      className: "AudioListener",
      property: "upX",
    },
    {
      className: "AudioListener",
      property: "upY",
    },
    {
      className: "AudioListener",
      property: "upZ",
    },
    {
      className: "AudioParam",
      property: "automationRate",
    },
    {
      className: "AudioParam",
      property: "cancelAndHoldAtTime",
    },
    {
      className: "AuthenticatorAttestationResponse",
      property: "getTransports",
    },
    {
      className: "BaseAudioContext",
      property: "audioWorklet",
    },
    {
      className: "BlobEvent",
      property: "timecode",
    },
    {
      className: "CanvasRenderingContext2D",
      property: "getContextAttributes",
    },
    {
      className: "CanvasRenderingContext2D",
      property: "getTransform",
    },
    {
      className: "CanvasRenderingContext2D",
      property: "imageSmoothingQuality",
    },
    {
      className: "Clipboard",
      property: "read",
    },
    {
      className: "Clipboard",
      property: "readText",
    },
    {
      className: "Clipboard",
      property: "write",
    },
    {
      className: "console",
      property: "context",
    },
    {
      className: "console",
      property: "memory",
    },
    { className: "CSS", property: "ch", objectMissingOnWindow: false },
    { className: "CSS", property: "cm", objectMissingOnWindow: false },
    { className: "CSS", property: "deg", objectMissingOnWindow: false },
    { className: "CSS", property: "dpcm", objectMissingOnWindow: false },
    { className: "CSS", property: "dpi", objectMissingOnWindow: false },
    { className: "CSS", property: "dppx", objectMissingOnWindow: false },
    { className: "CSS", property: "em", objectMissingOnWindow: false },
    { className: "CSS", property: "ex", objectMissingOnWindow: false },
    { className: "CSS", property: "fr", objectMissingOnWindow: false },
    { className: "CSS", property: "grad", objectMissingOnWindow: false },
    { className: "CSS", property: "Hz", objectMissingOnWindow: false },
    { className: "CSS", property: "in", objectMissingOnWindow: false },
    { className: "CSS", property: "kHz", objectMissingOnWindow: false },
    { className: "CSS", property: "mm", objectMissingOnWindow: false },
    { className: "CSS", property: "ms", objectMissingOnWindow: false },
    { className: "CSS", property: "number", objectMissingOnWindow: false },
    {
      className: "CSS",
      property: "paintWorklet",
    },
    { className: "CSS", property: "pc", objectMissingOnWindow: false },
    { className: "CSS", property: "percent", objectMissingOnWindow: false },
    { className: "CSS", property: "pt", objectMissingOnWindow: false },
    { className: "CSS", property: "px", objectMissingOnWindow: false },
    { className: "CSS", property: "Q", objectMissingOnWindow: false },
    { className: "CSS", property: "rad", objectMissingOnWindow: false },
    { className: "CSS", property: "rem", objectMissingOnWindow: false },
    { className: "CSS", property: "s", objectMissingOnWindow: false },
    { className: "CSS", property: "turn", objectMissingOnWindow: false },
    { className: "CSS", property: "vh", objectMissingOnWindow: false },
    { className: "CSS", property: "vmax", objectMissingOnWindow: false },
    { className: "CSS", property: "vmin", objectMissingOnWindow: false },
    { className: "CSS", property: "vw", objectMissingOnWindow: false },
    {
      className: "CSSPageRule",
      property: "selectorText",
    },
    {
      className: "CSSStyleDeclaration",
      property: "alignmentBaseline",
    },
    {
      className: "CSSStyleDeclaration",
      property: "backdropFilter",
    },
    {
      className: "CSSStyleDeclaration",
      property: "backgroundRepeatX",
    },
    {
      className: "CSSStyleDeclaration",
      property: "backgroundRepeatY",
    },
    {
      className: "CSSStyleDeclaration",
      property: "baselineShift",
    },
    {
      className: "CSSStyleDeclaration",
      property: "bufferedRendering",
    },
    {
      className: "CSSStyleDeclaration",
      property: "colorRendering",
    },
    {
      className: "CSSStyleDeclaration",
      property: "columnSpan",
    },
    {
      className: "CSSStyleDeclaration",
      property: "d",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubCaptionSide",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextCombine",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextEmphasis",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextEmphasisColor",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextEmphasisStyle",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextOrientation",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextTransform",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubWordBreak",
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubWritingMode",
    },
    {
      className: "CSSStyleDeclaration",
      property: "fontDisplay",
    },
    {
      className: "CSSStyleDeclaration",
      property: "maxZoom",
    },
    {
      className: "CSSStyleDeclaration",
      property: "minZoom",
    },
    {
      className: "CSSStyleDeclaration",
      property: "offset",
    },
    {
      className: "CSSStyleDeclaration",
      property: "offsetDistance",
    },
    {
      className: "CSSStyleDeclaration",
      property: "offsetPath",
    },
    {
      className: "CSSStyleDeclaration",
      property: "offsetRotate",
    },
    {
      className: "CSSStyleDeclaration",
      property: "orientation",
    },
    {
      className: "CSSStyleDeclaration",
      property: "orphans",
    },
    {
      className: "CSSStyleDeclaration",
      property: "page",
    },
    {
      className: "CSSStyleDeclaration",
      property: "scrollSnapStop",
    },
    {
      className: "CSSStyleDeclaration",
      property: "size",
    },
    {
      className: "CSSStyleDeclaration",
      property: "speak",
    },
    {
      className: "CSSStyleDeclaration",
      property: "src",
    },
    {
      className: "CSSStyleDeclaration",
      property: "tabSize",
    },
    {
      className: "CSSStyleDeclaration",
      property: "textDecorationSkipInk",
    },
    {
      className: "CSSStyleDeclaration",
      property: "textSizeAdjust",
    },
    {
      className: "CSSStyleDeclaration",
      property: "textUnderlinePosition",
    },
    {
      className: "CSSStyleDeclaration",
      property: "unicodeRange",
    },
    {
      className: "CSSStyleDeclaration",
      property: "userZoom",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitAppRegion",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderAfter",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderAfterColor",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderAfterStyle",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderAfterWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderBefore",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderBeforeColor",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderBeforeStyle",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderBeforeWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderEnd",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderEndColor",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderEndStyle",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderEndWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderHorizontalSpacing",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderStart",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderStartColor",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderStartStyle",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderStartWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderVerticalSpacing",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBoxDecorationBreak",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBoxReflect",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitClipPath",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnBreakAfter",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnBreakBefore",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnBreakInside",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnCount",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnGap",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnRule",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnRuleColor",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnRuleStyle",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnRuleWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumns",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnSpan",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitFontFeatureSettings",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitFontSizeDelta",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitFontSmoothing",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitHighlight",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitHyphenateCharacter",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitLineBreak",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitLocale",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitLogicalHeight",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitLogicalWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginAfter",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginAfterCollapse",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginBefore",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginBeforeCollapse",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginBottomCollapse",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginCollapse",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginEnd",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginStart",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginTopCollapse",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImage",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageOutset",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageRepeat",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageSlice",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageSource",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskRepeatX",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskRepeatY",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaxLogicalHeight",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaxLogicalWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMinLogicalHeight",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMinLogicalWidth",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitOpacity",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPaddingAfter",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPaddingBefore",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPaddingEnd",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPaddingStart",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPerspectiveOriginX",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPerspectiveOriginY",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPrintColorAdjust",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitRtlOrdering",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitRubyPosition",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitShapeImageThreshold",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitShapeMargin",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitShapeOutside",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTapHighlightColor",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextCombine",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextDecorationsInEffect",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextEmphasis",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextEmphasisColor",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextEmphasisPosition",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextEmphasisStyle",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextOrientation",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextSecurity",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTransformOriginX",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTransformOriginY",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTransformOriginZ",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitUserDrag",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitUserModify",
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitWritingMode",
    },
    {
      className: "CSSStyleDeclaration",
      property: "widows",
    },
    {
      className: "CSSStyleDeclaration",
      property: "zoom",
    },
    {
      className: "CSSStyleRule",
      property: "styleMap",
    },
    {
      className: "CSSStyleSheet",
      property: "replace",
    },
    {
      className: "CSSStyleSheet",
      property: "replaceSync",
    },
    {
      className: "DateTimeFormat",
      property: "formatRange",
    },
    {
      className: "DateTimeFormat",
      property: "formatRangeToParts",
    },
    {
      className: "DeprecatedStorageInfo",
      property: "queryUsageAndQuota",
    },
    {
      className: "DeprecatedStorageInfo",
      property: "requestQuota",
    },
    {
      className: "DeprecatedStorageQuota",
      property: "queryUsageAndQuota",
    },
    {
      className: "DeprecatedStorageQuota",
      property: "requestQuota",
    },
    {
      className: "Document",
      property: "adoptedStyleSheets",
    },
    {
      className: "document",
      property: "adoptedStyleSheets",
    },
    { className: "Document", property: "all", objectMissingOnWindow: false },
    {
      className: "Document",
      property: "captureEvents",
    },
    {
      className: "Document",
      property: "caretRangeFromPoint",
    },
    {
      className: "Document",
      property: "clear",
    },
    {
      className: "Document",
      property: "exitPictureInPicture",
    },
    {
      className: "Document",
      property: "featurePolicy",
    },
    {
      className: "document",
      property: "featurePolicy",
    },
    {
      className: "Document",
      property: "onbeforecopy",
    },
    {
      className: "document",
      property: "onbeforecopy",
    },
    {
      className: "Document",
      property: "onbeforecut",
    },
    {
      className: "document",
      property: "onbeforecut",
    },
    {
      className: "Document",
      property: "onbeforepaste",
    },
    {
      className: "document",
      property: "onbeforepaste",
    },
    {
      className: "Document",
      property: "oncancel",
    },
    {
      className: "document",
      property: "oncancel",
    },
    {
      className: "Document",
      property: "onfreeze",
    },
    {
      className: "document",
      property: "onfreeze",
    },
    {
      className: "Document",
      property: "onmousewheel",
    },
    {
      className: "document",
      property: "onmousewheel",
    },
    {
      className: "Document",
      property: "onresume",
    },
    {
      className: "document",
      property: "onresume",
    },
    {
      className: "Document",
      property: "onsearch",
    },
    {
      className: "document",
      property: "onsearch",
    },
    {
      className: "Document",
      property: "onsecuritypolicyviolation",
    },
    {
      className: "document",
      property: "onsecuritypolicyviolation",
    },
    {
      className: "Document",
      property: "onwebkitfullscreenchange",
    },
    {
      className: "document",
      property: "onwebkitfullscreenchange",
    },
    {
      className: "Document",
      property: "onwebkitfullscreenerror",
    },
    {
      className: "document",
      property: "onwebkitfullscreenerror",
    },
    {
      className: "Document",
      property: "pictureInPictureElement",
    },
    {
      className: "document",
      property: "pictureInPictureElement",
    },
    {
      className: "Document",
      property: "pictureInPictureEnabled",
    },
    {
      className: "document",
      property: "pictureInPictureEnabled",
    },
    {
      className: "Document",
      property: "registerElement",
    },
    {
      className: "Document",
      property: "releaseEvents",
    },
    {
      className: "Document",
      property: "wasDiscarded",
    },
    {
      className: "document",
      property: "wasDiscarded",
    },
    {
      className: "Document",
      property: "webkitCancelFullScreen",
    },
    {
      className: "Document",
      property: "webkitCurrentFullScreenElement",
    },
    {
      className: "document",
      property: "webkitCurrentFullScreenElement",
    },
    {
      className: "Document",
      property: "webkitExitFullscreen",
    },
    {
      className: "Document",
      property: "webkitFullscreenElement",
    },
    {
      className: "document",
      property: "webkitFullscreenElement",
    },
    {
      className: "Document",
      property: "webkitFullscreenEnabled",
    },
    {
      className: "document",
      property: "webkitFullscreenEnabled",
    },
    {
      className: "Document",
      property: "webkitHidden",
    },
    {
      className: "document",
      property: "webkitHidden",
    },
    {
      className: "Document",
      property: "webkitIsFullScreen",
    },
    {
      className: "document",
      property: "webkitIsFullScreen",
    },
    {
      className: "Document",
      property: "webkitVisibilityState",
    },
    {
      className: "document",
      property: "webkitVisibilityState",
    },
    {
      className: "Document",
      property: "xmlEncoding",
    },
    {
      className: "document",
      property: "xmlEncoding",
    },
    {
      className: "Document",
      property: "xmlStandalone",
    },
    {
      className: "document",
      property: "xmlStandalone",
    },
    {
      className: "Document",
      property: "xmlVersion",
    },
    {
      className: "document",
      property: "xmlVersion",
    },
    {
      className: "Element",
      property: "attributeStyleMap",
    },
    {
      className: "Element",
      property: "computedStyleMap",
    },
    {
      className: "Element",
      property: "createShadowRoot",
    },
    {
      className: "Element",
      property: "getDestinationInsertionPoints",
    },
    {
      className: "Element",
      property: "onbeforecopy",
    },
    {
      className: "Element",
      property: "onbeforecut",
    },
    {
      className: "Element",
      property: "onbeforepaste",
    },
    {
      className: "Element",
      property: "onsearch",
    },
    {
      className: "Element",
      property: "onwebkitfullscreenchange",
    },
    {
      className: "Element",
      property: "onwebkitfullscreenerror",
    },
    { className: "Element", property: "part", objectMissingOnWindow: false },
    {
      className: "Element",
      property: "scrollIntoViewIfNeeded",
    },
    {
      className: "Element",
      property: "webkitRequestFullScreen",
    },
    {
      className: "Element",
      property: "webkitRequestFullscreen",
    },
    {
      className: "Error",
      property: "captureStackTrace",
    },
    {
      className: "Error",
      property: "stackTraceLimit",
    },
    {
      className: "event",
      property: "fromElement",
    },
    { className: "Event", property: "path", objectMissingOnWindow: false },
    { className: "event", property: "path", objectMissingOnWindow: false },
    {
      className: "event",
      property: "sourceCapabilities",
    },
    {
      className: "event",
      property: "toElement",
    },
    {
      className: "FeaturePolicy",
      property: "allowedFeatures",
    },
    {
      className: "FeaturePolicy",
      property: "allowsFeature",
    },
    {
      className: "FeaturePolicy",
      property: "features",
    },
    {
      className: "FeaturePolicy",
      property: "getAllowlistForFeature",
    },
    {
      className: "File",
      property: "lastModifiedDate",
    },
    {
      className: "Gamepad",
      property: "vibrationActuator",
    },
    {
      className: "GamepadHapticActuator",
      property: "playEffect",
    },
    {
      className: "GamepadHapticActuator",
      property: "reset",
    },
    {
      className: "Geolocation",
      property: "clearWatch",
    },
    {
      className: "Geolocation",
      property: "getCurrentPosition",
    },
    {
      className: "Geolocation",
      property: "watchPosition",
    },
    {
      className: "HTMLCanvasElement",
      property: "transferControlToOffscreen",
    },
    {
      className: "HTMLDocument",
      property: "adoptedStyleSheets",
    },
    {
      className: "HTMLDocument",
      property: "featurePolicy",
    },
    {
      className: "HTMLDocument",
      property: "onbeforecopy",
    },
    {
      className: "HTMLDocument",
      property: "onbeforecut",
    },
    {
      className: "HTMLDocument",
      property: "onbeforepaste",
    },
    {
      className: "HTMLDocument",
      property: "oncancel",
    },
    {
      className: "HTMLDocument",
      property: "onfreeze",
    },
    {
      className: "HTMLDocument",
      property: "onmousewheel",
    },
    {
      className: "HTMLDocument",
      property: "onresume",
    },
    {
      className: "HTMLDocument",
      property: "onsearch",
    },
    {
      className: "HTMLDocument",
      property: "onsecuritypolicyviolation",
    },
    {
      className: "HTMLDocument",
      property: "onwebkitfullscreenchange",
    },
    {
      className: "HTMLDocument",
      property: "onwebkitfullscreenerror",
    },
    {
      className: "HTMLDocument",
      property: "pictureInPictureElement",
    },
    {
      className: "HTMLDocument",
      property: "pictureInPictureEnabled",
    },
    {
      className: "HTMLDocument",
      property: "wasDiscarded",
    },
    {
      className: "HTMLDocument",
      property: "webkitCurrentFullScreenElement",
    },
    {
      className: "HTMLDocument",
      property: "webkitFullscreenElement",
    },
    {
      className: "HTMLDocument",
      property: "webkitFullscreenEnabled",
    },
    {
      className: "HTMLDocument",
      property: "webkitHidden",
    },
    {
      className: "HTMLDocument",
      property: "webkitIsFullScreen",
    },
    {
      className: "HTMLDocument",
      property: "webkitVisibilityState",
    },
    {
      className: "HTMLDocument",
      property: "xmlEncoding",
    },
    {
      className: "HTMLDocument",
      property: "xmlStandalone",
    },
    {
      className: "HTMLDocument",
      property: "xmlVersion",
    },
    {
      className: "HTMLElement",
      property: "autocapitalize",
    },
    {
      className: "HTMLElement",
      property: "inputMode",
    },
    {
      className: "HTMLElement",
      property: "nonce",
    },
    {
      className: "HTMLElement",
      property: "oncancel",
    },
    {
      className: "HTMLElement",
      property: "onmousewheel",
    },
    {
      className: "HTMLElement",
      property: "onselectionchange",
    },
    {
      className: "HTMLElement",
      property: "outerText",
    },
    {
      className: "HTMLElement",
      property: "translate",
    },
    {
      className: "HTMLFormElement",
      property: "requestSubmit",
    },
    {
      className: "HTMLIFrameElement",
      property: "allow",
    },
    {
      className: "HTMLIFrameElement",
      property: "csp",
    },
    {
      className: "HTMLIFrameElement",
      property: "featurePolicy",
    },
    {
      className: "HTMLInputElement",
      property: "dirName",
    },
    {
      className: "HTMLInputElement",
      property: "incremental",
    },
    {
      className: "HTMLLinkElement",
      property: "imageSizes",
    },
    {
      className: "HTMLLinkElement",
      property: "imageSrcset",
    },
    {
      className: "HTMLLinkElement",
      property: "import",
    },
    {
      className: "HTMLMediaElement",
      property: "captureStream",
    },
    {
      className: "HTMLMediaElement",
      property: "controlsList",
    },
    {
      className: "HTMLMediaElement",
      property: "disableRemotePlayback",
    },
    {
      className: "HTMLMediaElement",
      property: "remote",
    },
    {
      className: "HTMLMediaElement",
      property: "setSinkId",
    },
    {
      className: "HTMLMediaElement",
      property: "sinkId",
    },
    {
      className: "HTMLMediaElement",
      property: "webkitAudioDecodedByteCount",
    },
    {
      className: "HTMLMediaElement",
      property: "webkitVideoDecodedByteCount",
    },
    {
      className: "HTMLTextAreaElement",
      property: "dirName",
    },
    {
      className: "HTMLVideoElement",
      property: "disablePictureInPicture",
    },
    {
      className: "HTMLVideoElement",
      property: "onenterpictureinpicture",
    },
    {
      className: "HTMLVideoElement",
      property: "onleavepictureinpicture",
    },
    {
      className: "HTMLVideoElement",
      property: "playsInline",
    },
    {
      className: "HTMLVideoElement",
      property: "requestPictureInPicture",
    },
    {
      className: "HTMLVideoElement",
      property: "webkitDecodedFrameCount",
    },
    {
      className: "HTMLVideoElement",
      property: "webkitDisplayingFullscreen",
    },
    {
      className: "HTMLVideoElement",
      property: "webkitDroppedFrameCount",
    },
    {
      className: "HTMLVideoElement",
      property: "webkitEnterFullScreen",
    },
    {
      className: "HTMLVideoElement",
      property: "webkitEnterFullscreen",
    },
    {
      className: "HTMLVideoElement",
      property: "webkitExitFullScreen",
    },
    {
      className: "HTMLVideoElement",
      property: "webkitExitFullscreen",
    },
    {
      className: "HTMLVideoElement",
      property: "webkitSupportsFullscreen",
    },
    {
      className: "IDBCursor",
      property: "request",
    },
    {
      className: "IDBFactory",
      property: "databases",
    },
    {
      className: "IDBTransaction",
      property: "commit",
    },
    {
      className: "IDBVersionChangeEvent",
      property: "dataLoss",
    },
    {
      className: "IDBVersionChangeEvent",
      property: "dataLossMessage",
    },
    {
      className: "ImageBitmapRenderingContext",
      property: "canvas",
    },
    {
      className: "InputEvent",
      property: "getTargetRanges",
    },
    {
      className: "IntersectionObserver",
      property: "delay",
    },
    {
      className: "IntersectionObserver",
      property: "trackVisibility",
    },
    {
      className: "IntersectionObserverEntry",
      property: "isVisible",
    },
    {
      className: "Intl",
      property: "ListFormat",
    },
    { className: "Intl", property: "Locale", objectMissingOnWindow: false },
    {
      className: "Intl",
      property: "v8BreakIterator",
    },
    {
      className: "ListFormat",
      property: "format",
    },
    {
      className: "ListFormat",
      property: "formatToParts",
    },
    {
      className: "ListFormat",
      property: "resolvedOptions",
    },
    {
      className: "ListFormat",
      property: "supportedLocalesOf",
    },
    {
      className: "Locale",
      property: "baseName",
    },
    {
      className: "Locale",
      property: "calendar",
    },
    {
      className: "Locale",
      property: "caseFirst",
    },
    {
      className: "Locale",
      property: "collation",
    },
    {
      className: "Locale",
      property: "hourCycle",
    },
    {
      className: "Locale",
      property: "language",
    },
    {
      className: "Locale",
      property: "maximize",
    },
    {
      className: "Locale",
      property: "minimize",
    },
    {
      className: "Locale",
      property: "numberingSystem",
    },
    {
      className: "Locale",
      property: "numeric",
    },
    {
      className: "Locale",
      property: "region",
    },
    {
      className: "Locale",
      property: "script",
    },
    {
      className: "location",
      property: "ancestorOrigins",
    },
    {
      className: "MediaElementAudioSourceNode",
      property: "mediaElement",
    },
    {
      className: "MediaKeys",
      property: "getStatusForPolicy",
    },
    {
      className: "MediaRecorder",
      property: "audioBitsPerSecond",
    },
    {
      className: "MediaRecorder",
      property: "videoBitsPerSecond",
    },
    {
      className: "MediaSource",
      property: "onsourceclose",
    },
    {
      className: "MediaStream",
      property: "onactive",
    },
    {
      className: "MediaStream",
      property: "oninactive",
    },
    {
      className: "MediaStreamAudioSourceNode",
      property: "mediaStream",
    },
    {
      className: "MediaStreamTrack",
      property: "contentHint",
    },
    {
      className: "MediaStreamTrack",
      property: "getCapabilities",
    },
    {
      className: "MemoryInfo",
      property: "jsHeapSizeLimit",
    },
    {
      className: "MemoryInfo",
      property: "totalJSHeapSize",
    },
    {
      className: "MemoryInfo",
      property: "usedJSHeapSize",
    },
    {
      className: "MessageEvent",
      property: "userActivation",
    },
    {
      className: "MimeTypeArray",
      property: "application/pdf",
    },
    {
      className: "MimeTypeArray",
      property: "application/x-google-chrome-pdf",
    },
    {
      className: "MimeTypeArray",
      property: "application/x-nacl",
    },
    {
      className: "MimeTypeArray",
      property: "application/x-pnacl",
    },
    {
      className: "MouseEvent",
      property: "fromElement",
    },
    {
      className: "MouseEvent",
      property: "path",
    },
    {
      className: "MouseEvent",
      property: "sourceCapabilities",
    },
    {
      className: "MouseEvent",
      property: "toElement",
    },
    {
      className: "Navigator",
      property: "bluetooth",
    },
    {
      className: "navigator",
      property: "bluetooth",
    },
    {
      className: "Navigator",
      property: "connection",
    },
    {
      className: "navigator",
      property: "connection",
    },
    {
      className: "Navigator",
      property: "deviceMemory",
    },
    {
      className: "navigator",
      property: "deviceMemory",
    },
    {
      className: "Navigator",
      property: "getBattery",
    },
    {
      className: "Navigator",
      property: "getUserMedia",
    },
    {
      className: "Navigator",
      property: "keyboard",
    },
    {
      className: "navigator",
      property: "keyboard",
    },
    {
      className: "Navigator",
      property: "locks",
    },
    {
      className: "navigator",
      property: "locks",
    },
    {
      className: "Navigator",
      property: "mediaSession",
    },
    {
      className: "navigator",
      property: "mediaSession",
    },
    {
      className: "Navigator",
      property: "presentation",
    },
    {
      className: "navigator",
      property: "presentation",
    },
    {
      className: "Navigator",
      property: "requestMIDIAccess",
    },
    {
      className: "Navigator",
      property: "unregisterProtocolHandler",
    },
    {
      className: "Navigator",
      property: "usb",
    },
    {
      className: "navigator",
      property: "usb",
    },
    {
      className: "Navigator",
      property: "userActivation",
    },
    {
      className: "navigator",
      property: "userActivation",
    },
    {
      className: "Navigator",
      property: "webkitGetUserMedia",
    },
    {
      className: "Navigator",
      property: "webkitPersistentStorage",
    },
    {
      className: "navigator",
      property: "webkitPersistentStorage",
    },
    {
      className: "Navigator",
      property: "webkitTemporaryStorage",
    },
    {
      className: "navigator",
      property: "webkitTemporaryStorage",
    },
    {
      className: "Notification",
      property: "actions",
    },
    {
      className: "Notification",
      property: "badge",
    },
    {
      className: "Notification",
      property: "maxActions",
    },
    {
      className: "Notification",
      property: "renotify",
    },
    {
      className: "Notification",
      property: "requireInteraction",
    },
    {
      className: "Notification",
      property: "silent",
    },
    {
      className: "Notification",
      property: "timestamp",
    },
    {
      className: "Notification",
      property: "vibrate",
    },
    {
      className: "OfflineAudioContext",
      property: "resume",
    },
    {
      className: "OfflineAudioContext",
      property: "suspend",
    },
    {
      className: "Performance",
      property: "memory",
    },
    {
      className: "performance",
      property: "memory",
    },
    {
      className: "Plugin",
      property: "application/pdf",
    },
    {
      className: "Plugin",
      property: "application/x-google-chrome-pdf",
    },
    {
      className: "Plugin",
      property: "application/x-nacl",
    },
    {
      className: "Plugin",
      property: "application/x-pnacl",
    },
    {
      className: "PluginArray",
      property: "Chrome PDF Plugin",
    },
    {
      className: "PluginArray",
      property: "Chrome PDF Viewer",
    },
    {
      className: "PluginArray",
      property: "Native Client",
    },
    {
      className: "Promise",
      property: "allSettled",
    },
    {
      className: "PushManager",
      property: "supportedContentEncodings",
    },
    {
      className: "PushSubscription",
      property: "expirationTime",
    },
    {
      className: "PushSubscriptionOptions",
      property: "userVisibleOnly",
    },
    {
      className: "Range",
      property: "collapsed",
    },
    {
      className: "Range",
      property: "endContainer",
    },
    {
      className: "Range",
      property: "endOffset",
    },
    { className: "Range", property: "expand", objectMissingOnWindow: false },
    {
      className: "Range",
      property: "startContainer",
    },
    {
      className: "Range",
      property: "startOffset",
    },
    {
      className: "ReadableStream",
      property: "pipeThrough",
    },
    {
      className: "ReadableStream",
      property: "pipeTo",
    },
    {
      className: "RegExp",
      property: "dotAll",
    },
    {
      className: "RelativeTimeFormat",
      property: "formatToParts",
    },
    {
      className: "Request",
      property: "isHistoryNavigation",
    },
    {
      className: "Request",
      property: "keepalive",
    },
    {
      className: "RTCCertificate",
      property: "getFingerprints",
    },
    {
      className: "RTCDataChannel",
      property: "maxRetransmitTime",
    },
    {
      className: "RTCDTMFSender",
      property: "canInsertDTMF",
    },
    {
      className: "RTCIceCandidate",
      property: "address",
    },
    {
      className: "RTCIceCandidate",
      property: "component",
    },
    {
      className: "RTCIceCandidate",
      property: "foundation",
    },
    {
      className: "RTCIceCandidate",
      property: "port",
    },
    {
      className: "RTCIceCandidate",
      property: "priority",
    },
    {
      className: "RTCIceCandidate",
      property: "protocol",
    },
    {
      className: "RTCIceCandidate",
      property: "relatedAddress",
    },
    {
      className: "RTCIceCandidate",
      property: "relatedPort",
    },
    {
      className: "RTCIceCandidate",
      property: "tcpType",
    },
    {
      className: "RTCIceCandidate",
      property: "type",
    },
    {
      className: "RTCPeerConnection",
      property: "connectionState",
    },
    {
      className: "RTCPeerConnection",
      property: "createDTMFSender",
    },
    {
      className: "RTCPeerConnection",
      property: "onconnectionstatechange",
    },
    {
      className: "RTCPeerConnection",
      property: "onremovestream",
    },
    {
      className: "RTCPeerConnection",
      property: "removeStream",
    },
    {
      className: "RTCPeerConnection",
      property: "sctp",
    },
    {
      className: "RTCPeerConnection",
      property: "setConfiguration",
    },
    {
      className: "RTCRtpReceiver",
      property: "getCapabilities",
    },
    {
      className: "RTCRtpReceiver",
      property: "getParameters",
    },
    {
      className: "RTCRtpReceiver",
      property: "rtcpTransport",
    },
    {
      className: "RTCRtpReceiver",
      property: "transport",
    },
    {
      className: "RTCRtpSender",
      property: "getCapabilities",
    },
    {
      className: "RTCRtpSender",
      property: "rtcpTransport",
    },
    {
      className: "RTCRtpSender",
      property: "setStreams",
    },
    {
      className: "RTCRtpSender",
      property: "transport",
    },
    {
      className: "RTCRtpTransceiver",
      property: "setCodecPreferences",
    },
    {
      className: "Selection",
      property: "baseNode",
    },
    {
      className: "Selection",
      property: "baseOffset",
    },
    {
      className: "Selection",
      property: "extentNode",
    },
    {
      className: "Selection",
      property: "extentOffset",
    },
    {
      className: "ServiceWorkerRegistration",
      property: "active",
    },
    {
      className: "ServiceWorkerRegistration",
      property: "backgroundFetch",
    },
    {
      className: "ServiceWorkerRegistration",
      property: "installing",
    },
    {
      className: "ServiceWorkerRegistration",
      property: "navigationPreload",
    },
    {
      className: "ServiceWorkerRegistration",
      property: "paymentManager",
    },
    {
      className: "ServiceWorkerRegistration",
      property: "sync",
    },
    {
      className: "ServiceWorkerRegistration",
      property: "waiting",
    },
    {
      className: "ShadowRoot",
      property: "adoptedStyleSheets",
    },
    {
      className: "ShadowRoot",
      property: "delegatesFocus",
    },
    {
      className: "ShadowRoot",
      property: "getSelection",
    },
    {
      className: "ShadowRoot",
      property: "pictureInPictureElement",
    },
    {
      className: "SpeechGrammar",
      property: "src",
    },
    {
      className: "SpeechGrammar",
      property: "weight",
    },
    {
      className: "SpeechGrammarList",
      property: "addFromString",
    },
    {
      className: "SpeechGrammarList",
      property: "addFromUri",
    },
    {
      className: "SpeechGrammarList",
      property: "item",
    },
    {
      className: "SpeechGrammarList",
      property: "length",
    },
    {
      className: "SpeechRecognition",
      property: "abort",
    },
    {
      className: "SpeechRecognition",
      property: "continuous",
    },
    {
      className: "SpeechRecognition",
      property: "grammars",
    },
    {
      className: "SpeechRecognition",
      property: "interimResults",
    },
    {
      className: "SpeechRecognition",
      property: "lang",
    },
    {
      className: "SpeechRecognition",
      property: "maxAlternatives",
    },
    {
      className: "SpeechRecognition",
      property: "onaudioend",
    },
    {
      className: "SpeechRecognition",
      property: "onaudiostart",
    },
    {
      className: "SpeechRecognition",
      property: "onend",
    },
    {
      className: "SpeechRecognition",
      property: "onerror",
    },
    {
      className: "SpeechRecognition",
      property: "onnomatch",
    },
    {
      className: "SpeechRecognition",
      property: "onresult",
    },
    {
      className: "SpeechRecognition",
      property: "onsoundend",
    },
    {
      className: "SpeechRecognition",
      property: "onsoundstart",
    },
    {
      className: "SpeechRecognition",
      property: "onspeechend",
    },
    {
      className: "SpeechRecognition",
      property: "onspeechstart",
    },
    {
      className: "SpeechRecognition",
      property: "onstart",
    },
    {
      className: "SpeechRecognition",
      property: "start",
    },
    {
      className: "SpeechRecognition",
      property: "stop",
    },
    {
      className: "SpeechRecognitionError",
      property: "error",
    },
    {
      className: "SpeechRecognitionError",
      property: "message",
    },
    {
      className: "SpeechRecognitionEvent",
      property: "emma",
    },
    {
      className: "SpeechRecognitionEvent",
      property: "interpretation",
    },
    {
      className: "SpeechRecognitionEvent",
      property: "resultIndex",
    },
    {
      className: "SpeechRecognitionEvent",
      property: "results",
    },
    {
      className: "StaticRange",
      property: "collapsed",
    },
    {
      className: "StaticRange",
      property: "endContainer",
    },
    {
      className: "StaticRange",
      property: "endOffset",
    },
    {
      className: "StaticRange",
      property: "startContainer",
    },
    {
      className: "StaticRange",
      property: "startOffset",
    },
    {
      className: "StyleMedia",
      property: "matchMedium",
    },
    {
      className: "StyleMedia",
      property: "type",
    },
    {
      className: "SVGAnimationElement",
      property: "onbegin",
    },
    {
      className: "SVGAnimationElement",
      property: "onend",
    },
    {
      className: "SVGAnimationElement",
      property: "onrepeat",
    },
    {
      className: "SVGElement",
      property: "nonce",
    },
    {
      className: "SVGElement",
      property: "oncancel",
    },
    {
      className: "SVGElement",
      property: "onmousewheel",
    },
    {
      className: "SVGElement",
      property: "onselectionchange",
    },
    {
      className: "SVGMaskElement",
      property: "requiredExtensions",
    },
    {
      className: "SVGMaskElement",
      property: "systemLanguage",
    },
    {
      className: "SVGPatternElement",
      property: "requiredExtensions",
    },
    {
      className: "SVGPatternElement",
      property: "systemLanguage",
    },
    {
      className: "SVGStyleElement",
      property: "disabled",
    },
    {
      className: "SVGSVGElement",
      property: "checkEnclosure",
    },
    {
      className: "SVGSVGElement",
      property: "checkIntersection",
    },
    {
      className: "SVGSVGElement",
      property: "getEnclosureList",
    },
    {
      className: "SVGSVGElement",
      property: "getIntersectionList",
    },
    {
      className: "Text",
      property: "getDestinationInsertionPoints",
    },
    {
      className: "UIEvent",
      property: "sourceCapabilities",
    },
    {
      className: "v8BreakIterator",
      property: "adoptText",
    },
    {
      className: "v8BreakIterator",
      property: "breakType",
    },
    {
      className: "v8BreakIterator",
      property: "current",
    },
    {
      className: "v8BreakIterator",
      property: "first",
    },
    {
      className: "v8BreakIterator",
      property: "next",
    },
    {
      className: "v8BreakIterator",
      property: "resolvedOptions",
    },
    {
      className: "v8BreakIterator",
      property: "supportedLocalesOf",
    },
    {
      className: "WheelEvent",
      property: "wheelDelta",
    },
    {
      className: "WheelEvent",
      property: "wheelDeltaX",
    },
    {
      className: "WheelEvent",
      property: "wheelDeltaY",
    },
    {
      className: "Window",
      property: "AbsoluteOrientationSensor",
    },
    {
      className: "Window",
      property: "Accelerometer",
    },
    {
      className: "Window",
      property: "ApplicationCache",
    },
    {
      className: "Window",
      property: "ApplicationCacheErrorEvent",
    },
    {
      className: "Window",
      property: "Atomics",
    },
    {
      className: "Window",
      property: "AudioParamMap",
    },
    {
      className: "Window",
      property: "AudioWorklet",
    },
    {
      className: "Window",
      property: "AudioWorkletNode",
    },
    {
      className: "Window",
      property: "BackgroundFetchManager",
    },
    {
      className: "Window",
      property: "BackgroundFetchRecord",
    },
    {
      className: "Window",
      property: "BackgroundFetchRegistration",
    },
    {
      className: "Window",
      property: "BeforeInstallPromptEvent",
    },
    {
      className: "Window",
      property: "Bluetooth",
    },
    {
      className: "Window",
      property: "BluetoothCharacteristicProperties",
    },
    {
      className: "Window",
      property: "BluetoothDevice",
    },
    {
      className: "Window",
      property: "BluetoothRemoteGATTCharacteristic",
    },
    {
      className: "Window",
      property: "BluetoothRemoteGATTDescriptor",
    },
    {
      className: "Window",
      property: "BluetoothRemoteGATTServer",
    },
    {
      className: "Window",
      property: "BluetoothRemoteGATTService",
    },
    {
      className: "Window",
      property: "BluetoothUUID",
    },
    {
      className: "Window",
      property: "CanvasCaptureMediaStreamTrack",
    },
    {
      className: "Window",
      property: "chrome",
    },
    {
      className: "Window",
      property: "clientInformation",
    },
    {
      className: "Window",
      property: "ClipboardItem",
    },
    {
      className: "Window",
      property: "CSSImageValue",
    },
    {
      className: "Window",
      property: "CSSKeywordValue",
    },
    {
      className: "Window",
      property: "CSSMathInvert",
    },
    {
      className: "Window",
      property: "CSSMathMax",
    },
    {
      className: "Window",
      property: "CSSMathMin",
    },
    {
      className: "Window",
      property: "CSSMathNegate",
    },
    {
      className: "Window",
      property: "CSSMathProduct",
    },
    {
      className: "Window",
      property: "CSSMathSum",
    },
    {
      className: "Window",
      property: "CSSMathValue",
    },
    {
      className: "Window",
      property: "CSSMatrixComponent",
    },
    {
      className: "Window",
      property: "CSSNumericArray",
    },
    {
      className: "Window",
      property: "CSSNumericValue",
    },
    {
      className: "Window",
      property: "CSSPerspective",
    },
    {
      className: "Window",
      property: "CSSPositionValue",
    },
    {
      className: "Window",
      property: "CSSRotate",
    },
    {
      className: "Window",
      property: "CSSScale",
    },
    {
      className: "Window",
      property: "CSSSkew",
    },
    {
      className: "Window",
      property: "CSSSkewX",
    },
    {
      className: "Window",
      property: "CSSSkewY",
    },
    {
      className: "Window",
      property: "CSSStyleValue",
    },
    {
      className: "Window",
      property: "CSSTransformComponent",
    },
    {
      className: "Window",
      property: "CSSTransformValue",
    },
    {
      className: "Window",
      property: "CSSTranslate",
    },
    {
      className: "Window",
      property: "CSSUnitValue",
    },
    {
      className: "Window",
      property: "CSSUnparsedValue",
    },
    {
      className: "Window",
      property: "CSSVariableReferenceValue",
    },
    {
      className: "Window",
      property: "defaultStatus",
    },
    {
      className: "Window",
      property: "defaultstatus",
    },
    {
      className: "Window",
      property: "DeviceMotionEventAcceleration",
    },
    {
      className: "Window",
      property: "DeviceMotionEventRotationRate",
    },
    {
      className: "Window",
      property: "DOMError",
    },
    {
      className: "Window",
      property: "EnterPictureInPictureEvent",
    },
    {
      className: "Window",
      property: "External",
    },
    {
      className: "Window",
      property: "FederatedCredential",
    },
    {
      className: "Window",
      property: "Gyroscope",
    },
    {
      className: "Window",
      property: "HTMLContentElement",
    },
    {
      className: "Window",
      property: "HTMLDialogElement",
    },
    {
      className: "Window",
      property: "HTMLShadowElement",
    },
    {
      className: "Window",
      property: "ImageCapture",
    },
    {
      className: "Window",
      property: "InputDeviceCapabilities",
    },
    {
      className: "Window",
      property: "InputDeviceInfo",
    },
    {
      className: "Window",
      property: "Keyboard",
    },
    {
      className: "Window",
      property: "KeyboardLayoutMap",
    },
    {
      className: "Window",
      property: "LinearAccelerationSensor",
    },
    { className: "Window", property: "Lock", objectMissingOnWindow: false },
    {
      className: "Window",
      property: "LockManager",
    },
    {
      className: "Window",
      property: "MediaMetadata",
    },
    {
      className: "Window",
      property: "MediaSession",
    },
    {
      className: "Window",
      property: "MediaSettingsRange",
    },
    {
      className: "Window",
      property: "MIDIAccess",
    },
    {
      className: "Window",
      property: "MIDIConnectionEvent",
    },
    {
      className: "Window",
      property: "MIDIInput",
    },
    {
      className: "Window",
      property: "MIDIInputMap",
    },
    {
      className: "Window",
      property: "MIDIMessageEvent",
    },
    {
      className: "Window",
      property: "MIDIOutput",
    },
    {
      className: "Window",
      property: "MIDIOutputMap",
    },
    {
      className: "Window",
      property: "MIDIPort",
    },
    {
      className: "Window",
      property: "NavigationPreloadManager",
    },
    {
      className: "Window",
      property: "NetworkInformation",
    },
    {
      className: "Window",
      property: "offscreenBuffering",
    },
    {
      className: "Window",
      property: "OffscreenCanvas",
    },
    {
      className: "Window",
      property: "OffscreenCanvasRenderingContext2D",
    },
    {
      className: "Window",
      property: "onappinstalled",
    },
    {
      className: "Window",
      property: "onbeforeinstallprompt",
    },
    {
      className: "Window",
      property: "oncancel",
    },
    {
      className: "Window",
      property: "ondeviceorientationabsolute",
    },
    {
      className: "Window",
      property: "onmousewheel",
    },
    {
      className: "Window",
      property: "onsearch",
    },
    {
      className: "Window",
      property: "onselectionchange",
    },
    {
      className: "Window",
      property: "openDatabase",
    },
    {
      className: "Window",
      property: "OrientationSensor",
    },
    {
      className: "Window",
      property: "OverconstrainedError",
    },
    {
      className: "Window",
      property: "PasswordCredential",
    },
    {
      className: "Window",
      property: "PaymentAddress",
    },
    {
      className: "Window",
      property: "PaymentInstruments",
    },
    {
      className: "Window",
      property: "PaymentManager",
    },
    {
      className: "Window",
      property: "PaymentMethodChangeEvent",
    },
    {
      className: "Window",
      property: "PaymentRequest",
    },
    {
      className: "Window",
      property: "PaymentRequestUpdateEvent",
    },
    {
      className: "Window",
      property: "PaymentResponse",
    },
    {
      className: "Window",
      property: "PerformanceEventTiming",
    },
    {
      className: "Window",
      property: "PerformanceLongTaskTiming",
    },
    {
      className: "Window",
      property: "PerformancePaintTiming",
    },
    {
      className: "Window",
      property: "PhotoCapabilities",
    },
    {
      className: "Window",
      property: "PictureInPictureWindow",
    },
    {
      className: "Window",
      property: "Presentation",
    },
    {
      className: "Window",
      property: "PresentationAvailability",
    },
    {
      className: "Window",
      property: "PresentationConnection",
    },
    {
      className: "Window",
      property: "PresentationConnectionAvailableEvent",
    },
    {
      className: "Window",
      property: "PresentationConnectionCloseEvent",
    },
    {
      className: "Window",
      property: "PresentationConnectionList",
    },
    {
      className: "Window",
      property: "PresentationReceiver",
    },
    {
      className: "Window",
      property: "PresentationRequest",
    },
    {
      className: "Window",
      property: "RelativeOrientationSensor",
    },
    {
      className: "Window",
      property: "RemotePlayback",
    },
    {
      className: "Window",
      property: "ReportingObserver",
    },
    {
      className: "Window",
      property: "RTCDtlsTransport",
    },
    {
      className: "Window",
      property: "RTCError",
    },
    {
      className: "Window",
      property: "RTCErrorEvent",
    },
    {
      className: "Window",
      property: "RTCIceTransport",
    },
    {
      className: "Window",
      property: "RTCSctpTransport",
    },
    {
      className: "Window",
      property: "Sensor",
    },
    {
      className: "Window",
      property: "SensorErrorEvent",
    },
    {
      className: "Window",
      property: "SharedArrayBuffer",
    },
    {
      className: "Window",
      property: "styleMedia",
    },
    {
      className: "Window",
      property: "StylePropertyMap",
    },
    {
      className: "Window",
      property: "StylePropertyMapReadOnly",
    },
    {
      className: "Window",
      property: "SVGDiscardElement",
    },
    {
      className: "Window",
      property: "SyncManager",
    },
    {
      className: "Window",
      property: "TaskAttributionTiming",
    },
    {
      className: "Window",
      property: "TextDecoderStream",
    },
    {
      className: "Window",
      property: "TextEncoderStream",
    },
    {
      className: "Window",
      property: "TextEvent",
    },
    { className: "Window", property: "Touch", objectMissingOnWindow: false },
    {
      className: "Window",
      property: "TouchEvent",
    },
    {
      className: "Window",
      property: "TouchList",
    },
    {
      className: "Window",
      property: "TransformStream",
    },
    { className: "Window", property: "USB", objectMissingOnWindow: false },
    {
      className: "Window",
      property: "USBAlternateInterface",
    },
    {
      className: "Window",
      property: "USBConfiguration",
    },
    {
      className: "Window",
      property: "USBConnectionEvent",
    },
    {
      className: "Window",
      property: "USBDevice",
    },
    {
      className: "Window",
      property: "USBEndpoint",
    },
    {
      className: "Window",
      property: "USBInterface",
    },
    {
      className: "Window",
      property: "USBInTransferResult",
    },
    {
      className: "Window",
      property: "USBIsochronousInTransferPacket",
    },
    {
      className: "Window",
      property: "USBIsochronousInTransferResult",
    },
    {
      className: "Window",
      property: "USBIsochronousOutTransferPacket",
    },
    {
      className: "Window",
      property: "USBIsochronousOutTransferResult",
    },
    {
      className: "Window",
      property: "USBOutTransferResult",
    },
    {
      className: "Window",
      property: "UserActivation",
    },
    {
      className: "Window",
      property: "visualViewport",
    },
    {
      className: "Window",
      property: "webkitCancelAnimationFrame",
    },
    {
      className: "Window",
      property: "webkitMediaStream",
    },
    {
      className: "Window",
      property: "WebKitMutationObserver",
    },
    {
      className: "Window",
      property: "webkitRequestAnimationFrame",
    },
    {
      className: "Window",
      property: "webkitRequestFileSystem",
    },
    {
      className: "Window",
      property: "webkitResolveLocalFileSystemURL",
    },
    {
      className: "Window",
      property: "webkitRTCPeerConnection",
    },
    {
      className: "Window",
      property: "webkitSpeechGrammar",
    },
    {
      className: "Window",
      property: "webkitSpeechGrammarList",
    },
    {
      className: "Window",
      property: "webkitSpeechRecognition",
    },
    {
      className: "Window",
      property: "webkitSpeechRecognitionError",
    },
    {
      className: "Window",
      property: "webkitSpeechRecognitionEvent",
    },
    {
      className: "Window",
      property: "webkitStorageInfo",
    },
    {
      className: "Window",
      property: "Worklet",
    },
    {
      className: "Window",
      property: "WritableStream",
    },
    {
      className: "Accelerometer",
      property: "x",
    },
    {
      className: "Accelerometer",
      property: "y",
    },
    {
      className: "Accelerometer",
      property: "z",
    },
    {
      className: "ApplicationCache",
      property: "abort",
    },
    {
      className: "ApplicationCache",
      property: "oncached",
    },
    {
      className: "ApplicationCache",
      property: "onchecking",
    },
    {
      className: "ApplicationCache",
      property: "ondownloading",
    },
    {
      className: "ApplicationCache",
      property: "onerror",
    },
    {
      className: "ApplicationCache",
      property: "onnoupdate",
    },
    {
      className: "ApplicationCache",
      property: "onobsolete",
    },
    {
      className: "ApplicationCache",
      property: "onprogress",
    },
    {
      className: "ApplicationCache",
      property: "onupdateready",
    },
    {
      className: "ApplicationCache",
      property: "status",
    },
    {
      className: "ApplicationCache",
      property: "swapCache",
    },
    {
      className: "ApplicationCache",
      property: "update",
    },
    {
      className: "ApplicationCacheErrorEvent",
      property: "message",
    },
    {
      className: "ApplicationCacheErrorEvent",
      property: "reason",
    },
    {
      className: "ApplicationCacheErrorEvent",
      property: "status",
    },
    {
      className: "ApplicationCacheErrorEvent",
      property: "url",
    },
    { className: "Atomics", property: "add", objectMissingOnWindow: true },
    { className: "Atomics", property: "and", objectMissingOnWindow: true },
    {
      className: "Atomics",
      property: "compareExchange",
    },
    {
      className: "Atomics",
      property: "exchange",
    },
    {
      className: "Atomics",
      property: "isLockFree",
    },
    { className: "Atomics", property: "load", objectMissingOnWindow: true },
    {
      className: "Atomics",
      property: "notify",
    },
    { className: "Atomics", property: "or", objectMissingOnWindow: true },
    { className: "Atomics", property: "store", objectMissingOnWindow: true },
    { className: "Atomics", property: "sub", objectMissingOnWindow: true },
    { className: "Atomics", property: "wait", objectMissingOnWindow: true },
    { className: "Atomics", property: "wake", objectMissingOnWindow: true },
    { className: "Atomics", property: "xor", objectMissingOnWindow: true },
    {
      className: "AudioParamMap",
      property: "entries",
    },
    {
      className: "AudioParamMap",
      property: "forEach",
    },
    {
      className: "AudioParamMap",
      property: "get",
    },
    {
      className: "AudioParamMap",
      property: "has",
    },
    {
      className: "AudioParamMap",
      property: "keys",
    },
    {
      className: "AudioParamMap",
      property: "size",
    },
    {
      className: "AudioParamMap",
      property: "values",
    },
    {
      className: "AudioWorkletNode",
      property: "onprocessorerror",
    },
    {
      className: "AudioWorkletNode",
      property: "parameters",
    },
    {
      className: "AudioWorkletNode",
      property: "port",
    },
    {
      className: "BackgroundFetchManager",
      property: "fetch",
    },
    {
      className: "BackgroundFetchManager",
      property: "get",
    },
    {
      className: "BackgroundFetchManager",
      property: "getIds",
    },
    {
      className: "BackgroundFetchRecord",
      property: "request",
    },
    {
      className: "BackgroundFetchRecord",
      property: "responseReady",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "abort",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "downloaded",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "downloadTotal",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "failureReason",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "id",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "match",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "matchAll",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "onprogress",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "recordsAvailable",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "result",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "uploaded",
    },
    {
      className: "BackgroundFetchRegistration",
      property: "uploadTotal",
    },
    {
      className: "BeforeInstallPromptEvent",
      property: "platforms",
    },
    {
      className: "BeforeInstallPromptEvent",
      property: "prompt",
    },
    {
      className: "BeforeInstallPromptEvent",
      property: "userChoice",
    },
    {
      className: "Bluetooth",
      property: "requestDevice",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "authenticatedSignedWrites",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "broadcast",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "indicate",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "notify",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "read",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "reliableWrite",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "writableAuxiliaries",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "write",
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "writeWithoutResponse",
    },
    {
      className: "BluetoothDevice",
      property: "gatt",
    },
    {
      className: "BluetoothDevice",
      property: "id",
    },
    {
      className: "BluetoothDevice",
      property: "name",
    },
    {
      className: "BluetoothDevice",
      property: "ongattserverdisconnected",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "getDescriptor",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "getDescriptors",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "oncharacteristicvaluechanged",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "properties",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "readValue",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "service",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "startNotifications",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "stopNotifications",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "uuid",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "value",
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "writeValue",
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "characteristic",
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "readValue",
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "uuid",
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "value",
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "writeValue",
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "connect",
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "connected",
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "device",
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "disconnect",
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "getPrimaryService",
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "getPrimaryServices",
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "device",
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "getCharacteristic",
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "getCharacteristics",
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "isPrimary",
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "uuid",
    },
    {
      className: "BluetoothUUID",
      property: "canonicalUUID",
    },
    {
      className: "BluetoothUUID",
      property: "getCharacteristic",
    },
    {
      className: "BluetoothUUID",
      property: "getDescriptor",
    },
    {
      className: "BluetoothUUID",
      property: "getService",
    },
    {
      className: "CanvasCaptureMediaStreamTrack",
      property: "canvas",
    },
    {
      className: "CanvasCaptureMediaStreamTrack",
      property: "requestFrame",
    },
    { className: "chrome", property: "app", objectMissingOnWindow: true },
    { className: "chrome", property: "csi", objectMissingOnWindow: true },
    {
      className: "chrome",
      property: "loadTimes",
    },
    {
      className: "chrome",
      property: "runtime",
    },
    {
      className: "clientInformation",
      property: "appCodeName",
    },
    {
      className: "clientInformation",
      property: "appName",
    },
    {
      className: "clientInformation",
      property: "appVersion",
    },
    {
      className: "clientInformation",
      property: "bluetooth",
    },
    {
      className: "clientInformation",
      property: "clipboard",
    },
    {
      className: "clientInformation",
      property: "connection",
    },
    {
      className: "clientInformation",
      property: "cookieEnabled",
    },
    {
      className: "clientInformation",
      property: "credentials",
    },
    {
      className: "clientInformation",
      property: "deviceMemory",
    },
    {
      className: "clientInformation",
      property: "doNotTrack",
    },
    {
      className: "clientInformation",
      property: "geolocation",
    },
    {
      className: "clientInformation",
      property: "hardwareConcurrency",
    },
    {
      className: "clientInformation",
      property: "keyboard",
    },
    {
      className: "clientInformation",
      property: "language",
    },
    {
      className: "clientInformation",
      property: "languages",
    },
    {
      className: "clientInformation",
      property: "locks",
    },
    {
      className: "clientInformation",
      property: "maxTouchPoints",
    },
    {
      className: "clientInformation",
      property: "mediaCapabilities",
    },
    {
      className: "clientInformation",
      property: "mediaDevices",
    },
    {
      className: "clientInformation",
      property: "mediaSession",
    },
    {
      className: "clientInformation",
      property: "mimeTypes",
    },
    {
      className: "clientInformation",
      property: "onLine",
    },
    {
      className: "clientInformation",
      property: "permissions",
    },
    {
      className: "clientInformation",
      property: "platform",
    },
    {
      className: "clientInformation",
      property: "plugins",
    },
    {
      className: "clientInformation",
      property: "presentation",
    },
    {
      className: "clientInformation",
      property: "product",
    },
    {
      className: "clientInformation",
      property: "productSub",
    },
    {
      className: "clientInformation",
      property: "serviceWorker",
    },
    {
      className: "clientInformation",
      property: "storage",
    },
    {
      className: "clientInformation",
      property: "usb",
    },
    {
      className: "clientInformation",
      property: "userActivation",
    },
    {
      className: "clientInformation",
      property: "userAgent",
    },
    {
      className: "clientInformation",
      property: "vendor",
    },
    {
      className: "clientInformation",
      property: "vendorSub",
    },
    {
      className: "clientInformation",
      property: "webkitPersistentStorage",
    },
    {
      className: "clientInformation",
      property: "webkitTemporaryStorage",
    },
    {
      className: "ClipboardItem",
      property: "getType",
    },
    {
      className: "ClipboardItem",
      property: "types",
    },
    {
      className: "CSSKeywordValue",
      property: "value",
    },
    {
      className: "CSSMathInvert",
      property: "value",
    },
    {
      className: "CSSMathMax",
      property: "values",
    },
    {
      className: "CSSMathMin",
      property: "values",
    },
    {
      className: "CSSMathNegate",
      property: "value",
    },
    {
      className: "CSSMathProduct",
      property: "values",
    },
    {
      className: "CSSMathSum",
      property: "values",
    },
    {
      className: "CSSMathValue",
      property: "operator",
    },
    {
      className: "CSSMatrixComponent",
      property: "matrix",
    },
    {
      className: "CSSNumericArray",
      property: "entries",
    },
    {
      className: "CSSNumericArray",
      property: "forEach",
    },
    {
      className: "CSSNumericArray",
      property: "keys",
    },
    {
      className: "CSSNumericArray",
      property: "length",
    },
    {
      className: "CSSNumericArray",
      property: "values",
    },
    {
      className: "CSSNumericValue",
      property: "add",
    },
    {
      className: "CSSNumericValue",
      property: "div",
    },
    {
      className: "CSSNumericValue",
      property: "equals",
    },
    {
      className: "CSSNumericValue",
      property: "max",
    },
    {
      className: "CSSNumericValue",
      property: "min",
    },
    {
      className: "CSSNumericValue",
      property: "mul",
    },
    {
      className: "CSSNumericValue",
      property: "parse",
    },
    {
      className: "CSSNumericValue",
      property: "sub",
    },
    {
      className: "CSSNumericValue",
      property: "to",
    },
    {
      className: "CSSNumericValue",
      property: "toSum",
    },
    {
      className: "CSSNumericValue",
      property: "type",
    },
    {
      className: "CSSPerspective",
      property: "length",
    },
    {
      className: "CSSPositionValue",
      property: "x",
    },
    {
      className: "CSSPositionValue",
      property: "y",
    },
    {
      className: "CSSRotate",
      property: "angle",
    },
    { className: "CSSRotate", property: "x", objectMissingOnWindow: true },
    { className: "CSSRotate", property: "y", objectMissingOnWindow: true },
    { className: "CSSRotate", property: "z", objectMissingOnWindow: true },
    { className: "CSSScale", property: "x", objectMissingOnWindow: true },
    { className: "CSSScale", property: "y", objectMissingOnWindow: true },
    { className: "CSSScale", property: "z", objectMissingOnWindow: true },
    { className: "CSSSkew", property: "ax", objectMissingOnWindow: true },
    { className: "CSSSkew", property: "ay", objectMissingOnWindow: true },
    { className: "CSSSkewX", property: "ax", objectMissingOnWindow: true },
    { className: "CSSSkewY", property: "ay", objectMissingOnWindow: true },
    {
      className: "CSSStyleValue",
      property: "parse",
    },
    {
      className: "CSSStyleValue",
      property: "parseAll",
    },
    {
      className: "CSSTransformComponent",
      property: "is2D",
    },
    {
      className: "CSSTransformComponent",
      property: "toMatrix",
    },
    {
      className: "CSSTransformValue",
      property: "entries",
    },
    {
      className: "CSSTransformValue",
      property: "forEach",
    },
    {
      className: "CSSTransformValue",
      property: "is2D",
    },
    {
      className: "CSSTransformValue",
      property: "keys",
    },
    {
      className: "CSSTransformValue",
      property: "length",
    },
    {
      className: "CSSTransformValue",
      property: "toMatrix",
    },
    {
      className: "CSSTransformValue",
      property: "values",
    },
    {
      className: "CSSTranslate",
      property: "x",
    },
    {
      className: "CSSTranslate",
      property: "y",
    },
    {
      className: "CSSTranslate",
      property: "z",
    },
    {
      className: "CSSUnitValue",
      property: "unit",
    },
    {
      className: "CSSUnitValue",
      property: "value",
    },
    {
      className: "CSSUnparsedValue",
      property: "entries",
    },
    {
      className: "CSSUnparsedValue",
      property: "forEach",
    },
    {
      className: "CSSUnparsedValue",
      property: "keys",
    },
    {
      className: "CSSUnparsedValue",
      property: "length",
    },
    {
      className: "CSSUnparsedValue",
      property: "values",
    },
    {
      className: "CSSVariableReferenceValue",
      property: "fallback",
    },
    {
      className: "CSSVariableReferenceValue",
      property: "variable",
    },
    {
      className: "DeviceMotionEventAcceleration",
      property: "x",
    },
    {
      className: "DeviceMotionEventAcceleration",
      property: "y",
    },
    {
      className: "DeviceMotionEventAcceleration",
      property: "z",
    },
    {
      className: "DeviceMotionEventRotationRate",
      property: "alpha",
    },
    {
      className: "DeviceMotionEventRotationRate",
      property: "beta",
    },
    {
      className: "DeviceMotionEventRotationRate",
      property: "gamma",
    },
    {
      className: "DOMError",
      property: "message",
    },
    { className: "DOMError", property: "name", objectMissingOnWindow: true },
    {
      className: "EnterPictureInPictureEvent",
      property: "pictureInPictureWindow",
    },
    {
      className: "FederatedCredential",
      property: "iconURL",
    },
    {
      className: "FederatedCredential",
      property: "name",
    },
    {
      className: "FederatedCredential",
      property: "protocol",
    },
    {
      className: "FederatedCredential",
      property: "provider",
    },
    { className: "Gyroscope", property: "x", objectMissingOnWindow: true },
    { className: "Gyroscope", property: "y", objectMissingOnWindow: true },
    { className: "Gyroscope", property: "z", objectMissingOnWindow: true },
    {
      className: "HTMLContentElement",
      property: "getDistributedNodes",
    },
    {
      className: "HTMLContentElement",
      property: "select",
    },
    {
      className: "HTMLDialogElement",
      property: "close",
    },
    {
      className: "HTMLDialogElement",
      property: "open",
    },
    {
      className: "HTMLDialogElement",
      property: "returnValue",
    },
    {
      className: "HTMLDialogElement",
      property: "show",
    },
    {
      className: "HTMLDialogElement",
      property: "showModal",
    },
    {
      className: "HTMLShadowElement",
      property: "getDistributedNodes",
    },
    {
      className: "ImageCapture",
      property: "getPhotoCapabilities",
    },
    {
      className: "ImageCapture",
      property: "getPhotoSettings",
    },
    {
      className: "ImageCapture",
      property: "grabFrame",
    },
    {
      className: "ImageCapture",
      property: "takePhoto",
    },
    {
      className: "ImageCapture",
      property: "track",
    },
    {
      className: "InputDeviceCapabilities",
      property: "firesTouchEvents",
    },
    {
      className: "InputDeviceInfo",
      property: "getCapabilities",
    },
    {
      className: "Keyboard",
      property: "getLayoutMap",
    },
    { className: "Keyboard", property: "lock", objectMissingOnWindow: true },
    {
      className: "Keyboard",
      property: "unlock",
    },
    {
      className: "KeyboardLayoutMap",
      property: "entries",
    },
    {
      className: "KeyboardLayoutMap",
      property: "forEach",
    },
    {
      className: "KeyboardLayoutMap",
      property: "get",
    },
    {
      className: "KeyboardLayoutMap",
      property: "has",
    },
    {
      className: "KeyboardLayoutMap",
      property: "keys",
    },
    {
      className: "KeyboardLayoutMap",
      property: "size",
    },
    {
      className: "KeyboardLayoutMap",
      property: "values",
    },
    { className: "Lock", property: "mode", objectMissingOnWindow: true },
    { className: "Lock", property: "name", objectMissingOnWindow: true },
    {
      className: "LockManager",
      property: "query",
    },
    {
      className: "LockManager",
      property: "request",
    },
    {
      className: "MediaMetadata",
      property: "album",
    },
    {
      className: "MediaMetadata",
      property: "artist",
    },
    {
      className: "MediaMetadata",
      property: "artwork",
    },
    {
      className: "MediaMetadata",
      property: "title",
    },
    {
      className: "MediaSession",
      property: "metadata",
    },
    {
      className: "MediaSession",
      property: "playbackState",
    },
    {
      className: "MediaSession",
      property: "setActionHandler",
    },
    {
      className: "MediaSettingsRange",
      property: "max",
    },
    {
      className: "MediaSettingsRange",
      property: "min",
    },
    {
      className: "MediaSettingsRange",
      property: "step",
    },
    {
      className: "MIDIAccess",
      property: "inputs",
    },
    {
      className: "MIDIAccess",
      property: "onstatechange",
    },
    {
      className: "MIDIAccess",
      property: "outputs",
    },
    {
      className: "MIDIAccess",
      property: "sysexEnabled",
    },
    {
      className: "MIDIConnectionEvent",
      property: "port",
    },
    {
      className: "MIDIInput",
      property: "onmidimessage",
    },
    {
      className: "MIDIInputMap",
      property: "entries",
    },
    {
      className: "MIDIInputMap",
      property: "forEach",
    },
    {
      className: "MIDIInputMap",
      property: "get",
    },
    {
      className: "MIDIInputMap",
      property: "has",
    },
    {
      className: "MIDIInputMap",
      property: "keys",
    },
    {
      className: "MIDIInputMap",
      property: "size",
    },
    {
      className: "MIDIInputMap",
      property: "values",
    },
    {
      className: "MIDIMessageEvent",
      property: "data",
    },
    {
      className: "MIDIOutput",
      property: "send",
    },
    {
      className: "MIDIOutputMap",
      property: "entries",
    },
    {
      className: "MIDIOutputMap",
      property: "forEach",
    },
    {
      className: "MIDIOutputMap",
      property: "get",
    },
    {
      className: "MIDIOutputMap",
      property: "has",
    },
    {
      className: "MIDIOutputMap",
      property: "keys",
    },
    {
      className: "MIDIOutputMap",
      property: "size",
    },
    {
      className: "MIDIOutputMap",
      property: "values",
    },
    {
      className: "MIDIPort",
      property: "close",
    },
    {
      className: "MIDIPort",
      property: "connection",
    },
    { className: "MIDIPort", property: "id", objectMissingOnWindow: true },
    {
      className: "MIDIPort",
      property: "manufacturer",
    },
    { className: "MIDIPort", property: "name", objectMissingOnWindow: true },
    {
      className: "MIDIPort",
      property: "onstatechange",
    },
    { className: "MIDIPort", property: "open", objectMissingOnWindow: true },
    {
      className: "MIDIPort",
      property: "state",
    },
    { className: "MIDIPort", property: "type", objectMissingOnWindow: true },
    {
      className: "MIDIPort",
      property: "version",
    },
    {
      className: "NavigationPreloadManager",
      property: "disable",
    },
    {
      className: "NavigationPreloadManager",
      property: "enable",
    },
    {
      className: "NavigationPreloadManager",
      property: "getState",
    },
    {
      className: "NavigationPreloadManager",
      property: "setHeaderValue",
    },
    {
      className: "NetworkInformation",
      property: "downlink",
    },
    {
      className: "NetworkInformation",
      property: "effectiveType",
    },
    {
      className: "NetworkInformation",
      property: "onchange",
    },
    {
      className: "NetworkInformation",
      property: "rtt",
    },
    {
      className: "NetworkInformation",
      property: "saveData",
    },
    {
      className: "OffscreenCanvas",
      property: "convertToBlob",
    },
    {
      className: "OffscreenCanvas",
      property: "getContext",
    },
    {
      className: "OffscreenCanvas",
      property: "height",
    },
    {
      className: "OffscreenCanvas",
      property: "transferToImageBitmap",
    },
    {
      className: "OffscreenCanvas",
      property: "width",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "arc",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "arcTo",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "beginPath",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "bezierCurveTo",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "canvas",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "clearRect",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "clip",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "closePath",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "createImageData",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "createLinearGradient",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "createPattern",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "createRadialGradient",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "direction",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "drawImage",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "ellipse",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "fill",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "fillRect",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "fillStyle",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "fillText",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "filter",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "font",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "getImageData",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "getLineDash",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "globalAlpha",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "globalCompositeOperation",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "imageSmoothingEnabled",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "imageSmoothingQuality",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "isPointInPath",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "isPointInStroke",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineCap",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineDashOffset",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineJoin",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineTo",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineWidth",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "measureText",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "miterLimit",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "moveTo",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "putImageData",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "quadraticCurveTo",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "rect",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "resetTransform",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "restore",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "rotate",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "save",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "scale",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "setLineDash",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "setTransform",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "shadowBlur",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "shadowColor",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "shadowOffsetX",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "shadowOffsetY",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "stroke",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "strokeRect",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "strokeStyle",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "strokeText",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "textAlign",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "textBaseline",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "transform",
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "translate",
    },
    {
      className: "OrientationSensor",
      property: "populateMatrix",
    },
    {
      className: "OrientationSensor",
      property: "quaternion",
    },
    {
      className: "OverconstrainedError",
      property: "constraint",
    },
    {
      className: "OverconstrainedError",
      property: "message",
    },
    {
      className: "OverconstrainedError",
      property: "name",
    },
    {
      className: "PasswordCredential",
      property: "iconURL",
    },
    {
      className: "PasswordCredential",
      property: "name",
    },
    {
      className: "PasswordCredential",
      property: "password",
    },
    {
      className: "PaymentAddress",
      property: "addressLine",
    },
    {
      className: "PaymentAddress",
      property: "city",
    },
    {
      className: "PaymentAddress",
      property: "country",
    },
    {
      className: "PaymentAddress",
      property: "dependentLocality",
    },
    {
      className: "PaymentAddress",
      property: "organization",
    },
    {
      className: "PaymentAddress",
      property: "phone",
    },
    {
      className: "PaymentAddress",
      property: "postalCode",
    },
    {
      className: "PaymentAddress",
      property: "recipient",
    },
    {
      className: "PaymentAddress",
      property: "region",
    },
    {
      className: "PaymentAddress",
      property: "sortingCode",
    },
    {
      className: "PaymentAddress",
      property: "toJSON",
    },
    {
      className: "PaymentInstruments",
      property: "clear",
    },
    {
      className: "PaymentInstruments",
      property: "delete",
    },
    {
      className: "PaymentInstruments",
      property: "get",
    },
    {
      className: "PaymentInstruments",
      property: "has",
    },
    {
      className: "PaymentInstruments",
      property: "keys",
    },
    {
      className: "PaymentInstruments",
      property: "set",
    },
    {
      className: "PaymentManager",
      property: "instruments",
    },
    {
      className: "PaymentManager",
      property: "userHint",
    },
    {
      className: "PaymentMethodChangeEvent",
      property: "methodDetails",
    },
    {
      className: "PaymentMethodChangeEvent",
      property: "methodName",
    },
    {
      className: "PaymentRequest",
      property: "abort",
    },
    {
      className: "PaymentRequest",
      property: "canMakePayment",
    },
    {
      className: "PaymentRequest",
      property: "hasEnrolledInstrument",
    },
    {
      className: "PaymentRequest",
      property: "id",
    },
    {
      className: "PaymentRequest",
      property: "onpaymentmethodchange",
    },
    {
      className: "PaymentRequest",
      property: "onshippingaddresschange",
    },
    {
      className: "PaymentRequest",
      property: "onshippingoptionchange",
    },
    {
      className: "PaymentRequest",
      property: "shippingAddress",
    },
    {
      className: "PaymentRequest",
      property: "shippingOption",
    },
    {
      className: "PaymentRequest",
      property: "shippingType",
    },
    {
      className: "PaymentRequest",
      property: "show",
    },
    {
      className: "PaymentRequestUpdateEvent",
      property: "updateWith",
    },
    {
      className: "PaymentResponse",
      property: "complete",
    },
    {
      className: "PaymentResponse",
      property: "details",
    },
    {
      className: "PaymentResponse",
      property: "methodName",
    },
    {
      className: "PaymentResponse",
      property: "payerEmail",
    },
    {
      className: "PaymentResponse",
      property: "payerName",
    },
    {
      className: "PaymentResponse",
      property: "payerPhone",
    },
    {
      className: "PaymentResponse",
      property: "requestId",
    },
    {
      className: "PaymentResponse",
      property: "shippingAddress",
    },
    {
      className: "PaymentResponse",
      property: "shippingOption",
    },
    {
      className: "PaymentResponse",
      property: "toJSON",
    },
    {
      className: "PerformanceEventTiming",
      property: "cancelable",
    },
    {
      className: "PerformanceEventTiming",
      property: "processingEnd",
    },
    {
      className: "PerformanceEventTiming",
      property: "processingStart",
    },
    {
      className: "PerformanceLongTaskTiming",
      property: "attribution",
    },
    {
      className: "PhotoCapabilities",
      property: "fillLightMode",
    },
    {
      className: "PhotoCapabilities",
      property: "imageHeight",
    },
    {
      className: "PhotoCapabilities",
      property: "imageWidth",
    },
    {
      className: "PhotoCapabilities",
      property: "redEyeReduction",
    },
    {
      className: "PictureInPictureWindow",
      property: "height",
    },
    {
      className: "PictureInPictureWindow",
      property: "onresize",
    },
    {
      className: "PictureInPictureWindow",
      property: "width",
    },
    {
      className: "Presentation",
      property: "defaultRequest",
    },
    {
      className: "Presentation",
      property: "receiver",
    },
    {
      className: "PresentationAvailability",
      property: "onchange",
    },
    {
      className: "PresentationAvailability",
      property: "value",
    },
    {
      className: "PresentationConnection",
      property: "binaryType",
    },
    {
      className: "PresentationConnection",
      property: "close",
    },
    {
      className: "PresentationConnection",
      property: "id",
    },
    {
      className: "PresentationConnection",
      property: "onclose",
    },
    {
      className: "PresentationConnection",
      property: "onconnect",
    },
    {
      className: "PresentationConnection",
      property: "onmessage",
    },
    {
      className: "PresentationConnection",
      property: "onterminate",
    },
    {
      className: "PresentationConnection",
      property: "send",
    },
    {
      className: "PresentationConnection",
      property: "state",
    },
    {
      className: "PresentationConnection",
      property: "terminate",
    },
    {
      className: "PresentationConnection",
      property: "url",
    },
    {
      className: "PresentationConnectionAvailableEvent",
      property: "connection",
    },
    {
      className: "PresentationConnectionCloseEvent",
      property: "message",
    },
    {
      className: "PresentationConnectionCloseEvent",
      property: "reason",
    },
    {
      className: "PresentationConnectionList",
      property: "connections",
    },
    {
      className: "PresentationConnectionList",
      property: "onconnectionavailable",
    },
    {
      className: "PresentationReceiver",
      property: "connectionList",
    },
    {
      className: "PresentationRequest",
      property: "getAvailability",
    },
    {
      className: "PresentationRequest",
      property: "onconnectionavailable",
    },
    {
      className: "PresentationRequest",
      property: "reconnect",
    },
    {
      className: "PresentationRequest",
      property: "start",
    },
    {
      className: "RemotePlayback",
      property: "cancelWatchAvailability",
    },
    {
      className: "RemotePlayback",
      property: "onconnect",
    },
    {
      className: "RemotePlayback",
      property: "onconnecting",
    },
    {
      className: "RemotePlayback",
      property: "ondisconnect",
    },
    {
      className: "RemotePlayback",
      property: "prompt",
    },
    {
      className: "RemotePlayback",
      property: "state",
    },
    {
      className: "RemotePlayback",
      property: "watchAvailability",
    },
    {
      className: "ReportingObserver",
      property: "disconnect",
    },
    {
      className: "ReportingObserver",
      property: "observe",
    },
    {
      className: "ReportingObserver",
      property: "takeRecords",
    },
    {
      className: "RTCDtlsTransport",
      property: "getRemoteCertificates",
    },
    {
      className: "RTCDtlsTransport",
      property: "iceTransport",
    },
    {
      className: "RTCDtlsTransport",
      property: "onerror",
    },
    {
      className: "RTCDtlsTransport",
      property: "onstatechange",
    },
    {
      className: "RTCDtlsTransport",
      property: "state",
    },
    {
      className: "RTCError",
      property: "errorDetail",
    },
    {
      className: "RTCError",
      property: "httpRequestStatusCode",
    },
    {
      className: "RTCError",
      property: "receivedAlert",
    },
    {
      className: "RTCError",
      property: "sctpCauseCode",
    },
    {
      className: "RTCError",
      property: "sdpLineNumber",
    },
    {
      className: "RTCError",
      property: "sentAlert",
    },
    {
      className: "RTCErrorEvent",
      property: "error",
    },
    {
      className: "RTCIceTransport",
      property: "gatheringState",
    },
    {
      className: "RTCIceTransport",
      property: "getLocalCandidates",
    },
    {
      className: "RTCIceTransport",
      property: "getLocalParameters",
    },
    {
      className: "RTCIceTransport",
      property: "getRemoteCandidates",
    },
    {
      className: "RTCIceTransport",
      property: "getRemoteParameters",
    },
    {
      className: "RTCIceTransport",
      property: "getSelectedCandidatePair",
    },
    {
      className: "RTCIceTransport",
      property: "ongatheringstatechange",
    },
    {
      className: "RTCIceTransport",
      property: "onselectedcandidatepairchange",
    },
    {
      className: "RTCIceTransport",
      property: "onstatechange",
    },
    {
      className: "RTCIceTransport",
      property: "role",
    },
    {
      className: "RTCIceTransport",
      property: "state",
    },
    {
      className: "RTCSctpTransport",
      property: "maxChannels",
    },
    {
      className: "RTCSctpTransport",
      property: "maxMessageSize",
    },
    {
      className: "RTCSctpTransport",
      property: "onstatechange",
    },
    {
      className: "RTCSctpTransport",
      property: "state",
    },
    {
      className: "RTCSctpTransport",
      property: "transport",
    },
    {
      className: "Sensor",
      property: "activated",
    },
    {
      className: "Sensor",
      property: "hasReading",
    },
    {
      className: "Sensor",
      property: "onactivate",
    },
    {
      className: "Sensor",
      property: "onerror",
    },
    {
      className: "Sensor",
      property: "onreading",
    },
    { className: "Sensor", property: "start", objectMissingOnWindow: true },
    { className: "Sensor", property: "stop", objectMissingOnWindow: true },
    {
      className: "Sensor",
      property: "timestamp",
    },
    {
      className: "SensorErrorEvent",
      property: "error",
    },
    {
      className: "SharedArrayBuffer",
      property: "byteLength",
    },
    {
      className: "SharedArrayBuffer",
      property: "slice",
    },
    {
      className: "styleMedia",
      property: "type",
    },
    {
      className: "StylePropertyMap",
      property: "append",
    },
    {
      className: "StylePropertyMap",
      property: "clear",
    },
    {
      className: "StylePropertyMap",
      property: "delete",
    },
    {
      className: "StylePropertyMap",
      property: "set",
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "entries",
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "forEach",
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "get",
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "getAll",
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "has",
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "keys",
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "size",
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "values",
    },
    {
      className: "SyncManager",
      property: "getTags",
    },
    {
      className: "SyncManager",
      property: "register",
    },
    {
      className: "TaskAttributionTiming",
      property: "containerId",
    },
    {
      className: "TaskAttributionTiming",
      property: "containerName",
    },
    {
      className: "TaskAttributionTiming",
      property: "containerSrc",
    },
    {
      className: "TaskAttributionTiming",
      property: "containerType",
    },
    {
      className: "TextDecoderStream",
      property: "encoding",
    },
    {
      className: "TextDecoderStream",
      property: "fatal",
    },
    {
      className: "TextDecoderStream",
      property: "ignoreBOM",
    },
    {
      className: "TextDecoderStream",
      property: "readable",
    },
    {
      className: "TextDecoderStream",
      property: "writable",
    },
    {
      className: "TextEncoderStream",
      property: "encoding",
    },
    {
      className: "TextEncoderStream",
      property: "readable",
    },
    {
      className: "TextEncoderStream",
      property: "writable",
    },
    {
      className: "TextEvent",
      property: "data",
    },
    {
      className: "TextEvent",
      property: "initTextEvent",
    },
    { className: "Touch", property: "clientX", objectMissingOnWindow: true },
    { className: "Touch", property: "clientY", objectMissingOnWindow: true },
    { className: "Touch", property: "force", objectMissingOnWindow: true },
    {
      className: "Touch",
      property: "identifier",
    },
    { className: "Touch", property: "pageX", objectMissingOnWindow: true },
    { className: "Touch", property: "pageY", objectMissingOnWindow: true },
    { className: "Touch", property: "radiusX", objectMissingOnWindow: true },
    { className: "Touch", property: "radiusY", objectMissingOnWindow: true },
    {
      className: "Touch",
      property: "rotationAngle",
    },
    { className: "Touch", property: "screenX", objectMissingOnWindow: true },
    { className: "Touch", property: "screenY", objectMissingOnWindow: true },
    { className: "Touch", property: "target", objectMissingOnWindow: true },
    {
      className: "TouchEvent",
      property: "altKey",
    },
    {
      className: "TouchEvent",
      property: "changedTouches",
    },
    {
      className: "TouchEvent",
      property: "ctrlKey",
    },
    {
      className: "TouchEvent",
      property: "metaKey",
    },
    {
      className: "TouchEvent",
      property: "shiftKey",
    },
    {
      className: "TouchEvent",
      property: "targetTouches",
    },
    {
      className: "TouchEvent",
      property: "touches",
    },
    {
      className: "TouchList",
      property: "item",
    },
    {
      className: "TouchList",
      property: "length",
    },
    {
      className: "TransformStream",
      property: "readable",
    },
    {
      className: "TransformStream",
      property: "writable",
    },
    {
      className: "USB",
      property: "getDevices",
    },
    { className: "USB", property: "onconnect", objectMissingOnWindow: true },
    {
      className: "USB",
      property: "ondisconnect",
    },
    {
      className: "USB",
      property: "requestDevice",
    },
    {
      className: "USBAlternateInterface",
      property: "alternateSetting",
    },
    {
      className: "USBAlternateInterface",
      property: "endpoints",
    },
    {
      className: "USBAlternateInterface",
      property: "interfaceClass",
    },
    {
      className: "USBAlternateInterface",
      property: "interfaceName",
    },
    {
      className: "USBAlternateInterface",
      property: "interfaceProtocol",
    },
    {
      className: "USBAlternateInterface",
      property: "interfaceSubclass",
    },
    {
      className: "USBConfiguration",
      property: "configurationName",
    },
    {
      className: "USBConfiguration",
      property: "configurationValue",
    },
    {
      className: "USBConfiguration",
      property: "interfaces",
    },
    {
      className: "USBConnectionEvent",
      property: "device",
    },
    {
      className: "USBDevice",
      property: "claimInterface",
    },
    {
      className: "USBDevice",
      property: "clearHalt",
    },
    {
      className: "USBDevice",
      property: "close",
    },
    {
      className: "USBDevice",
      property: "configuration",
    },
    {
      className: "USBDevice",
      property: "configurations",
    },
    {
      className: "USBDevice",
      property: "controlTransferIn",
    },
    {
      className: "USBDevice",
      property: "controlTransferOut",
    },
    {
      className: "USBDevice",
      property: "deviceClass",
    },
    {
      className: "USBDevice",
      property: "deviceProtocol",
    },
    {
      className: "USBDevice",
      property: "deviceSubclass",
    },
    {
      className: "USBDevice",
      property: "deviceVersionMajor",
    },
    {
      className: "USBDevice",
      property: "deviceVersionMinor",
    },
    {
      className: "USBDevice",
      property: "deviceVersionSubminor",
    },
    {
      className: "USBDevice",
      property: "isochronousTransferIn",
    },
    {
      className: "USBDevice",
      property: "isochronousTransferOut",
    },
    {
      className: "USBDevice",
      property: "manufacturerName",
    },
    {
      className: "USBDevice",
      property: "open",
    },
    {
      className: "USBDevice",
      property: "opened",
    },
    {
      className: "USBDevice",
      property: "productId",
    },
    {
      className: "USBDevice",
      property: "productName",
    },
    {
      className: "USBDevice",
      property: "releaseInterface",
    },
    {
      className: "USBDevice",
      property: "reset",
    },
    {
      className: "USBDevice",
      property: "selectAlternateInterface",
    },
    {
      className: "USBDevice",
      property: "selectConfiguration",
    },
    {
      className: "USBDevice",
      property: "serialNumber",
    },
    {
      className: "USBDevice",
      property: "transferIn",
    },
    {
      className: "USBDevice",
      property: "transferOut",
    },
    {
      className: "USBDevice",
      property: "usbVersionMajor",
    },
    {
      className: "USBDevice",
      property: "usbVersionMinor",
    },
    {
      className: "USBDevice",
      property: "usbVersionSubminor",
    },
    {
      className: "USBDevice",
      property: "vendorId",
    },
    {
      className: "USBEndpoint",
      property: "direction",
    },
    {
      className: "USBEndpoint",
      property: "endpointNumber",
    },
    {
      className: "USBEndpoint",
      property: "packetSize",
    },
    {
      className: "USBEndpoint",
      property: "type",
    },
    {
      className: "USBInterface",
      property: "alternate",
    },
    {
      className: "USBInterface",
      property: "alternates",
    },
    {
      className: "USBInterface",
      property: "claimed",
    },
    {
      className: "USBInterface",
      property: "interfaceNumber",
    },
    {
      className: "USBInTransferResult",
      property: "data",
    },
    {
      className: "USBInTransferResult",
      property: "status",
    },
    {
      className: "USBIsochronousInTransferPacket",
      property: "data",
    },
    {
      className: "USBIsochronousInTransferPacket",
      property: "status",
    },
    {
      className: "USBIsochronousInTransferResult",
      property: "data",
    },
    {
      className: "USBIsochronousInTransferResult",
      property: "packets",
    },
    {
      className: "USBIsochronousOutTransferPacket",
      property: "bytesWritten",
    },
    {
      className: "USBIsochronousOutTransferPacket",
      property: "status",
    },
    {
      className: "USBIsochronousOutTransferResult",
      property: "packets",
    },
    {
      className: "USBOutTransferResult",
      property: "bytesWritten",
    },
    {
      className: "USBOutTransferResult",
      property: "status",
    },
    {
      className: "UserActivation",
      property: "hasBeenActive",
    },
    {
      className: "UserActivation",
      property: "isActive",
    },
    {
      className: "visualViewport",
      property: "height",
    },
    {
      className: "visualViewport",
      property: "offsetLeft",
    },
    {
      className: "visualViewport",
      property: "offsetTop",
    },
    {
      className: "visualViewport",
      property: "onresize",
    },
    {
      className: "visualViewport",
      property: "onscroll",
    },
    {
      className: "visualViewport",
      property: "pageLeft",
    },
    {
      className: "visualViewport",
      property: "pageTop",
    },
    {
      className: "visualViewport",
      property: "scale",
    },
    {
      className: "visualViewport",
      property: "width",
    },
    {
      className: "webkitMediaStream",
      property: "active",
    },
    {
      className: "webkitMediaStream",
      property: "addTrack",
    },
    {
      className: "webkitMediaStream",
      property: "clone",
    },
    {
      className: "webkitMediaStream",
      property: "getAudioTracks",
    },
    {
      className: "webkitMediaStream",
      property: "getTrackById",
    },
    {
      className: "webkitMediaStream",
      property: "getTracks",
    },
    {
      className: "webkitMediaStream",
      property: "getVideoTracks",
    },
    {
      className: "webkitMediaStream",
      property: "id",
    },
    {
      className: "webkitMediaStream",
      property: "onactive",
    },
    {
      className: "webkitMediaStream",
      property: "onaddtrack",
    },
    {
      className: "webkitMediaStream",
      property: "oninactive",
    },
    {
      className: "webkitMediaStream",
      property: "onremovetrack",
    },
    {
      className: "webkitMediaStream",
      property: "removeTrack",
    },
    {
      className: "WebKitMutationObserver",
      property: "disconnect",
    },
    {
      className: "WebKitMutationObserver",
      property: "observe",
    },
    {
      className: "WebKitMutationObserver",
      property: "takeRecords",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "addIceCandidate",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "addStream",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "addTrack",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "addTransceiver",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "close",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "connectionState",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "createAnswer",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "createDataChannel",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "createDTMFSender",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "createOffer",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "currentLocalDescription",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "currentRemoteDescription",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "generateCertificate",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getConfiguration",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getLocalStreams",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getReceivers",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getRemoteStreams",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getSenders",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getStats",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getTransceivers",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "iceConnectionState",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "iceGatheringState",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "localDescription",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onaddstream",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onconnectionstatechange",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "ondatachannel",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onicecandidate",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "oniceconnectionstatechange",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onicegatheringstatechange",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onnegotiationneeded",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onremovestream",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onsignalingstatechange",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "ontrack",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "pendingLocalDescription",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "pendingRemoteDescription",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "remoteDescription",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "removeStream",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "removeTrack",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "sctp",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "setConfiguration",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "setLocalDescription",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "setRemoteDescription",
    },
    {
      className: "webkitRTCPeerConnection",
      property: "signalingState",
    },
    {
      className: "webkitSpeechGrammar",
      property: "src",
    },
    {
      className: "webkitSpeechGrammar",
      property: "weight",
    },
    {
      className: "webkitSpeechGrammarList",
      property: "addFromString",
    },
    {
      className: "webkitSpeechGrammarList",
      property: "addFromUri",
    },
    {
      className: "webkitSpeechGrammarList",
      property: "item",
    },
    {
      className: "webkitSpeechGrammarList",
      property: "length",
    },
    {
      className: "webkitSpeechRecognition",
      property: "abort",
    },
    {
      className: "webkitSpeechRecognition",
      property: "continuous",
    },
    {
      className: "webkitSpeechRecognition",
      property: "grammars",
    },
    {
      className: "webkitSpeechRecognition",
      property: "interimResults",
    },
    {
      className: "webkitSpeechRecognition",
      property: "lang",
    },
    {
      className: "webkitSpeechRecognition",
      property: "maxAlternatives",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onaudioend",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onaudiostart",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onend",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onerror",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onnomatch",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onresult",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onsoundend",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onsoundstart",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onspeechend",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onspeechstart",
    },
    {
      className: "webkitSpeechRecognition",
      property: "onstart",
    },
    {
      className: "webkitSpeechRecognition",
      property: "start",
    },
    {
      className: "webkitSpeechRecognition",
      property: "stop",
    },
    {
      className: "webkitSpeechRecognitionError",
      property: "error",
    },
    {
      className: "webkitSpeechRecognitionError",
      property: "message",
    },
    {
      className: "webkitSpeechRecognitionEvent",
      property: "emma",
    },
    {
      className: "webkitSpeechRecognitionEvent",
      property: "interpretation",
    },
    {
      className: "webkitSpeechRecognitionEvent",
      property: "resultIndex",
    },
    {
      className: "webkitSpeechRecognitionEvent",
      property: "results",
    },
    {
      className: "Worklet",
      property: "addModule",
    },
    {
      className: "WritableStream",
      property: "abort",
    },
    {
      className: "WritableStream",
      property: "getWriter",
    },
    {
      className: "WritableStream",
      property: "locked",
    },
  ];
  // Typing this long list here instead of above avoids TS2590
  const $nonExistingPropertiesToInstrumentData: PropertyToInstrumentConfiguration[] = nonExistingPropertiesToInstrumentData;

  // Configuration switches (hard-coded for now)
  const configMockNonExistingWindowClassNames = false;

  const startsWithLowercase = (str: string) => {
    const firstChar = str.charAt(0);
    return firstChar.toLowerCase() === firstChar;
  };

  const instrumentPossiblyNonExistingObject = (
    className,
    nonExistingPropertiesToInstrument,
  ) => {
    // console.debug({ className, nonExistingPropertiesToInstrument });
    const classIsWindow = className.toLowerCase() === "window";

    if (classIsWindow) {
      throw new Error(
        "Window-level properties should be instrumented separately",
      );
    }

    const objectName = "window." + className;

    // Assume classNames starting with lower case and prefixed with "webkit" to be already instantiated
    // Eg window.document, window.console, window.navigator
    const classIsLikelyInstantiatedAlready =
      startsWithLowercase(className) && className.substr(0, 6) !== "webkit";

    // console.debug(`typeof window[${className}]`, typeof window[className]);
    // console.debug(`typeof window[${className}].prototype`, typeof window[className].prototype);

    // To be able to instrument properties of non-existing classes,
    // we must create a mock class item or instance first
    if (typeof window[className] === "undefined") {
      if (!configMockNonExistingWindowClassNames) {
        // If we don't mock non-existing window classes, we make
        // sure not to instrument them
        return;
      }

      const MockClass = function() {};
      if (classIsLikelyInstantiatedAlready) {
        console.info(`Creating a mock class instance on window.${className}`);
        const mockClassInstance = new MockClass();
        window[className] = mockClassInstance;
      } else {
        console.info(`Creating a mock class on window.${className}`);
        window[className] = MockClass as any;
      }
    }

    // Instrument the prototype if available so that new instances of the class subsequently gets instrumented
    if (typeof window[className].prototype !== "undefined") {
      console.info(
        `Instrumenting ${nonExistingPropertiesToInstrument.length} properties on window.${className}.prototype`,
      );

      instrumentObject(window[className].prototype, objectName, {
        propertiesToInstrument: [], // Prevents default mode of instrumenting all properties
        nonExistingPropertiesToInstrument,
        logCallStack: true,
        logFunctionGets: true,
      });
    }

    // Instrument the class instance and it's properties

    console.info(
      `Instrumenting ${nonExistingPropertiesToInstrument.length} properties on window.${className}`,
    );
    instrumentObject(window[className], objectName, {
      propertiesToInstrument: [], // Prevents default mode of instrumenting all properties
      nonExistingPropertiesToInstrument,
      logCallStack: true,
      logFunctionGets: true,
    });
  };

  const nonExistingPropertiesToInstrumentByClassName: {
    [className: string]: string[];
  } = $nonExistingPropertiesToInstrumentData.reduce(
    (_, propertyToInstrumentData) => {
      if (!_[propertyToInstrumentData.className]) {
        _[propertyToInstrumentData.className] = [];
      }
      _[propertyToInstrumentData.className].push(
        propertyToInstrumentData.property,
      );
      return _;
    },
    {},
  );

  console.log(
    "Instrumenting webcompat-related properties",
    nonExistingPropertiesToInstrumentByClassName,
  );

  // Instrument conflicting window-level properties separately
  const windowProperties = nonExistingPropertiesToInstrumentByClassName.Window.concat(
    nonExistingPropertiesToInstrumentByClassName.window
      ? nonExistingPropertiesToInstrumentByClassName.window
      : [],
  );
  delete nonExistingPropertiesToInstrumentByClassName.Window;
  delete nonExistingPropertiesToInstrumentByClassName.window;

  // Instrument non-window-level properties
  for (const className of Object.keys(
    nonExistingPropertiesToInstrumentByClassName,
  )) {
    const nonExistingPropertiesToInstrument =
      nonExistingPropertiesToInstrumentByClassName[className];
    instrumentPossiblyNonExistingObject(
      className,
      nonExistingPropertiesToInstrument,
    );
  }

  // Instrument window-level properties last
  {
    console.info(
      `Instrumenting ${windowProperties.length} properties on window`,
    );

    instrumentObject(window, `window`, {
      propertiesToInstrument: [], // Prevents default mode of instrumenting all properties
      nonExistingPropertiesToInstrument: windowProperties,
      logCallStack: true,
      logFunctionGets: true,
    });

    // Instrument a trap window-level class
    window.NothingToSeeHere = function() {};

    instrumentObject(window, `window`, {
      propertiesToInstrument: ["NothingToSeeHere"],
      logCallStack: true,
      logFunctionGets: true,
    });
  }
}
