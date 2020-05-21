// Code below is not a content script: no Firefox APIs should be used
// Also, no webpack/es6 imports may be used in this file since the script
// is exported as a page script as a string

export const pageScript = function($getInstrumentJS, $instrumentionRequests) {
  // messages the injected script
  function sendMessagesToLogger($event_id, messages) {
    document.dispatchEvent(
      new CustomEvent($event_id, {
        detail: messages,
      }),
    );
  }

  const event_id = document.currentScript.getAttribute("data-event-id");
  const testing = document.currentScript.getAttribute("data-testing");
  const instrumentJS = $getInstrumentJS(event_id, sendMessagesToLogger);
  let t0: number;
  if (testing === "true") {
    console.log("OpenWPM: Currently testing");
    t0 = performance.now();
    console.log("Begin loading JS instrumentation.");
  }
  instrumentJS($instrumentionRequests);
  if (testing === "true") {
    const t1 = performance.now();
    console.log(`Call to instrumentJS took ${t1 - t0} milliseconds.`);
    (window as any).instrumentJS = instrumentJS;
    console.log(
      "OpenWPM: Content-side javascript instrumentation started with spec:",
      $instrumentionRequests,
      new Date().toISOString(),
      "(if spec is '<unavailable>' check web console.)",
    );
  }
};
