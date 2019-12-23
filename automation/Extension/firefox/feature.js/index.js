import {
  CookieInstrument,
  JavascriptInstrument,
  HttpInstrument,
  NavigationInstrument,
} from "openwpm-webext-instrumentation";

import * as loggingDB from "./loggingdb.js";

async function main() {
  // Read the browser configuration from file
  let filename = "browser_params.json";
  let config = await browser.profileDirIO.readFile(filename);
  if (config) {
    config = JSON.parse(config);
    console.log("Browser Config:", config);
  } else {
    config = {
      navigation_instrument:false,
      cookie_instrument:false,
      js_instrument:false,
      js_instrument_modules:"fingerprinting",
      http_instrument:false,
      save_content:false,
      testing:true,
      crawl_id:0
    };
    console.log("WARNING: config not found. Assuming this is a test run of",
                "the extension. Outputting all queries to console.", {config});
  }

  await loggingDB.open(config['aggregator_address'],
                       config['logger_address'],
                       config['crawl_id']);

  if (config["navigation_instrument"]) {
    loggingDB.logDebug("Navigation instrumentation enabled");
    let navigationInstrument = new NavigationInstrument(loggingDB);
    navigationInstrument.run(config["crawl_id"]);
  }

  if (config['cookie_instrument']) {
    loggingDB.logDebug("Cookie instrumentation enabled");
    let cookieInstrument = new CookieInstrument(loggingDB);
    cookieInstrument.run(config['crawl_id']);
  }

  if (config['js_instrument']) {
    loggingDB.logDebug("Javascript instrumentation enabled");
    let jsInstrument = new JavascriptInstrument(loggingDB);
    jsInstrument.run(config['crawl_id']);
    await jsInstrument.registerContentScript(config['testing'], config['js_instrument_modules']);
  }

  if (config['http_instrument']) {
    loggingDB.logDebug("HTTP Instrumentation enabled");
    let httpInstrument = new HttpInstrument(loggingDB);
    httpInstrument.run(config['crawl_id'],
                       config['save_content']);
  }

  browser.webRequest.onBeforeRequest.addListener((details) => {
    console.log(`req id: ${details.requestId}`);
  }, {urls: ["<all_urls>"]});

  browser.stackDump.onStackAvailable.addListener((requestId, stack) => {
    console.log(requestId, stack);
  });
}

main();

