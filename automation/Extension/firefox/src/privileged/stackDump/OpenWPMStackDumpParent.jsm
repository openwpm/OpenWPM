"use strict";

var EXPORTED_SYMBOLS = ["OpenWPMStackDumpParent"];

const { Services } = ChromeUtils.import("resource://gre/modules/Services.jsm");
const { XPCOMUtils } = ChromeUtils.import(
  "resource://gre/modules/XPCOMUtils.jsm"
);

XPCOMUtils.defineLazyModuleGetters(this, {
  setTimeout: "resource://gre/modules/Timer.jsm",
});

let gChannelMap = new Map();

let observer = {
  QueryInterface: ChromeUtils.generateQI([
    Ci.nsIObserver,
    Ci.nsISupportsWeakReference,
  ]),
  observe(subject, topic, data) {
    let channel, channelId;
    switch (topic) {
    case "http-on-opening-request":
    case "document-on-opening-request":
      try {
        channel = subject.QueryInterface(Ci.nsIHttpChannel);
        channelId = channel.channelId;
      } catch(e) {
        return;
      }
      gChannelMap.set(channelId, channel);
      break;
    case "http-on-examine-response":
      try {
        channel = subject.QueryInterface(Ci.nsIHttpChannel);
        channelId = channel.channelId;
      } catch(e) {
        return;
      }
      gChannelMap.delete(channelId);
      break;
    }
  }
};

class OpenWPMStackDumpParent extends JSWindowActorParent {
  constructor() {
    super();
    Services.obs.addObserver(observer, "http-on-opening-request", true);
    Services.obs.addObserver(observer, "document-on-opening-request", true);
    Services.obs.addObserver(observer, "http-on-examine-response", true);
  }
  async receiveMessage({ data: { channelId, stacktrace }}) {
    while (!gChannelMap.has(channelId)) {
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    let requestId = ChannelWrapper.get(gChannelMap.get(channelId)).id;
    Services.obs.notifyObservers(
      { wrappedJSObject: { requestId, stacktrace } },
      "openwpm-stacktrace"
    );
  }
}
