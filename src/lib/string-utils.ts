export function encode_utf8(s) {
  return unescape(encodeURIComponent(s));
}

export const escapeString = function(string) {
  // Convert to string if necessary
  if (typeof string != "string") {
    string = "" + string;
  }

  return encode_utf8(string);
};

export const boolToInt = function(bool) {
  return bool ? 1 : 0;
};
