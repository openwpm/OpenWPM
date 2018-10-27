import { WebRequestOnBeforeRequestEventDetails } from "../types/browser-web-reqest-event-details";
import { sha256Buffer } from "./sha256";

export class ResponseBodyListener {
  private responseBody: Promise<string>;
  private contentHash: Promise<string>;
  private resolveResponseBody: (responseBody: string) => void;
  private resolveContentHash: (contentHash: string) => void;

  constructor(details: WebRequestOnBeforeRequestEventDetails) {
    this.responseBody = new Promise(resolve => {
      this.resolveResponseBody = resolve;
    });
    this.contentHash = new Promise(resolve => {
      this.resolveContentHash = resolve;
    });
    console.log("response body request listener", details);

    // Used to parse Response stream
    const filter: any = browser.webRequest.filterResponseData(
      details.requestId,
    ) as any;

    const decoder = new TextDecoder("utf-8");
    // const encoder = new TextEncoder();

    filter.ondata = event => {
      sha256Buffer(event.data).then(digest => {
        this.resolveContentHash(digest);
      });
      const str = decoder.decode(event.data, { stream: true });
      console.log("blocking request listener ondata: event, str", event, str);
      filter.disconnect();
      this.resolveResponseBody(str);
    };
  }

  public async getResponseBody() {
    return this.responseBody;
  }

  public async getContentHash() {
    return this.contentHash;
  }
}
