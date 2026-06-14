import * as loggingDB from "./loggingdb";
import { escapeString } from "./lib/string-utils";

/**
 * Test-only "echo mode" (config flag `echo_mode`, default off).
 *
 * Instead of running any instrument, the extension emits a fixed set of
 * synthetic payloads over the already-connected storageController
 * `SendingSocket`. This drives the real `sockets.sendData` framing path that
 * PR #1180 hardened (the `>Lc` length prefix, the `j`/`n` tags, the
 * byte-string narrowing) end to end into a Python `ServerSocket`, so a test
 * can assert exact round-trip fidelity without standing up a StorageController
 * or a real crawl. See `test/test_socket_echo.py`.
 *
 * Payloads (matching the real wire path):
 *  - A `j` (JSON) record whose string values were run through `escapeString`
 *    just like every real instrument does. `escapeString` =
 *    `unescape(encodeURIComponent(s))`, i.e. it turns the source text into
 *    UTF-8 and exposes each byte as a Latin-1 char. `JSON.stringify` therefore
 *    produces a byte-string; api.js narrows each char to a byte; the Python
 *    reader decodes the frame as UTF-8 and `json.loads` it back to the
 *    original Unicode record.
 *  - An `n` (raw byte-string) payload sent via `send(data, false)` (json=false).
 *    `data` is `escapeString("café/🌍")` -- the UTF-8 bytes as Latin-1 chars --
 *    so api.js puts the raw UTF-8 bytes on the wire and the Python reader
 *    returns them as `bytes`, untouched.
 *
 * The non-ASCII content mirrors what `test/test_socket_interface.py` pins: a
 * double UTF-8 encode on the send side would turn it into mojibake, so an exact
 * round-trip is a real regression guard for #1180.
 */

// The decoded (original) Unicode strings the `j` record carries. The test
// asserts against these post-decode values; echo escapes them on the way out.
export const ECHO_J_RECORD = [
  "echo",
  {
    s: "你好 — Привет — 🌍",
    n: "naïve café λ — 例え",
  },
];

// The source text for the `n` payload. On the wire this is its UTF-8 bytes; the
// Python side receives `"café/🌍".encode("utf-8")` as raw `bytes`.
export const ECHO_N_TEXT = "café/🌍";

function escapeValue(value: any): any {
  if (typeof value === "string") {
    return escapeString(value);
  }
  if (Array.isArray(value)) {
    return value.map(escapeValue);
  }
  if (value !== null && typeof value === "object") {
    const out: any = {};
    for (const k of Object.keys(value)) {
      out[escapeString(k)] = escapeValue(value[k]);
    }
    return out;
  }
  return value;
}

export const runEchoMode = function (): void {
  console.warn(
    "OpenWPM echo_mode is ENABLED: skipping all instruments and emitting " +
      "synthetic protocol-test payloads on the storage socket. This is a " +
      "test-only affordance and must never be set for a real crawl.",
  );

  const storageController = loggingDB.getStorageController();
  if (storageController == null) {
    console.error(
      "echo_mode: storageController socket is not connected; cannot emit " +
        "payloads. Did the harness inject storage_controller_address?",
    );
    return;
  }

  // (A) JSON record with non-ASCII content, via the 'j' tag. Escape string
  // values first, exactly like the real instruments, so the bytes on the wire
  // match production.
  const escaped = escapeValue(ECHO_J_RECORD);
  storageController.send(JSON.stringify(escaped), true);

  // (B) Raw byte-string payload, via the 'n' tag. send(data, false) skips JSON
  // and api.js narrows the (already byte-sized) chars straight to the wire.
  storageController.send(escapeString(ECHO_N_TEXT), false);
};
