import { CookieInstrument, JavascriptInstrument, HttpInstrument, NavigationInstrument } from "openwpm-webext-instrumentation";
import * as loggingDB from './lib/loggingdb.js';
import { ListeningSocket } from './lib/socket.js';

console.log("OpenWPM background script start");

const configPromise = new Promise(function(resolve, reject) {

  // Read the browser configuration over socket, supplied as a `config` event
  const listeningSocket = new ListeningSocket("configuration");
  console.log("Starting socket listening for incoming configuration messages");
  listeningSocket.startListening();
  listeningSocket.socket.on('config', function({ browser_params, manager_params }) {
    console.log('Received config', { browser_params, manager_params });
    const config = {
      ...browser_params,
    };
    config['logger_address'] = manager_params['logger_address'];
    config['sqlite_address'] = manager_params['aggregator_address'];
    config['leveldb_address'] = manager_params['ldb_address'] || null;
    config['testing'] = manager_params['testing'];
    console.log("Browser Config:", config);
    resolve(config);
  });
  listeningSocket.socket.on('connect_error', function(err) {
    listeningSocket.socket.close();
    reject(err);
  });
  listeningSocket.socket.emit('request');

});

const exposeConfig = function(config) {
  browser.runtime.onMessage.addListener(function(message, sender) {
    if (message === 'requestingConfig') {
      sendConfig(sender.tab.id);
    }
  });
  const sendConfig = function(tabId) {
    browser.tabs.sendMessage(
      tabId,
      { type: 'config', config }
    ).catch(function(err) {
      console.log(`OpenWPM background to content script sendMessage to tab ${tabId} failed`);
      console.error(err);
    });
  };
};

const start = function(config) {

  // Allow content-scripts to request the current config via messaging
  exposeConfig(config);

  loggingDB.open(config['sqlite_address'],
                 config['leveldb_address'],
                 config['logger_address'],
                 config['crawl_id']);

  if (config["navigation_instrument"]) {
    loggingDB.logDebug("Navigation instrumentation enabled");
    const navigationInstrument = new NavigationInstrument(loggingDB);
    navigationInstrument.run(config["crawl_id"]);
  }
  if (config['cookie_instrument']) {
    loggingDB.logDebug("Cookie instrumentation enabled");
    const cookieInstrument = new CookieInstrument(loggingDB);
    cookieInstrument.run(config['crawl_id']);
  }
  if (config['js_instrument']) {
    loggingDB.logDebug("Javascript instrumentation enabled");
    const jsInstrument = new JavascriptInstrument(loggingDB);
    jsInstrument.run(config['crawl_id']);
  }
  if (config['http_instrument']) {
    loggingDB.logDebug("HTTP Instrumentation enabled");
    const httpInstrument = new HttpInstrument(loggingDB);
    httpInstrument.run(config['crawl_id'], config['save_javascript'],
                       config['save_all_content']);
  }
};

(async() => {

  let config;
  try {
    config = await configPromise;
  } catch (err) {
    console.log("Error encountered when listening for OpenWPM configuration (sent to console.error here below)");
    console.error(err);

    // Assume test run if the socket server is not launched / available
    console.log("WARNING: config not read. Assuming this is a test run of",
      "the extension. Outputting all queries to console.");
    config = {
      sqlite_address: null,
      leveldb_address: null,
      logger_address: null,
      navigation_instrument: true,
      cookie_instrument: true,
      js_instrument: true,
      http_instrument: true,
      save_javascript: true,
      save_all_content: true,
      testing: true,
      crawl_id: ''
    };

  }
  start(config);

})();
