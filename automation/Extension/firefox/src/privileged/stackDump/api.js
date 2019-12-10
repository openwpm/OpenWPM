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

    Cu.reportError("Hello!!!");
this.stackDump = class extends ExtensionAPI {
  getAPI(context) {
    Cu.reportError("Registering actor!");
    let uri = Services.io.newURI(context.extension.getURL(""));
    resProto.setSubstitution("openwpm", uri);
    ChromeUtils.registerWindowActor("OpenWPM", {
      child: {
        moduleURI: "resource://openwpm/privileged/stackDump/OpenWPMStackDumpChild.jsm",
        events: {
          load: {},
        },
      },
      allFrames: true,
    });
    Cu.reportError("Done!");

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
