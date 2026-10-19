// One observer per content process (not per actor): with allFrames, a
// per-actor observer reports a same-process iframe's request once for every
// ancestor frame.
// ref: https://searchfox.org/firefox-main/rev/66b70484481af2e01d4da8bb33f4a756aba77d74/devtools/server/actors/resources/network-events-stacktraces.js#83-188 (the DevTools watcher this mirrors)

// Live actors in this process; any of them can carry a stack to the parent,
// which only needs the channel key to resolve the requestId.
const gActors = new Set();

// Bounds the per-request cost of deep stacks: each frame read is an XPCOM
// call, and Components.stack itself captures up to 100 frames.
const MAX_FRAMES = 64;

// Keys already reported. Fetch reports the same channel via both
// http-on-opening-request and network-monitor-alternate-stack; the first wins.
const gReported = new Set();
const MAX_REPORTED = 4096;

// Frames are newline-separated `name@file:line:column;asyncCause`. Function
// names are page-controlled, so escape anything a line-based reader could
// split on, and `@` in names so the first `@` always ends the name (URLs
// contain `@`, e.g. unpkg's pkg@version paths). Lone surrogates cannot be
// stored as UTF-8.
const UNSAFE_CHARS =
  // eslint-disable-next-line no-control-regex
  /[\\\u0000-\u001f\u007f-\u009f\u2028\u2029]|[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/g;
const UNSAFE_NAME_CHARS = new RegExp(`${UNSAFE_CHARS.source}|@`, "g");
function escapeField(value, unsafe = UNSAFE_CHARS) {
  return String(value).replace(unsafe, (c) =>
    c === "\\" ? "\\\\" : "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"),
  );
}

function formatFrame(name, filename, line, column, asyncCause) {
  // Firefox's own code (e.g. FaviconLoader) is not a request initiator.
  if (filename.startsWith("resource://") || filename.startsWith("chrome://")) {
    return null;
  }
  return (
    `${escapeField(name, UNSAFE_NAME_CHARS)}@${escapeField(filename)}:` +
    `${line}:${column};${escapeField(asyncCause)}`
  );
}

function currentStack() {
  const frames = [];
  let frame = Components.stack.caller;
  while (frame && frames.length < MAX_FRAMES) {
    const formatted = formatFrame(
      frame.name,
      frame.filename,
      frame.lineNumber,
      frame.columnNumber,
      frame.asyncCause,
    );
    if (formatted) {
      frames.push(formatted);
    }
    frame = frame.caller || frame.asyncCaller;
  }
  return frames;
}

// The alternate stack is a JSON-serialized SavedFrame chain.
// ref: https://searchfox.org/firefox-main/rev/66b70484481af2e01d4da8bb33f4a756aba77d74/dom/base/SerializedStackHolder.cpp#111-150
function alternateStack(data) {
  const frames = [];
  let frame;
  try {
    frame = JSON.parse(data);
  } catch {
    return frames;
  }
  while (frame && frames.length < MAX_FRAMES) {
    const formatted = formatFrame(
      frame.functionDisplayName,
      String(frame.source),
      frame.line,
      frame.column,
      frame.asyncCause ?? null,
    );
    if (formatted) {
      frames.push(formatted);
    }
    frame = frame.parent || frame.asyncParent;
  }
  return frames;
}

// HTTP and document channels share their channelId with the parent-process
// channel; a worker's fetch is announced by a stand-in carrying that id. A
// WebSocket's HTTP channel exists only in the parent, which finds it by the
// WebSocket's serial. The serial is only unique within a content process, so
// it is qualified by the owning window, whose id is unique across processes. A
// dedicated worker's WebSocket has no window id of its own; the worker's window
// is found through its browsing context. Shared and service workers have
// neither and are not attributed. Must match webSocketKey in the parent.
function webSocketKey(wsChannel) {
  const { loadInfo } = wsChannel;
  const windowId =
    loadInfo.innerWindowID ||
    loadInfo.associatedBrowsingContext?.currentWindowContext?.innerWindowId;
  return windowId ? `ws:${windowId}:${wsChannel.serial}` : null;
}

function channelKey(subject) {
  for (const iface of [Ci.nsIIdentChannel, Ci.nsIWorkerChannelInfo]) {
    try {
      return subject.QueryInterface(iface).channelId;
    } catch {
      // Try the next kind of subject.
    }
  }
  try {
    return webSocketKey(subject.QueryInterface(Ci.nsIWebSocketChannel));
  } catch {
    return null;
  }
}

function report(key, frames) {
  if (gReported.has(key)) {
    return;
  }
  for (const actor of gActors) {
    try {
      actor.sendAsyncMessage("OpenWPM:Callstack", {
        key,
        stacktrace: frames.join("\n"),
      });
    } catch {
      gActors.delete(actor);
      continue;
    }
    gReported.add(key);
    if (gReported.size > MAX_REPORTED) {
      gReported.delete(gReported.values().next().value);
    }
    return;
  }
}

const observer = {
  observe(subject, topic, data) {
    if (!gActors.size) {
      return;
    }
    const loadInfo = subject instanceof Ci.nsIChannel ? subject.loadInfo : null;
    if (loadInfo?.triggeringPrincipal?.isSystemPrincipal) {
      return;
    }
    const key = channelKey(subject);
    if (key === null || gReported.has(key)) {
      return;
    }
    const frames =
      topic === "network-monitor-alternate-stack"
        ? alternateStack(data)
        : currentStack();
    if (frames.length) {
      report(key, frames);
    }
  },
};

if (Services.appinfo.processType === Services.appinfo.PROCESS_TYPE_CONTENT) {
  for (const topic of [
    "http-on-opening-request",
    "document-on-opening-request",
    // Carries the initiator stack for requests whose channel is opened without
    // the initiating JS on the stack (worker fetch/XHR, WebSocket). Only fired
    // while the top BrowsingContext is watchedByDevTools, which the parent
    // module sets.
    // ref: https://searchfox.org/firefox-main/rev/66b70484481af2e01d4da8bb33f4a756aba77d74/dom/fetch/Fetch.cpp#812,846
    // ref: https://searchfox.org/firefox-main/rev/66b70484481af2e01d4da8bb33f4a756aba77d74/dom/websocket/WebSocket.cpp#1519,1537
    "network-monitor-alternate-stack",
  ]) {
    Services.obs.addObserver(observer, topic);
  }
}

export class OpenWPMStackDumpChild extends JSWindowActorChild {
  actorCreated() {
    gActors.add(this);
  }
  didDestroy() {
    gActors.delete(this);
  }
  // DOMWindowCreated only serves to instantiate the actor.
  handleEvent() {}
}
