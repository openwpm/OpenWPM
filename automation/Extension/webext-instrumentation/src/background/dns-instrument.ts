import { PendingResponse } from "../lib/pending-response";
import { DnsResolved } from "../schema";
import RequestFilter = browser.webRequest.RequestFilter;
import ResourceType = browser.webRequest.ResourceType;
import {
  WebRequestOnCompletedEventDetails,
} from "../types/browser-web-request-event-details";


export class DnsInstrument {
  private readonly dataReceiver;
  private onCompleteListener;
  private pendingResponses: {
    [requestId: number]: PendingResponse;
  } = {};
  
  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }
  
  public run(crawlID){
    // Adopted from http-instrument.ts
    const allTypes: ResourceType[] = [
      "beacon",
      "csp_report",
      "font",
      "image",
      "imageset",
      "main_frame",
      "media",
      "object",
      "object_subrequest",
      "ping",
      "script",
      // "speculative",
      "stylesheet",
      "sub_frame",
      "web_manifest",
      "websocket",
      "xbl",
      "xml_dtd",
      "xmlhttprequest",
      "xslt",
      "other",
    ];
    const filter: RequestFilter = { urls: ["<all_urls>"], types: allTypes };
    
    const requestStemsFromExtension = details => {
        return (
          details.originUrl && 
            details.originUrl.indexOf("moz-extension://") > -1 && 
            details.originUrl.includes("fakeRequest")
        );
    };
    
    /*
     * Attach handlers to event listeners
     */
    this.onCompleteListener = (
      details: WebRequestOnCompletedEventDetails,
    ) => {      
      // Ignore requests made by extensions
      if (requestStemsFromExtension(details)) {
        return;
      }
      const pendingResponse = this.getPendingResponse(details.requestId);
      pendingResponse.resolveOnCompletedEventDetails(details); 
               
      this.onCompleteDnsHandler(
        details,
        crawlID,
      );
    };
    
    browser.webRequest.onCompleted.addListener(
      this.onCompleteListener,
      filter,
    );
  }
    
  public cleanup() {
    if (this.onCompleteListener) {
      browser.webRequest.onCompleted.removeListener(
        this.onCompleteListener,
      );
    }
  }
  
  private getPendingResponse(requestId): PendingResponse {
    if (!this.pendingResponses[requestId]) {
      this.pendingResponses[requestId] = new PendingResponse();
    }
    return this.pendingResponses[requestId];
  }

  private handleResolvedDnsData(dnsRecordObj, dataReceiver) {
    // Curring the data returned by API call.
    return function(record) {
      // Get data from API call
      dnsRecordObj.addresses = record.addresses.toString()
      dnsRecordObj.canonical_name = record.canonicalName 
      dnsRecordObj.is_TRR = record.isTRR

      // Send data to main OpenWPM data aggregator.
      dataReceiver.saveRecord("dns_responses", dnsRecordObj);
    }
  }
  
  private async onCompleteDnsHandler(
    details: WebRequestOnCompletedEventDetails,
    crawlID,
  ) {
      // Create and populate DnsResolve object
      const dnsRecord = {} as DnsResolved;
      dnsRecord.crawl_id = crawlID;
      dnsRecord.request_id =  details.requestId;
      dnsRecord.used_address = details.ip;
      const currentTime = new Date(details.timeStamp);
      dnsRecord.time_stamp = currentTime.toISOString();
      
      // Query DNS API
      const url = new URL(details.url);
      dnsRecord.hostname = url.hostname;
      const dnsResolve = browser.dns.resolve(dnsRecord.hostname, ["canonical_name"]);
      dnsResolve.then(this.handleResolvedDnsData(dnsRecord, this.dataReceiver));
    }
    
}
