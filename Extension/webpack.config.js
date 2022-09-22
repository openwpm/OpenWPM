const path = require("path");

module.exports = {
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
