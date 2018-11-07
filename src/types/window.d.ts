export {}; // this file needs to be a module
declare global {
  interface Window {
    Storage: any;
    HTMLCanvasElement: any;
    CanvasRenderingContext2D: any;
    RTCPeerConnection: any;
    AudioContext: any;
    OfflineAudioContext: any;
    OscillatorNode: any;
    AnalyserNode: any;
    GainNode: any;
    ScriptProcessorNode: any;
  }
}
