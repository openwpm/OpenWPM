import { WebRequestOnBeforeRequestEventDetails } from "../types/browser-web-request-event-details";
import { digestMessage } from "./sha256";

export class ResponseBodyListener {
  private readonly responseBody: Promise<Uint8Array>;
  private readonly contentHash: Promise<string>;
  private resolveResponseBody: (responseBody: Uint8Array) => void;
  private resolveContentHash: (contentHash: string) => void;

  constructor(details: WebRequestOnBeforeRequestEventDetails) {
    this.responseBody = new Promise((resolve) => {
      this.resolveResponseBody = resolve;
    });
    this.contentHash = new Promise((resolve) => {
      this.resolveContentHash = resolve;
    });

    // Used to parse Response stream
    const filter: any = browser.webRequest.filterResponseData(
      details.requestId.toString(),
    ) as any;

    let responseBody = new Uint8Array();
    filter.ondata = (event) => {
      digestMessage(event.data).then((digest) => {
        this.resolveContentHash(digest);
      });
      const incoming = new Uint8Array(event.data);
      const tmp = new Uint8Array(responseBody.length + incoming.length);
      tmp.set(responseBody);
      tmp.set(incoming, responseBody.length);
      responseBody = tmp;
      filter.write(event.data);
    };

    filter.onstop = (_event) => {
      this.resolveResponseBody(responseBody);
      filter.disconnect();
    };
  }

  public async getResponseBody() {
    return this.responseBody;
  }

  public async getContentHash() {
    return this.contentHash;
  }
}
