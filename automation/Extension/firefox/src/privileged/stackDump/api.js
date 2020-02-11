ChromeUtils.defineModuleGetter(this, "ExtensionCommon",
                               "resource://gre/modules/ExtensionCommon.jsm");
ChromeUtils.defineModuleGetter(this, "Services",
                               "resource://gre/modules/Services.jsm");
const { XPCOMUtils } = ChromeUtils.import(
  "resource://gre/modules/XPCOMUtils.jsm"
);

XPCOMUtils.defineLazyServiceGetter(
  this,
  "resProto",
  "@mozilla.org/network/protocol;1?name=resource",
  "nsISubstitutingProtocolHandler"
);

gOnStackAvailableListeners = new Set();

this.stackDump = class extends ExtensionAPI {
  getAPI(context) {
    Services.obs.addObserver((data) => {
      data = data.wrappedJSObject;
      gOnStackAvailableListeners.forEach((listener) => {
        listener(data.requestId, data.stacktrace);
      });
    }, "openwpm-stacktrace");

    resProto.setSubstitution("openwpm", context.extension.rootURI);
    ChromeUtils.registerWindowActor("OpenWPMStackDump", {
      parent: {
        moduleURI: "resource://openwpm/privileged/stackDump/OpenWPMStackDumpParent.jsm",
      },
      child: {
        moduleURI: "resource://openwpm/privileged/stackDump/OpenWPMStackDumpChild.jsm",
        observers: ["content-document-global-created"],
      },
      allFrames: true,
    });

    return {
      stackDump: {
        onStackAvailable: new ExtensionCommon.EventManager({
          context: context,
          name: "stackDump.onStackAvailable",
          register: (fire) => {
            let listener = (id, data) => {
              fire.async(id, data);
            };
            gOnStackAvailableListeners.add(listener);
            return () => {
              gOnStackAvailableListeners.delete(listener);
            };
          }
        }).api(),
      },
    };
  }
};
