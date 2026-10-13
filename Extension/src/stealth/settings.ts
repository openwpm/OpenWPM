import { StealthJSInstrumentSettings } from "../types/stealth_js_instrument_settings";

export const jsInstrumentationSettings: StealthJSInstrumentSettings = [
  {
    object: "ScriptProcessorNode", // Deprecated. Replaced by AudioWorkletNode
    instrumentedName: "ScriptProcessorNode",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "AudioWorkletNode",
    instrumentedName: "AudioWorkletNode",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "GainNode",
    instrumentedName: "GainNode",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "AnalyserNode",
    instrumentedName: "AnalyserNode",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "OscillatorNode",
    instrumentedName: "OscillatorNode",
    depth: 1,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  // Members shared by every audio node (connect, disconnect, ...) live on
  // AudioNode.prototype and are recorded once under that interface's name.
  {
    object: "AudioNode",
    instrumentedName: "AudioNode",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "OfflineAudioContext",
    instrumentedName: "OfflineAudioContext",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "AudioContext",
    instrumentedName: "AudioContext",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  // Add shared prototype by AudioContext/OfflineAudioContext
  {
    object: "AudioContext",
    instrumentedName: "[AudioContext|OfflineAudioContext]",
    depth: 1,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "RTCPeerConnection",
    instrumentedName: "RTCPeerConnection",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "HTMLCanvasElement",
    instrumentedName: "HTMLCanvasElement",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "Storage",
    instrumentedName: "Storage",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "Navigator",
    instrumentedName: "window.navigator",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      // Called from pagehide, where a wrapper loses the call when the
      // document's process shuts down; http_instrument records beacons.
      excludedProperties: ["sendBeacon"],
      overwrittenProperties: [{ key: "webdriver", value: false }],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "CanvasRenderingContext2D",
    instrumentedName: "CanvasRenderingContext2D",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [
        "transform",
        "globalAlpha",
        "clearRect",
        "closePath",
        "canvas",
        "quadraticCurveTo",
        "lineTo",
        "moveTo",
        "setTransform",
        "drawImage",
        "beginPath",
        "translate",
      ],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "Screen",
    instrumentedName: "window.screen",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [],
      // in OpenWPM is only this one used:
      // {"depth":0, "propertyNames":["colorDepth","pixelDepth"
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  {
    object: "document",
    instrumentedName: "window.document",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [
        { depth: 2, propertyNames: ["cookie", "referrer"] },
      ],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: true,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },

  // These three are own accessors of the window instance (depth 0), not of
  // Window.prototype. Layout properties (innerWidth, ...) are left out: they
  // fire constantly and carry no tracking signal.
  {
    object: "window",
    instrumentedName: "window",
    depth: 0,
    logSettings: {
      propertiesToInstrument: [
        { depth: 0, propertyNames: ["name", "localStorage", "sessionStorage"] },
      ],
      nonExistingPropertiesToInstrument: [],
      excludedProperties: [],
      overwrittenProperties: [],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
    },
  },
];
