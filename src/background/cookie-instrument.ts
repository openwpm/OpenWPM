// import { Cc, Ci } from 'chrome';
// import events from 'sdk/system/events';
// import { data } from 'sdk/self';
import { boolToInt, escapeString } from "../lib/string-utils";
import Cookie = browser.cookies.Cookie;

interface CookieRecord {
  crawl_id: string;
  change: "deleted" | "added" | "changed";
  creationTime: string;
  expiry: string;
  is_http_only: number;
  is_session: number;
  last_accessed: string;
  raw_host: string;
  expires: string;
  host: string;
  is_domain: number;
  is_secure: number;
  name: string;
  path: string;
  policy: string;
  status: string;
  value: string;
}

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
      "evicted"
      | "expired"
      | "explicit"
      | "expired_overwrite"
      | "overwrite";
      */

      const change = changeInfo.removed ? "deleted" : "added";

      // TODO: Support other cookie operations
      if (change === "deleted" || change === "added" || change === "changed") {
        const update = {} as CookieRecord;
        update.change = change;
        // TODO: Add changeInfo.cause
        update.crawl_id = crawlID;

        const cookie: Cookie = changeInfo.cookie;

        // Creation time (in microseconds)
        const creationTime = new Date(cookie.creationTime / 1000); // requires milliseconds
        update.creationTime = creationTime.toLocaleFormat("%Y-%m-%d %H:%M:%S");

        // Expiry time (in seconds)
        // May return ~Max(int64). I believe this is a session
        // cookie which doesn't expire. Sessions cookies with
        // non-max expiry time expire after session or at expiry.
        const expiryTime = cookie.expiry; // returns seconds
        let expiryTimeString;
        if (expiryTime === 9223372036854776000) {
          expiryTimeString = "9999-12-31 23:59:59";
        } else {
          const expiryTimeDate = new Date(expiryTime * 1000); // requires milliseconds
          expiryTimeString = expiryTimeDate.toLocaleFormat("%Y-%m-%d %H:%M:%S");
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
    });
  }
}
