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
  const propertiesToInstrumentData: any[] = [
    {
      className: "AudioContext",
      property: "baseLatency",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioContext",
      property: "getOutputTimestamp",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioContext",
      property: "resume",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "forwardX",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "forwardY",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "forwardZ",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "positionX",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "positionY",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "positionZ",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "upX",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "upY",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioListener",
      property: "upZ",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioParam",
      property: "automationRate",
      objectMissingOnWindow: false,
    },
    {
      className: "AudioParam",
      property: "cancelAndHoldAtTime",
      objectMissingOnWindow: false,
    },
    {
      className: "AuthenticatorAttestationResponse",
      property: "getTransports",
      objectMissingOnWindow: false,
    },
    {
      className: "BaseAudioContext",
      property: "audioWorklet",
      objectMissingOnWindow: false,
    },
    {
      className: "BlobEvent",
      property: "timecode",
      objectMissingOnWindow: false,
    },
    {
      className: "CanvasRenderingContext2D",
      property: "getContextAttributes",
      objectMissingOnWindow: false,
    },
    {
      className: "CanvasRenderingContext2D",
      property: "getTransform",
      objectMissingOnWindow: false,
    },
    {
      className: "CanvasRenderingContext2D",
      property: "imageSmoothingQuality",
      objectMissingOnWindow: false,
    },
    {
      className: "Clipboard",
      property: "read",
      objectMissingOnWindow: false,
    },
    {
      className: "Clipboard",
      property: "readText",
      objectMissingOnWindow: false,
    },
    {
      className: "Clipboard",
      property: "write",
      objectMissingOnWindow: false,
    },
    {
      className: "console",
      property: "context",
      objectMissingOnWindow: false,
    },
    {
      className: "console",
      property: "memory",
      objectMissingOnWindow: false,
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
      objectMissingOnWindow: false,
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
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "alignmentBaseline",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "backdropFilter",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "backgroundRepeatX",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "backgroundRepeatY",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "baselineShift",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "bufferedRendering",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "colorRendering",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "columnSpan",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "d",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubCaptionSide",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextCombine",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextEmphasis",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextEmphasisColor",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextEmphasisStyle",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextOrientation",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubTextTransform",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubWordBreak",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "epubWritingMode",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "fontDisplay",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "maxZoom",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "minZoom",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "offset",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "offsetDistance",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "offsetPath",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "offsetRotate",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "orientation",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "orphans",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "page",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "scrollSnapStop",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "size",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "speak",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "src",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "tabSize",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "textDecorationSkipInk",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "textSizeAdjust",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "textUnderlinePosition",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "unicodeRange",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "userZoom",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitAppRegion",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderAfter",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderAfterColor",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderAfterStyle",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderAfterWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderBefore",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderBeforeColor",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderBeforeStyle",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderBeforeWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderEnd",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderEndColor",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderEndStyle",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderEndWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderHorizontalSpacing",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderStart",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderStartColor",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderStartStyle",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderStartWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBorderVerticalSpacing",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBoxDecorationBreak",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitBoxReflect",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitClipPath",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnBreakAfter",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnBreakBefore",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnBreakInside",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnCount",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnGap",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnRule",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnRuleColor",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnRuleStyle",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnRuleWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumns",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnSpan",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitColumnWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitFontFeatureSettings",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitFontSizeDelta",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitFontSmoothing",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitHighlight",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitHyphenateCharacter",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitLineBreak",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitLocale",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitLogicalHeight",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitLogicalWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginAfter",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginAfterCollapse",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginBefore",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginBeforeCollapse",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginBottomCollapse",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginCollapse",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginEnd",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginStart",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMarginTopCollapse",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImage",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageOutset",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageRepeat",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageSlice",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageSource",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskBoxImageWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskRepeatX",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaskRepeatY",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaxLogicalHeight",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMaxLogicalWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMinLogicalHeight",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitMinLogicalWidth",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitOpacity",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPaddingAfter",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPaddingBefore",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPaddingEnd",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPaddingStart",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPerspectiveOriginX",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPerspectiveOriginY",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitPrintColorAdjust",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitRtlOrdering",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitRubyPosition",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitShapeImageThreshold",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitShapeMargin",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitShapeOutside",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTapHighlightColor",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextCombine",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextDecorationsInEffect",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextEmphasis",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextEmphasisColor",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextEmphasisPosition",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextEmphasisStyle",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextOrientation",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTextSecurity",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTransformOriginX",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTransformOriginY",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitTransformOriginZ",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitUserDrag",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitUserModify",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "webkitWritingMode",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "widows",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleDeclaration",
      property: "zoom",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleRule",
      property: "styleMap",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleSheet",
      property: "replace",
      objectMissingOnWindow: false,
    },
    {
      className: "CSSStyleSheet",
      property: "replaceSync",
      objectMissingOnWindow: false,
    },
    {
      className: "DateTimeFormat",
      property: "formatRange",
      objectMissingOnWindow: false,
    },
    {
      className: "DateTimeFormat",
      property: "formatRangeToParts",
      objectMissingOnWindow: false,
    },
    {
      className: "DeprecatedStorageInfo",
      property: "queryUsageAndQuota",
      objectMissingOnWindow: false,
    },
    {
      className: "DeprecatedStorageInfo",
      property: "requestQuota",
      objectMissingOnWindow: false,
    },
    {
      className: "DeprecatedStorageQuota",
      property: "queryUsageAndQuota",
      objectMissingOnWindow: false,
    },
    {
      className: "DeprecatedStorageQuota",
      property: "requestQuota",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "adoptedStyleSheets",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "adoptedStyleSheets",
      objectMissingOnWindow: false,
    },
    { className: "Document", property: "all", objectMissingOnWindow: false },
    {
      className: "Document",
      property: "captureEvents",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "caretRangeFromPoint",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "clear",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "exitPictureInPicture",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "featurePolicy",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "featurePolicy",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onbeforecopy",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onbeforecopy",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onbeforecut",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onbeforecut",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onbeforepaste",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onbeforepaste",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "oncancel",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "oncancel",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onfreeze",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onfreeze",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onmousewheel",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onmousewheel",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onresume",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onresume",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onsearch",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onsearch",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onsecuritypolicyviolation",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onsecuritypolicyviolation",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onwebkitfullscreenchange",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onwebkitfullscreenchange",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "onwebkitfullscreenerror",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "onwebkitfullscreenerror",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "pictureInPictureElement",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "pictureInPictureElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "pictureInPictureEnabled",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "pictureInPictureEnabled",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "registerElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "releaseEvents",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "wasDiscarded",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "wasDiscarded",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "webkitCancelFullScreen",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "webkitCurrentFullScreenElement",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "webkitCurrentFullScreenElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "webkitExitFullscreen",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "webkitFullscreenElement",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "webkitFullscreenElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "webkitFullscreenEnabled",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "webkitFullscreenEnabled",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "webkitHidden",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "webkitHidden",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "webkitIsFullScreen",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "webkitIsFullScreen",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "webkitVisibilityState",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "webkitVisibilityState",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "xmlEncoding",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "xmlEncoding",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "xmlStandalone",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "xmlStandalone",
      objectMissingOnWindow: false,
    },
    {
      className: "Document",
      property: "xmlVersion",
      objectMissingOnWindow: false,
    },
    {
      className: "document",
      property: "xmlVersion",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "attributeStyleMap",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "computedStyleMap",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "createShadowRoot",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "getDestinationInsertionPoints",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "onbeforecopy",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "onbeforecut",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "onbeforepaste",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "onsearch",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "onwebkitfullscreenchange",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "onwebkitfullscreenerror",
      objectMissingOnWindow: false,
    },
    { className: "Element", property: "part", objectMissingOnWindow: false },
    {
      className: "Element",
      property: "scrollIntoViewIfNeeded",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "webkitRequestFullScreen",
      objectMissingOnWindow: false,
    },
    {
      className: "Element",
      property: "webkitRequestFullscreen",
      objectMissingOnWindow: false,
    },
    {
      className: "Error",
      property: "captureStackTrace",
      objectMissingOnWindow: false,
    },
    {
      className: "Error",
      property: "stackTraceLimit",
      objectMissingOnWindow: false,
    },
    {
      className: "event",
      property: "fromElement",
      objectMissingOnWindow: false,
    },
    { className: "Event", property: "path", objectMissingOnWindow: false },
    { className: "event", property: "path", objectMissingOnWindow: false },
    {
      className: "event",
      property: "sourceCapabilities",
      objectMissingOnWindow: false,
    },
    {
      className: "event",
      property: "toElement",
      objectMissingOnWindow: false,
    },
    {
      className: "FeaturePolicy",
      property: "allowedFeatures",
      objectMissingOnWindow: false,
    },
    {
      className: "FeaturePolicy",
      property: "allowsFeature",
      objectMissingOnWindow: false,
    },
    {
      className: "FeaturePolicy",
      property: "features",
      objectMissingOnWindow: false,
    },
    {
      className: "FeaturePolicy",
      property: "getAllowlistForFeature",
      objectMissingOnWindow: false,
    },
    {
      className: "File",
      property: "lastModifiedDate",
      objectMissingOnWindow: false,
    },
    {
      className: "Gamepad",
      property: "vibrationActuator",
      objectMissingOnWindow: false,
    },
    {
      className: "GamepadHapticActuator",
      property: "playEffect",
      objectMissingOnWindow: false,
    },
    {
      className: "GamepadHapticActuator",
      property: "reset",
      objectMissingOnWindow: false,
    },
    {
      className: "Geolocation",
      property: "clearWatch",
      objectMissingOnWindow: false,
    },
    {
      className: "Geolocation",
      property: "getCurrentPosition",
      objectMissingOnWindow: false,
    },
    {
      className: "Geolocation",
      property: "watchPosition",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLCanvasElement",
      property: "transferControlToOffscreen",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "adoptedStyleSheets",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "featurePolicy",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onbeforecopy",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onbeforecut",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onbeforepaste",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "oncancel",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onfreeze",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onmousewheel",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onresume",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onsearch",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onsecuritypolicyviolation",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onwebkitfullscreenchange",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "onwebkitfullscreenerror",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "pictureInPictureElement",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "pictureInPictureEnabled",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "wasDiscarded",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "webkitCurrentFullScreenElement",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "webkitFullscreenElement",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "webkitFullscreenEnabled",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "webkitHidden",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "webkitIsFullScreen",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "webkitVisibilityState",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "xmlEncoding",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "xmlStandalone",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLDocument",
      property: "xmlVersion",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLElement",
      property: "autocapitalize",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLElement",
      property: "inputMode",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLElement",
      property: "nonce",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLElement",
      property: "oncancel",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLElement",
      property: "onmousewheel",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLElement",
      property: "onselectionchange",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLElement",
      property: "outerText",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLElement",
      property: "translate",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLFormElement",
      property: "requestSubmit",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLIFrameElement",
      property: "allow",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLIFrameElement",
      property: "csp",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLIFrameElement",
      property: "featurePolicy",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLInputElement",
      property: "dirName",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLInputElement",
      property: "incremental",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLLinkElement",
      property: "imageSizes",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLLinkElement",
      property: "imageSrcset",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLLinkElement",
      property: "import",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLMediaElement",
      property: "captureStream",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLMediaElement",
      property: "controlsList",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLMediaElement",
      property: "disableRemotePlayback",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLMediaElement",
      property: "remote",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLMediaElement",
      property: "setSinkId",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLMediaElement",
      property: "sinkId",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLMediaElement",
      property: "webkitAudioDecodedByteCount",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLMediaElement",
      property: "webkitVideoDecodedByteCount",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLTextAreaElement",
      property: "dirName",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "disablePictureInPicture",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "onenterpictureinpicture",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "onleavepictureinpicture",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "playsInline",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "requestPictureInPicture",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "webkitDecodedFrameCount",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "webkitDisplayingFullscreen",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "webkitDroppedFrameCount",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "webkitEnterFullScreen",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "webkitEnterFullscreen",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "webkitExitFullScreen",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "webkitExitFullscreen",
      objectMissingOnWindow: false,
    },
    {
      className: "HTMLVideoElement",
      property: "webkitSupportsFullscreen",
      objectMissingOnWindow: false,
    },
    {
      className: "IDBCursor",
      property: "request",
      objectMissingOnWindow: false,
    },
    {
      className: "IDBFactory",
      property: "databases",
      objectMissingOnWindow: false,
    },
    {
      className: "IDBTransaction",
      property: "commit",
      objectMissingOnWindow: false,
    },
    {
      className: "IDBVersionChangeEvent",
      property: "dataLoss",
      objectMissingOnWindow: false,
    },
    {
      className: "IDBVersionChangeEvent",
      property: "dataLossMessage",
      objectMissingOnWindow: false,
    },
    {
      className: "ImageBitmapRenderingContext",
      property: "canvas",
      objectMissingOnWindow: false,
    },
    {
      className: "InputEvent",
      property: "getTargetRanges",
      objectMissingOnWindow: false,
    },
    {
      className: "IntersectionObserver",
      property: "delay",
      objectMissingOnWindow: false,
    },
    {
      className: "IntersectionObserver",
      property: "trackVisibility",
      objectMissingOnWindow: false,
    },
    {
      className: "IntersectionObserverEntry",
      property: "isVisible",
      objectMissingOnWindow: false,
    },
    {
      className: "Intl",
      property: "ListFormat",
      objectMissingOnWindow: false,
    },
    { className: "Intl", property: "Locale", objectMissingOnWindow: false },
    {
      className: "Intl",
      property: "v8BreakIterator",
      objectMissingOnWindow: false,
    },
    {
      className: "ListFormat",
      property: "format",
      objectMissingOnWindow: false,
    },
    {
      className: "ListFormat",
      property: "formatToParts",
      objectMissingOnWindow: false,
    },
    {
      className: "ListFormat",
      property: "resolvedOptions",
      objectMissingOnWindow: false,
    },
    {
      className: "ListFormat",
      property: "supportedLocalesOf",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "baseName",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "calendar",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "caseFirst",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "collation",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "hourCycle",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "language",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "maximize",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "minimize",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "numberingSystem",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "numeric",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "region",
      objectMissingOnWindow: false,
    },
    {
      className: "Locale",
      property: "script",
      objectMissingOnWindow: false,
    },
    {
      className: "location",
      property: "ancestorOrigins",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaElementAudioSourceNode",
      property: "mediaElement",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaKeys",
      property: "getStatusForPolicy",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaRecorder",
      property: "audioBitsPerSecond",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaRecorder",
      property: "videoBitsPerSecond",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaSource",
      property: "onsourceclose",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaStream",
      property: "onactive",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaStream",
      property: "oninactive",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaStreamAudioSourceNode",
      property: "mediaStream",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaStreamTrack",
      property: "contentHint",
      objectMissingOnWindow: false,
    },
    {
      className: "MediaStreamTrack",
      property: "getCapabilities",
      objectMissingOnWindow: false,
    },
    {
      className: "MemoryInfo",
      property: "jsHeapSizeLimit",
      objectMissingOnWindow: false,
    },
    {
      className: "MemoryInfo",
      property: "totalJSHeapSize",
      objectMissingOnWindow: false,
    },
    {
      className: "MemoryInfo",
      property: "usedJSHeapSize",
      objectMissingOnWindow: false,
    },
    {
      className: "MessageEvent",
      property: "userActivation",
      objectMissingOnWindow: false,
    },
    {
      className: "MimeTypeArray",
      property: "application/pdf",
      objectMissingOnWindow: false,
    },
    {
      className: "MimeTypeArray",
      property: "application/x-google-chrome-pdf",
      objectMissingOnWindow: false,
    },
    {
      className: "MimeTypeArray",
      property: "application/x-nacl",
      objectMissingOnWindow: false,
    },
    {
      className: "MimeTypeArray",
      property: "application/x-pnacl",
      objectMissingOnWindow: false,
    },
    {
      className: "MouseEvent",
      property: "fromElement",
      objectMissingOnWindow: false,
    },
    {
      className: "MouseEvent",
      property: "path",
      objectMissingOnWindow: false,
    },
    {
      className: "MouseEvent",
      property: "sourceCapabilities",
      objectMissingOnWindow: false,
    },
    {
      className: "MouseEvent",
      property: "toElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "bluetooth",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "bluetooth",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "connection",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "connection",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "deviceMemory",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "deviceMemory",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "getBattery",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "getUserMedia",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "keyboard",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "keyboard",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "locks",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "locks",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "mediaSession",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "mediaSession",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "presentation",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "presentation",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "requestMIDIAccess",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "unregisterProtocolHandler",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "usb",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "usb",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "userActivation",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "userActivation",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "webkitGetUserMedia",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "webkitPersistentStorage",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "webkitPersistentStorage",
      objectMissingOnWindow: false,
    },
    {
      className: "Navigator",
      property: "webkitTemporaryStorage",
      objectMissingOnWindow: false,
    },
    {
      className: "navigator",
      property: "webkitTemporaryStorage",
      objectMissingOnWindow: false,
    },
    {
      className: "Notification",
      property: "actions",
      objectMissingOnWindow: false,
    },
    {
      className: "Notification",
      property: "badge",
      objectMissingOnWindow: false,
    },
    {
      className: "Notification",
      property: "maxActions",
      objectMissingOnWindow: false,
    },
    {
      className: "Notification",
      property: "renotify",
      objectMissingOnWindow: false,
    },
    {
      className: "Notification",
      property: "requireInteraction",
      objectMissingOnWindow: false,
    },
    {
      className: "Notification",
      property: "silent",
      objectMissingOnWindow: false,
    },
    {
      className: "Notification",
      property: "timestamp",
      objectMissingOnWindow: false,
    },
    {
      className: "Notification",
      property: "vibrate",
      objectMissingOnWindow: false,
    },
    {
      className: "OfflineAudioContext",
      property: "resume",
      objectMissingOnWindow: false,
    },
    {
      className: "OfflineAudioContext",
      property: "suspend",
      objectMissingOnWindow: false,
    },
    {
      className: "Performance",
      property: "memory",
      objectMissingOnWindow: false,
    },
    {
      className: "performance",
      property: "memory",
      objectMissingOnWindow: false,
    },
    {
      className: "Plugin",
      property: "application/pdf",
      objectMissingOnWindow: false,
    },
    {
      className: "Plugin",
      property: "application/x-google-chrome-pdf",
      objectMissingOnWindow: false,
    },
    {
      className: "Plugin",
      property: "application/x-nacl",
      objectMissingOnWindow: false,
    },
    {
      className: "Plugin",
      property: "application/x-pnacl",
      objectMissingOnWindow: false,
    },
    {
      className: "PluginArray",
      property: "Chrome PDF Plugin",
      objectMissingOnWindow: false,
    },
    {
      className: "PluginArray",
      property: "Chrome PDF Viewer",
      objectMissingOnWindow: false,
    },
    {
      className: "PluginArray",
      property: "Native Client",
      objectMissingOnWindow: false,
    },
    {
      className: "Promise",
      property: "allSettled",
      objectMissingOnWindow: false,
    },
    {
      className: "PushManager",
      property: "supportedContentEncodings",
      objectMissingOnWindow: false,
    },
    {
      className: "PushSubscription",
      property: "expirationTime",
      objectMissingOnWindow: false,
    },
    {
      className: "PushSubscriptionOptions",
      property: "userVisibleOnly",
      objectMissingOnWindow: false,
    },
    {
      className: "Range",
      property: "collapsed",
      objectMissingOnWindow: false,
    },
    {
      className: "Range",
      property: "endContainer",
      objectMissingOnWindow: false,
    },
    {
      className: "Range",
      property: "endOffset",
      objectMissingOnWindow: false,
    },
    { className: "Range", property: "expand", objectMissingOnWindow: false },
    {
      className: "Range",
      property: "startContainer",
      objectMissingOnWindow: false,
    },
    {
      className: "Range",
      property: "startOffset",
      objectMissingOnWindow: false,
    },
    {
      className: "ReadableStream",
      property: "pipeThrough",
      objectMissingOnWindow: false,
    },
    {
      className: "ReadableStream",
      property: "pipeTo",
      objectMissingOnWindow: false,
    },
    {
      className: "RegExp",
      property: "dotAll",
      objectMissingOnWindow: false,
    },
    {
      className: "RelativeTimeFormat",
      property: "formatToParts",
      objectMissingOnWindow: false,
    },
    {
      className: "Request",
      property: "isHistoryNavigation",
      objectMissingOnWindow: false,
    },
    {
      className: "Request",
      property: "keepalive",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCCertificate",
      property: "getFingerprints",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCDataChannel",
      property: "maxRetransmitTime",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCDTMFSender",
      property: "canInsertDTMF",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "address",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "component",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "foundation",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "port",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "priority",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "protocol",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "relatedAddress",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "relatedPort",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "tcpType",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCIceCandidate",
      property: "type",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCPeerConnection",
      property: "connectionState",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCPeerConnection",
      property: "createDTMFSender",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCPeerConnection",
      property: "onconnectionstatechange",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCPeerConnection",
      property: "onremovestream",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCPeerConnection",
      property: "removeStream",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCPeerConnection",
      property: "sctp",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCPeerConnection",
      property: "setConfiguration",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpReceiver",
      property: "getCapabilities",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpReceiver",
      property: "getParameters",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpReceiver",
      property: "rtcpTransport",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpReceiver",
      property: "transport",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpSender",
      property: "getCapabilities",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpSender",
      property: "rtcpTransport",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpSender",
      property: "setStreams",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpSender",
      property: "transport",
      objectMissingOnWindow: false,
    },
    {
      className: "RTCRtpTransceiver",
      property: "setCodecPreferences",
      objectMissingOnWindow: false,
    },
    {
      className: "Selection",
      property: "baseNode",
      objectMissingOnWindow: false,
    },
    {
      className: "Selection",
      property: "baseOffset",
      objectMissingOnWindow: false,
    },
    {
      className: "Selection",
      property: "extentNode",
      objectMissingOnWindow: false,
    },
    {
      className: "Selection",
      property: "extentOffset",
      objectMissingOnWindow: false,
    },
    {
      className: "ServiceWorkerRegistration",
      property: "active",
      objectMissingOnWindow: false,
    },
    {
      className: "ServiceWorkerRegistration",
      property: "backgroundFetch",
      objectMissingOnWindow: false,
    },
    {
      className: "ServiceWorkerRegistration",
      property: "installing",
      objectMissingOnWindow: false,
    },
    {
      className: "ServiceWorkerRegistration",
      property: "navigationPreload",
      objectMissingOnWindow: false,
    },
    {
      className: "ServiceWorkerRegistration",
      property: "paymentManager",
      objectMissingOnWindow: false,
    },
    {
      className: "ServiceWorkerRegistration",
      property: "sync",
      objectMissingOnWindow: false,
    },
    {
      className: "ServiceWorkerRegistration",
      property: "waiting",
      objectMissingOnWindow: false,
    },
    {
      className: "ShadowRoot",
      property: "adoptedStyleSheets",
      objectMissingOnWindow: false,
    },
    {
      className: "ShadowRoot",
      property: "delegatesFocus",
      objectMissingOnWindow: false,
    },
    {
      className: "ShadowRoot",
      property: "getSelection",
      objectMissingOnWindow: false,
    },
    {
      className: "ShadowRoot",
      property: "pictureInPictureElement",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechGrammar",
      property: "src",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechGrammar",
      property: "weight",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechGrammarList",
      property: "addFromString",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechGrammarList",
      property: "addFromUri",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechGrammarList",
      property: "item",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechGrammarList",
      property: "length",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "abort",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "continuous",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "grammars",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "interimResults",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "lang",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "maxAlternatives",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onaudioend",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onaudiostart",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onend",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onerror",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onnomatch",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onresult",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onsoundend",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onsoundstart",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onspeechend",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onspeechstart",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "onstart",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "start",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognition",
      property: "stop",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognitionError",
      property: "error",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognitionError",
      property: "message",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognitionEvent",
      property: "emma",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognitionEvent",
      property: "interpretation",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognitionEvent",
      property: "resultIndex",
      objectMissingOnWindow: false,
    },
    {
      className: "SpeechRecognitionEvent",
      property: "results",
      objectMissingOnWindow: false,
    },
    {
      className: "StaticRange",
      property: "collapsed",
      objectMissingOnWindow: false,
    },
    {
      className: "StaticRange",
      property: "endContainer",
      objectMissingOnWindow: false,
    },
    {
      className: "StaticRange",
      property: "endOffset",
      objectMissingOnWindow: false,
    },
    {
      className: "StaticRange",
      property: "startContainer",
      objectMissingOnWindow: false,
    },
    {
      className: "StaticRange",
      property: "startOffset",
      objectMissingOnWindow: false,
    },
    {
      className: "StyleMedia",
      property: "matchMedium",
      objectMissingOnWindow: false,
    },
    {
      className: "StyleMedia",
      property: "type",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGAnimationElement",
      property: "onbegin",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGAnimationElement",
      property: "onend",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGAnimationElement",
      property: "onrepeat",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGElement",
      property: "nonce",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGElement",
      property: "oncancel",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGElement",
      property: "onmousewheel",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGElement",
      property: "onselectionchange",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGMaskElement",
      property: "requiredExtensions",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGMaskElement",
      property: "systemLanguage",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGPatternElement",
      property: "requiredExtensions",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGPatternElement",
      property: "systemLanguage",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGStyleElement",
      property: "disabled",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGSVGElement",
      property: "checkEnclosure",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGSVGElement",
      property: "checkIntersection",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGSVGElement",
      property: "getEnclosureList",
      objectMissingOnWindow: false,
    },
    {
      className: "SVGSVGElement",
      property: "getIntersectionList",
      objectMissingOnWindow: false,
    },
    {
      className: "Text",
      property: "getDestinationInsertionPoints",
      objectMissingOnWindow: false,
    },
    {
      className: "UIEvent",
      property: "sourceCapabilities",
      objectMissingOnWindow: false,
    },
    {
      className: "v8BreakIterator",
      property: "adoptText",
      objectMissingOnWindow: false,
    },
    {
      className: "v8BreakIterator",
      property: "breakType",
      objectMissingOnWindow: false,
    },
    {
      className: "v8BreakIterator",
      property: "current",
      objectMissingOnWindow: false,
    },
    {
      className: "v8BreakIterator",
      property: "first",
      objectMissingOnWindow: false,
    },
    {
      className: "v8BreakIterator",
      property: "next",
      objectMissingOnWindow: false,
    },
    {
      className: "v8BreakIterator",
      property: "resolvedOptions",
      objectMissingOnWindow: false,
    },
    {
      className: "v8BreakIterator",
      property: "supportedLocalesOf",
      objectMissingOnWindow: false,
    },
    {
      className: "WheelEvent",
      property: "wheelDelta",
      objectMissingOnWindow: false,
    },
    {
      className: "WheelEvent",
      property: "wheelDeltaX",
      objectMissingOnWindow: false,
    },
    {
      className: "WheelEvent",
      property: "wheelDeltaY",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "AbsoluteOrientationSensor",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "Accelerometer",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "ApplicationCache",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "ApplicationCacheErrorEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "Atomics",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "AudioParamMap",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "AudioWorklet",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "AudioWorkletNode",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BackgroundFetchManager",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BackgroundFetchRecord",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BackgroundFetchRegistration",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BeforeInstallPromptEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "Bluetooth",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BluetoothCharacteristicProperties",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BluetoothDevice",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BluetoothRemoteGATTCharacteristic",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BluetoothRemoteGATTDescriptor",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BluetoothRemoteGATTServer",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BluetoothRemoteGATTService",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "BluetoothUUID",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CanvasCaptureMediaStreamTrack",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "chrome",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "clientInformation",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "ClipboardItem",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSImageValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSKeywordValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSMathInvert",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSMathMax",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSMathMin",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSMathNegate",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSMathProduct",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSMathSum",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSMathValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSMatrixComponent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSNumericArray",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSNumericValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSPerspective",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSPositionValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSRotate",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSScale",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSSkew",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSSkewX",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSSkewY",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSStyleValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSTransformComponent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSTransformValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSTranslate",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSUnitValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSUnparsedValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "CSSVariableReferenceValue",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "defaultStatus",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "defaultstatus",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "DeviceMotionEventAcceleration",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "DeviceMotionEventRotationRate",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "DOMError",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "EnterPictureInPictureEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "External",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "FederatedCredential",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "Gyroscope",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "HTMLContentElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "HTMLDialogElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "HTMLShadowElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "ImageCapture",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "InputDeviceCapabilities",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "InputDeviceInfo",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "Keyboard",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "KeyboardLayoutMap",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "LinearAccelerationSensor",
      objectMissingOnWindow: false,
    },
    { className: "Window", property: "Lock", objectMissingOnWindow: false },
    {
      className: "Window",
      property: "LockManager",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MediaMetadata",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MediaSession",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MediaSettingsRange",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MIDIAccess",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MIDIConnectionEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MIDIInput",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MIDIInputMap",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MIDIMessageEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MIDIOutput",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MIDIOutputMap",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "MIDIPort",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "NavigationPreloadManager",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "NetworkInformation",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "offscreenBuffering",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "OffscreenCanvas",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "OffscreenCanvasRenderingContext2D",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "onappinstalled",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "onbeforeinstallprompt",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "oncancel",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "ondeviceorientationabsolute",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "onmousewheel",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "onsearch",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "onselectionchange",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "openDatabase",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "OrientationSensor",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "OverconstrainedError",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PasswordCredential",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PaymentAddress",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PaymentInstruments",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PaymentManager",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PaymentMethodChangeEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PaymentRequest",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PaymentRequestUpdateEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PaymentResponse",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PerformanceEventTiming",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PerformanceLongTaskTiming",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PerformancePaintTiming",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PhotoCapabilities",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PictureInPictureWindow",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "Presentation",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PresentationAvailability",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PresentationConnection",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PresentationConnectionAvailableEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PresentationConnectionCloseEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PresentationConnectionList",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PresentationReceiver",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "PresentationRequest",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "RelativeOrientationSensor",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "RemotePlayback",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "ReportingObserver",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "RTCDtlsTransport",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "RTCError",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "RTCErrorEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "RTCIceTransport",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "RTCSctpTransport",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "Sensor",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "SensorErrorEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "SharedArrayBuffer",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "styleMedia",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "StylePropertyMap",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "StylePropertyMapReadOnly",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "SVGDiscardElement",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "SyncManager",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "TaskAttributionTiming",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "TextDecoderStream",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "TextEncoderStream",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "TextEvent",
      objectMissingOnWindow: false,
    },
    { className: "Window", property: "Touch", objectMissingOnWindow: false },
    {
      className: "Window",
      property: "TouchEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "TouchList",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "TransformStream",
      objectMissingOnWindow: false,
    },
    { className: "Window", property: "USB", objectMissingOnWindow: false },
    {
      className: "Window",
      property: "USBAlternateInterface",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBConfiguration",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBConnectionEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBDevice",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBEndpoint",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBInterface",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBInTransferResult",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBIsochronousInTransferPacket",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBIsochronousInTransferResult",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBIsochronousOutTransferPacket",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBIsochronousOutTransferResult",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "USBOutTransferResult",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "UserActivation",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "visualViewport",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitCancelAnimationFrame",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitMediaStream",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "WebKitMutationObserver",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitRequestAnimationFrame",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitRequestFileSystem",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitResolveLocalFileSystemURL",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitRTCPeerConnection",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitSpeechGrammar",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitSpeechGrammarList",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitSpeechRecognition",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitSpeechRecognitionError",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitSpeechRecognitionEvent",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "webkitStorageInfo",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "Worklet",
      objectMissingOnWindow: false,
    },
    {
      className: "Window",
      property: "WritableStream",
      objectMissingOnWindow: false,
    },
    {
      className: "Accelerometer",
      property: "x",
      objectMissingOnWindow: true,
    },
    {
      className: "Accelerometer",
      property: "y",
      objectMissingOnWindow: true,
    },
    {
      className: "Accelerometer",
      property: "z",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "abort",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "oncached",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "onchecking",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "ondownloading",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "onerror",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "onnoupdate",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "onobsolete",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "onprogress",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "onupdateready",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "status",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "swapCache",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCache",
      property: "update",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCacheErrorEvent",
      property: "message",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCacheErrorEvent",
      property: "reason",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCacheErrorEvent",
      property: "status",
      objectMissingOnWindow: true,
    },
    {
      className: "ApplicationCacheErrorEvent",
      property: "url",
      objectMissingOnWindow: true,
    },
    { className: "Atomics", property: "add", objectMissingOnWindow: true },
    { className: "Atomics", property: "and", objectMissingOnWindow: true },
    {
      className: "Atomics",
      property: "compareExchange",
      objectMissingOnWindow: true,
    },
    {
      className: "Atomics",
      property: "exchange",
      objectMissingOnWindow: true,
    },
    {
      className: "Atomics",
      property: "isLockFree",
      objectMissingOnWindow: true,
    },
    { className: "Atomics", property: "load", objectMissingOnWindow: true },
    {
      className: "Atomics",
      property: "notify",
      objectMissingOnWindow: true,
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
      objectMissingOnWindow: true,
    },
    {
      className: "AudioParamMap",
      property: "forEach",
      objectMissingOnWindow: true,
    },
    {
      className: "AudioParamMap",
      property: "get",
      objectMissingOnWindow: true,
    },
    {
      className: "AudioParamMap",
      property: "has",
      objectMissingOnWindow: true,
    },
    {
      className: "AudioParamMap",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "AudioParamMap",
      property: "size",
      objectMissingOnWindow: true,
    },
    {
      className: "AudioParamMap",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "AudioWorkletNode",
      property: "onprocessorerror",
      objectMissingOnWindow: true,
    },
    {
      className: "AudioWorkletNode",
      property: "parameters",
      objectMissingOnWindow: true,
    },
    {
      className: "AudioWorkletNode",
      property: "port",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchManager",
      property: "fetch",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchManager",
      property: "get",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchManager",
      property: "getIds",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRecord",
      property: "request",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRecord",
      property: "responseReady",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "abort",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "downloaded",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "downloadTotal",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "failureReason",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "id",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "match",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "matchAll",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "onprogress",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "recordsAvailable",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "result",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "uploaded",
      objectMissingOnWindow: true,
    },
    {
      className: "BackgroundFetchRegistration",
      property: "uploadTotal",
      objectMissingOnWindow: true,
    },
    {
      className: "BeforeInstallPromptEvent",
      property: "platforms",
      objectMissingOnWindow: true,
    },
    {
      className: "BeforeInstallPromptEvent",
      property: "prompt",
      objectMissingOnWindow: true,
    },
    {
      className: "BeforeInstallPromptEvent",
      property: "userChoice",
      objectMissingOnWindow: true,
    },
    {
      className: "Bluetooth",
      property: "requestDevice",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "authenticatedSignedWrites",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "broadcast",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "indicate",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "notify",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "read",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "reliableWrite",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "writableAuxiliaries",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "write",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothCharacteristicProperties",
      property: "writeWithoutResponse",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothDevice",
      property: "gatt",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothDevice",
      property: "id",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothDevice",
      property: "name",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothDevice",
      property: "ongattserverdisconnected",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "getDescriptor",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "getDescriptors",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "oncharacteristicvaluechanged",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "properties",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "readValue",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "service",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "startNotifications",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "stopNotifications",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "uuid",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "value",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTCharacteristic",
      property: "writeValue",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "characteristic",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "readValue",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "uuid",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "value",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTDescriptor",
      property: "writeValue",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "connect",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "connected",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "device",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "disconnect",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "getPrimaryService",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTServer",
      property: "getPrimaryServices",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "device",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "getCharacteristic",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "getCharacteristics",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "isPrimary",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothRemoteGATTService",
      property: "uuid",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothUUID",
      property: "canonicalUUID",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothUUID",
      property: "getCharacteristic",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothUUID",
      property: "getDescriptor",
      objectMissingOnWindow: true,
    },
    {
      className: "BluetoothUUID",
      property: "getService",
      objectMissingOnWindow: true,
    },
    {
      className: "CanvasCaptureMediaStreamTrack",
      property: "canvas",
      objectMissingOnWindow: true,
    },
    {
      className: "CanvasCaptureMediaStreamTrack",
      property: "requestFrame",
      objectMissingOnWindow: true,
    },
    { className: "chrome", property: "app", objectMissingOnWindow: true },
    { className: "chrome", property: "csi", objectMissingOnWindow: true },
    {
      className: "chrome",
      property: "loadTimes",
      objectMissingOnWindow: true,
    },
    {
      className: "chrome",
      property: "runtime",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "appCodeName",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "appName",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "appVersion",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "bluetooth",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "clipboard",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "connection",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "cookieEnabled",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "credentials",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "deviceMemory",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "doNotTrack",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "geolocation",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "hardwareConcurrency",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "keyboard",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "language",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "languages",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "locks",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "maxTouchPoints",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "mediaCapabilities",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "mediaDevices",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "mediaSession",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "mimeTypes",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "onLine",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "permissions",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "platform",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "plugins",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "presentation",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "product",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "productSub",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "serviceWorker",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "storage",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "usb",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "userActivation",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "userAgent",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "vendor",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "vendorSub",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "webkitPersistentStorage",
      objectMissingOnWindow: true,
    },
    {
      className: "clientInformation",
      property: "webkitTemporaryStorage",
      objectMissingOnWindow: true,
    },
    {
      className: "ClipboardItem",
      property: "getType",
      objectMissingOnWindow: true,
    },
    {
      className: "ClipboardItem",
      property: "types",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSKeywordValue",
      property: "value",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSMathInvert",
      property: "value",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSMathMax",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSMathMin",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSMathNegate",
      property: "value",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSMathProduct",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSMathSum",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSMathValue",
      property: "operator",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSMatrixComponent",
      property: "matrix",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericArray",
      property: "entries",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericArray",
      property: "forEach",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericArray",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericArray",
      property: "length",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericArray",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "add",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "div",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "equals",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "max",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "min",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "mul",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "parse",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "sub",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "to",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "toSum",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSNumericValue",
      property: "type",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSPerspective",
      property: "length",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSPositionValue",
      property: "x",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSPositionValue",
      property: "y",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSRotate",
      property: "angle",
      objectMissingOnWindow: true,
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
      objectMissingOnWindow: true,
    },
    {
      className: "CSSStyleValue",
      property: "parseAll",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformComponent",
      property: "is2D",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformComponent",
      property: "toMatrix",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformValue",
      property: "entries",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformValue",
      property: "forEach",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformValue",
      property: "is2D",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformValue",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformValue",
      property: "length",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformValue",
      property: "toMatrix",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTransformValue",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTranslate",
      property: "x",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTranslate",
      property: "y",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSTranslate",
      property: "z",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSUnitValue",
      property: "unit",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSUnitValue",
      property: "value",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSUnparsedValue",
      property: "entries",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSUnparsedValue",
      property: "forEach",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSUnparsedValue",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSUnparsedValue",
      property: "length",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSUnparsedValue",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSVariableReferenceValue",
      property: "fallback",
      objectMissingOnWindow: true,
    },
    {
      className: "CSSVariableReferenceValue",
      property: "variable",
      objectMissingOnWindow: true,
    },
    {
      className: "DeviceMotionEventAcceleration",
      property: "x",
      objectMissingOnWindow: true,
    },
    {
      className: "DeviceMotionEventAcceleration",
      property: "y",
      objectMissingOnWindow: true,
    },
    {
      className: "DeviceMotionEventAcceleration",
      property: "z",
      objectMissingOnWindow: true,
    },
    {
      className: "DeviceMotionEventRotationRate",
      property: "alpha",
      objectMissingOnWindow: true,
    },
    {
      className: "DeviceMotionEventRotationRate",
      property: "beta",
      objectMissingOnWindow: true,
    },
    {
      className: "DeviceMotionEventRotationRate",
      property: "gamma",
      objectMissingOnWindow: true,
    },
    {
      className: "DOMError",
      property: "message",
      objectMissingOnWindow: true,
    },
    { className: "DOMError", property: "name", objectMissingOnWindow: true },
    {
      className: "EnterPictureInPictureEvent",
      property: "pictureInPictureWindow",
      objectMissingOnWindow: true,
    },
    {
      className: "FederatedCredential",
      property: "iconURL",
      objectMissingOnWindow: true,
    },
    {
      className: "FederatedCredential",
      property: "name",
      objectMissingOnWindow: true,
    },
    {
      className: "FederatedCredential",
      property: "protocol",
      objectMissingOnWindow: true,
    },
    {
      className: "FederatedCredential",
      property: "provider",
      objectMissingOnWindow: true,
    },
    { className: "Gyroscope", property: "x", objectMissingOnWindow: true },
    { className: "Gyroscope", property: "y", objectMissingOnWindow: true },
    { className: "Gyroscope", property: "z", objectMissingOnWindow: true },
    {
      className: "HTMLContentElement",
      property: "getDistributedNodes",
      objectMissingOnWindow: true,
    },
    {
      className: "HTMLContentElement",
      property: "select",
      objectMissingOnWindow: true,
    },
    {
      className: "HTMLDialogElement",
      property: "close",
      objectMissingOnWindow: true,
    },
    {
      className: "HTMLDialogElement",
      property: "open",
      objectMissingOnWindow: true,
    },
    {
      className: "HTMLDialogElement",
      property: "returnValue",
      objectMissingOnWindow: true,
    },
    {
      className: "HTMLDialogElement",
      property: "show",
      objectMissingOnWindow: true,
    },
    {
      className: "HTMLDialogElement",
      property: "showModal",
      objectMissingOnWindow: true,
    },
    {
      className: "HTMLShadowElement",
      property: "getDistributedNodes",
      objectMissingOnWindow: true,
    },
    {
      className: "ImageCapture",
      property: "getPhotoCapabilities",
      objectMissingOnWindow: true,
    },
    {
      className: "ImageCapture",
      property: "getPhotoSettings",
      objectMissingOnWindow: true,
    },
    {
      className: "ImageCapture",
      property: "grabFrame",
      objectMissingOnWindow: true,
    },
    {
      className: "ImageCapture",
      property: "takePhoto",
      objectMissingOnWindow: true,
    },
    {
      className: "ImageCapture",
      property: "track",
      objectMissingOnWindow: true,
    },
    {
      className: "InputDeviceCapabilities",
      property: "firesTouchEvents",
      objectMissingOnWindow: true,
    },
    {
      className: "InputDeviceInfo",
      property: "getCapabilities",
      objectMissingOnWindow: true,
    },
    {
      className: "Keyboard",
      property: "getLayoutMap",
      objectMissingOnWindow: true,
    },
    { className: "Keyboard", property: "lock", objectMissingOnWindow: true },
    {
      className: "Keyboard",
      property: "unlock",
      objectMissingOnWindow: true,
    },
    {
      className: "KeyboardLayoutMap",
      property: "entries",
      objectMissingOnWindow: true,
    },
    {
      className: "KeyboardLayoutMap",
      property: "forEach",
      objectMissingOnWindow: true,
    },
    {
      className: "KeyboardLayoutMap",
      property: "get",
      objectMissingOnWindow: true,
    },
    {
      className: "KeyboardLayoutMap",
      property: "has",
      objectMissingOnWindow: true,
    },
    {
      className: "KeyboardLayoutMap",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "KeyboardLayoutMap",
      property: "size",
      objectMissingOnWindow: true,
    },
    {
      className: "KeyboardLayoutMap",
      property: "values",
      objectMissingOnWindow: true,
    },
    { className: "Lock", property: "mode", objectMissingOnWindow: true },
    { className: "Lock", property: "name", objectMissingOnWindow: true },
    {
      className: "LockManager",
      property: "query",
      objectMissingOnWindow: true,
    },
    {
      className: "LockManager",
      property: "request",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaMetadata",
      property: "album",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaMetadata",
      property: "artist",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaMetadata",
      property: "artwork",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaMetadata",
      property: "title",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaSession",
      property: "metadata",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaSession",
      property: "playbackState",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaSession",
      property: "setActionHandler",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaSettingsRange",
      property: "max",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaSettingsRange",
      property: "min",
      objectMissingOnWindow: true,
    },
    {
      className: "MediaSettingsRange",
      property: "step",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIAccess",
      property: "inputs",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIAccess",
      property: "onstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIAccess",
      property: "outputs",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIAccess",
      property: "sysexEnabled",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIConnectionEvent",
      property: "port",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIInput",
      property: "onmidimessage",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIInputMap",
      property: "entries",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIInputMap",
      property: "forEach",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIInputMap",
      property: "get",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIInputMap",
      property: "has",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIInputMap",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIInputMap",
      property: "size",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIInputMap",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIMessageEvent",
      property: "data",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIOutput",
      property: "send",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIOutputMap",
      property: "entries",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIOutputMap",
      property: "forEach",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIOutputMap",
      property: "get",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIOutputMap",
      property: "has",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIOutputMap",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIOutputMap",
      property: "size",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIOutputMap",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIPort",
      property: "close",
      objectMissingOnWindow: true,
    },
    {
      className: "MIDIPort",
      property: "connection",
      objectMissingOnWindow: true,
    },
    { className: "MIDIPort", property: "id", objectMissingOnWindow: true },
    {
      className: "MIDIPort",
      property: "manufacturer",
      objectMissingOnWindow: true,
    },
    { className: "MIDIPort", property: "name", objectMissingOnWindow: true },
    {
      className: "MIDIPort",
      property: "onstatechange",
      objectMissingOnWindow: true,
    },
    { className: "MIDIPort", property: "open", objectMissingOnWindow: true },
    {
      className: "MIDIPort",
      property: "state",
      objectMissingOnWindow: true,
    },
    { className: "MIDIPort", property: "type", objectMissingOnWindow: true },
    {
      className: "MIDIPort",
      property: "version",
      objectMissingOnWindow: true,
    },
    {
      className: "NavigationPreloadManager",
      property: "disable",
      objectMissingOnWindow: true,
    },
    {
      className: "NavigationPreloadManager",
      property: "enable",
      objectMissingOnWindow: true,
    },
    {
      className: "NavigationPreloadManager",
      property: "getState",
      objectMissingOnWindow: true,
    },
    {
      className: "NavigationPreloadManager",
      property: "setHeaderValue",
      objectMissingOnWindow: true,
    },
    {
      className: "NetworkInformation",
      property: "downlink",
      objectMissingOnWindow: true,
    },
    {
      className: "NetworkInformation",
      property: "effectiveType",
      objectMissingOnWindow: true,
    },
    {
      className: "NetworkInformation",
      property: "onchange",
      objectMissingOnWindow: true,
    },
    {
      className: "NetworkInformation",
      property: "rtt",
      objectMissingOnWindow: true,
    },
    {
      className: "NetworkInformation",
      property: "saveData",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvas",
      property: "convertToBlob",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvas",
      property: "getContext",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvas",
      property: "height",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvas",
      property: "transferToImageBitmap",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvas",
      property: "width",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "arc",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "arcTo",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "beginPath",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "bezierCurveTo",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "canvas",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "clearRect",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "clip",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "closePath",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "createImageData",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "createLinearGradient",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "createPattern",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "createRadialGradient",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "direction",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "drawImage",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "ellipse",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "fill",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "fillRect",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "fillStyle",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "fillText",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "filter",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "font",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "getImageData",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "getLineDash",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "globalAlpha",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "globalCompositeOperation",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "imageSmoothingEnabled",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "imageSmoothingQuality",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "isPointInPath",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "isPointInStroke",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineCap",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineDashOffset",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineJoin",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineTo",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "lineWidth",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "measureText",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "miterLimit",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "moveTo",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "putImageData",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "quadraticCurveTo",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "rect",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "resetTransform",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "restore",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "rotate",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "save",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "scale",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "setLineDash",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "setTransform",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "shadowBlur",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "shadowColor",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "shadowOffsetX",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "shadowOffsetY",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "stroke",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "strokeRect",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "strokeStyle",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "strokeText",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "textAlign",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "textBaseline",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "transform",
      objectMissingOnWindow: true,
    },
    {
      className: "OffscreenCanvasRenderingContext2D",
      property: "translate",
      objectMissingOnWindow: true,
    },
    {
      className: "OrientationSensor",
      property: "populateMatrix",
      objectMissingOnWindow: true,
    },
    {
      className: "OrientationSensor",
      property: "quaternion",
      objectMissingOnWindow: true,
    },
    {
      className: "OverconstrainedError",
      property: "constraint",
      objectMissingOnWindow: true,
    },
    {
      className: "OverconstrainedError",
      property: "message",
      objectMissingOnWindow: true,
    },
    {
      className: "OverconstrainedError",
      property: "name",
      objectMissingOnWindow: true,
    },
    {
      className: "PasswordCredential",
      property: "iconURL",
      objectMissingOnWindow: true,
    },
    {
      className: "PasswordCredential",
      property: "name",
      objectMissingOnWindow: true,
    },
    {
      className: "PasswordCredential",
      property: "password",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "addressLine",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "city",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "country",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "dependentLocality",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "organization",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "phone",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "postalCode",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "recipient",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "region",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "sortingCode",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentAddress",
      property: "toJSON",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentInstruments",
      property: "clear",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentInstruments",
      property: "delete",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentInstruments",
      property: "get",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentInstruments",
      property: "has",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentInstruments",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentInstruments",
      property: "set",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentManager",
      property: "instruments",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentManager",
      property: "userHint",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentMethodChangeEvent",
      property: "methodDetails",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentMethodChangeEvent",
      property: "methodName",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "abort",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "canMakePayment",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "hasEnrolledInstrument",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "id",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "onpaymentmethodchange",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "onshippingaddresschange",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "onshippingoptionchange",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "shippingAddress",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "shippingOption",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "shippingType",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequest",
      property: "show",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentRequestUpdateEvent",
      property: "updateWith",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "complete",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "details",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "methodName",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "payerEmail",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "payerName",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "payerPhone",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "requestId",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "shippingAddress",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "shippingOption",
      objectMissingOnWindow: true,
    },
    {
      className: "PaymentResponse",
      property: "toJSON",
      objectMissingOnWindow: true,
    },
    {
      className: "PerformanceEventTiming",
      property: "cancelable",
      objectMissingOnWindow: true,
    },
    {
      className: "PerformanceEventTiming",
      property: "processingEnd",
      objectMissingOnWindow: true,
    },
    {
      className: "PerformanceEventTiming",
      property: "processingStart",
      objectMissingOnWindow: true,
    },
    {
      className: "PerformanceLongTaskTiming",
      property: "attribution",
      objectMissingOnWindow: true,
    },
    {
      className: "PhotoCapabilities",
      property: "fillLightMode",
      objectMissingOnWindow: true,
    },
    {
      className: "PhotoCapabilities",
      property: "imageHeight",
      objectMissingOnWindow: true,
    },
    {
      className: "PhotoCapabilities",
      property: "imageWidth",
      objectMissingOnWindow: true,
    },
    {
      className: "PhotoCapabilities",
      property: "redEyeReduction",
      objectMissingOnWindow: true,
    },
    {
      className: "PictureInPictureWindow",
      property: "height",
      objectMissingOnWindow: true,
    },
    {
      className: "PictureInPictureWindow",
      property: "onresize",
      objectMissingOnWindow: true,
    },
    {
      className: "PictureInPictureWindow",
      property: "width",
      objectMissingOnWindow: true,
    },
    {
      className: "Presentation",
      property: "defaultRequest",
      objectMissingOnWindow: true,
    },
    {
      className: "Presentation",
      property: "receiver",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationAvailability",
      property: "onchange",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationAvailability",
      property: "value",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "binaryType",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "close",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "id",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "onclose",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "onconnect",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "onmessage",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "onterminate",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "send",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "state",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "terminate",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnection",
      property: "url",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnectionAvailableEvent",
      property: "connection",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnectionCloseEvent",
      property: "message",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnectionCloseEvent",
      property: "reason",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnectionList",
      property: "connections",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationConnectionList",
      property: "onconnectionavailable",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationReceiver",
      property: "connectionList",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationRequest",
      property: "getAvailability",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationRequest",
      property: "onconnectionavailable",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationRequest",
      property: "reconnect",
      objectMissingOnWindow: true,
    },
    {
      className: "PresentationRequest",
      property: "start",
      objectMissingOnWindow: true,
    },
    {
      className: "RemotePlayback",
      property: "cancelWatchAvailability",
      objectMissingOnWindow: true,
    },
    {
      className: "RemotePlayback",
      property: "onconnect",
      objectMissingOnWindow: true,
    },
    {
      className: "RemotePlayback",
      property: "onconnecting",
      objectMissingOnWindow: true,
    },
    {
      className: "RemotePlayback",
      property: "ondisconnect",
      objectMissingOnWindow: true,
    },
    {
      className: "RemotePlayback",
      property: "prompt",
      objectMissingOnWindow: true,
    },
    {
      className: "RemotePlayback",
      property: "state",
      objectMissingOnWindow: true,
    },
    {
      className: "RemotePlayback",
      property: "watchAvailability",
      objectMissingOnWindow: true,
    },
    {
      className: "ReportingObserver",
      property: "disconnect",
      objectMissingOnWindow: true,
    },
    {
      className: "ReportingObserver",
      property: "observe",
      objectMissingOnWindow: true,
    },
    {
      className: "ReportingObserver",
      property: "takeRecords",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCDtlsTransport",
      property: "getRemoteCertificates",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCDtlsTransport",
      property: "iceTransport",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCDtlsTransport",
      property: "onerror",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCDtlsTransport",
      property: "onstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCDtlsTransport",
      property: "state",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCError",
      property: "errorDetail",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCError",
      property: "httpRequestStatusCode",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCError",
      property: "receivedAlert",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCError",
      property: "sctpCauseCode",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCError",
      property: "sdpLineNumber",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCError",
      property: "sentAlert",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCErrorEvent",
      property: "error",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "gatheringState",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "getLocalCandidates",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "getLocalParameters",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "getRemoteCandidates",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "getRemoteParameters",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "getSelectedCandidatePair",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "ongatheringstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "onselectedcandidatepairchange",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "onstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "role",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCIceTransport",
      property: "state",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCSctpTransport",
      property: "maxChannels",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCSctpTransport",
      property: "maxMessageSize",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCSctpTransport",
      property: "onstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCSctpTransport",
      property: "state",
      objectMissingOnWindow: true,
    },
    {
      className: "RTCSctpTransport",
      property: "transport",
      objectMissingOnWindow: true,
    },
    {
      className: "Sensor",
      property: "activated",
      objectMissingOnWindow: true,
    },
    {
      className: "Sensor",
      property: "hasReading",
      objectMissingOnWindow: true,
    },
    {
      className: "Sensor",
      property: "onactivate",
      objectMissingOnWindow: true,
    },
    {
      className: "Sensor",
      property: "onerror",
      objectMissingOnWindow: true,
    },
    {
      className: "Sensor",
      property: "onreading",
      objectMissingOnWindow: true,
    },
    { className: "Sensor", property: "start", objectMissingOnWindow: true },
    { className: "Sensor", property: "stop", objectMissingOnWindow: true },
    {
      className: "Sensor",
      property: "timestamp",
      objectMissingOnWindow: true,
    },
    {
      className: "SensorErrorEvent",
      property: "error",
      objectMissingOnWindow: true,
    },
    {
      className: "SharedArrayBuffer",
      property: "byteLength",
      objectMissingOnWindow: true,
    },
    {
      className: "SharedArrayBuffer",
      property: "slice",
      objectMissingOnWindow: true,
    },
    {
      className: "styleMedia",
      property: "type",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMap",
      property: "append",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMap",
      property: "clear",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMap",
      property: "delete",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMap",
      property: "set",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "entries",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "forEach",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "get",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "getAll",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "has",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "keys",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "size",
      objectMissingOnWindow: true,
    },
    {
      className: "StylePropertyMapReadOnly",
      property: "values",
      objectMissingOnWindow: true,
    },
    {
      className: "SyncManager",
      property: "getTags",
      objectMissingOnWindow: true,
    },
    {
      className: "SyncManager",
      property: "register",
      objectMissingOnWindow: true,
    },
    {
      className: "TaskAttributionTiming",
      property: "containerId",
      objectMissingOnWindow: true,
    },
    {
      className: "TaskAttributionTiming",
      property: "containerName",
      objectMissingOnWindow: true,
    },
    {
      className: "TaskAttributionTiming",
      property: "containerSrc",
      objectMissingOnWindow: true,
    },
    {
      className: "TaskAttributionTiming",
      property: "containerType",
      objectMissingOnWindow: true,
    },
    {
      className: "TextDecoderStream",
      property: "encoding",
      objectMissingOnWindow: true,
    },
    {
      className: "TextDecoderStream",
      property: "fatal",
      objectMissingOnWindow: true,
    },
    {
      className: "TextDecoderStream",
      property: "ignoreBOM",
      objectMissingOnWindow: true,
    },
    {
      className: "TextDecoderStream",
      property: "readable",
      objectMissingOnWindow: true,
    },
    {
      className: "TextDecoderStream",
      property: "writable",
      objectMissingOnWindow: true,
    },
    {
      className: "TextEncoderStream",
      property: "encoding",
      objectMissingOnWindow: true,
    },
    {
      className: "TextEncoderStream",
      property: "readable",
      objectMissingOnWindow: true,
    },
    {
      className: "TextEncoderStream",
      property: "writable",
      objectMissingOnWindow: true,
    },
    {
      className: "TextEvent",
      property: "data",
      objectMissingOnWindow: true,
    },
    {
      className: "TextEvent",
      property: "initTextEvent",
      objectMissingOnWindow: true,
    },
    { className: "Touch", property: "clientX", objectMissingOnWindow: true },
    { className: "Touch", property: "clientY", objectMissingOnWindow: true },
    { className: "Touch", property: "force", objectMissingOnWindow: true },
    {
      className: "Touch",
      property: "identifier",
      objectMissingOnWindow: true,
    },
    { className: "Touch", property: "pageX", objectMissingOnWindow: true },
    { className: "Touch", property: "pageY", objectMissingOnWindow: true },
    { className: "Touch", property: "radiusX", objectMissingOnWindow: true },
    { className: "Touch", property: "radiusY", objectMissingOnWindow: true },
    {
      className: "Touch",
      property: "rotationAngle",
      objectMissingOnWindow: true,
    },
    { className: "Touch", property: "screenX", objectMissingOnWindow: true },
    { className: "Touch", property: "screenY", objectMissingOnWindow: true },
    { className: "Touch", property: "target", objectMissingOnWindow: true },
    {
      className: "TouchEvent",
      property: "altKey",
      objectMissingOnWindow: true,
    },
    {
      className: "TouchEvent",
      property: "changedTouches",
      objectMissingOnWindow: true,
    },
    {
      className: "TouchEvent",
      property: "ctrlKey",
      objectMissingOnWindow: true,
    },
    {
      className: "TouchEvent",
      property: "metaKey",
      objectMissingOnWindow: true,
    },
    {
      className: "TouchEvent",
      property: "shiftKey",
      objectMissingOnWindow: true,
    },
    {
      className: "TouchEvent",
      property: "targetTouches",
      objectMissingOnWindow: true,
    },
    {
      className: "TouchEvent",
      property: "touches",
      objectMissingOnWindow: true,
    },
    {
      className: "TouchList",
      property: "item",
      objectMissingOnWindow: true,
    },
    {
      className: "TouchList",
      property: "length",
      objectMissingOnWindow: true,
    },
    {
      className: "TransformStream",
      property: "readable",
      objectMissingOnWindow: true,
    },
    {
      className: "TransformStream",
      property: "writable",
      objectMissingOnWindow: true,
    },
    {
      className: "USB",
      property: "getDevices",
      objectMissingOnWindow: true,
    },
    { className: "USB", property: "onconnect", objectMissingOnWindow: true },
    {
      className: "USB",
      property: "ondisconnect",
      objectMissingOnWindow: true,
    },
    {
      className: "USB",
      property: "requestDevice",
      objectMissingOnWindow: true,
    },
    {
      className: "USBAlternateInterface",
      property: "alternateSetting",
      objectMissingOnWindow: true,
    },
    {
      className: "USBAlternateInterface",
      property: "endpoints",
      objectMissingOnWindow: true,
    },
    {
      className: "USBAlternateInterface",
      property: "interfaceClass",
      objectMissingOnWindow: true,
    },
    {
      className: "USBAlternateInterface",
      property: "interfaceName",
      objectMissingOnWindow: true,
    },
    {
      className: "USBAlternateInterface",
      property: "interfaceProtocol",
      objectMissingOnWindow: true,
    },
    {
      className: "USBAlternateInterface",
      property: "interfaceSubclass",
      objectMissingOnWindow: true,
    },
    {
      className: "USBConfiguration",
      property: "configurationName",
      objectMissingOnWindow: true,
    },
    {
      className: "USBConfiguration",
      property: "configurationValue",
      objectMissingOnWindow: true,
    },
    {
      className: "USBConfiguration",
      property: "interfaces",
      objectMissingOnWindow: true,
    },
    {
      className: "USBConnectionEvent",
      property: "device",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "claimInterface",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "clearHalt",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "close",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "configuration",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "configurations",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "controlTransferIn",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "controlTransferOut",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "deviceClass",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "deviceProtocol",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "deviceSubclass",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "deviceVersionMajor",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "deviceVersionMinor",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "deviceVersionSubminor",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "isochronousTransferIn",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "isochronousTransferOut",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "manufacturerName",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "open",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "opened",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "productId",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "productName",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "releaseInterface",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "reset",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "selectAlternateInterface",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "selectConfiguration",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "serialNumber",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "transferIn",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "transferOut",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "usbVersionMajor",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "usbVersionMinor",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "usbVersionSubminor",
      objectMissingOnWindow: true,
    },
    {
      className: "USBDevice",
      property: "vendorId",
      objectMissingOnWindow: true,
    },
    {
      className: "USBEndpoint",
      property: "direction",
      objectMissingOnWindow: true,
    },
    {
      className: "USBEndpoint",
      property: "endpointNumber",
      objectMissingOnWindow: true,
    },
    {
      className: "USBEndpoint",
      property: "packetSize",
      objectMissingOnWindow: true,
    },
    {
      className: "USBEndpoint",
      property: "type",
      objectMissingOnWindow: true,
    },
    {
      className: "USBInterface",
      property: "alternate",
      objectMissingOnWindow: true,
    },
    {
      className: "USBInterface",
      property: "alternates",
      objectMissingOnWindow: true,
    },
    {
      className: "USBInterface",
      property: "claimed",
      objectMissingOnWindow: true,
    },
    {
      className: "USBInterface",
      property: "interfaceNumber",
      objectMissingOnWindow: true,
    },
    {
      className: "USBInTransferResult",
      property: "data",
      objectMissingOnWindow: true,
    },
    {
      className: "USBInTransferResult",
      property: "status",
      objectMissingOnWindow: true,
    },
    {
      className: "USBIsochronousInTransferPacket",
      property: "data",
      objectMissingOnWindow: true,
    },
    {
      className: "USBIsochronousInTransferPacket",
      property: "status",
      objectMissingOnWindow: true,
    },
    {
      className: "USBIsochronousInTransferResult",
      property: "data",
      objectMissingOnWindow: true,
    },
    {
      className: "USBIsochronousInTransferResult",
      property: "packets",
      objectMissingOnWindow: true,
    },
    {
      className: "USBIsochronousOutTransferPacket",
      property: "bytesWritten",
      objectMissingOnWindow: true,
    },
    {
      className: "USBIsochronousOutTransferPacket",
      property: "status",
      objectMissingOnWindow: true,
    },
    {
      className: "USBIsochronousOutTransferResult",
      property: "packets",
      objectMissingOnWindow: true,
    },
    {
      className: "USBOutTransferResult",
      property: "bytesWritten",
      objectMissingOnWindow: true,
    },
    {
      className: "USBOutTransferResult",
      property: "status",
      objectMissingOnWindow: true,
    },
    {
      className: "UserActivation",
      property: "hasBeenActive",
      objectMissingOnWindow: true,
    },
    {
      className: "UserActivation",
      property: "isActive",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "height",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "offsetLeft",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "offsetTop",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "onresize",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "onscroll",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "pageLeft",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "pageTop",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "scale",
      objectMissingOnWindow: true,
    },
    {
      className: "visualViewport",
      property: "width",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "active",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "addTrack",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "clone",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "getAudioTracks",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "getTrackById",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "getTracks",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "getVideoTracks",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "id",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "onactive",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "onaddtrack",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "oninactive",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "onremovetrack",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitMediaStream",
      property: "removeTrack",
      objectMissingOnWindow: true,
    },
    {
      className: "WebKitMutationObserver",
      property: "disconnect",
      objectMissingOnWindow: true,
    },
    {
      className: "WebKitMutationObserver",
      property: "observe",
      objectMissingOnWindow: true,
    },
    {
      className: "WebKitMutationObserver",
      property: "takeRecords",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "addIceCandidate",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "addStream",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "addTrack",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "addTransceiver",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "close",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "connectionState",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "createAnswer",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "createDataChannel",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "createDTMFSender",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "createOffer",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "currentLocalDescription",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "currentRemoteDescription",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "generateCertificate",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getConfiguration",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getLocalStreams",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getReceivers",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getRemoteStreams",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getSenders",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getStats",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "getTransceivers",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "iceConnectionState",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "iceGatheringState",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "localDescription",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onaddstream",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onconnectionstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "ondatachannel",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onicecandidate",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "oniceconnectionstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onicegatheringstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onnegotiationneeded",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onremovestream",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "onsignalingstatechange",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "ontrack",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "pendingLocalDescription",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "pendingRemoteDescription",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "remoteDescription",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "removeStream",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "removeTrack",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "sctp",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "setConfiguration",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "setLocalDescription",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "setRemoteDescription",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitRTCPeerConnection",
      property: "signalingState",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechGrammar",
      property: "src",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechGrammar",
      property: "weight",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechGrammarList",
      property: "addFromString",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechGrammarList",
      property: "addFromUri",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechGrammarList",
      property: "item",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechGrammarList",
      property: "length",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "abort",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "continuous",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "grammars",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "interimResults",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "lang",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "maxAlternatives",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onaudioend",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onaudiostart",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onend",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onerror",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onnomatch",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onresult",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onsoundend",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onsoundstart",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onspeechend",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onspeechstart",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "onstart",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "start",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognition",
      property: "stop",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognitionError",
      property: "error",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognitionError",
      property: "message",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognitionEvent",
      property: "emma",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognitionEvent",
      property: "interpretation",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognitionEvent",
      property: "resultIndex",
      objectMissingOnWindow: true,
    },
    {
      className: "webkitSpeechRecognitionEvent",
      property: "results",
      objectMissingOnWindow: true,
    },
    {
      className: "Worklet",
      property: "addModule",
      objectMissingOnWindow: true,
    },
    {
      className: "WritableStream",
      property: "abort",
      objectMissingOnWindow: true,
    },
    {
      className: "WritableStream",
      property: "getWriter",
      objectMissingOnWindow: true,
    },
    {
      className: "WritableStream",
      property: "locked",
      objectMissingOnWindow: true,
    },
  ];
  // Typing this long list here instead of above avoids TS2590
  const $propertiesToInstrumentData: PropertyToInstrumentConfiguration[] = propertiesToInstrumentData;

  const startsWithLowercase = (str: string) => {
    const firstChar = str.charAt(0);
    return firstChar.toLowerCase() === firstChar;
  };

  const instrumentPossiblyNonExistingObject = (
    className,
    propertiesToInstrument,
  ) => {
    // console.debug({ className, propertiesToInstrument });
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

    // To be able to instrument to instrument properties to
    // non-existing classes, we must create a mock class item or instance first
    if (typeof window[className] === "undefined") {
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
        `Instrumenting ${propertiesToInstrument.length} properties on window.${className}.prototype`,
      );
      instrumentObject(window[className].prototype, objectName, {
        propertiesToInstrument,
        logCallStack: true,
        logFunctionGets: true,
      });
    }

    // Instrument the class instance and it's properties
    console.info(
      `Instrumenting ${propertiesToInstrument.length} properties on window.${className}`,
    );
    instrumentObject(window[className], objectName, {
      propertiesToInstrument,
      logCallStack: true,
      logFunctionGets: true,
    });
  };

  const propertiesToInstrumentByClassName: {
    [className: string]: string[];
  } = $propertiesToInstrumentData.reduce((_, propertyToInstrumentData) => {
    if (!_[propertyToInstrumentData.className]) {
      _[propertyToInstrumentData.className] = [];
    }
    _[propertyToInstrumentData.className].push(
      propertyToInstrumentData.property,
    );
    return _;
  }, {});

  console.log(
    "Instrumenting webcompat-related properties",
    propertiesToInstrumentByClassName,
  );

  // Instrument conflicting window-level properties separately
  const windowProperties = propertiesToInstrumentByClassName.Window.concat(
    propertiesToInstrumentByClassName.window
      ? propertiesToInstrumentByClassName.window
      : [],
  );
  delete propertiesToInstrumentByClassName.Window;
  delete propertiesToInstrumentByClassName.window;

  // Instrument non-window-level properties
  for (const className of Object.keys(propertiesToInstrumentByClassName)) {
    const propertiesToInstrument = propertiesToInstrumentByClassName[className];
    instrumentPossiblyNonExistingObject(className, propertiesToInstrument);
  }

  // Instrument window-level properties last
  {
    console.info(
      `Instrumenting ${windowProperties.length} properties on window`,
    );
    instrumentObject(window, `window`, {
      propertiesToInstrument: windowProperties,
      logCallStack: true,
      logFunctionGets: true,
    });
  }
}
