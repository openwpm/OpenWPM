import { DnsResolved } from "../schema";
import { allTypes } from "./http-instrument";
import {
  WebRequestOnErrorOccurredDetails,
  WebRequestOnHeadersReceivedDetails,
} from "../types/browser-web-request-event-details";
import RequestFilter = browser.webRequest.RequestFilter;

// Firefox error strings that indicate DNS resolution failure
const DNS_ERROR_STRINGS = [
  "NS_ERROR_UNKNOWN_HOST",
  "NS_ERROR_DNS_RESOLVE_UNKNOWN_HOST",
  "NS_ERROR_NET_TIMEOUT",
];

export class DnsInstrument {
  private readonly dataReceiver;
  private onHeadersReceivedListener;
  private onErrorOccurredListener;

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
    this.onHeadersReceivedListener = (
      details: WebRequestOnHeadersReceivedDetails,
    ) => {
      // Ignore requests made by extensions
      if (requestStemsFromExtension(details)) {
        return;
      }

      this.onHeadersReceivedDnsHandler(details, crawlID);
    };

    browser.webRequest.onHeadersReceived.addListener(
      this.onHeadersReceivedListener,
      filter,
    );

    this.onErrorOccurredListener = (
      details: WebRequestOnErrorOccurredDetails,
    ) => {
      // Ignore requests made by extensions
      if (requestStemsFromExtension(details)) {
        return;
      }

      // Only capture DNS-related errors
      const isDnsError = DNS_ERROR_STRINGS.some((errStr) =>
        details.error.includes(errStr),
      );
      if (!isDnsError) {
        return;
      }

      this.onErrorOccurredDnsHandler(details, crawlID);
    };

    browser.webRequest.onErrorOccurred.addListener(
      this.onErrorOccurredListener,
      filter,
    );
  }

  public cleanup() {
    if (this.onHeadersReceivedListener) {
      browser.webRequest.onHeadersReceived.removeListener(
        this.onHeadersReceivedListener,
      );
    }
    if (this.onErrorOccurredListener) {
      browser.webRequest.onErrorOccurred.removeListener(
        this.onErrorOccurredListener,
      );
    }
  }

  private async onHeadersReceivedDnsHandler(
    details: WebRequestOnHeadersReceivedDetails,
    crawlID,
  ) {
    // Create and populate DnsResolve object
    const dnsRecord = {} as DnsResolved;
    dnsRecord.browser_id = crawlID;
    dnsRecord.request_id = Number(details.requestId);
    dnsRecord.used_address = details.ip;
    dnsRecord.redirect_url = details.url;
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

  private onErrorOccurredDnsHandler(
    details: WebRequestOnErrorOccurredDetails,
    crawlID,
  ) {
    const dnsRecord = {} as DnsResolved;
    dnsRecord.browser_id = crawlID;
    dnsRecord.request_id = Number(details.requestId);
    dnsRecord.redirect_url = details.url;
    const currentTime = new Date(details.timeStamp);
    dnsRecord.time_stamp = currentTime.toISOString();

    const url = new URL(details.url);
    dnsRecord.hostname = url.hostname;
    dnsRecord.error = details.error;

    this.dataReceiver.saveRecord("dns_responses", dnsRecord);
  }
}
