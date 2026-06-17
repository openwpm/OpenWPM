// Code below is not a content script: no Firefox APIs should be used
// Also, no runtime es6 imports may be used in this file since the script
// is exported as a page script as a string. Type-only imports are erased by
// the compiler and therefore safe.
import type {
  GetInstrumentJS,
  InstrumentMessage,
  JSInstrumentRequest,
} from "../lib/js-instruments";

export function pageScript(
  getInstrumentJS: GetInstrumentJS,
  jsInstrumentationSettings: JSInstrumentRequest[],
) {
  // messages the injected script
  const sendMessagesToLogger = (
    eventId: string,
    messages: InstrumentMessage[],
  ) => {
    document.dispatchEvent(
      new CustomEvent(eventId, {
        detail: messages,
      }),
    );
  };

  const currentScript = document.currentScript as HTMLScriptElement | null;
  const eventId = currentScript?.getAttribute("data-event-id") ?? "";
  const testing = currentScript?.getAttribute("data-testing");
  const instrumentJS = getInstrumentJS(eventId, sendMessagesToLogger);
  let t0 = 0;
  if (testing === "true") {
    console.log("OpenWPM: Currently testing");
    t0 = performance.now();
    console.log("Begin loading JS instrumentation.");
  }
  instrumentJS(jsInstrumentationSettings);
  if (testing === "true") {
    const t1 = performance.now();
    console.log(`Call to instrumentJS took ${t1 - t0} milliseconds.`);
    (window as unknown as { instrumentJS: typeof instrumentJS }).instrumentJS =
      instrumentJS;
    console.log(
      "OpenWPM: Content-side javascript instrumentation started with spec:",
      jsInstrumentationSettings,
      new Date().toISOString(),
      "(if spec is '<unavailable>' check web console.)",
    );
  }
}
