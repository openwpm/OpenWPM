import { WebRequestOnBeforeRequestEventDetails } from "../types/browser-web-reqest-event-details";

export class ResponseBodyListener {
  public promiseDone;
  private responseBody;
  private deferredDone;

  constructor(details: WebRequestOnBeforeRequestEventDetails) {
    /*
    // array for incoming data.
    // onStopRequest we combine these to get the full source
    this.receivedChunks = [];
    */
    this.responseBody;

    this.deferredDone = {
      promise: null,
      resolve: null,
      reject: null,
    };
    this.deferredDone.promise = new Promise(
      function(resolve, reject) {
        this.resolve = resolve;
        this.reject = reject;
      }.bind(this.deferredDone),
    );
    Object.freeze(this.deferredDone);
    this.promiseDone = this.deferredDone.promise;

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
      this.deferredDone.resolve(str);
    };
  }
}
