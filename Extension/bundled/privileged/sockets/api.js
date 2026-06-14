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
              const socketListener = {
                onInputStreamReady: () => {
                  try {
                    inputStream.available();
                  } catch (e) {
                    if (e.result !== Cr.NS_BASE_STREAM_CLOSED) {
                      // Abnormal close, let's log the error.
                      console.error(e);
                    }
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
                      listener(port, string, tag === "j");
                    });
                  } else if (tag === "n") {
                    const rawBytes = new Uint8Array(payloadBytes);
                    gManager.onDataReceivedListeners.forEach((listener) => {
                      listener(port, rawBytes, false);
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
            const listener = (id, data, is_json) => {
              fire.async(id, data, is_json);
            };
            gManager.onDataReceivedListeners.add(listener);
            return () => {
              gManager.onDataReceivedListeners.delete(listener);
            };
          },
        }).api(),

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

          const socket = gManager.sendingSocketMap.get(id);
          try {
            const serializationSymbol = json ? "j" : "n";
            // `data` is ALREADY a byte-string, NOT a Unicode string. Every
            // caller funnels payloads through escapeString()/encode_utf8()
            // (see Extension/src/lib/string-utils.ts), which converts the
            // source text to UTF-8 and exposes each byte as a Latin-1 char
            // (code points 0-255); binary POST bodies arrive the same way. The
            // bytes we must put on the wire are therefore exactly those char
            // codes narrowed to one byte each -- this is the lossless byte
            // pass-through the Python reader (socket_interface._parse) decodes
            // as UTF-8. Running TextEncoder over this already-encoded
            // byte-string would double-encode it (the UTF-8 of "你好" turns
            // into the UTF-8 of "ä½\xa0å¥½" mojibake), so we narrow instead of
            // re-encode (api.js narrows each char to a byte below). Framing on
            // bytes.length (== data.length here, since every char is one byte)
            // keeps the length prefix consistent with the payload.
            // Assigning into a Uint8Array applies ToUint8 (mod 256), so each
            // already-byte-sized char code lands as the intended raw byte.
            const bytes = new Uint8Array(data.length);
            for (let i = 0; i < data.length; i++) {
              bytes[i] = data.charCodeAt(i);
            }
            // The length field is a big-endian u32 (`>L`); bufferpack silently
            // clamps out-of-range values, which would emit a wrong length and
            // permanently desync the stream. Reject oversized payloads instead.
            if (bytes.length > 0xffffffff) {
              throw new Error(
                `Payload of ${bytes.length} bytes exceeds the u32 length ` +
                  `field (max ${0xffffffff}); refusing to send to avoid ` +
                  `framing desync.`,
              );
            }
            const buff = bufferpack.pack(">Lc", [
              bytes.length,
              serializationSymbol,
            ]);
            writeAll(socket.bOutputStream, buff);
            writeAll(socket.bOutputStream, bytes);
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
