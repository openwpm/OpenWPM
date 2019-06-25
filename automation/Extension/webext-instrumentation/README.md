# OpenWPM instrumentation library for WebExtensions

Allows WebExtensions to track and monitor privacy-related browsing behavior

## Installation

This package is yet to be published to npm.

## Instrumentation

The instrumentation leverages the available [JavaScript APIs for WebExtensions](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API) and listens to navigation, web requests, cookie modifications and access to certain javascript API:s, as described in [the main OpenWPM project README](https://github.com/citp/OpenWPM/tree/develop#instrumentation-and-data-access) under the following bullet points:
 - HTTP Request and Response Headers, redirects, and POST request bodies
 - Javascript Calls
 - Response body content
 - Cookie Access (Experimental)

More specifically, all packets sent by the instrumentation conform to [these interfaces](https://github.com/mozilla/openwpm-webext-instrumentation/blob/refactor-legacy-sdk-code-to-webext-equivalent/src/schema.ts).

## Usage

The instrumentation is designed to invoke a `dataReceiver` object whenever a packet or log entry is available.

Pending proper documentation, the best way to see how this library is used is to check how the instrumentation is incorporated into the following extensions:

 * https://github.com/mozilla/OpenWPM/tree/master/automation/Extension/firefox
 * https://github.com/motin/jestr-pioneer-shield-study
