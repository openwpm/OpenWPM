import { WebRequestOnBeforeRequestEventDetails } from "../types/browser-web-reqest-event-details";

export class ResponseBodyListener {
  private responseBody: Promise<string>;
  private resolveResponseBody: (responseBody: string) => void;

  constructor(details: WebRequestOnBeforeRequestEventDetails) {
    this.responseBody = new Promise(resolve => {
      this.resolveResponseBody = resolve;
    });
    console.log("response body request listener", details);

    // Used to parse Response stream
    const filter: any = browser.webRequest.filterResponseData(
      details.requestId,
    ) as any;

    const decoder = new TextDecoder("utf-8");
    // const encoder = new TextEncoder();

    filter.ondata = event => {
      const str = decoder.decode(event.data, { stream: true });
      console.log("blocking request listener ondata: event, str", event, str);
      filter.disconnect();
      this.resolveResponseBody(str);
    };
  }

  public async getResponseBody() {
    return this.responseBody;
  }
}
