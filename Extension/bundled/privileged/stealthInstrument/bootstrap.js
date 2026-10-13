/**
 * Opens the extension's XPI in each new content process before its sandbox is
 * applied.
 *
 * The extension is installed temporarily, so its XPI is
 * `<profile>/addon-test-<uuid>.xpi`, and the Linux content sandbox lets content
 * processes read only `<profile>/chrome` and `<profile>/extensions`. A delayed
 * process script runs during a new process's startup, before the sandbox, and
 * the zip reader it opens stays usable (memory pressure does not evict it;
 * reloading, disabling or uninstalling the add-on flushes it, and OpenWPM does
 * none of these). Without it, a process first reads the XPI at its first
 * window, after the sandbox, and the actor module fails to load. A process
 * alive at install time cannot read the XPI at all, not even this script.
 *
 * The `setSubstitution` repeats the parent's, which already reaches every
 * process; harmless. The root URI is read from `sharedData`, which a process
 * receives at launch, with the pref the parent also sets as the fallback.
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
      ChromeUtils.importESModule(
        "resource://openwpm/privileged/stealthInstrument/OpenWPMStealthWorkers.sys.mjs",
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
