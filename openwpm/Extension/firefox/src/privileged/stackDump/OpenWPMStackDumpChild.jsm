"use strict";

var EXPORTED_SYMBOLS = ["OpenWPMStackDumpChild"];
const { Services } = ChromeUtils.import("resource://gre/modules/Services.jsm");

class Controller {
  constructor(actor) {
    this.actor = actor;
    Services.obs.addObserver(this, "http-on-opening-request");
    Services.obs.addObserver(this, "document-on-opening-request");
  }
  matchRequest(channel, filters) {
    // Log everything if no filter is specified
    if (!filters.outerWindowID && !filters.window) {
      return true;
    }

    // Ignore requests from chrome or add-on code when we are monitoring
    // content.
    // TODO: one particular test (browser_styleeditor_fetch-from-cache.js) needs
    // the flags.testing check. We will move to a better way to serve
    // its needs in bug 1167188, where this check should be removed.
    if (
      channel.loadInfo &&
      channel.loadInfo.loadingDocument === null &&
      channel.loadInfo.loadingPrincipal ===
        Services.scriptSecurityManager.getSystemPrincipal()
    ) {
      return false;
    }

    if (filters.window) {
      // Since frames support, this.window may not be the top level content
      // frame, so that we can't only compare with win.top.
      let win = this.getWindowForRequest(channel);
      while (win) {
        if (win == filters.window) {
          return true;
        }
        if (win.parent == win) {
          break;
        }
        win = win.parent;
      }
    }

    if (filters.outerWindowID) {
      const topFrame = this.getTopFrameForRequest(channel);
      // topFrame is typically null for some chrome requests like favicons
      if (topFrame) {
        try {
          if (topFrame.outerWindowID == filters.outerWindowID) {
            return true;
          }
        } catch (e) {
          // outerWindowID getter from browser.js (non-remote <xul:browser>) may
          // throw when closing a tab while resources are still loading.
        }
      }
    }

    return false;
  }

  getTopFrameForRequest(request) {
    try {
      return this.getRequestLoadContext(request).topFrameElement;
    } catch (ex) {
      // request loadContent is not always available.
    }
    return null;
  }

  getWindowForRequest(request) {
    try {
      return this.getRequestLoadContext(request).associatedWindow;
    } catch (ex) {
      // TODO: bug 802246 - getWindowForRequest() throws on b2g: there is no
      // associatedWindow property.
    }
    return null;
  }

  /**
   * Gets the nsILoadContext that is associated with request.
   *
   * @param nsIHttpChannel request
   * @returns nsILoadContext or null
   */
  getRequestLoadContext(request) {
    try {
      return request.notificationCallbacks.getInterface(Ci.nsILoadContext);
    } catch (ex) {
      // Ignore.
    }

    try {
      return request.loadGroup.notificationCallbacks.getInterface(
        Ci.nsILoadContext
      );
    } catch (ex) {
      // Ignore.
    }

    return null;
  }

  observe(subject, topic, data) {
    switch (topic) {
    case "http-on-opening-request":
    case "document-on-opening-request":
      let channel, channelId;
      try {
        channel = subject.QueryInterface(Ci.nsIHttpChannel);
        channelId = channel.channelId;
      } catch(e) {
        return;
      }
      if (!this.matchRequest(channel, { window: this.actor.contentWindow })) {
        return;
      }
      let frame = Components.stack;
      let stacktrace = [];
      if (frame && frame.caller) {
        frame = frame.caller;
        while (frame) {
          const scheme = frame.filename.split("://")[0];
         /*  Maybe enable this later if we need to
            if (["resource", "chrome", "file"].contains(scheme)) {
            return;
          } */
          // Format described here https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/Stack
          stacktrace.push(
            frame.name +
              "@" +
              frame.filename +
              ":" +
              frame.lineNumber +
              ":" +
              frame.columnNumber +
              ";" +
              frame.asyncCause
          );
          frame = frame.caller || frame.asyncCaller;
        }
      }
      if (!stacktrace.length) return;
      stacktrace = stacktrace.join("\n");
      //Passes the message up to the parent
      this.actor.sendAsyncMessage("OpenWPM:Callstack", { stacktrace, channelId });
      break;
    }
  }
  willDestroy() {
    Services.obs.removeObserver(this, "http-on-opening-request");
    Services.obs.removeObserver(this, "document-on-opening-request");
  }
}

// JSWindowActorChild (which is a WebIDL class) instances are not directly
// usable as nsIObserver instances, so we need to use a separate object to observe requests.
class OpenWPMStackDumpChild extends JSWindowActorChild {
  constructor() {
    super();
  }
  actorCreated() {
    this.controller = new Controller(this);
  }
  willDestroy() {
    this.controller.willDestroy();
  }
  observe() {
    // stuff
  }
};
