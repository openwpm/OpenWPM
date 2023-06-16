import {
  WebRequestOnBeforeRequestEventDetails,
  WebRequestOnBeforeSendHeadersEventDetails,
} from "../types/browser-web-request-event-details";

/**
 * Ties together the two separate events that together holds information about both request headers and body
 */
export class PendingRequest {
  public readonly onBeforeRequestEventDetails: Promise<WebRequestOnBeforeRequestEventDetails>;
  public readonly onBeforeSendHeadersEventDetails: Promise<WebRequestOnBeforeSendHeadersEventDetails>;
  public resolveOnBeforeRequestEventDetails: (
    details: WebRequestOnBeforeRequestEventDetails,
  ) => void;
  public resolveOnBeforeSendHeadersEventDetails: (
    details: WebRequestOnBeforeSendHeadersEventDetails,
  ) => void;
  constructor() {
    this.onBeforeRequestEventDetails = new Promise((resolve) => {
      this.resolveOnBeforeRequestEventDetails = resolve;
    });
    this.onBeforeSendHeadersEventDetails = new Promise((resolve) => {
      this.resolveOnBeforeSendHeadersEventDetails = resolve;
    });
  }
  public resolved() {
    return Promise.all([
      this.onBeforeRequestEventDetails,
      this.onBeforeSendHeadersEventDetails,
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
