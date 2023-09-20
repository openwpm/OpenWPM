/* globals resProto*/
XPCOMUtils.defineLazyServiceGetter(
  this,
  "resProto",
  "@mozilla.org/network/protocol;1?name=resource",
  "nsISubstitutingProtocolHandler",
);

const gOnStackAvailableListeners = new Set();

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
        moduleURI:
          "resource://openwpm/privileged/stackDump/OpenWPMStackDumpParent.jsm",
      },
      child: {
        moduleURI:
          "resource://openwpm/privileged/stackDump/OpenWPMStackDumpChild.jsm",
        observers: ["content-document-global-created"],
      },
      allFrames: true,
    });

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
