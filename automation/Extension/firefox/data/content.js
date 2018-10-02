import * as jsInstrumentContentScope from './javascript-instrument-content-scope.js';

console.log("OpenWPM content script start");

// request current configuration from background script
// before injecting the instrumentation so that we can
// set the testing flag properly
const configListener = function(message) {
  if (message.type === 'config') {
    console.log("Content script received config from background script", JSON.stringify(message.config));
    jsInstrumentContentScope.run(message.config.testing);
    browser.runtime.onMessage.removeListener(configListener);
  }
};
browser.runtime.onMessage.addListener(configListener);

browser.runtime.sendMessage(
  'requestingConfig',
).catch(function(err) {
  console.log("OpenWPM content to background script 'requestingConfig' sendMessage failed");
  // console.error(err);
});
