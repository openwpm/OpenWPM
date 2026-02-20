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
              const outputStream = transport.openOutputStream(0, 0, 0);

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

          const conn = gManager.connectionMap.get(connectionId);
          try {
            const serializationSymbol = json ? "j" : "n";
            const buff = bufferpack.pack(">Lc", [
              data.length,
              serializationSymbol,
            ]);
            conn.bOutputStream.writeByteArray(buff, buff.length);
            conn.stream.write(data, data.length);
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

          const socket = gManager.sendingSocketMap.get(id);
          try {
            const serializationSymbol = json ? "j" : "n";
            const buff = bufferpack.pack(">Lc", [
              data.length,
              serializationSymbol,
            ]);
            socket.bOutputStream.writeByteArray(buff, buff.length);
            socket.stream.write(data, data.length);
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
