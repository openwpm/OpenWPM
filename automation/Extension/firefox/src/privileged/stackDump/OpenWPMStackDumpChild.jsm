"use strict";

var EXPORTED_SYMBOLS = ["OpenWPMChild"];

Cu.reportError("EXECUTING CHILD SCRIPT!");

class OpenWPMChild extends JSWindowActorChild {
  constructor() {
    super();
    Cu.reportError("YO CONSTRUCTED!");
  }
  handleEvent(e) {
    Cu.reportError(e);
  }
  observe(subject, topic, data) {
    Cu.reportError(topic);
  }
}
