const path = require('path');
const webpack = require('webpack');
const ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
  entry: {
    main: './src/oscar/static/oscar/js/main.js'
  },

  output: {
    filename: 'js/bundle.js',
    path: path.join(__dirname, 'src', 'oscar', 'static', 'oscar')
  },

  devtool: 'source-map',

  module: {
    rules: [
      {
        test: /\.scss$/,
        use: ExtractTextPlugin.extract({
          use: [
            { loader: "css-loader" },
            { loader: "sass-loader" }
          ],
          fallback: "style-loader"
        })
      }
    ]
  },

  resolve: {
    modules: [
      'node_modules'
    ]
  },

  plugins: [
    new ExtractTextPlugin('css/dashboard-new.css'),
    new webpack.ProvidePlugin({
      '$': "jquery",
      'jQuery': "jquery",
    }),
  ]
};
