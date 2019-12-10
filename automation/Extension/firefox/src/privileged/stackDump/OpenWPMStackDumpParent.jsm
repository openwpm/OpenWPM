"use strict";

var EXPORTED_SYMBOLS = ["OpenWPMStackDumpParent"];

const { Services } = ChromeUtils.import("resource://gre/modules/Services.jsm");

class OpenWPMStackDumpParent extends JSWindowActorParent {
  constructor() {
    super();
  }
  receiveMessage(msg, data) {
    Services.obs.notifyObservers(
      { wrappedJSObject: msg.data },
      "openwpm-stacktrace"
    );
  }
}
