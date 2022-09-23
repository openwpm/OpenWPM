/**
 * Code from the example at
 * https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest
 */

export async function digestMessage(msgUint8: Uint8Array) {
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgUint8); // hash the message
  const hashArray = Array.from(new Uint8Array(hashBuffer)); // convert buffer to byte array
  const hashHex = hashArray
    .map((b) => b.toString(16).padStart(2, "0"))
    .join(""); // convert bytes to hex string
  return hashHex;
}
