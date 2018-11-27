export function encode_utf8(s) {
  return unescape(encodeURIComponent(s));
}

export const escapeString = function(str: any) {
  // Convert to string if necessary
  if (typeof str != "string") {
    str = String(str);
  }

  return encode_utf8(str);
};

export const escapeUrl = function(
  url: string,
  stripDataUrlData: boolean = true,
) {
  url = escapeString(url);
  // data:[<mediatype>][;base64],<data>
  if (
    url.substr(0, 5) === "data:" &&
    stripDataUrlData &&
    url.indexOf(",") > -1
  ) {
    url = url.substr(0, url.indexOf(",") + 1) + "<data-stripped>";
  }
  return url;
};

export const boolToInt = function(bool: boolean) {
  return bool ? 1 : 0;
};
