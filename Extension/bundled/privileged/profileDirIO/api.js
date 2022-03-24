ChromeUtils.defineModuleGetter(
  this,
  "ExtensionCommon",
  "resource://gre/modules/ExtensionCommon.jsm",
);
ChromeUtils.defineModuleGetter(this, "OS", "resource://gre/modules/osfile.jsm");
Cu.importGlobalProperties(["TextEncoder", "TextDecoder"]);

this.profileDirIO = class extends ExtensionAPI {
  getAPI(_context) {
    return {
      profileDirIO: {
        async writeFile(filename, data) {
          const encoder = new TextEncoder();
          const array = encoder.encode(data);
          const path = OS.Path.join(OS.Constants.Path.profileDir, filename);
          const tmpPath = OS.Path.join(
            OS.Constants.Path.profileDir,
            filename + ".tmp",
          );
          try {
            await OS.File.writeAtomic(path, array, { tmpPath });
            console.log(`Wrote to ${path}`);
            return true;
          } catch (e) {
            Cu.reportError(e);
            return false;
          }
        },
        async readFile(filename) {
          const decoder = new TextDecoder();
          const path = OS.Path.join(OS.Constants.Path.profileDir, filename);
          try {
            const array = await OS.File.read(path);
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
