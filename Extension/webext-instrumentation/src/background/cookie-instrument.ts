import { incrementedEventOrdinal } from "../lib/extension-session-event-ordinal";
import { extensionSessionUuid } from "../lib/extension-session-uuid";
import { boolToInt, escapeString } from "../lib/string-utils";
import { JavascriptCookie, JavascriptCookieRecord } from "../schema";
import Cookie = browser.cookies.Cookie;
import OnChangedCause = browser.cookies.OnChangedCause;

export const transformCookieObjectToMatchOpenWPMSchema = (cookie: Cookie) => {
  const javascriptCookie = {} as JavascriptCookie;

  // Expiry time (in seconds)
  // May return ~Max(int64). I believe this is a session
  // cookie which doesn't expire. Sessions cookies with
  // non-max expiry time expire after session or at expiry.
  const expiryTime = cookie.expirationDate; // returns seconds
  let expiryTimeString;
  const maxInt64 = 9223372036854776000;
  if (!cookie.expirationDate || expiryTime === maxInt64) {
    expiryTimeString = "9999-12-31T21:59:59.000Z";
  } else {
    const expiryTimeDate = new Date(expiryTime * 1000); // requires milliseconds
    expiryTimeString = expiryTimeDate.toISOString();
  }
  javascriptCookie.expiry = expiryTimeString;
  javascriptCookie.is_http_only = boolToInt(cookie.httpOnly);
  javascriptCookie.is_host_only = boolToInt(cookie.hostOnly);
  javascriptCookie.is_session = boolToInt(cookie.session);

  javascriptCookie.host = escapeString(cookie.domain);
  javascriptCookie.is_secure = boolToInt(cookie.secure);
  javascriptCookie.name = escapeString(cookie.name);
  javascriptCookie.path = escapeString(cookie.path);
  javascriptCookie.value = escapeString(cookie.value);
  javascriptCookie.same_site = escapeString(cookie.sameSite);
  javascriptCookie.first_party_domain = escapeString(cookie.firstPartyDomain);
  javascriptCookie.store_id = escapeString(cookie.storeId);

  javascriptCookie.time_stamp = new Date().toISOString();

  return javascriptCookie;
};

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
      const eventType = changeInfo.removed ? "deleted" : "added-or-changed";
      const update: JavascriptCookieRecord = {
        record_type: eventType,
        change_cause: changeInfo.cause,
        browser_id: crawlID,
        extension_session_uuid: extensionSessionUuid,
        event_ordinal: incrementedEventOrdinal(),
        ...transformCookieObjectToMatchOpenWPMSchema(changeInfo.cookie),
      };
      this.dataReceiver.saveRecord("javascript_cookies", update);
    };
    browser.cookies.onChanged.addListener(this.onChangedListener);
  }

  public async saveAllCookies(crawlID) {
    const allCookies = await browser.cookies.getAll({});
    await Promise.all(
      allCookies.map((cookie: Cookie) => {
        const update: JavascriptCookieRecord = {
          record_type: "manual-export",
          browser_id: crawlID,
          extension_session_uuid: extensionSessionUuid,
          ...transformCookieObjectToMatchOpenWPMSchema(cookie),
        };
        return this.dataReceiver.saveRecord("javascript_cookies", update);
      }),
    );
  }

  public cleanup() {
    if (this.onChangedListener) {
      browser.cookies.onChanged.removeListener(this.onChangedListener);
    }
  }
}
