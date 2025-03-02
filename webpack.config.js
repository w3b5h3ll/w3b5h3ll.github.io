const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
    mode: 'development', // 或 'production'
    entry: {
        app: "./dev/app.js",
        cv: "./dev/cv.js",
    },
    output: {
        filename: "[name].min.js",
        path: path.resolve(__dirname, "dist"),
    },
    module: {
        rules: [
            {
                test: /\.s[ac]ss$/i,
                use: [
                    MiniCssExtractPlugin.loader,
                    "css-loader",
                    "sass-loader",
                ]
            },
        ],
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: "[name].min.css",
        }),
        new CopyPlugin({
            patterns: [
                { from: "dist/*.min.css", to: "../assets/css/[name][ext]" },
                { from: "dist/*.min.css.map", to: "../assets/css/[name][ext]" },
                { from: "dist/*.min.js", to: "../assets/js/[name][ext]" },
                { from: "dist/*.min.js.map", to: "../assets/js/[name][ext]" },
            ],
            options: {
                concurrency: 100,
            },
        }),
    ],
    devtool: 'source-map',
    watchOptions: {
        ignored: /node_modules/
    },
};
