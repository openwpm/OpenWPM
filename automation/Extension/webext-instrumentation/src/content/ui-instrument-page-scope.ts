// Code below is not a content script: no Firefox APIs should be used
// Also, no webpack/es6 imports except for type definitions
// may be used in this file since the script
// is exported as a page script as a string

export interface OpenWPMObjectifiedEventTarget {
  xpath: string;
  outerHTMLWithoutInnerHTML: string;
}

export interface OpenWPMUiInteractionData {
  target: OpenWPMObjectifiedEventTarget;
  composedPath: OpenWPMObjectifiedEventTarget[];
  ordinal: number;
}

export interface OpenWPMUiStateData {
  documentHidden: boolean;
  audioElementIsPlaying: boolean;
  videoElementIsPlaying: boolean;
  intervalMs: number;
  ordinal: number;
}

export const pageScript = function({ xpath }) {
  const injection_uuid = document.currentScript.getAttribute(
    "data-injection-uuid",
  );

  // To keep track of the original order of events
  let ordinal = 0;

  // messages the injected script
  function sendMessagesToLogger(messages) {
    document.dispatchEvent(
      new CustomEvent(injection_uuid, {
        detail: messages,
      }),
    );
  }

  const testing =
    document.currentScript.getAttribute("data-testing") === "true";

  if (testing) {
    console.log("OpenWPM: Currently testing");
  }

  /*
   * Start Instrumentation
   */
  const clicksConfigString = document.currentScript.getAttribute("data-clicks");
  const clicks =
    clicksConfigString ||
    clicksConfigString === "true" ||
    clicksConfigString === "1";

  if (clicks) {
    const tag = e =>
      e.outerHTML ? e.outerHTML.replace(e.innerHTML, "") : null;
    const objectifyDOMEventTarget = (
      eventTarget: EventTarget,
    ): OpenWPMObjectifiedEventTarget => {
      return {
        xpath: xpath(eventTarget),
        outerHTMLWithoutInnerHTML: tag(eventTarget),
      };
    };
    const addClickListener = () => {
      if (window.openWpmUiInstrumentClickListenerAdded) {
        return;
      }
      document.body.addEventListener("click", function(event) {
        const content: OpenWPMUiInteractionData = {
          target: objectifyDOMEventTarget(event.target),
          composedPath: event.composedPath().map(objectifyDOMEventTarget),
          ordinal: ordinal++,
        };
        const message = { type: "click", content };
        sendMessagesToLogger([message]);
      });
      window.openWpmUiInstrumentClickListenerAdded = true;
    };
    if (document.body) {
      addClickListener();
    } else {
      window.addEventListener("DOMContentLoaded", addClickListener);
    }
  }

  const stateConfigString = document.currentScript.getAttribute("data-state");
  const state =
    stateConfigString ||
    stateConfigString === "true" ||
    stateConfigString === "1";
  if (state) {
    // Checks specific state properties of the user interface every this amount of milliseconds
    // and attributes this interval to the state at every check.
    // Eg if the page is visible / tab is active at the time of measurement (!document.hidden),
    // it is assumed that it has visible/active the last <interval> milliseconds.
    // This heuristic allows for assessing approximate durations of ui state
    // even across periods of computer sleep and sudden browser terminations
    const stateIntervalMsConfigString = document.currentScript.getAttribute(
      "data-state-interval-ms",
    );
    const intervalMs = stateIntervalMsConfigString
      ? parseInt(stateIntervalMsConfigString, 10)
      : 1000;

    const mediaElementIsPlaying = el => {
      return (
        el && el.currentTime > 0 && !el.paused && !el.ended && el.readyState > 2
      );
    };

    const reportUiState = () => {
      const audioElementIsPlaying = !![
        // @ts-ignore
        ...document.getElementsByTagName("audio"),
      ].find(el => mediaElementIsPlaying(el));
      const videoElementIsPlaying = !![
        // @ts-ignore
        ...document.getElementsByTagName("video"),
      ].find(el => mediaElementIsPlaying(el));
      const content: OpenWPMUiStateData = {
        documentHidden: document.hidden,
        audioElementIsPlaying,
        videoElementIsPlaying,
        intervalMs,
        ordinal: ordinal++,
      };
      const message = { type: "state", content };
      sendMessagesToLogger([message]);
    };

    const setUiStateCheckInterval = () => {
      if (window.openWpmUiInstrumentUiStateCheckIntervalSet) {
        return;
      }
      setInterval(reportUiState, intervalMs);
      window.openWpmUiInstrumentUiStateCheckIntervalSet = true;
    };

    if (document.body) {
      setUiStateCheckInterval();
    } else {
      window.addEventListener("DOMContentLoaded", setUiStateCheckInterval);
    }
  }

  if (testing) {
    console.log(
      "OpenWPM: Content-side ui instrumentation started",
      { clicks, state },
      new Date().toISOString(),
    );
  }
};
