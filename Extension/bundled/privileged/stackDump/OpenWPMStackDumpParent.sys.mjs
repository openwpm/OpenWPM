// ESM module (.sys.mjs). `Services`, `ChromeUtils`, `Ci`, `ChannelWrapper` and
// `JSWindowActorParent` are ambient globals in system ES modules. The legacy
// Services.jsm / XPCOMUtils.jsm imports were removed in Firefox 136
// (Bug 1881888 https://bugzilla.mozilla.org/show_bug.cgi?id=1881888);
// setTimeout now comes from Timer.sys.mjs directly.
import { setTimeout } from "resource://gre/modules/Timer.sys.mjs";

// ChannelWrapper.get(someChannel).id in the parent process corresponds to
// WebRequest requestId values - which is what we want to propagate to api.js so
// the captured call stack can be joined against http_requests. The child only
// knows the cross-process channelId, so the parent observer resolves
// channelId -> requestId here, at http-on-opening-request, while the channel is
// still alive, and the actor's receiveMessage looks the requestId up by the
// channelId the child sent.
//
// We deliberately resolve and store the *requestId* (a plain number) rather than
// the channel object, and we do NOT delete the entry when the response is
// examined. An earlier design stored the channel and deleted it at
// on-examine-*-response, but receiveMessage runs asynchronously (it awaits a
// timer while waiting for the channel to be recorded), and on a fast connection
// http-on-examine-response fires and deletes the entry within a single poll gap
// -- before the async loop ever observes it. The consumer then spins to its
// deadline and drops every stack, capturing zero rows. Retaining a small,
// bounded history of resolved requestIds removes that record-then-delete race
// entirely; the map is capped FIFO so it stays bounded over a long crawl.
const gRequestIdMap = new Map();
// Upper bound on retained channelId -> requestId entries. The window between
// http-on-opening-request and a stack being consumed is short, so a few thousand
// in-flight entries is far more than enough; the cap only guards against
// unbounded growth if some stacks are never consumed.
const MAX_TRACKED_REQUESTS = 4096;
function recordRequestId(channelId, requestId) {
  // Refresh insertion order so the most recently seen requests are evicted last.
  gRequestIdMap.delete(channelId);
  gRequestIdMap.set(channelId, requestId);
  if (gRequestIdMap.size > MAX_TRACKED_REQUESTS) {
    // Map preserves insertion order, so the first key is the oldest.
    const oldest = gRequestIdMap.keys().next().value;
    gRequestIdMap.delete(oldest);
  }
}

// Upper bound on how long receiveMessage waits for the *-on-opening-request
// observer to resolve a channel's requestId before giving up and dropping the
// stack. The child frequently sends its formatted stack before the parent
// observer fires, so we poll briefly; the deadline only guards the pathological
// case where the requestId never arrives, preventing an unbounded spin that
// leaks the task.
const CHANNEL_WAIT_TIMEOUT_MS = 5000;
// Poll interval while waiting. A small non-zero value caps busy-spinning if the
// requestId is slow to appear.
const CHANNEL_WAIT_POLL_MS = 10;

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
//
// ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/devtools/server/actors/resources/network-events-stacktraces.js#157-170 (the "network-monitor-alternate-stack" case: JSON.parse(data) then walk frame.parent || frame.asyncParent — the loop this mirrors)
// ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/dom/base/SerializedStackHolder.cpp#111-137 (ConvertSerializedStackToJSON: JS::ConvertSavedFrameToPlainObject + StringifyJSON produce the JSON string we parse)
// ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/js/src/vm/SavedStacks.cpp#1132 (ConvertSavedFrameToPlainObject: defines the source/line/column/functionDisplayName/asyncCause/parent/asyncParent field names this walks)
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

// Topics the channel-tracking observer listens to. A request's requestId is
// resolved and recorded at *-on-opening-request; we do not observe the examine
// responses (see gRequestIdMap comment -- deleting there raced the async
// consumer and dropped every stack). `network-monitor-alternate-stack` carries
// the initiator stack for requests whose channel is opened off the JS stack
// (fetch/XHR/WebSocket/worker), for which Components.stack in the content
// process is empty; see #1177.
// ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/devtools/server/actors/resources/network-events-stacktraces.js#41-43 (DevTools registers http-on-opening-request / document-on-opening-request / network-monitor-alternate-stack)
const OBSERVED_TOPICS = [
  "http-on-opening-request",
  "document-on-opening-request",
  "network-monitor-alternate-stack",
];

