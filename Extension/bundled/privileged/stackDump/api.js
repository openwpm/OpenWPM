// The resource:// substituting protocol handler lets us register a
// `resource://openwpm/...` substitution that points at the extension root, so
// the privileged JSWindowActor ES modules can be referenced by a stable URI.
// Historically this was obtained via XPCOMUtils.defineLazyServiceGetter, but in
// Firefox 136+ that lazy getter fails to convert the contract-id argument
// (NS_ERROR_XPC_BAD_CONVERT_JS). Services.io.getProtocolHandler is the modern,
// equivalent idiom.
const resProto = Services.io
  .getProtocolHandler("resource")
  .QueryInterface(Ci.nsISubstitutingProtocolHandler);

const gOnStackAvailableListeners = new Set();

this.stackDump = class extends ExtensionAPI {
  getAPI(context) {
    Services.obs.addObserver((data) => {
      data = data.wrappedJSObject;
      gOnStackAvailableListeners.forEach((listener) => {
        listener(data.requestId, data.stacktrace);
      });
    }, "openwpm-stacktrace");

    // Register a plain resource://openwpm substitution (no ALLOW_CONTENT_ACCESS).
    // The substitution mapping is propagated to content processes regardless of
    // the flag, so the child JSWindowActor ES module can still be resolved and
    // loaded there by the privileged actor machinery. Crucially, WITHOUT
    // ALLOW_CONTENT_ACCESS, nsResProtocolHandler::AllowContentToAccess returns
    // false, so page JavaScript cannot fetch("resource://openwpm/...") to probe
    // for and fingerprint OpenWPM. The content process can read the backing
    // extension files because OpenWPM installs the extension into the Firefox
    // profile's extensions/ directory (see deploy_firefox.py), which the content
    // sandbox broker grants as a read-only tree by default. System ES modules
    // must be loaded from a trusted scheme (resource://), which is why the actor
    // modules are referenced via this substitution rather than a moz-extension://
    // URL.
    try {
      resProto.setSubstitution("openwpm", context.extension.rootURI);
      ChromeUtils.registerWindowActor("OpenWPMStackDump", {
        parent: {
          esModuleURI:
            "resource://openwpm/privileged/stackDump/OpenWPMStackDumpParent.sys.mjs",
        },
        child: {
          esModuleURI:
            "resource://openwpm/privileged/stackDump/OpenWPMStackDumpChild.sys.mjs",
          events: {
            DOMWindowCreated: {},
          },
        },
        allFrames: true,
      });
      // Runtime actor registrations reach content processes via the
      // process-message-manager sharedData map. Flush so already-running and
      // newly-spawned content processes pick up the OpenWPMStackDump child actor;
      // without this the child side is never instantiated.
      Services.ppmm.sharedData.flush();
    } catch (e) {
      // This only catches synchronous failures of the PARENT-side setup above
      // (resource substitution and window-actor registration). It does NOT see
      // the child ES module failing to load in a content process -- that happens
      // asynchronously in another process and never reaches here. A dead child
      // surfaces instead as zero captured call stacks, which CI catches via
      // test_callstack_instrument.py asserting a specific captured stack. We
      // still report+rethrow parent-side failures so a broken registration is
      // loud rather than silently disabling capture.
      Cu.reportError(
        "OpenWPM callstack instrument failed to register the stackDump " +
          "resource substitution / window actor: " +
          e,
      );
      throw e;
    }

    return {
      stackDump: {
        onStackAvailable: new ExtensionCommon.EventManager({
          context,
          name: "stackDump.onStackAvailable",
          register: (fire) => {
            const listener = (id, data) => {
              fire.async(id, data);
            };
            gOnStackAvailableListeners.add(listener);
            return () => {
              gOnStackAvailableListeners.delete(listener);
            };
          },
        }).api(),
      },
    };
  }
};
