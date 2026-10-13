"use strict";

const { ExtensionParent } = ChromeUtils.importESModule(
  "resource://gre/modules/ExtensionParent.sys.mjs",
);
const { ExtensionUtils } = ChromeUtils.importESModule(
  "resource://gre/modules/ExtensionUtils.sys.mjs",
);
const { WebNavigationFrames } = ChromeUtils.importESModule(
  "resource://gre/modules/WebNavigationFrames.sys.mjs",
);
// `BrowsingContext` and `WindowGlobalParent` are ChromeOnly WebIDL globals of
// the shared system global, which every `.sys.mjs` runs in -- but an
// ExtensionAPI script does not: its sandbox is created with
// `wantGlobalProperties: ["Blob", "URL"]` and nothing else
// (ExtensionParent.sys.mjs). Referencing them here is a ReferenceError, so
// reach them through the system global a system module lives in.
const { BrowsingContext, WindowGlobalParent } =
  Cu.getGlobalForObject(WebNavigationFrames);

const ACTOR_NAME = "OpenWPMStealth";
const RESOURCE_BASE = "resource://openwpm/privileged/stealthInstrument/";
const BOOTSTRAP_PATH = "privileged/stealthInstrument/bootstrap.js";
const ROOT_PREF = "extensions.openwpm.rootURI";
const SETTINGS_KEY = "openwpm-stealth-settings";
const ROOT_KEY = "openwpm-root-uri";
const RECORD_MESSAGE = "openwpm-stealth-record";

let BOOTSTRAP_URL = null;

/**
 * The `resource:` handler, used to map this extension's files to
 * `resource://openwpm/` so the actor module can be loaded by URI. Queried as
 * `nsIResProtocolHandler`, as Extension.sys.mjs `resourceProtocol` does.
 */
function resourceProtocol() {
  return Services.io
    .getProtocolHandler("resource")
    .QueryInterface(Ci.nsIResProtocolHandler);
}

/**
 * Bookkeeping: inner window id -> the process that hosted it and its tab and
 * frame, recorded while the window global is alive. A realm's members outlive
 * its window global (a removed frame, a document navigated away, cross-process
 * included), so later records reuse the entry. Bounded; an evicted entry falls
 * back to `attributeUnknown`.
 */
const attributions = new Map();
const MAX_ATTRIBUTIONS = 20000;

/** The tab id of the tab whose top browsing context is `top`, or 0. */
function tabIdOf(top) {
  const browser = top?.embedderElement;
  const tabData =
    browser &&
    ExtensionParent.apiManager.global.tabTracker.getBrowserData(browser);
  return tabData?.tabId > 0 ? tabData.tabId : 0;
}

/**
 * Attribution of a record whose window global the parent no longer knows: the
 * claimed tab only if the sending process hosts a document in it, else none.
 */
function attributeUnknown(data, senderPid) {
  const top = BrowsingContext.get(data.topBrowsingContextId);
  if (
    !top ||
    top.isDiscarded ||
    !top
      .getAllBrowsingContextsInSubtree()
      .some((each) => each.currentWindowGlobal?.osPid === senderPid)
  ) {
    return { pid: senderPid, tabId: 0, frameId: 0 };
  }
  return {
    pid: senderPid,
    tabId: tabIdOf(top),
    frameId: data.browsingContextId === top.id ? 0 : data.browsingContextId,
  };
}

/**
 * Maps the window global a record was made in to the tab/frame identity the
 * WebExtension collector expects, which the child cannot compute: `tabId` is a
 * parent-process concept, and `frameId` derives from the browsing-context tree
 * the parent owns. Null when the window global belongs to another process than
 * the sender's, which only an instrument bug or a compromised content process
 * produces (page script cannot reach this channel). The browsing context's
 * *current* window global is no evidence either way: a frame navigated
 * cross-site lives in another process while the old document's members keep
 * being called.
 */
function resolveSender(data, senderPid, extension) {
  const sender = { tab: null, frameId: 0, url: data.documentUrl || "" };
  try {
    let attribution = attributions.get(data.innerWindowId);
    if (!attribution) {
      const wgp =
        data.innerWindowId &&
        WindowGlobalParent.getByInnerWindowId(data.innerWindowId);
      if (wgp) {
        if (wgp.osPid !== senderPid) {
          return null;
        }
        const bc = wgp.browsingContext;
        attribution = {
          pid: senderPid,
          tabId: tabIdOf(bc.top),
          frameId: WebNavigationFrames.getFrameId(bc),
        };
        if (attributions.size >= MAX_ATTRIBUTIONS) {
          attributions.delete(attributions.keys().next().value);
        }
        attributions.set(data.innerWindowId, attribution);
      } else {
        attribution = attributeUnknown(data, senderPid);
      }
    }
    if (attribution.pid !== senderPid) {
      return null;
    }
    // `convert()` produces the same `tabs.Tab` shape a real MessageSender
    // carries (id/windowId/url/incognito), which is all the collector reads.
    sender.tab = attribution.tabId
      ? (extension.tabManager.get(attribution.tabId, null)?.convert() ?? null)
      : null;
    sender.frameId = sender.tab ? attribution.frameId : 0;
  } catch (error) {
    console.error("OpenWPM: could not resolve stealth record sender", error);
  }
  return sender;
}

