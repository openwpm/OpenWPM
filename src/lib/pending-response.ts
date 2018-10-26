import {
  WebRequestOnBeforeRequestEventDetails,
  WebRequestOnCompletedEventDetails,
} from "../types/browser-web-reqest-event-details";

/**
 * Ties together the two separate events that together holds information about both response headers and body
 */
export class PendingResponse {
  public readonly onBeforeRequestEventDetails: Promise<
    WebRequestOnBeforeRequestEventDetails
  >;
  public readonly onCompletedEventDetails: Promise<
    WebRequestOnCompletedEventDetails
  >;
  public resolveBeforeRequestEventDetails: (
    details: WebRequestOnBeforeRequestEventDetails,
  ) => void;
  public resolveOnCompletedEventDetails: (
    details: WebRequestOnCompletedEventDetails,
  ) => void;
  // private requestBody: Promise<string>;
  constructor() {
    this.onBeforeRequestEventDetails = new Promise(resolve => {
      this.resolveBeforeRequestEventDetails = resolve;
    });
    this.onCompletedEventDetails = new Promise(resolve => {
      this.resolveOnCompletedEventDetails = resolve;
    });
  }
  public resolved() {
    return Promise.all([
      this.onBeforeRequestEventDetails,
      this.onCompletedEventDetails,
    ]);
  }
  public async resolvedWithinTimeout(ms) {
    const resolved = await Promise.race([
      this.resolved(),
      new Promise(resolve => setTimeout(resolve, ms)),
    ]);
    console.log("PendingResponse resolvedWithinTimeout", resolved);
    return resolved;
  }
}
