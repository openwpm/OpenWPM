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

export const boolToInt = function(bool: boolean) {
  return bool ? 1 : 0;
};
