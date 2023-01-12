import { PendingResponse } from "../lib/pending-response";
import { DnsResolved } from "../schema";
import { allTypes } from "./http-instrument";
import RequestFilter = browser.webRequest.RequestFilter;
import { WebRequestOnHeadersReceivedDetails } from "../types/browser-web-request-event-details";

export class DnsInstrument {
  private readonly dataReceiver;
  private onHeadersReceivedListener;
  private pendingResponses: {
    [requestId: number]: PendingResponse;
  } = {};

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID) {
    const filter: RequestFilter = { urls: ["<all_urls>"], types: allTypes };

    const requestStemsFromExtension = (details) => {
      return (
        details.originUrl &&
        details.originUrl.includes("moz-extension://") &&
        details.originUrl.includes("fakeRequest")
      );
    };

    /*
     * Attach handlers to event listeners
     */
    this.onHeadersReceivedListener = (details: browser.webRequest._OnHeadersReceivedDetails) => {
      // Ignore requests made by extensions
      if (requestStemsFromExtension(details)) {
        return;
      }
      const pendingResponse = this.getPendingResponse(details.requestId);
      pendingResponse.resolveOnHeadersReceivedDetails(details);

      this.onCompleteDnsHandler(details, crawlID);
    };

    browser.webRequest.onHeadersReceived.addListener(this.onHeadersReceivedListener, filter);
  }

  public cleanup() {
    if (this.onHeadersReceivedListener) {
      browser.webRequest.onHeadersReceived.removeListener(this.onHeadersReceivedListener);
    }
  }

  private getPendingResponse(requestId): PendingResponse {
    if (!this.pendingResponses[requestId]) {
      this.pendingResponses[requestId] = new PendingResponse();
    }
    return this.pendingResponses[requestId];
  }

  private async onCompleteDnsHandler(
    details: WebRequestOnHeadersReceivedDetails,
    crawlID,
  ) {
    // Create and populate DnsResolve object
    const dnsRecord = {} as DnsResolved;
    dnsRecord.browser_id = crawlID;
    dnsRecord.request_id = Number(details.requestId);
    dnsRecord.used_address = details.ip;
    const currentTime = new Date(details.timeStamp);
    dnsRecord.time_stamp = currentTime.toISOString();

    // Query DNS API
    const url = new URL(details.url);
    dnsRecord.hostname = url.hostname;
    const record = await browser.dns.resolve(dnsRecord.hostname, [
      "canonical_name",
    ]);

    dnsRecord.addresses = record.addresses.toString();
    dnsRecord.canonical_name = record.canonicalName;
    dnsRecord.is_TRR = record.isTRR;
    this.dataReceiver.saveRecord("dns_responses", dnsRecord);
  }
}
