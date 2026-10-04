/**
 * Registers `resource://openwpm/` in whichever process loads this.
 *
 * The actor's `esModuleURI` is a `resource://openwpm/` URL, and a resource:
 * substitution is per-process: setting it in the parent leaves content processes
 * unable to resolve the actor module ("Failed to load ..."). Loaded via
 * `loadProcessScript(..., true)` so processes started later run it during process
 * init, ahead of any document.
 *
 * The extension's root URI is read from `sharedData`, which a process receives
 * at launch, with the pref the parent also sets as the fallback.
 */

"use strict";

(function () {
  const ROOT_PREF = "extensions.openwpm.rootURI";
  const ROOT_KEY = "openwpm-root-uri";

  try {
    // A pref set at runtime in the parent does not reliably reach a content
    // process launched afterwards.
    const shared = Services.cpmm ?? Services.ppmm;
    const root =
      shared?.sharedData?.get(ROOT_KEY) ||
      Services.prefs.getStringPref(ROOT_PREF, "");
    if (root) {
      Services.io
        .getProtocolHandler("resource")
        .QueryInterface(Ci.nsIResProtocolHandler)
        .setSubstitution("openwpm", Services.io.newURI(root));
      // Starts compiling the realm script now, not at the first page.
      ChromeUtils.importESModule(
        "resource://openwpm/privileged/stealthInstrument/OpenWPMStealthChild.sys.mjs",
      );
    }
    if (
      Services.prefs.getBoolPref("extensions.openwpm.stealthVerbose", false)
    ) {
      console.log(
        "OpenWPM: bootstrap ran in pid " +
          Services.appinfo.processID +
          " root=" +
          root,
      );
    }
  } catch (error) {
    console.error("OpenWPM: failed to register resource://openwpm/", error);
  }
})();
