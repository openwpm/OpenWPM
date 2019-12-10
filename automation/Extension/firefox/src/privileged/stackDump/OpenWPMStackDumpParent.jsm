"use strict";

var EXPORTED_SYMBOLS = ["OpenWPMStackDumpParent"];

class OpenWPMStackDumpParent extends JSWindowActorParent {
  constructor() {
    super();
  }
  handleEvent(e) {
    Cu.reportError(e);
  }
  observe(subject, topic, data) {
    Cu.reportError(topic);
  }
}
