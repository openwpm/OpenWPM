import moment from "moment";
import { boolToInt, escapeString } from "../lib/string-utils";
import Cookie = browser.cookies.Cookie;
import OnChangedCause = browser.cookies.OnChangedCause;
import { JavascriptCookieChange } from "../types/schema";

export class CookieInstrument {
  private readonly dataReceiver;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID) {
    // Instrument cookie changes
    browser.cookies.onChanged.addListener(
      async (changeInfo: {
        /** True if a cookie was removed. */
        removed: boolean;
        /** Information about the cookie that was set or removed. */
        cookie: Cookie;
        /** The underlying reason behind the cookie's change. */
        cause: OnChangedCause;
      }) => {
        const change = changeInfo.removed ? "deleted" : "added";

        // TODO: Support other cookie operations
        if (
          change === "deleted" ||
          change === "added" ||
          change === "changed"
        ) {
          const update = {} as JavascriptCookieChange;

          update.change = change;
          // TODO: Add changeInfo.cause
          update.crawl_id = crawlID;

          const cookie: Cookie = changeInfo.cookie;

          // Creation time (in microseconds)
          // const creationTime = new Date(cookie.creationTime / 1000); // requires milliseconds
          // update.creationTime = creationTime.toLocaleFormat("%Y-%m-%d %H:%M:%S");

          // Expiry time (in seconds)
          // A comment from pre-webextension code, which may still be valid:
          // May return ~Max(int64). I believe this is a session
          // cookie which doesn't expire. Sessions cookies with
          // non-max expiry time expire after session or at expiry.
          const expiryTime = cookie.expirationDate; // returns seconds
          let expiryTimeString;
          if (!cookie.expirationDate || expiryTime === 9223372036854776000) {
            expiryTimeString = "9999-12-31 23:59:59";
          } else {
            const expiryTimeDate = new Date(expiryTime * 1000); // requires milliseconds
            expiryTimeString = moment(expiryTimeDate).format(
              "YYYY-MM-DD HH:mm:ss",
            );
          }
          update.expiry = expiryTimeString;
          update.is_http_only = boolToInt(cookie.httpOnly);
          update.is_host_only = boolToInt(cookie.hostOnly);
          update.is_session = boolToInt(cookie.session);

          // Accessed time (in microseconds)
          // const lastAccessedTime = new Date(cookie.lastAccessed / 1000); // requires milliseconds
          // update.last_accessed = lastAccessedTime.toLocaleFormat("%Y-%m-%d %H:%M:%S");
          // update.raw_host = escapeString(cookie.rawHost);

          // update.expires = cookie.expires;
          update.host = escapeString(cookie.domain);
          // update.is_domain = boolToInt(cookie.isDomain);
          update.is_secure = boolToInt(cookie.secure);
          update.name = escapeString(cookie.name);
          update.path = escapeString(cookie.path);
          // update.policy = cookie.policy;
          // update.status = cookie.status;
          update.value = escapeString(cookie.value);
          update.same_site = escapeString(cookie.sameSite);
          update.first_party_domain = escapeString(cookie.firstPartyDomain);

          this.dataReceiver.saveRecord("javascript_cookies", update);
        }
      },
    );
  }
}
