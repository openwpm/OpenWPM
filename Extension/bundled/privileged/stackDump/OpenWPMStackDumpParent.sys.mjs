// Channel key (see channelKey in the child) -> WebRequest requestId, which is
// what the callstacks table joins on. Resolved at *-on-opening-request while
// the channel is alive. Entries are not deleted at examine-response: the child's
// message can arrive after that, and deleting there dropped every stack on a
// fast connection. Capped FIFO instead.
const gRequestIdMap = new Map();
const MAX_TRACKED_REQUESTS = 4096;
function recordRequestId(key, requestId) {
  gRequestIdMap.delete(key);
  gRequestIdMap.set(key, requestId);
  if (gRequestIdMap.size > MAX_TRACKED_REQUESTS) {
    gRequestIdMap.delete(gRequestIdMap.keys().next().value);
  }
  const pending = gPendingStacks.get(key);
  if (pending) {
    gPendingStacks.delete(key);
    emit(requestId, pending.stacktrace);
  }
}

// Channel key -> stack whose message beat the parent's opening-request
// observer. A WebSocket's request is only opened once the admission manager
// lets it connect (one connecting socket per host, the rest wait up to
// network.websocket.timeout.open each), so there is no useful deadline. Capped
// FIFO; entries for requests that never open expire.
const gPendingStacks = new Map();
const MAX_PENDING_STACKS = 1024;
const PENDING_STACK_MAX_AGE_MS = 10 * 60 * 1000;
function addPendingStack(key, stacktrace) {
  const now = Date.now();
  for (const [oldKey, { added }] of gPendingStacks) {
    if (
      gPendingStacks.size < MAX_PENDING_STACKS &&
      now - added < PENDING_STACK_MAX_AGE_MS
    ) {
      break;
    }
    gPendingStacks.delete(oldKey);
  }
  gPendingStacks.set(key, { stacktrace, added: now });
}

function emit(requestId, stacktrace) {
  Services.obs.notifyObservers(
    { wrappedJSObject: { requestId, stacktrace } },
    "openwpm-stacktrace",
  );
}

// Must match webSocketKey in the child.
function webSocketKey(wsChannel) {
  const { loadInfo } = wsChannel;
  const windowId =
    loadInfo.innerWindowID ||
    loadInfo.associatedBrowsingContext?.currentWindowContext?.innerWindowId;
  return windowId ? `ws:${windowId}:${wsChannel.serial}` : null;
}

const observer = {
  observe(subject, _topic, _data) {
    let channel;
    try {
      channel = subject.QueryInterface(Ci.nsIHttpChannel);
    } catch {
      return;
    }
    let requestId;
    try {
      requestId = ChannelWrapper.get(channel).id;
    } catch {
      return;
    }
    recordRequestId(channel.channelId, requestId);
    // ref: https://searchfox.org/firefox-main/rev/66b70484481af2e01d4da8bb33f4a756aba77d74/devtools/shared/network-observer/NetworkUtils.sys.mjs#415-427
    let wsChannel = null;
    try {
      wsChannel = channel.notificationCallbacks?.QueryInterface(
        Ci.nsIWebSocketChannel,
      );
    } catch {
      // Not a WebSocket handshake.
    }
    const wsKey = wsChannel && webSocketKey(wsChannel);
    if (wsKey) {
      recordRequestId(wsKey, requestId);
    }
  },
};
// Module scope runs once per process; actors are created per window global.
Services.obs.addObserver(observer, "http-on-opening-request");
Services.obs.addObserver(observer, "document-on-opening-request");

// Content processes only emit network-monitor-alternate-stack for top
// BrowsingContexts watched by DevTools. The flag can only be set from the
// parent process while DevTools are reported open (Firefox 158+). That report
// is a per-process counter, so content processes are unaffected. Setting it
// also stops top-level document loads from starting in the parent process
// (SupportsLoadingInParent).
// ref: https://searchfox.org/firefox-main/rev/66b70484481af2e01d4da8bb33f4a756aba77d74/docshell/base/BrowsingContext.cpp#3806-3834
// ref: https://searchfox.org/firefox-main/rev/66b70484481af2e01d4da8bb33f4a756aba77d74/docshell/base/CanonicalBrowsingContext.cpp#2748-2757
ChromeUtils.notifyDevToolsOpened();
function watch(browsingContext) {
  if (
    browsingContext.isContent &&
    !browsingContext.parent &&
    !browsingContext.watchedByDevTools
  ) {
    browsingContext.watchedByDevTools = true;
  }
}
// Fires before the context loads anything, so the flag is set before any page
// script can start a worker or WebSocket.
Services.obs.addObserver(watch, "browsing-context-attached");
for (const window of Services.wm.getEnumerator("navigator:browser")) {
  for (const browser of window.gBrowser?.browsers ?? []) {
    if (browser.browsingContext) {
      watch(browser.browsingContext);
    }
  }
}

export class OpenWPMStackDumpParent extends JSWindowActorParent {
  receiveMessage({ data: { key, stacktrace } }) {
    const requestId = gRequestIdMap.get(key);
    if (requestId === undefined) {
      addPendingStack(key, stacktrace);
    } else {
      emit(requestId, stacktrace);
    }
  }
}
