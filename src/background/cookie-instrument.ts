import { extensionSessionUuid } from "../lib/extension-session-uuid";
import { boolToInt, escapeString } from "../lib/string-utils";
import Cookie = browser.cookies.Cookie;
import OnChangedCause = browser.cookies.OnChangedCause;
import { JavascriptCookieChange } from "../schema";

export class CookieInstrument {
  private readonly dataReceiver;
  private onChangedListener;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID) {
    // Instrument cookie changes
    this.onChangedListener = async (changeInfo: {
      /** True if a cookie was removed. */
      removed: boolean;
      /** Information about the cookie that was set or removed. */
      cookie: Cookie;
      /** The underlying reason behind the cookie's change. */
      cause: OnChangedCause;
    }) => {
      const change = changeInfo.removed ? "deleted" : "added";

      // TODO: Support other cookie operations
      if (change === "deleted" || change === "added" || change === "changed") {
        const update = {} as JavascriptCookieChange;

        update.change = change;
        update.change_cause = changeInfo.cause;
        update.crawl_id = crawlID;
        update.extension_session_uuid = extensionSessionUuid;

        const cookie: Cookie = changeInfo.cookie;

        // Expiry time (in seconds)
        // A comment from pre-webextension code, which may still be valid:
        // May return ~Max(int64). I believe this is a session
        // cookie which doesn't expire. Sessions cookies with
        // non-max expiry time expire after session or at expiry.
        const expiryTime = cookie.expirationDate; // returns seconds
        let expiryTimeString;
        if (!cookie.expirationDate || expiryTime === 9223372036854776000) {
          expiryTimeString = "9999-12-31T21:59:59.000Z";
        } else {
          const expiryTimeDate = new Date(expiryTime * 1000); // requires milliseconds
          expiryTimeString = expiryTimeDate.toISOString();
        }
        update.expiry = expiryTimeString;
        update.is_http_only = boolToInt(cookie.httpOnly);
        update.is_host_only = boolToInt(cookie.hostOnly);
        update.is_session = boolToInt(cookie.session);

        update.host = escapeString(cookie.domain);
        update.is_secure = boolToInt(cookie.secure);
        update.name = escapeString(cookie.name);
        update.path = escapeString(cookie.path);
        update.value = escapeString(cookie.value);
        update.same_site = escapeString(cookie.sameSite);
        update.first_party_domain = escapeString(cookie.firstPartyDomain);
        update.store_id = escapeString(cookie.storeId);

        update.time_stamp = new Date().toISOString();

        this.dataReceiver.saveRecord("javascript_cookies", update);
      }
    };
    browser.cookies.onChanged.addListener(this.onChangedListener);
  }

  public cleanup() {
    if (this.onChangedListener) {
      browser.cookies.onChanged.removeListener(this.onChangedListener);
    }
  }
}
