/**
 * Prototype: starts the stealth instrument in dedicated workers.
 *
 * No content script or observer reaches a worker global. The worker debugger
 * API does: `onRegister` runs on the main thread before the worker's main
 * script is dispatched, and `initialize` queues the debugger script on the
 * debugger queue, which the worker's run loop drains first. The debugger
 * script (worker-debugger.js) evaluates the realm instrument inside the worker
 * global; see there for why it cannot patch the worker from its own realm.
 *
 * Opt-in (`extensions.openwpm.stealthWorkers`, a `BrowserParams.prefs` entry);
 * imported per process by bootstrap.js. Remote worker debugging is off on
 * release (`dom.worker.remoteDebugger.enabled`), so the listener lives in each
 * content process, as DevTools' worker target watcher does.
 */

import { setInterval } from "resource://gre/modules/Timer.sys.mjs";

const DEBUGGER_SCRIPT =
  "resource://openwpm/privileged/stealthInstrument/worker-debugger.js";
// The worker realm cannot reach the debugger global (opaque wrappers), so
// records are pulled. A worker that ends between two pulls loses its last
// records.
const DRAIN_INTERVAL_MS = 100;
const ENABLED_PREF = "extensions.openwpm.stealthWorkers";
const RECORD_MESSAGE = "openwpm-stealth-record";
const VERBOSE_PREF = "extensions.openwpm.stealthVerbose";

// Interfaces exposed to workers; the CanvasRenderingContext2D exclusions of the
// default window surface (settings.ts) apply to its offscreen twin.
const WORKER_SURFACE = [
  { object: "WorkerNavigator", properties: null, excluded: [] },
  {
    object: "OffscreenCanvas",
    properties: ["getContext", "convertToBlob"],
    excluded: [],
  },
  {
    object: "OffscreenCanvasRenderingContext2D",
    properties: null,
    excluded: [
      "transform",
      "globalAlpha",
      "clearRect",
      "closePath",
      "canvas",
      "quadraticCurveTo",
      "lineTo",
      "moveTo",
      "setTransform",
      "drawImage",
      "beginPath",
      "translate",
    ],
  },
];

/** Live instrumented workers: debugger -> owner attribution. */
const live = new Map();

function verbose(message) {
  if (Services.prefs.getBoolPref(VERBOSE_PREF, false)) {
    console.log("OpenWPM workers: " + message);
  }
}

function isContentPrincipal(principal) {
  return Boolean(
    principal && !principal.isSystemPrincipal && !principal.addonPolicy,
  );
}

/** The owner document's identity, read once: the worker dies with it. */
function ownerOf(win) {
  const bc = win.browsingContext;
  return {
    documentUrl: win.document?.documentURI ?? "",
    innerWindowId: win.windowGlobalChild?.innerWindowId ?? 0,
    browsingContextId: bc?.id ?? 0,
    topBrowsingContextId: bc?.top?.id ?? 0,
  };
}

function forward(owner, batch) {
  let records;
  try {
    records = JSON.parse(batch);
  } catch (error) {
    console.error("OpenWPM workers: unparseable batch", error);
    return;
  }
  for (const { type, data } of records) {
    Services.cpmm.sendAsyncMessage(RECORD_MESSAGE, {
      type,
      payload: JSON.stringify(data),
      ...owner,
    });
  }
}

function onRegister(dbg) {
  if (
    dbg.type !== Ci.nsIWorkerDebugger.TYPE_DEDICATED ||
    dbg.isChrome ||
    dbg.isInitialized ||
    !isContentPrincipal(dbg.principal)
  ) {
    return;
  }
  const win = dbg.window;
  if (!win || !isContentPrincipal(win.document?.nodePrincipal)) {
    return;
  }
  const owner = ownerOf(win);
  const listener = {
    onMessage: (batch) => forward(owner, batch),
    onError(filename, lineno, message) {
      console.error(
        `OpenWPM workers: ${message} (${filename}:${lineno}) in ${dbg.url}`,
      );
    },
    onClose() {
      live.delete(dbg);
      dbg.removeListener(listener);
    },
  };
  dbg.addListener(listener);
  // Both land on the debugger queue ahead of the main script.
  dbg.initialize(DEBUGGER_SCRIPT);
  dbg.postMessage(JSON.stringify({ install: WORKER_SURFACE }));
  live.set(dbg, owner);
  verbose(`instrumenting ${dbg.url} for ${owner.documentUrl}`);
}

function drainAll() {
  for (const dbg of live.keys()) {
    if (dbg.isClosed) {
      live.delete(dbg);
      continue;
    }
    try {
      dbg.postMessage('{"drain":true}');
    } catch {
      live.delete(dbg);
    }
  }
}

if (
  Services.appinfo.processType === Services.appinfo.PROCESS_TYPE_CONTENT &&
  Services.prefs.getBoolPref(ENABLED_PREF, false)
) {
  Cc["@mozilla.org/dom/workers/workerdebuggermanager;1"]
    .getService(Ci.nsIWorkerDebuggerManager)
    .addListener({
      onRegister(dbg) {
        try {
          onRegister(dbg);
        } catch (error) {
          console.error("OpenWPM workers: onRegister failed", error);
        }
      },
      onUnregister(dbg) {
        live.delete(dbg);
      },
    });
  setInterval(drainAll, DRAIN_INTERVAL_MS);
  verbose("listener registered in pid " + Services.appinfo.processID);
}
