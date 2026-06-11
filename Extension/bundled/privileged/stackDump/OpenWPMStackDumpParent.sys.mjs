// ESM module (.sys.mjs). `Services`, `ChromeUtils`, `Ci`, `ChannelWrapper` and
// `JSWindowActorParent` are ambient globals in system ES modules. The legacy
// Services.jsm / XPCOMUtils.jsm imports were removed in Firefox 136
// (Bug 1881888); setTimeout now comes from Timer.sys.mjs directly.
import { setTimeout } from "resource://gre/modules/Timer.sys.mjs";

// ChannelWrapper.get(someChannel).id in the parent process corresponds to
// WebRequest requestId values - which is what we want to propagate. This lets
// us associate instrumented requests with the corresponding call stacks.
// We need channels to look up the ChannelWrapper, ids are not sufficient.
// Channels are stored in this map by channel ID, at *-on-opening-request.
// They're cleared at on-examine-*-response when we won't need them anymore.
const gChannelMap = new Map();

// Serializes a request's initiator call stack into the same one-frame-per-line
// `name@file:line:col;asyncCause` format the content-process child emits for
// synchronously script-initiated requests, so both the sync and async paths
// feed identical strings into the callstacks table. Used for the async path
// below, where Firefox hands us a structured stack rather than the child's
// already-formatted string.
function formatStackFrame(name, filename, line, column, asyncCause) {
  // Format described here:
  // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/Stack
  return `${name}@${filename}:${line}:${column};${asyncCause}`;
}

// Deserializes the alternate stack delivered with the
// `network-monitor-alternate-stack` notification. Firefox captures the JS
// initiator stack off the main thread (e.g. when a fetch/XHR channel is opened
// asynchronously) and, in SerializedStackHolder.cpp, converts the SavedFrame
// into a plain object via JS::ConvertSavedFrameToPlainObject and JSON-stringifies
// it into the observer `data` string. That plain object uses SavedFrame field
// names (`source`/`line`/`column`/`functionDisplayName`) and links frames via
// `parent`, with async boundaries linked via `asyncParent`/`asyncCause`. We walk
// that chain and reformat each frame to match the sync path. Mirrors devtools'
// network-events-stacktraces.js handling of the same topic.
function deserializeAlternateStack(data) {
  let frame;
  try {
    frame = JSON.parse(data);
  } catch {
    return null;
  }
  const stacktrace = [];
  while (frame) {
    stacktrace.push(
      formatStackFrame(
        frame.functionDisplayName,
        frame.source,
        frame.line,
        frame.column,
        frame.asyncCause,
      ),
    );
    frame = frame.parent || frame.asyncParent;
  }
  return stacktrace.length ? stacktrace.join("\n") : null;
}

// Topics the channel-tracking observer listens to. A request channel is
// recorded at *-on-opening-request and dropped at on-examine-*-response.
// `network-monitor-alternate-stack` carries the initiator stack for requests
// whose channel is opened off the JS stack (fetch/XHR/WebSocket/worker), for
// which Components.stack in the content process is empty; see #1177.
const OBSERVED_TOPICS = [
  "http-on-opening-request",
  "document-on-opening-request",
  "http-on-examine-response",
  "http-on-examine-cached-response",
  "http-on-examine-merged-response",
  "network-monitor-alternate-stack",
];

