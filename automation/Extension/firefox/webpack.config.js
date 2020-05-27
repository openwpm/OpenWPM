/* global require, module, __dirname */

const path = require("path");

module.exports = {
  entry: {
    feature: "./feature.js/index.js",
    "js-instrument-content-script": "./js-instrument-content-script.js/index.js",
    "ui-instrument-content-script": "./ui-instrument-content-script.js/index.js",
  },
  output: {
    path: path.resolve(__dirname, "src"),
    filename: "[name].js",
    sourceMapFilename: "[name].js.map",
    pathinfo: true,
  },
  resolve: {
    extensions: [".js"],
  },
  mode: "development",
  devtool: "inline-source-map",
};
