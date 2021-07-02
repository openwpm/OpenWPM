import { WebRequestOnBeforeRequestEventDetails } from "../types/browser-web-request-event-details";
import { escapeString, Uint8ToBase64 } from "./string-utils";

export interface ParsedPostRequest {
  post_headers?: any;
  post_body?: any;
  post_body_raw?: string;
}

export class HttpPostParser {
  private readonly onBeforeRequestEventDetails: WebRequestOnBeforeRequestEventDetails;
  private readonly dataReceiver;

  constructor(
    onBeforeRequestEventDetails: WebRequestOnBeforeRequestEventDetails,
    dataReceiver,
  ) {
    this.onBeforeRequestEventDetails = onBeforeRequestEventDetails;
    this.dataReceiver = dataReceiver;
  }

  public parsePostRequest() {
    const requestBody = this.onBeforeRequestEventDetails.requestBody;
    if (requestBody.error) {
      this.dataReceiver.logError(
        "Exception: Upstream failed to parse POST: " + requestBody.error,
      );
    }
    if (requestBody.formData) {
      return {
        post_body: escapeString(JSON.stringify(requestBody.formData)),
      };
    }
    if (requestBody.raw) {
      return {
        post_body_raw: JSON.stringify(
          requestBody.raw.map((x) => [
            x.file,
            Uint8ToBase64(new Uint8Array(x.bytes)),
          ]),
        ),
      };
    }
    return {};
  }
}
