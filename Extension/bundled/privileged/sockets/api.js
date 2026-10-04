Cu.importGlobalProperties(["TextDecoder"]);

// Cache a single UTF-8 decoder for the instrumentation hot path. A new
// TextDecoder per received frame would allocate on every "j"/"u" decode; one
// shared instance is safe because decode() is synchronous and stateless for
// our one-shot (non-streaming) calls. Only the "j"/"u" UTF-8 text path uses
// this; the "n" raw-bytes path never decodes.
const gUtf8Decoder = new TextDecoder("utf-8");

const tm = Cc["@mozilla.org/thread-manager;1"].getService();
const socketService = Cc[
  "@mozilla.org/network/socket-transport-service;1"
].getService(Ci.nsISocketTransportService);

const gManager = {
  // Map of port -> server socket
  serverSocketMap: new Map(),
  // Map of ID -> server socket
  sendingSocketMap: new Map(),
  nextSendingSocketId: 0,
  onDataReceivedListeners: new Set(),
  // Map of connectionId -> { stream, bOutputStream } for accepted connections
  connectionMap: new Map(),
  nextConnectionId: 0,
};

let bufferpack;

// Write the full byte array to a *blocking* nsIBinaryOutputStream. We open the
// stream with OPEN_BLOCKING (see connect()), where writeByteArray has all-or-
// throw semantics: it writes every byte or throws. A partial/short write
// therefore cannot silently truncate a length-framed payload, so a single call
// suffices.
function writeAll(bOutputStream, bytes) {
  bOutputStream.writeByteArray(bytes, bytes.length);
}

// Narrow an already-encoded byte-string (each char in 0-255, as produced by
// escapeString()/encode_utf8() in Extension/src/lib/string-utils.ts) into a
// Uint8Array of raw bytes. Running TextEncoder over this already-UTF-8 string
// would double-encode it; assigning into a Uint8Array applies ToUint8 (mod
// 256), so each already-byte-sized char code lands as the intended raw byte.
function toBytes(data) {
  const bytes = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) {
    bytes[i] = data.charCodeAt(i);
  }
  return bytes;
}

// Pack the length-prefixed header for a payload of `byteLength` bytes. The
// length field is a big-endian u32 (`>L`); bufferpack silently clamps
// out-of-range values, which would emit a wrong length and permanently desync
// the stream. Reject oversized payloads instead.
function packHeader(byteLength, serializationSymbol) {
  if (byteLength > 0xffffffff) {
    throw new Error(
      `Payload of ${byteLength} bytes exceeds the u32 length ` +
        `field (max ${0xffffffff}); refusing to send to avoid ` +
        `framing desync.`,
    );
  }
  return bufferpack.pack(">Lc", [byteLength, serializationSymbol]);
}

/**
 * Write a length-prefixed message to a connection's output stream.
 *
 * The wire format matches the Python `socket_interface` framing: a 4-byte
 * big-endian length, a 1-byte serialization tag, then the payload.
 *
 * `conn` is a `{ stream, bOutputStream }` pair as stored in `sendingSocketMap`
 * (outbound connections) or `connectionMap` (replies on accepted connections).
 *
 * `data` is an already-encoded byte-string (see `toBytes`); framing on the
 * narrowed byte length keeps the prefix consistent with the bytes on the wire
 * for non-ASCII payloads too. Both the header and the payload go through
 * `writeAll` on the blocking binary stream so a frame can never be partially
 * written (which would desync the length-prefixed stream).
 */
