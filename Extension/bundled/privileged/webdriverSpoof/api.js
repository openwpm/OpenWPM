"use strict";

const ACTOR_NAME = "OpenWPMWebdriverSpoof";
const RESOURCE_BASE = "resource://openwpm/privileged/webdriverSpoof/";
const BOOTSTRAP_PATH = "privileged/webdriverSpoof/bootstrap.js";
const ROOT_PREF = "extensions.openwpm.rootURI";
let BOOTSTRAP_URL = null;

/**
 * The `resource:` handler, used to map this extension's files to
 * `resource://openwpm/` so the actor module can be loaded by URI.
 *
 * Queried as `nsIResProtocolHandler`, matching Gecko's own callers
 * (`Extension.sys.mjs`, `BackgroundTasksManager.sys.mjs`). Note that
 * `defineLazyServiceGetter` wants an interface object, not its name as a
 * string -- passing a string fails with NS_ERROR_XPC_BAD_CONVERT_JS from inside
 * XPCOMUtils, which names neither the interface nor the real problem.
 */
function resourceProtocol() {
  return Services.io
    .getProtocolHandler("resource")
    .QueryInterface(Ci.nsIResProtocolHandler);
}

/**
 * Registers the window actor that makes `navigator.webdriver` read as `false`.
 *
 * The patch has to run from an actor rather than a content script because
 * content scripts are not injected into a frame's *uncommitted* initial
 * about:blank -- the document that exists between `appendChild` and the real
 * document committing. `ExtensionContent.sys.mjs` skips it deliberately
 * (see `isUncommittedInitialDocument`, and https://bugzilla.mozilla.org/1415539).
 * A parent that appends an iframe and reads `contentWindow.navigator.webdriver`
 * in the same task reads exactly that document, so a content script can never
 * cover the case.
 *
 * `content-document-global-created` fires synchronously in the content process
 * for every window global, uncommitted ones included, which is below the layer
 * that does the skipping.
 */
this.webdriverSpoof = class extends ExtensionAPI {
  getAPI(context) {
    return {
      webdriverSpoof: {
        async enable() {
          // Every step here is required for the spoof to work at all. A crawl
          // that silently lost it would produce plausible-looking data with the
          // automation flag still visible to sites, so fail loudly instead of
          // reporting status nobody reads.
          if (BOOTSTRAP_URL) {
            throw new ExtensionUtils.ExtensionError(
              "webdriverSpoof.enable() called twice",
            );
          }

          // resource: is the only scheme the system ESM loader accepts for an
          // actor module; moz-extension: and the XPI's own jar: URL are both
          // silently declined, with no error and no actor.
          const CHILD_URI =
            RESOURCE_BASE + "OpenWPMWebdriverSpoofChild.sys.mjs";
          const PARENT_URI =
            RESOURCE_BASE + "OpenWPMWebdriverSpoofParent.sys.mjs";

          // The handler does propagate this mapping to content processes
          // (SubstitutingProtocolHandler::SendSubstitution), but it does so
          // over IPC, asynchronously with respect to the actor registration
          // below -- register the actor straight after this and a child can be
          // asked for the module before the mapping arrives, which surfaces as
          // a bare "Failed to load resource://openwpm/...". The bootstrap below
          // makes it ordered by having each content process register the
          // mapping itself before it hosts a document.
          resourceProtocol().setSubstitution(
            "openwpm",
            context.extension.rootURI,
          );
          Services.prefs.setStringPref(
            ROOT_PREF,
            context.extension.rootURI.spec,
          );

          BOOTSTRAP_URL = context.extension.rootURI.resolve(BOOTSTRAP_PATH);
          // Processes created from here on run this during process init,
          // ahead of any document.
          Services.ppmm.loadProcessScript(BOOTSTRAP_URL, true);

          // Processes that already exist do not pick it up, so the
          // preallocated pool has to be replaced rather than patched: toggling
          // the pref tears it down, and it refills with processes that postdate
          // the registration above. Without this a page landing in a stale
          // pooled process is unhooked.
          const PRELAUNCH_PREF = "dom.ipc.processPrelaunch.enabled";
          if (!Services.prefs.getBoolPref(PRELAUNCH_PREF, false)) {
            // Preallocation is off, so the stale pool cannot be replaced and
            // pre-existing content processes stay unhooked. Better to refuse
            // than to crawl with partial coverage.
            throw new ExtensionUtils.ExtensionError(
              `webdriverSpoof requires ${PRELAUNCH_PREF} to be enabled`,
            );
          }
          Services.prefs.setBoolPref(PRELAUNCH_PREF, false);
          Services.prefs.setBoolPref(PRELAUNCH_PREF, true);

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
        },
      },
    };
  }

  onShutdown() {
    ChromeUtils.unregisterWindowActor(ACTOR_NAME);
    if (BOOTSTRAP_URL) {
      Services.ppmm.removeDelayedProcessScript(BOOTSTRAP_URL);
      BOOTSTRAP_URL = null;
    }
    // Leave nothing behind in the profile: the substitution points at an
    // install-specific path, and the pref would otherwise be archived with the
    // profile and outlive the extension.
    try {
      resourceProtocol().setSubstitution("openwpm", null);
    } catch (error) {
      console.error("OpenWPM: failed to clear resource://openwpm/", error);
    }
    Services.prefs.clearUserPref(ROOT_PREF);
  }
};
