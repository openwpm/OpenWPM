/**
 * Starts the stealth JS instrument in every content realm.
 *
 * `content-document-global-created` fires synchronously as each window global
 * is created, before any script in it, including a frame's uncommitted initial
 * about:blank, which content scripts never run in
 * (`isUncommittedInitialDocument`, https://bugzilla.mozilla.org/1415539).
 *
 * Each realm gets a sandbox with that realm's window as prototype (Xrays,
 * export helpers, `window`), so the instrument's module state is per realm.
 */

const REALM_SCRIPT = "resource://openwpm/privileged/stealthInstrument/realm.js";
const RECORD_MESSAGE = "openwpm-stealth-record";
const SETTINGS_KEY = "openwpm-stealth-settings";
const EXTENSION_ID = "openwpm@mozilla.org";
/**
 * Opt-in per-realm trace (set in `BrowserParams.prefs`). An unresolvable actor
 * module, a filtered realm or a process without the bootstrap logs nothing
 * otherwise.
 */
const VERBOSE_PREF = "extensions.openwpm.stealthVerbose";

/**
 * Window globals already instrumented, keyed by the global's own
 * `Object` constructor: `content-document-global-created` hands over the window
 * proxy, which survives every navigation, and fires again for a same-origin
 * document that reuses the global of the initial about:blank. That document
 * keeps the members already installed, as an uninstrumented Firefox keeps its
 * natives; instrumenting it again would wrap them twice.
 */
const seen = new WeakSet();

/**
 * The realm script, compiled once per process. Until the compile resolves --
 * the bootstrap imports this module as its process starts, so normally before
 * the first page -- a realm compiles its own copy.
 */
let realmScript = null;
ChromeUtils.compileScript(REALM_SCRIPT)
  .then((script) => {
    realmScript = script;
    return script;
  })
  .catch((error) =>
    console.error("OpenWPM: could not compile " + REALM_SCRIPT, error),
  );

export class OpenWPMStealthChild extends JSWindowActorChild {
  observe(subject, topic) {
    if (topic !== "content-document-global-created") {
      return;
    }
    if (verbose()) {
      console.log(
        "OpenWPM: realm observed in pid " +
          Services.appinfo.processID +
          " url=" +
          subject?.document?.documentURI,
      );
    }
    try {
      this.#instrument(subject);
    } catch (error) {
      console.error(
        "OpenWPM: failed to start the stealth instrument",
        error,
        error?.stack,
      );
    }
  }

  #instrument(win) {
    if (!win?.document || !isContentWindow(win)) {
      return;
    }
    if (seen.has(win.Object)) {
      return;
    }
    seen.add(win.Object);

    const browsingContext = win.browsingContext ?? this.browsingContext;
    const realm = {
      win,
      global: win.Object,
      url: "",
      innerWindowId: 0,
      browsingContextId: browsingContext?.id ?? 0,
      topBrowsingContextId: browsingContext?.top?.id ?? 0,
    };
    const sandbox = Cu.Sandbox(sandboxPrincipal(win), {
      sandboxName: "OpenWPM stealth instrument",
      sandboxPrototype: win,
      sameZoneAs: win,
      wantXrays: true,
      wantExportHelpers: true,
      // Exempts the sandbox from the PAGE's CSP, the way a content script is
      // exempt. Without it a page serving `script-src` without 'unsafe-eval'
      // would silently disable the instrument's arity forwarder.
      isWebExtensionContentScript: true,
      originAttributes: win.document.nodePrincipal.originAttributes,
    });

    // The realm script reads these off its global.
    sandbox.openwpmSettings = sharedData().get(SETTINGS_KEY) ?? "";
    const pinner = nativePinner(win);
    sandbox.openwpmPin = pinner.pin;
    sandbox.openwpmIsPinnerError = pinner.isOwnError;
    Cu.exportFunction((value) => Cu.isProxy(value), sandbox, {
      defineAs: "openwpmIsProxy",
    });
    // `Cu.exportFunction`, not a plain assignment: the sandbox is deliberately
    // NOT system (see `sandboxPrincipal`), so a chrome function assigned onto
    // it would be handed back through a security wrapper the sandbox cannot
    // call. Both arguments are strings, so nothing but primitives crosses.
    Cu.exportFunction(
      (type, payload) => {
        try {
          // Over the process message manager, not the actor: the actor dies
          // with its window global, and a page keeps calling members it took
          // from a removed frame. The parent checks the claimed identity
          // against the sending process.
          Services.cpmm.sendAsyncMessage(RECORD_MESSAGE, {
            type,
            payload,
            browsingContextId: realm.browsingContextId,
            topBrowsingContextId: realm.topBrowsingContextId,
            documentUrl: documentUrl(realm),
            innerWindowId: realm.innerWindowId,
          });
        } catch (error) {
          console.error("OpenWPM: could not deliver a stealth record", error);
        }
      },
      sandbox,
      { defineAs: "openwpmSend" },
    );

