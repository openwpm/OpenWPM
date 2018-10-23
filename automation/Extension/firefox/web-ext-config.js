/* eslint-env node */

const defaultConfig = {
  // Global options:
  sourceDir: "./webextension/",
  artifactsDir: "./",
  ignoreFiles: [".DS_Store"],
  // Command options:
  build: {
    overwriteDest: true,
  },
  run: {
    firefox: process.env.FIREFOX_BINARY || "firefoxdeveloperedition",
    browserConsole: true,
    startUrl: ["about:debugging"],
  },
};

module.exports = defaultConfig;