const observer = {
  QueryInterface: ChromeUtils.generateQI([
    Ci.nsIObserver,
    Ci.nsISupportsWeakReference,
  ]),
  observe(subject, topic, data) {
    let channel;
    let channelId;
    switch (topic) {
      case "http-on-opening-request":
      case "document-on-opening-request":
        try {
          channel = subject.QueryInterface(Ci.nsIHttpChannel);
          channelId = channel.channelId;
        } catch {
          return;
        }
        gChannelMap.set(channelId, channel);
        break;
      case "http-on-examine-response":
      case "http-on-examine-cached-response":
      case "http-on-examine-merged-response":
        try {
          channel = subject.QueryInterface(Ci.nsIHttpChannel);
          channelId = channel.channelId;
        } catch {
          return;
        }
        gChannelMap.delete(channelId);
        break;
      case "network-monitor-alternate-stack": {
        // The notification subject IS the channel (HTTP for fetch/XHR/WebSocket),
        // so we resolve the requestId straight from it instead of going through
        // gChannelMap. ChannelWrapper.get(channel).id matches WebRequest's
        // requestId, the same key the sync path uses to join the callstacks
        // table to http_requests.
        try {
          channel = subject.QueryInterface(Ci.nsIHttpChannel);
        } catch {
          return;
        }
        const stacktrace = deserializeAlternateStack(data);
        if (!stacktrace) {
          return;
        }
        let requestId;
        try {
          requestId = ChannelWrapper.get(channel).id;
        } catch {
          return;
        }
        Services.obs.notifyObservers(
          { wrappedJSObject: { requestId, stacktrace } },
          "openwpm-stacktrace",
        );
        break;
      }
    }
  },
};

// nsObserverService::AddObserver does NOT dedup; a parent actor is created per
// top-level content window, so registering in the constructor would append the
// same singleton observer to every topic's list once per page, accumulating
// unboundedly over a crawl and dispatching each request O(pages) times. The
// observer and gChannelMap are module-global singletons that live for the
// content-parent process lifetime, so we register the observer exactly once
// when this module is first loaded, guarded against duplicate registration.
let gObserverRegistered = false;
function ensureObserverRegistered() {
  if (gObserverRegistered) {
    return;
  }
  for (const topic of OBSERVED_TOPICS) {
    Services.obs.addObserver(observer, topic, true);
  }
  gObserverRegistered = true;
}
ensureObserverRegistered();

// Async-initiated requests (fetch/XHR/WebSocket/worker) open their channel off
// the JS stack, so Components.stack in the content process is empty and only the
// `network-monitor-alternate-stack` notification carries their initiator stack.
// Firefox only captures and emits that alternate stack when the top-level
// BrowsingContext is flagged `watchedByDevTools` -- the same gecko behavior the
// devtools network monitor relies on (see SerializedStackHolder.cpp callers in
// dom/fetch, dom/xhr, dom/websocket, all gated on WatchedByDevTools). Setting it
// here, on the top BrowsingContext only (the flag is rejected on subframes),
// turns on alternate-stack capture without attaching an actual devtools client.
//
// The flag is `[ChromeOnly]`, so page JS cannot read it directly, and it does
// not trip the standard anti-debugging vectors (devtools-detect, console.log
// getter, `debugger` timing). It does have side effects beyond stack capture:
//   - HTML-content reporting (used by view-source/devtools), benign here.
//   - `CanonicalBrowsingContext::SupportsLoadingInParent` returns false when set
//     (docshell/base/CanonicalBrowsingContext.cpp), so the top-level document
//     load is no longer eligible for parent-process initiation and is forced
//     through the content process. This is not page-script-visible, but it does
//     change the document load path and can perturb navigation timing. Judged
//     benign for measurement, but disclosed here so it is not overlooked.
function ensureAlternateStackCaptureEnabled(browsingContext) {
  const top = browsingContext?.top;
  if (!top || top.watchedByDevTools) {
    return;
  }
  try {
    top.watchedByDevTools = true;
  } catch {
    // Setter throws on non-top contexts or during teardown; capture of
    // sync script-initiated stacks still works regardless.
  }
}

export class OpenWPMStackDumpParent extends JSWindowActorParent {
  actorCreated() {
    ensureAlternateStackCaptureEnabled(this.browsingContext);
  }

  // receiving messages from the child
  async receiveMessage({ data: { channelId, stacktrace } }) {
    // Check if we've already got the channel, and if not, wait.
    while (!gChannelMap.has(channelId)) {
      // Spin the event loop - this lets us observe new channels while waiting here.
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
    // ChannelWrapper.get(someChannel).id in the parent process corresponds to
    // WebRequest requestId values.
    const requestId = ChannelWrapper.get(gChannelMap.get(channelId)).id;
    // Sends message to api.js
    Services.obs.notifyObservers(
      { wrappedJSObject: { requestId, stacktrace } },
      "openwpm-stacktrace",
    );
  }
}
