/**
 * Ambient declarations for Firefox's Xray-vision content-script globals.
 *
 * These functions are injected by the WebExtension content-script sandbox and
 * are not part of `@types/firefox-webext-browser`. The stealth instrument uses
 * `exportFunction` to hand page-world callables across the Xray boundary so the
 * page sees native-looking functions.
 *
 * See https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/Content_scripts#xray_vision_in_firefox
 */

interface ExportFunctionOptions {
  /** Name the exported function is defined as on the target object. */
  defineAs?: string;
  /** Allow the exported function to receive cross-origin arguments. */
  allowCrossOriginArguments?: boolean;
}

/**
 * Export a content-script function into a less-privileged (page) scope so the
 * page can call it. Returns a reference to the exported function.
 */
declare function exportFunction(
  func: (...args: any[]) => any,
  targetScope: any,
  options?: ExportFunctionOptions,
): any;
