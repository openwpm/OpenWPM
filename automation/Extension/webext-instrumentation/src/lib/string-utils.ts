export const encodeUtf8 = s => {
  return unescape(encodeURIComponent(s));
};

export const escapeString = (str: any) => {
  // Convert to string if necessary
  if (typeof str !== "string") {
    str = String(str);
  }

  return encodeUtf8(str);
};

export const escapeUrl = (url: string, stripDataUrlData: boolean = true) => {
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

// Base64 encoding, found on:
// https://stackoverflow.com/questions/12710001/how-to-convert-uint8-array-to-base64-encoded-string/25644409#25644409
export const Uint8ToBase64 = (u8Arr: Uint8Array) => {
  const CHUNK_SIZE = 0x8000; // arbitrary number
  let index = 0;
  const length = u8Arr.length;
  let result = "";
  let slice: Uint8Array;
  while (index < length) {
    slice = u8Arr.subarray(index, Math.min(index + CHUNK_SIZE, length));
    result += String.fromCharCode.apply(null, slice);
    index += CHUNK_SIZE;
  }
  return btoa(result);
};

export const boolToInt = (bool: boolean) => {
  return bool ? 1 : 0;
};
