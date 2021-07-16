# OpenWPM instrumentation library for WebExtensions

Allows WebExtensions to track and monitor privacy-related browsing behavior

## Installation

Add to `package.json`:

```bash
npm install @openwpm/webext-instrumentation
```

Your web extension needs to specify the following permissions in `manifest.json`.

```json
  "permissions": [
    "<all_urls>",
    "webRequest",
    "webRequestBlocking",
    "webNavigation",
    "cookies",
    "tabs"
  ],
```

## Instrumentation

The instrumentation leverages the available [JavaScript APIs for WebExtensions](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API) and listens to navigation, web requests, cookie modifications and access to certain javascript API:s, as described in [the main OpenWPM project README](../../../README.md#instrumentation-and-data-access) under the following bullet points:
- HTTP Request and Response Headers, redirects, and POST request bodies
- Javascript Calls
- Response body content
- Cookie Access (Experimental)

More specifically, all packets sent by the instrumentation conform to [these interfaces](https://github.com/mozilla/OpenWPM/tree/master/Extension/webext-instrumentation/src/schema.ts).

## Usage

The instrumentation is designed to invoke a `dataReceiver` object whenever a packet or log entry is available.

Pending proper documentation, the best way to see how this library is used is to check how the instrumentation is incorporated into the following extensions:

 * https://github.com/mozilla/OpenWPM/tree/master/Extension/firefox
 * https://github.com/mozilla/jestr-pioneer-shield-study

## Npm publishing

### From the master branch

Publishing is done by a core maintainer in the master branch. If there are any impediments to publishing, a PR should be created to address those issues and merged to master before publishing is attempted again.

### Bump the semantic package version

Choose the relevant command below based on the changes since the last version:

```bash
npm run version-patch # X.Y.Z+1
npm run version-minor # X.Y+1.0
npm run version-major # X+1.0.0
```

Note: This will stash any uncommitted changes, validate that the build succeeds, test passes and finally bump the package version in a new commit and add a git tag corresponding to the version number (using [standard-version](https://github.com/conventional-changelog/standard-version#cli-usage)).

### Publish the package

```bash
npm run publish-please
```

Note: This will run various additional validation and ask for explicit approval before actually publishing the package.

### Push the release commit and tag

Just a reminder. :)
