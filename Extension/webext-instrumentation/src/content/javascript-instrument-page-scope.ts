/* eslint-disable no-console */
// Code below is not a content script: no Firefox APIs should be used
// Also, no webpack/es6 imports may be used in this file since the script
// is exported as a page script as a string

export function pageScript (getInstrumentJS, jsInstrumentationSettings) {
  // messages the injected script
  const sendMessagesToLogger = (eventId, messages) => {
    document.dispatchEvent(
      new CustomEvent(eventId, {
        detail: messages,
      }),
    );
  };

  const eventId = document.currentScript.getAttribute("data-event-id");
  const testing = document.currentScript.getAttribute("data-testing");
  const instrumentJS = getInstrumentJS(eventId, sendMessagesToLogger);
  let t0: number;
  if (testing === "true") {
    console.log("OpenWPM: Currently testing");
    t0 = performance.now();
    console.log("Begin loading JS instrumentation.");
  }
  instrumentJS(jsInstrumentationSettings);
  if (testing === "true") {
    const t1 = performance.now();
    console.log(`Call to instrumentJS took ${t1 - t0} milliseconds.`);
    (window as any).instrumentJS = instrumentJS;
    console.log(
      "OpenWPM: Content-side javascript instrumentation started with spec:",
      jsInstrumentationSettings,
      new Date().toISOString(),
      "(if spec is '<unavailable>' check web console.)",
    );
  }
};
