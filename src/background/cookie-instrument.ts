// import { Cc, Ci } from 'chrome';
// import events from 'sdk/system/events';
// import { data } from 'sdk/self';
// import { boolToInt, escapeString } from "../lib/string-utils";

export class CookieInstrument {
  private readonly dataReceiver;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID) {
    console.log("CookieInstrument", crawlID, this.dataReceiver);

    // Instrument cookie changes
    browser.cookies.onChanged.addListener(function(changeInfo) {
      // Ignore requests made by extensions
      /*
        if (details.originUrl.indexOf("moz-extension://") > -1) {
          return;
        }
        */
      console.log(
        "Cookie changed: " +
          "\n * Cookie: " +
          JSON.stringify(changeInfo.cookie) +
          "\n * Cause: " +
          changeInfo.cause +
          "\n * Removed: " +
          changeInfo.removed,
        changeInfo,
      );

      /*
      const event = changeInfo;

      const data = event.data;
      // TODO: Support other cookie operations
      if (data === "deleted" || data === "added" || data === "changed") {
        const update: any = {};
        update.change = escapeString(data);
        update.crawl_id = crawlID;

        let cookie = event.subject.QueryInterface(Ci.nsICookie2);

        // Creation time (in microseconds)
        const creationTime = new Date(cookie.creationTime / 1000); // requires milliseconds
        update.creationTime = creationTime.toLocaleFormat("%Y-%m-%d %H:%M:%S");

        // Expiry time (in seconds)
        // May return ~Max(int64). I believe this is a session
        // cookie which doesn't expire. Sessions cookies with
        // non-max expiry time expire after session or at expiry.
        const expiryTime = cookie.expiry; // returns seconds
        if (expiryTime === 9223372036854776000) {
          const expiryTimeString = "9999-12-31 23:59:59";
        } else {
          const expiryTimeDate = new Date(expiryTime * 1000); // requires milliseconds
          const expiryTimeString = expiryTimeDate.toLocaleFormat(
            "%Y-%m-%d %H:%M:%S",
          );
        }
        update.expiry = expiryTimeString;
        update.is_http_only = boolToInt(cookie.isHttpOnly);
        update.is_session = boolToInt(cookie.isSession);

        // Accessed time (in microseconds)
        const lastAccessedTime = new Date(cookie.lastAccessed / 1000); // requires milliseconds
        update.last_accessed = lastAccessedTime.toLocaleFormat(
          "%Y-%m-%d %H:%M:%S",
        );
        update.raw_host = escapeString(cookie.rawHost);

        cookie = cookie.QueryInterface(Ci.nsICookie);
        update.expires = cookie.expires;
        update.host = escapeString(cookie.host);
        update.is_domain = boolToInt(cookie.isDomain);
        update.is_secure = boolToInt(cookie.isSecure);
        update.name = escapeString(cookie.name);
        update.path = escapeString(cookie.path);
        update.policy = cookie.policy;
        update.status = cookie.status;
        update.value = escapeString(cookie.value);

        this.dataReceiver.saveRecord("javascript_cookies", update);
      }
      */
    });
  }
}
