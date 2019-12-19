export class HideWebdriver {
  /**
   * Dynamically register the content script to proxy
   * `window.navigator`. The proxy object returns `false`
   * for the `window.navigator.webdriver` attribute.
   */
  public async registerContentScript() {
    return browser.contentScripts.register({
      js: [{ file: "/spoof.js" }],
      matches: ["<all_urls>"],
      allFrames: true,
      runAt: "document_start",
      matchAboutBlank: true,
    });
  }
}
