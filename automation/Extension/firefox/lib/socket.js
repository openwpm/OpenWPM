const {Cc, Ci}  = require("chrome");

var bufferpack  = require("bufferpack/bufferpack");

var tm = Cc["@mozilla.org/thread-manager;1"].getService();
var socketService = Cc["@mozilla.org/network/socket-transport-service;1"]
                          .getService(Ci.nsISocketTransportService);

class ListeningSocket {
  // Socket which feeds incomming messages to a queue
  constructor() {

    console.log("Initializing a listening sever socket...");
    this._serverSocket = Cc["@mozilla.org/network/server-socket;1"]
                              .createInstance(Ci.nsIServerSocket);
    this._inputStream = null;
    this._serverSocket.init(-1, true, -1); // init with random port

    this.port = this._serverSocket.port;
    this.queue = []; // stores messages sent to socket
    console.log("...serverSocket listening on port:",this.port);

  }

  startListening() {
    var thisSocket = this; // self reference for closure
    this._serverSocket.asyncListen({
      onSocketAccepted: function(sock, transport) {
          thisSocket._inputStream = transport.openInputStream(0, 0, 0);
          thisSocket._inputStream.asyncWait({
            onInputStreamReady: function() {
              thisSocket._updateQueue();
            }
          }, 0, 0, tm.mainThread);
      }
    });
  }

  _updateQueue() {
    var bInputStream = Cc["@mozilla.org/binaryinputstream;1"]
                              .createInstance(Ci.nsIBinaryInputStream);
    bInputStream.setInputStream(this._inputStream);

    var buff = bInputStream.readByteArray(5);
    var meta = bufferpack.unpack('>Lc', buff);
    var string = bInputStream.readBytes(meta[0]);
    if (meta[1] != 'n' && meta[1] == 'j') {
      string = JSON.parse(string);
    } else if (meta[1] != 'n') {
      console.error("Unsupported serialization type (",meta[1],").");
      return;
    }
    this.queue.push(string);

    var thisSocket = this; // self reference for closure
    this._inputStream.asyncWait({
      onInputStreamReady: function(){
        thisSocket._updateQueue();
      }
    }, 0, 0, tm.mainThread);
  }
}
exports.ListeningSocket = ListeningSocket;

class SendingSocket {
  // Socket which encodes messages and sets to specified (host, port)
  constructor() {
    this._stream = null;
    this._bOutputStream = Cc["@mozilla.org/binaryoutputstream;1"]
                              .createInstance(Ci.nsIBinaryOutputStream);
  }

  connect(host, port) {
    // Open socket connection to remote host
    try {
      var transport = socketService.createTransport(null, 0, host, port, null);
      this._stream = transport.openOutputStream(1, 4096, 1048575);
      this._bOutputStream.setOutputStream(this._stream)
      return true;
    } catch (err) {
      console.error(err,err.message);
      return false;
    }
  }

  send(record) {
    try {
      var msg = JSON.stringify(record);
      var buff = bufferpack.pack('>Lc',[msg.length,'j']);
      this._bOutputStream.writeByteArray(buff, buff.length);
      this._stream.write(msg, msg.length);
      return true;
    } catch (err) {
      console.error(err,err.message);
      return false;
    }
  }

  close() {
    this._stream.close();
  }
}
exports.SendingSocket = SendingSocket;