function writeFramedMessage(conn, data, json) {
  const serializationSymbol = json ? "j" : "n";
  const bytes = toBytes(data);
  const header = packHeader(bytes.length, serializationSymbol);
  writeAll(conn.bOutputStream, header);
  writeAll(conn.bOutputStream, bytes);
}
this.sockets = class extends ExtensionAPI {
  getAPI(context) {
    if (!bufferpack) {
      /* globals BufferPack */
      Services.scriptloader.loadSubScript(
        context.extension.getURL("privileged/sockets/bufferpack.js"),
      );
      bufferpack = new BufferPack();
    }

    return {
      sockets: {
        async createServerSocket() {
          const serverSocket = Cc[
            "@mozilla.org/network/server-socket;1"
          ].createInstance(Ci.nsIServerSocket);
          serverSocket.init(-1, true, -1); // init with random port
          gManager.serverSocketMap.set(serverSocket.port, serverSocket);
          return serverSocket.port;
        },

        startListening(port) {
          if (!gManager.serverSocketMap.has(port)) {
            return;
          }
          const socket = gManager.serverSocketMap.get(port);
          socket.asyncListen({
            onSocketAccepted: (sock, transport) => {
              const inputStream = transport.openInputStream(0, 0, 0);
              // Open the reply stream in blocking mode (the default flag 0
              // would yield a non-blocking stream whose write() can throw
              // NS_BASE_STREAM_WOULD_BLOCK). Replies are tiny and the peer is
              // a localhost socket that is actively reading, so a blocking
              // write returns immediately; this mirrors the outbound
              // `connect()` stream below.
              const outputStream = transport.openOutputStream(
                Ci.nsITransport.OPEN_BLOCKING,
                0,
                0,
              );

              gManager.nextConnectionId++;
              const connectionId = gManager.nextConnectionId;
              const bOutputStream = Cc[
                "@mozilla.org/binaryoutputstream;1"
              ].createInstance(Ci.nsIBinaryOutputStream);
              bOutputStream.setOutputStream(outputStream);
              gManager.connectionMap.set(connectionId, {
                stream: outputStream,
                bOutputStream,
              });

              const socketListener = {
                onInputStreamReady: () => {
                  try {
                    inputStream.available();
                  } catch (e) {
                    if (e.result !== Cr.NS_BASE_STREAM_CLOSED) {
                      // Abnormal close, let's log the error.
                      console.error(e);
                    }
                    // Connection closed: close the paired output stream so we
                    // don't leak it, then drop the bookkeeping entry.
                    const conn = gManager.connectionMap.get(connectionId);
                    if (conn) {
                      try {
                        conn.stream.close();
                      } catch {
                        // Already closed by the peer; nothing to do.
                      }
                    }
                    inputStream.close();
                    gManager.connectionMap.delete(connectionId);
                    return;
                  }
                  const bis = Cc[
                    "@mozilla.org/binaryinputstream;1"
                  ].createInstance(Ci.nsIBinaryInputStream);
                  bis.setInputStream(inputStream);
                  const buff = bis.readByteArray(5); // 32 bit int followed by a char = 5 bytes
                  const meta = bufferpack.unpack(">Lc", buff);
                  // Read the payload as raw bytes. Using bis.readBytes()
                  // narrows each byte to a Latin-1 char and would corrupt any
                  // multi-byte UTF-8 payload (the mirror of the send-side
                  // bug). The byte count is consumed regardless of tag, so the
                  // frame stays aligned even for an unsupported serialization
                  // type.
                  const payloadBytes = bis.readByteArray(meta[0]);
                  const tag = meta[1];

                  // Tag parity with the Python reader (socket_interface._parse):
                  //   "j" -> UTF-8 + JSON.parse, "u" -> UTF-8 string,
                  //   "n" -> RAW BYTES (returned unchanged on the Python side).
                  // Only "j" and "u" are UTF-8 text; "n" must be delivered as
                  // raw bytes, NOT UTF-8-decoded, or it would diverge from
                  // Python (which returns the bytes untouched) and could throw
                  // on a non-UTF-8 payload.
                  if (tag === "j" || tag === "u") {
                    const string = gUtf8Decoder.decode(
                      new Uint8Array(payloadBytes),
                    );
                    gManager.onDataReceivedListeners.forEach((listener) => {
                      listener(port, string, tag === "j", connectionId);
                    });
                  } else if (tag === "n") {
                    const rawBytes = new Uint8Array(payloadBytes);
                    gManager.onDataReceivedListeners.forEach((listener) => {
                      listener(port, rawBytes, false, connectionId);
                    });
                  } else {
                    console.error(`Unsupported serialization type ('${tag}').`);
                  }

                  inputStream.asyncWait(socketListener, 0, 0, tm.mainThread);
                },
              };
              inputStream.asyncWait(socketListener, 0, 0, tm.mainThread);
            },
          });
        },

        onDataReceived: new ExtensionCommon.EventManager({
          context,
          name: "sockets.onDataReceived",
          register: (fire) => {
            const listener = (id, data, is_json, connectionId) => {
              fire.async(id, data, is_json, connectionId);
            };
            gManager.onDataReceivedListeners.add(listener);
            return () => {
              gManager.onDataReceivedListeners.delete(listener);
            };
          },
        }).api(),

        sendResponse(connectionId, data, json) {
          if (!gManager.connectionMap.has(connectionId)) {
            console.error(
              "Unknown connection ID for sendResponse; connection may have closed.",
            );
            return false;
          }

          try {
            writeFramedMessage(
              gManager.connectionMap.get(connectionId),
              data,
              json,
            );
            return true;
          } catch (err) {
            console.error(err, err.message);
            return false;
          }
        },

        async createSendingSocket() {
          gManager.nextSendingSocketId++;
          gManager.sendingSocketMap.set(gManager.nextSendingSocketId, {
            stream: null,
            bOutputStream: Cc[
              "@mozilla.org/binaryoutputstream;1"
            ].createInstance(Ci.nsIBinaryOutputStream),
          });
          return gManager.nextSendingSocketId;
        },

        connect(id, host, port) {
          if (!gManager.sendingSocketMap.has(id)) {
            console.error(
              "Unknown socket ID; trying to use a socket that doesn't exist yet?",
            );
            return;
          }

          try {
            const socket = gManager.sendingSocketMap.get(id);
            const transport = socketService.createTransport(
              [],
              host,
              port,
              null,
              null,
            );
            // openFlags = 1 = OPEN_BLOCKING (NOT OPEN_UNBUFFERED, which is 2).
            // A blocking stream makes writeByteArray all-or-throw, so framed
            // payloads can never be partially written (which would desync the
            // length-prefixed stream). See writeAll().
            socket.stream = transport.openOutputStream(1, 4096, 1048575);
            socket.bOutputStream.setOutputStream(socket.stream);
            return true;
          } catch (err) {
            console.error(err, err.message);
            return false;
          }
        },

        sendData(id, data, json) {
          if (!gManager.sendingSocketMap.has(id)) {
            console.error(
              "Unknown socket ID; trying to use a socket that doesn't exist yet?",
            );
            return false;
          }

          try {
            // Outbound framing shares the hardened code path with replies:
            // `data` is an already-encoded byte-string (each char in 0-255 via
            // escapeString()/encode_utf8() in Extension/src/lib/string-utils.ts;
            // binary POST bodies arrive the same way). writeFramedMessage()
            // narrows those char codes back to raw bytes -- re-encoding with
            // TextEncoder would double-encode and corrupt non-ASCII payloads --
            // frames on the narrowed byte length, rejects payloads over the u32
            // length field, and writes header+payload through writeAll() on the
            // blocking stream so a frame can never be partially written.
            writeFramedMessage(gManager.sendingSocketMap.get(id), data, json);
            return true;
          } catch (err) {
            console.error(err, err.message);
            return false;
          }
        },

        close(id) {
          if (!gManager.sendingSocketMap.has(id)) {
            console.error(
              "Unknown socket ID; trying to use a socket that doesn't exist yet?",
            );
            return;
          }

          gManager.sendingSocketMap.get(id).stream.close();
        },
      },
    };
  }
};
