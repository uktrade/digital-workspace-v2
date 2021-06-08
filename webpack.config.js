const path = require("path");
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  context: __dirname,
  entry: {
    main: ['./assets/js/application.js', './assets/stylesheets/application.scss'],
    peoplefinder: ['./assets/js/peoplefinder.js'],
  },
  output: {
    path: path.resolve('./assets/webpack_bundles/'),
    publicPath: '/static/webpack_bundles/',
    filename: "[name]-[hash].js",
    // Access exports using DW.[entry].[export] format, e.g. `DW.peoplefinder.Cropper`.
    library: ["DW", "[name]"],
  },

  plugins: [
    new BundleTracker({ filename: './webpack-stats.json' }),
    new MiniCssExtractPlugin({
      filename: '[name]-[hash].css',
      chunkFilename: '[id]-[hash].css'
    })
  ],

  module: {
    rules: [
      // Use file-loader to handle image assets
      {
        test: /\.(png|jpe?g|gif|woff2?|svg|ico)$/i,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]',
            }
          }
        ]
      },

      // Extract compiled SCSS separately from JS
      {
        test: /\.(s[ac]ss|css)$/i,
        use: [
          {
            loader: MiniCssExtractPlugin.loader
          },
          'css-loader',
          'sass-loader'
        ]
      }
    ]
  },

  resolve: {
    modules: ['node_modules'],
    extensions: ['.js', '.scss']
  }
}