    if (realmScript) {
      realmScript.executeInGlobal(sandbox);
    } else {
      Services.scriptloader.loadSubScript(REALM_SCRIPT, sandbox);
    }
    // Reads the window global id while it is certainly this realm's.
    documentUrl(realm);
    if (verbose()) {
      console.log("OpenWPM: realm instrumented url=" + documentUrl(realm));
    }
  }
}

/**
 * `Function.prototype.bind.bind(Function.prototype.call)`, owned by a sandbox
 * with the page's own principal: pin(native) is a bound `call` through which
 * the instrument reaches that native.
 *
 * The instrument's sandbox cannot hold the native itself. When a window is
 * destroyed, `WindowDestroyedEvent` cuts every wrapper into it held by a
 * compartment that is not web content -- one whose principal is system or
 * expanded (`BrowserCompartmentMatcher`, `MightBeWebContent()`) -- so every
 * member a page took from a removed, navigated or closed frame would throw. A
 * web-content principal is left alone, the way a page keeps calling another
 * frame's natives. Bound natives add no scripted frame to a stack the page
 * can read. The page's own principal object, not an equal one, keeps the pair
 * same-origin through a `document.domain` change.
 */
function nativePinner(win) {
  const natives = Cu.Sandbox(win.document.nodePrincipal, {
    sandboxName: "OpenWPM stealth natives",
    sameZoneAs: win,
    wantXrays: false,
    wantComponents: false,
  });
  return {
    pin: Cu.evalInSandbox(
      "Function.prototype.bind.bind(Function.prototype.call)",
      natives,
    ),
    // Near the stack limit the bound call itself can throw, in this realm.
    isOwnError: Cu.evalInSandbox(
      "(e) => { try { return e instanceof Error; } catch { return false; } }",
      natives,
    ),
  };
}

/**
 * The principal the instrument runs under: the same expanded principal a
 * content script would get, [extension, page].
 *
 * NOT the system principal. Gecko refuses `eval`/`new Function` under a system
 * principal ("call to Function() blocked by CSP"), and the instrument's arity
 * forwarder -- which is what makes a wrapped function report the native
 * `.length` -- is built with `new Function`. A system-principal sandbox
 * therefore loses instrumentation of every function-valued member. An expanded
 * principal restores exactly the privilege a content script had, which is what
 * the instrument was written against, and keeps the blast radius of running
 * against hostile pages where it already was.
 */
function sandboxPrincipal(win) {
  const contentPrincipal = win.document.nodePrincipal;
  const policy = WebExtensionPolicy.getByID(EXTENSION_ID);
  if (!policy) {
    throw new Error("OpenWPM: extension policy not available in this process");
  }
  const extensionPrincipal =
    Services.scriptSecurityManager.createContentPrincipal(
      Services.io.newURI(`moz-extension://${policy.mozExtensionHostname}/`),
      contentPrincipal.originAttributes,
    );
  // An array makes Cu.Sandbox build an expanded principal.
  return [extensionPrincipal, contentPrincipal];
}

function verbose() {
  return Services.prefs.getBoolPref(VERBOSE_PREF, false);
}

/**
 * The process-local view of the parent's `sharedData` map.
 *
 * `cpmm` in a content process, `ppmm` in the parent (a non-remote document is
 * rare here but not impossible).
 */
function sharedData() {
  return (Services.cpmm ?? Services.ppmm).sharedData;
}

/** Only content is measured; leave privileged and extension documents alone. */
function isContentWindow(win) {
  const principal = win.document?.nodePrincipal;
  if (!principal || principal.isSystemPrincipal || principal.addonPolicy) {
    return false;
  }
  return true;
}

/**
 * The URL of the realm's own document when the record is made; also refreshes
 * the realm's window global id, which the parent authenticates.
 *
 * Read through the window proxy only while the proxy still shows this realm:
 * it shows whatever the frame holds NOW. Once the realm is navigated away
 * from or its window is gone, the last values read stand in.
 */
function documentUrl(realm) {
  try {
    if (realm.win.Object === realm.global) {
      realm.url = realm.win.document?.documentURI ?? realm.url;
      realm.innerWindowId =
        realm.win.windowGlobalChild?.innerWindowId ?? realm.innerWindowId;
    }
  } catch {
    // The window is gone.
  }
  return realm.url;
}
