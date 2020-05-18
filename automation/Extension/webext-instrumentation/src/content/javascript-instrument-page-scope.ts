// Code below is not a content script: no Firefox APIs should be used
// Also, no webpack/es6 imports may be used in this file since the script
// is exported as a page script as a string

export const pageScript = function({
  getInstrumentJS,
  instrumentionRequests, // Spec to pass to instrumentJS function
}) {

  // messages the injected script
  function sendMessagesToLogger($event_id, messages) {
    document.dispatchEvent(
      new CustomEvent($event_id, {
        detail: messages,
      }),
    );
  }

  const event_id = document.currentScript.getAttribute("data-event-id");
  const instrumentJS = getInstrumentJS(
    event_id,
    sendMessagesToLogger,
  );
  instrumentJS(instrumentionRequests);

  /*
   * Log if testing
   */
  const testing =
    document.currentScript.getAttribute("data-testing") === "true";
  if (testing) {
    console.log("OpenWPM: Currently testing");
    (window as any).instrumentJS = instrumentJS;
    console.log(
      "OpenWPM: Content-side javascript instrumentation started with spec:",
      instrumentionRequests,
      new Date().toISOString(),
    );
  }
};
