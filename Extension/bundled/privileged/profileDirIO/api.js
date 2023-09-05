Cu.importGlobalProperties(["TextEncoder", "TextDecoder"]);

this.profileDirIO = class extends ExtensionAPI {
  getAPI(_context) {
    return {
      profileDirIO: {
        async writeFile(filename, data) {
          const encoder = new TextEncoder();
          const array = encoder.encode(data);
          const path = PathUtils.join(PathUtils.profileDir, filename);
          const tmpPath = PathUtils.join(
            PathUtils.profileDir,
            filename + ".tmp",
          );
          try {
            await IOUtils.write(path, array, { tmpPath });
            console.log(`Wrote to ${path}`);
            return true;
          } catch (e) {
            Cu.reportError(e);
            return false;
          }
        },
        async readFile(filename) {
          const decoder = new TextDecoder();
          const path = PathUtils.join(PathUtils.profileDir, filename);
          try {
            const array = await IOUtils.read(path);
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
