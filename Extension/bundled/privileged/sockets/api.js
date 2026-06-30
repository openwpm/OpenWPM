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

/**
 * Write a length-prefixed message to a connection's output stream.
 *
 * The wire format matches the Python `socket_interface` framing: a 4-byte
 * big-endian length, a 1-byte serialization tag, then the payload.
 *
 * `conn` is a `{ stream, bOutputStream }` pair as stored in `sendingSocketMap`
 * (outbound connections) or `connectionMap` (replies on accepted connections).
 *
 * NOTE: the length prefix uses `data.length`, a UTF-16 code-unit count, which
 * equals the byte count only for ASCII payloads. Every message that currently
 * travels this framing -- storage records (already ASCII-escaped JSON) and the
 * control-socket Initialize/Finalize/FinalizeAck messages -- is ASCII, so this
 * is correct today. Routing arbitrary non-ASCII payloads would require moving
 * both senders to a UTF-8 byte length together; that is intentionally left as
 * a single follow-up so the two stay consistent.
 */
function writeFramedMessage(conn, data, json) {
  const serializationSymbol = json ? "j" : "n";
  const header = bufferpack.pack(">Lc", [data.length, serializationSymbol]);
  conn.bOutputStream.writeByteArray(header, header.length);
  conn.stream.write(data, data.length);
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
                  const string = bis.readBytes(meta[0]);

                  if (["j", "n"].includes(meta[1])) {
                    gManager.onDataReceivedListeners.forEach((listener) => {
                      listener(port, string, meta[1] === "j", connectionId);
                    });
                  } else {
                    console.error(
                      `Unsupported serialization type ('${meta[1]}').`,
                    );
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
            return;
          }

          try {
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
