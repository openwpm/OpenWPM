import { ResponseBodyListener } from "./response-body-listener";

/**
 * Ties together the two separate events that together holds information about both response headers and body
 */
export class PendingResponse {
  public readonly onBeforeRequestEventDetails: Promise<browser.webRequest._OnBeforeRequestDetails>;
  public readonly onCompletedEventDetails: Promise<browser.webRequest._OnCompletedDetails>;
  public responseBodyListener: ResponseBodyListener;
  public resolveOnBeforeRequestEventDetails: (
    details: browser.webRequest._OnBeforeRequestDetails,
  ) => void;
  public resolveOnCompletedEventDetails: (
    details: browser.webRequest._OnCompletedDetails,
  ) => void;
  constructor() {
    this.onBeforeRequestEventDetails = new Promise((resolve) => {
      this.resolveOnBeforeRequestEventDetails = resolve;
    });
    this.onCompletedEventDetails = new Promise((resolve) => {
      this.resolveOnCompletedEventDetails = resolve;
    });
  }
  public addResponseResponseBodyListener(
    details: browser.webRequest._OnBeforeRequestDetails,
  ) {
    this.responseBodyListener = new ResponseBodyListener(details);
  }
  public resolved() {
    return Promise.all([
      this.onBeforeRequestEventDetails,
      this.onCompletedEventDetails,
    ]);
  }

  /**
   * Either returns or times out and returns undefined or
   * returns the results from resolved() above
   *
   * @param ms
   */
  public async resolvedWithinTimeout(ms) {
    const resolved = await Promise.race([
      this.resolved(),
      new Promise((resolve) => setTimeout(resolve, ms)),
    ]);
    return resolved;
  }
}
