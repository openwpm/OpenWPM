ChromeUtils.defineModuleGetter(this, "ExtensionCommon",
                               "resource://gre/modules/ExtensionCommon.jsm");
ChromeUtils.defineModuleGetter(this, "OS", "resource://gre/modules/osfile.jsm");
Cu.importGlobalProperties(["TextEncoder", "TextDecoder"]);

this.profileDirIO = class extends ExtensionAPI {
  getAPI(context) {
    return {
      profileDirIO: {
        async writeFile(filename, data) {
          let encoder = new TextEncoder();
          let array = encoder.encode(data);
          let path = OS.Path.join(OS.Constants.Path.profileDir, filename);
          let tmpPath = OS.Path.join(OS.Constants.Path.profileDir, filename + ".tmp");
          try {
            await OS.File.writeAtomic(path, array, {tmpPath});
            console.log(`Wrote to ${path}`);
            return true;
          } catch (e) {
            Cu.reportError(e);
            return false;
          }
        },
        async readFile(filename) {
          let decoder = new TextDecoder();
          let path = OS.Path.join(OS.Constants.Path.profileDir, filename);
          try {
            let array = await OS.File.read(path);
            return decoder.decode(array);
          } catch (e) {
            Cu.reportError(e);
            return "";
          }
        },
      },
    };
  }
};
