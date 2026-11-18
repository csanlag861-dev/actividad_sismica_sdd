module.exports = function (config) {
  config.set({
    basePath: "",
    frameworks: ["jasmine"],
    plugins: [
      require("karma-jasmine"),
      require("karma-chrome-launcher")
    ],
    client: {
      jasmine: {
        random: false
      }
    },
    reporters: ["progress"],
    browsers: ["ChromeHeadless"],
    restartOnFileChange: false
  });
};
