// Code below is not a content script: no Firefox APIs should be used
// Also, no webpack/es6 imports may be used in this file since the script
// is exported as a page script as a string

export const pageScript = function({
  jsInstruments,
  instrumentedApiFuncs, // A list of functions that accept {instrumentObjectProperty, instrumentObject}
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

  const { instrumentObject, instrumentObjectProperty } = jsInstruments(
    event_id,
    sendMessagesToLogger,
  );

  /*
   * Start Instrumentation
   */
  instrumentedApiFuncs.forEach(instrumentedApiFunc =>
    instrumentedApiFunc({
      instrumentObjectProperty,
      instrumentObject,
    }),
  );

  /*
   * Log if testing
   */
  const testing =
    document.currentScript.getAttribute("data-testing") === "true";
  if (testing) {
    console.log("OpenWPM: Currently testing");
    (window as any).instrumentObject = instrumentObject;
    const modules = document.currentScript.getAttribute("data-modules");
    if (modules) {
      console.log(
        "OpenWPM: Content-side javascript instrumentation started",
        modules,
        new Date().toISOString(),
      );
    };
  }
};