const observer = {
  QueryInterface: ChromeUtils.generateQI([
    Ci.nsIObserver,
    Ci.nsISupportsWeakReference,
  ]),
  observe(subject, topic, data) {
    let channel;
    switch (topic) {
      case "http-on-opening-request":
      case "document-on-opening-request": {
        let channelId;
        try {
          channel = subject.QueryInterface(Ci.nsIHttpChannel);
          channelId = channel.channelId;
        } catch {
          return;
        }
        // Resolve the WebRequest requestId now, while the channel is alive.
        // ChannelWrapper.get(someChannel).id in the parent process corresponds
        // to WebRequest requestId values, the key the callstacks table joins on.
        let requestId;
        try {
          requestId = ChannelWrapper.get(channel).id;
        } catch {
          return;
        }
        recordRequestId(channelId, requestId);
        break;
      }
      case "network-monitor-alternate-stack": {
        // The notification subject IS the channel (HTTP for fetch/XHR/WebSocket),
        // so we resolve the requestId straight from it instead of going through
        // gRequestIdMap. ChannelWrapper.get(channel).id matches WebRequest's
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
// observer and gRequestIdMap are module-global singletons that live for the
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
// ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/dom/fetch/Fetch.cpp#801,835 (fetch captures the origin stack only when IsWatchedByDevTools())
// ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/dom/xhr/XMLHttpRequestMainThread.cpp#2915 (XHR hands its origin stack to NotifyNetworkMonitorAlternateStack, which emits the topic we observe)
// ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/dom/websocket/WebSocket.cpp#1510 (WebSocket gates origin-stack capture on browsingContext->WatchedByDevTools())
//
// The flag is `[ChromeOnly]`, so page JS cannot read it directly, and it does
// ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/dom/chrome-webidl/BrowsingContext.webidl#84-85,235 ([Exposed=Window, ChromeOnly] interface; [SetterThrows] attribute boolean watchedByDevTools)
// not trip the standard anti-debugging vectors (devtools-detect, console.log
// getter, `debugger` timing). It does have side effects beyond stack capture:
//   - HTML-content reporting (used by view-source/devtools), benign here.
//   - `CanonicalBrowsingContext::SupportsLoadingInParent` returns false when set
//     (docshell/base/CanonicalBrowsingContext.cpp), so the top-level document
//     load is no longer eligible for parent-process initiation and is forced
//     through the content process. This is not page-script-visible, but it does
//     ref: https://searchfox.org/firefox-main/rev/ad704963dac696aa26a7cb39eded9642c10c0ae0/docshell/base/CanonicalBrowsingContext.cpp#2696-2704 (SupportsLoadingInParent returns false when WatchedByDevTools())
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
    // Check if the *-on-opening-request observer has already resolved this
    // channel's requestId, and if not, wait briefly for it. The child can format
    // and send its stack before the parent-process observer fires, so a short
    // wait is expected. Bound it with a deadline: if the requestId never arrives
    // (e.g. the request was canceled before opening, or the observer dropped it),
    // bail rather than spinning forever and leaking this pending task.
    const deadline = Date.now() + CHANNEL_WAIT_TIMEOUT_MS;
    while (!gRequestIdMap.has(channelId)) {
      if (Date.now() >= deadline) {
        // requestId never showed up; drop this stack instead of hanging.
        return;
      }
      // Spin the event loop - this lets us observe new requests while waiting.
      await new Promise((resolve) => setTimeout(resolve, CHANNEL_WAIT_POLL_MS));
    }
    const requestId = gRequestIdMap.get(channelId);
    // Sends message to api.js
    Services.obs.notifyObservers(
      { wrappedJSObject: { requestId, stacktrace } },
      "openwpm-stacktrace",
    );
  }
}
