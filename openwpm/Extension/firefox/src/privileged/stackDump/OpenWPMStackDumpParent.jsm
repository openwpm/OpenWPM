"use strict";

var EXPORTED_SYMBOLS = ["OpenWPMStackDumpParent"];

const { Services } = ChromeUtils.import("resource://gre/modules/Services.jsm");
const { XPCOMUtils } = ChromeUtils.import(
  "resource://gre/modules/XPCOMUtils.jsm"
);

XPCOMUtils.defineLazyModuleGetters(this, {
  setTimeout: "resource://gre/modules/Timer.jsm",
});

// ChannelWrapper.get(someChannel).id in the parent process corresponds to
// WebRequest requestId values - which is what we want to propagate. This lets
// us associate instrumented requests with the corresponding call stacks.
// We need channels to look up the ChannelWrapper, ids are not sufficient.
// Channels are stored in this map by channel ID, at *-on-opening-request.
// They're cleared at on-examine-*-response when we won't need them anymore.
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
    case "http-on-examine-cached-response":
    case "http-on-examine-merged-response":
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
    Services.obs.addObserver(observer, "http-on-examine-cached-response", true);
    Services.obs.addObserver(observer, "http-on-examine-merged-response", true);
  }
  //receiving messages from the child
  async receiveMessage({ data: { channelId, stacktrace }}) {
    // Check if we've already got the channel, and if not, wait.
    while (!gChannelMap.has(channelId)) {
      // Spin the event loop - this lets us observe new channels while waiting here.
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    // ChannelWrapper.get(someChannel).id in the parent process corresponds to
    // WebRequest requestId values.
    let requestId = ChannelWrapper.get(gChannelMap.get(channelId)).id;
    //Sends message to api.js
    Services.obs.notifyObservers(
      { wrappedJSObject: { requestId, stacktrace } },
      "openwpm-stacktrace"
    );
  }
}
