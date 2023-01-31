# OpenWPM Client Extension

Used by the OpenWPM platform.
This extension implements the OpenWPM instrumentation as a WebExtension.
It allows users to track and monitor privacy-related browsing behavior.

## Installation

```bash
npm ci
```

## Instrumentation

The instrumentation leverages the available [JavaScript APIs for WebExtensions](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API) and listens to navigation, web requests, cookie modifications and access to certain javascript API:s, as described in [the main OpenWPM project README](../../README.md#instrumentation-and-data-access) under the following bullet points:

- HTTP Request and Response Headers, redirects, and POST request bodies
- Javascript Calls
- Response body content
- Cookie Access (Experimental)

More specifically, all packets sent by the instrumentation conform to [these interfaces](/src/schema.ts).
