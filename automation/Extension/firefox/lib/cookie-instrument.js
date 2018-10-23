// import { Cc, Ci } from 'chrome';
// import events from 'sdk/system/events';
// import { data } from 'sdk/self';

let loggingDB;
export const setLoggingDB = function($loggingDB) {
  loggingDB = $loggingDB;
};

export const run = function(crawlID) {
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
        changeInfo
        );
    });
    /*
    events.on("cookie-changed", function(event) {
        var data = event.data;
        // TODO: Support other cookie operations
        if(data == "deleted" || data == "added" || data == "changed") {
            var update = {};
            update["change"] = loggingDB.escapeString(data);
            update["crawl_id"] = crawlID;

            var cookie = event.subject.QueryInterface(Ci.nsICookie2);

            // Creation time (in microseconds)
            var creationTime = new Date(cookie.creationTime / 1000); // requires milliseconds
            update["creationTime"] = creationTime.toLocaleFormat('%Y-%m-%d %H:%M:%S');

            // Expiry time (in seconds)
            // May return ~Max(int64). I believe this is a session
            // cookie which doesn't expire. Sessions cookies with
            // non-max expiry time expire after session or at expiry.
            var expiryTime = cookie.expiry; // returns seconds
            if (expiryTime == 9223372036854776000) {
                var expiryTimeString = '9999-12-31 23:59:59';
            } else {
                var expiryTimeDate = new Date(expiryTime * 1000) // requires milliseconds
                var expiryTimeString = expiryTimeDate.toLocaleFormat('%Y-%m-%d %H:%M:%S');
            }
            update["expiry"] = expiryTimeString;
            update["is_http_only"] = loggingDB.boolToInt(cookie.isHttpOnly);
            update["is_session"] = loggingDB.boolToInt(cookie.isSession);

            // Accessed time (in microseconds)
            var lastAccessedTime = new Date(cookie.lastAccessed / 1000); // requires milliseconds
            update["last_accessed"] = lastAccessedTime.toLocaleFormat('%Y-%m-%d %H:%M:%S');
            update["raw_host"] = loggingDB.escapeString(cookie.rawHost);

            cookie = cookie.QueryInterface(Ci.nsICookie);
            update["expires"] = cookie.expires;
            update["host"] = loggingDB.escapeString(cookie.host);
            update["is_domain"] = loggingDB.boolToInt(cookie.isDomain);
            update["is_secure"] = loggingDB.boolToInt(cookie.isSecure);
            update["name"] = loggingDB.escapeString(cookie.name);
            update["path"] = loggingDB.escapeString(cookie.path);
            update["policy"] = cookie.policy;
            update["status"] = cookie.status;
            update["value"] = loggingDB.escapeString(cookie.value);

            loggingDB.saveRecord("javascript_cookies", update);
        }
    }, true);
    */
};
