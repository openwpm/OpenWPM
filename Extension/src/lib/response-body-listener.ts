import { digestMessage } from "./sha256";

export class ResponseBodyListener {
  private readonly responseBody: Promise<Uint8Array>;
  private readonly contentHash: Promise<string>;
  // Assigned synchronously inside the Promise executors in the constructor.
  private resolveResponseBody!: (responseBody: Uint8Array) => void;
  private resolveContentHash!: (contentHash: string) => void;

  constructor(details: browser.webRequest._OnBeforeRequestDetails) {
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
    filter.ondata = (event: { data: ArrayBuffer }) => {
      const incoming = new Uint8Array(event.data);
      void digestMessage(incoming).then(this.resolveContentHash);
      const tmp = new Uint8Array(responseBody.length + incoming.length);
      tmp.set(responseBody);
      tmp.set(incoming, responseBody.length);
      responseBody = tmp;
      filter.write(event.data);
    };

    filter.onstop = (_event: unknown) => {
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
