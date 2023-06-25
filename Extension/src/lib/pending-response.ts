import {
  WebRequestOnBeforeRequestEventDetails,
  WebRequestOnCompletedEventDetails,
} from "../types/browser-web-request-event-details";
import { ResponseBodyListener } from "./response-body-listener";

/**
 * Ties together the two separate events that together holds information about both response headers and body
 */
export class PendingResponse {
  public readonly onBeforeRequestEventDetails: Promise<WebRequestOnBeforeRequestEventDetails>;
  public readonly onCompletedEventDetails: Promise<WebRequestOnCompletedEventDetails>;
  public responseBodyListener: ResponseBodyListener;
  public resolveOnBeforeRequestEventDetails: (
    details: WebRequestOnBeforeRequestEventDetails,
  ) => void;
  public resolveOnCompletedEventDetails: (
    details: WebRequestOnCompletedEventDetails,
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
    details: WebRequestOnBeforeRequestEventDetails,
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
