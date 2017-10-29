const path = require('path');
const webpack = require('webpack');
const ExtractTextPlugin = require("extract-text-webpack-plugin");
const CopyWebpackPlugin = require('copy-webpack-plugin');

const staticPath = path.join(__dirname, 'src', 'oscar', 'static', 'oscar');

module.exports = {
  devtool: 'source-map',

  entry: {
    dashboard: './frontend/js/dashboard.js',
    ui: './frontend/js/ui.js'
  },

  output: {
    filename: 'js/[name].js',
    path: staticPath
  },

  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: 'babel-loader'
      },
      {
        test: /\.scss$/,
        use: ExtractTextPlugin.extract({
          use: [
            { loader: "css-loader" },
            { loader: "sass-loader" }
          ],
          fallback: "style-loader",
          publicPath: '../'
        }),
      },
      {
        test: /\.(jpg|png|svg)$/,
        loader: 'file-loader',
        options: {
          name: '[name].[ext]',
          outputPath: 'img/'
        },
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf|svg)$/,
        use: {
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
            outputPath: 'fonts/'
          }
        }
      },
    ]
  },

  resolve: {
    modules: [
      'node_modules'
    ]
  },

  plugins: [
    new ExtractTextPlugin('css/[name].css'),

    new CopyWebpackPlugin([
      { from: './frontend/favicon.ico' },
      { from: './frontend/js/vendor', to: './js/vendor' },
      { from: './frontend/js/old', to: './js/old' },
      { from: './frontend/img', to: './img' }
    ]),

    new webpack.ProvidePlugin({
      '$': "jquery",
      'jQuery': "jquery",
    }),
  ]
};
