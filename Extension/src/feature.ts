/* eslint no-eval: "off" */
import { CookieInstrument } from "./background/cookie-instrument";
import { DnsInstrument } from "./background/dns-instrument";
import { HttpInstrument } from "./background/http-instrument";
import { JavascriptInstrument } from "./background/javascript-instrument";
import { NavigationInstrument } from "./background/navigation-instrument";

import * as loggingDB from "./loggingdb";
import { CallstackInstrument } from "./callstack-instrument";

async function main() {
  // Read the browser configuration from file
  const filename = "browser_params.json";
  let config = await (browser as any).profileDirIO.readFile(filename);
  if (config) {
    config = JSON.parse(config);
    console.log("Browser Config:", config);
  } else {
    config = {
      navigation_instrument: true,
      cookie_instrument: true,
      js_instrument: true,
      cleaned_js_instrument_settings: [
        {
          object: `window.CanvasRenderingContext2D.prototype`,
          instrumentedName: "CanvasRenderingContext2D",
          logSettings: {
            propertiesToInstrument: [],
            nonExistingPropertiesToInstrument: [],
            excludedProperties: [],
            logCallStack: false,
            logFunctionsAsStrings: false,
            logFunctionGets: false,
            preventSets: false,
            recursive: false,
            depth: 5,
          },
        },
      ],
      http_instrument: true,
      callstack_instrument: true,
      save_content: false,
      testing: true,
      browser_id: 0,
      custom_params: {},
    };
    console.log(
      "WARNING: config not found. Assuming this is a test run of",
      "the extension. Outputting all queries to console.",
      { config },
    );
  }

  await loggingDB.open(
    config.storage_controller_address,
    config.logger_address,
    config.browser_id,
  );

  if (config.custom_params.pre_instrumentation_code) {
    eval(config.custom_params.pre_instrumentation_code);
  }
  if (config.navigation_instrument) {
    loggingDB.logDebug("Navigation instrumentation enabled");
    const navigationInstrument = new NavigationInstrument(loggingDB);
    navigationInstrument.run(config.browser_id);
  }

  if (config.cookie_instrument) {
    loggingDB.logDebug("Cookie instrumentation enabled");
    const cookieInstrument = new CookieInstrument(loggingDB);
    cookieInstrument.run(config.browser_id);
  }

  if (config.js_instrument) {
    loggingDB.logDebug("Javascript instrumentation enabled");
    const jsInstrument = new JavascriptInstrument(loggingDB);
    jsInstrument.run(config.browser_id);
    await jsInstrument.registerContentScript(
      config.testing,
      config.cleaned_js_instrument_settings,
    );
  }

  if (config.http_instrument) {
    loggingDB.logDebug("HTTP Instrumentation enabled");
    const httpInstrument = new HttpInstrument(loggingDB);
    httpInstrument.run(config.browser_id, config.save_content);
  }

  if (config.callstack_instrument) {
    loggingDB.logDebug("Callstack Instrumentation enabled");
    const callstackInstrument = new CallstackInstrument(loggingDB);
    callstackInstrument.run(config.browser_id);
  }

  if (config.dns_instrument) {
    loggingDB.logDebug("DNS instrumentation enabled");
    const dnsInstrument = new DnsInstrument(loggingDB);
    dnsInstrument.run(config.browser_id);
  }

  await (browser as any).profileDirIO.writeFile(
    "OPENWPM_STARTUP_SUCCESS.txt",
    "",
  );
}

main();
