const ExtractTextPlugin = require("extract-text-webpack-plugin");
const autoprefixer = require("autoprefixer");
const path = require("path");
const webpack = require("webpack");

var CleanWebpackPlugin = require("clean-webpack-plugin");

module.exports = [
  {
    entry: {
      main: ["./src/oscar/static/oscar/dashboard/js/main.js"]
    },
    output: {
      path: path.resolve(
        __dirname,
        "src",
        "oscar",
        "static",
        "oscar",
        "dashboard",
        "dist"
      ),
      filename: "[name].js",
      sourceMapFilename: "[file].map"
    },
    devtool: "source-map",
    module: {
      rules: [
        {
          test: /\.(css|scss)$/,
          loader: ExtractTextPlugin.extract({
            fallback: "style-loader",
            use: [
              {
                loader: "css-loader",
                options: {
                  sourceMap: true
                }
              },
              {
                loader: "postcss-loader",
                options: {
                  sourceMap: true,
                  plugins: [autoprefixer]
                }
              },
              {
                loader: "sass-loader?sourceMap"
              }
            ]
          })
        },
        {
          test: /\.(png|jpe?g|gif|svg|eot|woff|woff2|ttf)/,
          loader: "file-loader",
          options: {
            name: "[name].[ext]"
          }
        }
      ]
    },
    resolve: {
      modules: [path.resolve(), "node_modules"]
    },
    plugins: [
      new CleanWebpackPlugin(["dist"], {
        root: path.resolve(
          __dirname,
          "src",
          "oscar",
          "static",
          "oscar",
          "dashboard"
        ),
        verbose: true,
        dry: false
      }),
      new ExtractTextPlugin("[name].css"),
      new webpack.ProvidePlugin({
        $: "jquery",
        jQuery: "jquery"
      })
    ]
  },
];
