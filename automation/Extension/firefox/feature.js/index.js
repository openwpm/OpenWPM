import {
  CookieInstrument,
  JavascriptInstrument,
  HttpInstrument,
  NavigationInstrument,
} from "openwpm-webext-instrumentation";

import {Logger} from "./logging.js";

let logging = null;

async function main() {

  // Read the browser configuration from file
  let filename = "browser_params.json";
  let config = await browser.profileDirIO.readFile(filename);
  if (config) {
    config = JSON.parse(config);
  } else {
    console.log("WARNING: config not found. Assuming this is a test run of",
                "the extension. Outputting all queries to console.");
    config = {
      navigation_instrument:true,
      cookie_instrument:true,
      js_instrument:true,
      http_instrument:true,
      save_javascript:false,
      save_all_content:false,
      testing:true,
      crawl_id:0,
      visit_id:-99,
      ws_address: ['127.0.0.1', 9999],
    };
  }
  console.log("Browser Config:", config);

  logging = new Logger(
    config['ws_address'],
    config['crawl_id'],
    config['visit_id'],
    config['testing']
  );

  if (config["navigation_instrument"]) {
    logging.logDebug("Navigation instrumentation enabled");
    let navigationInstrument = new NavigationInstrument(logging);
    navigationInstrument.run(config["crawl_id"]);
  }

  if (config['cookie_instrument']) {
    logging.logDebug("Cookie instrumentation enabled");
    let cookieInstrument = new CookieInstrument(logging);
    cookieInstrument.run(config['crawl_id']);
  }

  if (config['js_instrument']) {
    logging.logDebug("Javascript instrumentation enabled");
    let jsInstrument = new JavascriptInstrument(logging);
    jsInstrument.run(config['crawl_id']);
    await jsInstrument.registerContentScript(config['testing']);
  }

  if (config['http_instrument']) {
    logging.logDebug("HTTP Instrumentation enabled");
    let httpInstrument = new HttpInstrument(logging);
    httpInstrument.run(config['crawl_id'],
                       config['save_javascript'],
                       config['save_all_content']);
  }
}

main();
