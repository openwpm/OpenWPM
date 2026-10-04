import { JSInstrumentSettings } from "../types/js_instrument_settings";

export const jsInstrumentationSettings: JSInstrumentSettings = [
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      overwrittenProperties: [{ key: "webdriver", value: false, level: 0 }],
      logCallStack: false,
      logFunctionsAsStrings: false,
      logFunctionGets: false,
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
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
      preventSets: false,
      recursive: false,
      depth: 5,
    },
  },
];