/** Prepares every process for the actor and registers it. */
async function enable(context, settings) {
  const CHILD_URI = RESOURCE_BASE + "OpenWPMStealthChild.sys.mjs";
  const PARENT_URI = RESOURCE_BASE + "OpenWPMStealthParent.sys.mjs";

  // Published before the actor exists, so the first realm already sees
  // it. `sharedData`, not a pref: a pref set at runtime does NOT
  // reliably reach content processes started later (measured -- the
  // root URI pref read back empty in every process launched after
  // startup), whereas sharedData is snapshotted into new processes and
  // is readable synchronously, which is what an observer that fires
  // during document creation needs. It leaves nothing in the page.
  Services.ppmm.sharedData.set(
    SETTINGS_KEY,
    settings ? JSON.stringify(settings) : "",
  );

  // Reaches every content process: live ones now, new ones in their
  // startup snapshot. resource: is the ONLY scheme the system ESM loader
  // accepts for an actor module: moz-extension: and the XPI's own jar: URL
  // are both silently declined. Any failure here rejects, which fails the
  // browser's start rather than letting a crawl run uninstrumented.
  resourceProtocol().setSubstitution("openwpm", context.extension.rootURI);
  Services.ppmm.sharedData.set(ROOT_KEY, context.extension.rootURI.spec);
  // Both channels: sharedData is what a late-launched process can
  // actually read back, the pref is kept as the fallback the
  // bootstrap tries second.
  Services.prefs.setStringPref(ROOT_PREF, context.extension.rootURI.spec);
  Services.ppmm.sharedData.flush();

  // Opens the XPI in each new content process before its sandbox is applied
  // (bootstrap.js). Needs no acknowledgement: a new process runs it during
  // its start, ahead of any document, and a live one receives it over
  // PContent (`ContentChild::RecvLoadProcessScript`) before the actor
  // registration that follows on the same ordered channel (`JSActorService::
  // RegisterWindowActor` -> `SendInitJSActorInfos`). A process alive at
  // install time cannot read the XPI, so cannot load it: the startup
  // about:blank tab's `web` process stays uninstrumented, and no crawled page
  // loads into it.
  BOOTSTRAP_URL = context.extension.rootURI.resolve(BOOTSTRAP_PATH);
  Services.ppmm.loadProcessScript(BOOTSTRAP_URL, true);
  // Preallocated processes were started, and sandboxed, before the install:
  // they receive the bootstrap but cannot load it. Toggling the pref replaces
  // them with processes that run it at launch.
  const PRELAUNCH_PREF = "dom.ipc.processPrelaunch.enabled";
  if (Services.prefs.getBoolPref(PRELAUNCH_PREF, false)) {
    Services.prefs.setBoolPref(PRELAUNCH_PREF, false);
    Services.prefs.setBoolPref(PRELAUNCH_PREF, true);
  }

  ChromeUtils.unregisterWindowActor(ACTOR_NAME);
  ChromeUtils.registerWindowActor(ACTOR_NAME, {
    parent: { esModuleURI: PARENT_URI },
    child: {
      esModuleURI: CHILD_URI,
      // Fires synchronously as each window global is created,
      // including the uncommitted initial about:blank that content
      // scripts skip.
      observers: ["content-document-global-created"],
    },
    allFrames: true,
    // Web content runs in untrusted content processes; without this
    // the actor is never instantiated there.
    safeForUntrustedWebProcess: true,
  });
}

/**
 * Registers the window actor that starts the stealth instrument in every realm.
 *
 * The instrument has to be started from an actor rather than a content script
 * because content scripts are not injected into a frame's *uncommitted* initial
 * about:blank -- the document that exists between `appendChild` and the real
 * document committing. `ExtensionContent.sys.mjs` skips it deliberately (see
 * `isUncommittedInitialDocument`, and https://bugzilla.mozilla.org/1415539). A
 * parent that appends an iframe and reads `contentWindow` in the same task reads
 * exactly that document, so a content script can never cover the case.
 *
 * `content-document-global-created` fires synchronously in the content process
 * for every window global, uncommitted ones included, which is below the layer
 * that does the skipping.
 */
this.stealthInstrument = class extends ExtensionAPI {
  getAPI(context) {
    return {
      stealthInstrument: {
        async enable(settings) {
          try {
            await enable(context, settings);
          } catch (error) {
            // Anything but an ExtensionError reaches the caller as "An
            // unexpected error occurred".
            throw new ExtensionUtils.ExtensionError(String(error));
          }
        },

        onRecord: new ExtensionCommon.EventManager({
          context,
          name: "stealthInstrument.onRecord",
          register: (fire) => {
            const listener = (message) => {
              const data = message.data;
              let payload;
              try {
                payload = JSON.parse(data.payload);
              } catch (error) {
                console.error("OpenWPM: unparseable stealth record", error);
                return;
              }
              const sender = resolveSender(
                data,
                message.target.osPid,
                context.extension,
              );
              if (!sender) {
                console.error(
                  "OpenWPM: dropped a stealth record whose window global is " +
                    "not in the sending process",
                );
                return;
              }
              fire.async({ type: data.type, data: payload, sender });
            };
            Services.ppmm.addMessageListener(RECORD_MESSAGE, listener);
            return () => {
              Services.ppmm.removeMessageListener(RECORD_MESSAGE, listener);
            };
          },
        }).api(),
      },
    };
  }

  onShutdown() {
    ChromeUtils.unregisterWindowActor(ACTOR_NAME);
    if (BOOTSTRAP_URL) {
      Services.ppmm.removeDelayedProcessScript(BOOTSTRAP_URL);
    }
  }
};
