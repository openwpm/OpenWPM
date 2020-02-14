import {
  CookieInstrument,
  JavascriptInstrument,
  HttpInstrument,
  NavigationInstrument
} from "openwpm-webext-instrumentation";

import * as loggingDB from "./loggingdb.js";
import { CallstackInstrument } from "./callstack-instrument.js";

async function main() {
  // Read the browser configuration from file
  let filename = "browser_params.json";
  let config = await browser.profileDirIO.readFile(filename);
  if (config) {
    config = JSON.parse(config);
    console.log("Browser Config:", config);
  } else {
    config = {
      navigation_instrument:true,
      cookie_instrument:true,
      js_instrument:true,
      js_instrument_modules:"fingerprinting",
      http_instrument:true,
      callstack_instrument:true,
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

  if (config['callstack_instrument']) {
    loggingDB.logDebug("Callstack Instrumentation enabled");
    let callstackInstrument = new CallstackInstrument(loggingDB);
    callstackInstrument.run(config['crawl_id']);
  }
}

main();

