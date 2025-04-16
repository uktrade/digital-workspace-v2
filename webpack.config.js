const path = require("path");
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  mode: 'production',
  context: __dirname,
  entry: {
    init: ['./assets/js/init.js'],
    main: ['./assets/js/application.js', './assets/stylesheets/application.scss'],
    peoplefinder: ['./assets/js/peoplefinder.js'],
  },
  output: {
    path: path.resolve('./assets/webpack_bundles/'),
    publicPath: '/static/webpack_bundles/',
    filename: "[name]-[contenthash].js",
    // Access exports using DW.[entry].[export] format, e.g. `DW.peoplefinder.Cropper`.
    library: ["DW", "[name]"],
  },

  plugins: [
    new BundleTracker({ filename: './webpack-stats.json' }),
    new MiniCssExtractPlugin({
      filename: '[name]-[contenthash].css',
      chunkFilename: '[id]-[contenthash].css'
    })
  ],

  module: {
    rules: [

      // Copy all images and fonts to the output directory ignoring moj assets
      {
        test: /\.(png|jpe?g|gif|woff2?|svg|ico|webp)$/i,
        exclude: /@ministryofjustice\/frontend\/moj\/assets\/.*\.(png|jpe?g|gif|svg)$/i,
        type: 'asset/resource',
        generator: {
          filename: '[name][ext]',
        },
      },

      // Copy MOJ assets into a custom output directory
      {
        test: /@ministryofjustice\/frontend\/moj\/assets\/.*\.(png|jpe?g|gif|svg|webp)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'moj/[name][ext]',
        },
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
