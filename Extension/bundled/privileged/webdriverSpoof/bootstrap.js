/**
 * Registers `resource://openwpm/` in whichever process loads this.
 *
 * The actor's `esModuleURI` is a `resource://openwpm/` URL, and a resource:
 * substitution is per-process: setting it in the parent leaves content
 * processes unable to resolve the actor module ("Failed to load ..."). Loaded
 * via `loadProcessScript(..., true)` so processes started later run it during
 * process init, ahead of any document.
 *
 * The extension's root URI is passed by pref because prefs propagate to content
 * processes on their own, which avoids a message round-trip during startup.
 */

"use strict";

(function () {
  const ROOT_PREF = "extensions.openwpm.rootURI";

  try {
    const root = Services.prefs.getStringPref(ROOT_PREF, "");
    if (root) {
      Services.io
        .getProtocolHandler("resource")
        .QueryInterface(Ci.nsIResProtocolHandler)
        .setSubstitution("openwpm", Services.io.newURI(root));
    }
  } catch (error) {
    console.error("OpenWPM: failed to register resource://openwpm/", error);
  }
})();
