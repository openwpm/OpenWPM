const path = require("path");

const shared = {
  entry: {
    feature: "./src/feature.ts",
    content: "./src/content.ts",
  },
  output: {
    path: path.resolve(__dirname, "bundled"),
    filename: "[name].js",
    sourceMapFilename: "[name].js.map",
    pathinfo: true,
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: [".ts", "..."],
  },
  mode: "development",
  devtool: "inline-source-map",
};

/**
 * The stealth instrument, bundled for the privileged actor, which runs it as a
 * classic script in a sandbox per window global (`src/stealth/actor.ts`).
 * `globalObject: "globalThis"` keeps the webpack runtime off `self`/`window`,
 * which the sandbox resolves through the page's prototype chain.
 */
const realm = {
  ...shared,
  entry: { realm: "./src/stealth/actor.ts" },
  output: {
    path: path.resolve(__dirname, "bundled/privileged/stealthInstrument"),
    filename: "[name].js",
    globalObject: "globalThis",
    iife: true,
    pathinfo: true,
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: "ts-loader",
        exclude: /node_modules/,
        // Compiled once per content process: no inline source maps.
        options: { compilerOptions: { inlineSourceMap: false } },
      },
    ],
  },
  devtool: false,
};

module.exports = [shared, realm];
