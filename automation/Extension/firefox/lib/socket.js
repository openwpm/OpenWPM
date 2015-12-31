const {Cc, Ci}  = require("chrome");
const fileIO    = require("sdk/io/file");
const system    = require("sdk/system");

var bufferpack  = require("bufferpack/bufferpack");

var tm = Cc["@mozilla.org/thread-manager;1"].getService();
var socket_service = Cc["@mozilla.org/network/socket-transport-service;1"]
                          .getService(Ci.nsISocketTransportService);
var binaryStream = Cc["@mozilla.org/binaryoutputstream;1"]
                             .createInstance(Ci.nsIBinaryOutputStream);

// Socket connection handle
var stream = null;
var binStream = null;

// Feeds incomming messages to a queue
exports.createListeningSocket = createListeningSocket;
function createListeningSocket() {
    console.log("Setting up server socket listening");
    var serverSocket = Cc["@mozilla.org/network/server-socket;1"]
                             .createInstance(Ci.nsIServerSocket);

    // init with random port
    serverSocket.init(-1, true, -1);
    console.log("Extension serverSocket listening on port:",serverSocket.port);

    // write port to file for OpenWPM
    var path = system.pathFor("ProfD") + '/extension_port.txt';
    var file = fileIO.open(path, 'w');
    if (!file.closed) {
        file.write(serverSocket.port);
        file.close();
    }

    var queue = [];
    serverSocket.asyncListen({
        onSocketAccepted: function(sock, transport) {
            var inputStream = transport.openInputStream(0, 0, 0);
            inputStream.asyncWait({
                onInputStreamReady: function() {
                    updateQueue(inputStream, queue);
                }
            }, 0, 0, tm.mainThread);
        }
    });

    return queue;
}

function updateQueue(inputStream, queue) {
    var bInputStream = Cc["@mozilla.org/binaryinputstream;1"]
                            .createInstance(Ci.nsIBinaryInputStream);

    bInputStream.setInputStream(inputStream);

    var buff = bInputStream.readByteArray(5);
    var meta = bufferpack.unpack('>Ib', buff);
    string = bInputStream.readBytes(meta[0]);
    if (meta[1]) {
        string = JSON.parse(string);
    }
    queue.push(string);

    inputStream.asyncWait({
        onInputStreamReady: function() {
            updateQueue(inputStream, queue);
        }
    }, 0, 0, tm.mainThread);
}

// Open socket connection
exports.connect = connect;
function connect(host, port) {
    try {
        transport = socket_service.createTransport(null, 0, host, port, null);
        stream = transport.openOutputStream(0, 0, 0);
        binaryStream.setOutputStream(stream)
        return true;
    } catch (err) {
        console.log("ERROR:",err,err.message);
        return false;
    }
}

// Format: [sql_query, [arg1, arg2, arg3]]
// e.g. ["INSERT INTO table (item1, item2) VALUES (?,?)", [val1, val2]]
exports.send = send;
function send(query) {
    try {
        var msg = JSON.stringify(query);
        var buff = bufferpack.pack('>Ib',[msg.length,1]);
        binaryStream.writeByteArray(buff, buff.length);
        stream.write(msg, msg.length);
        return true;
    } catch (err) {
        console.log("ERROR:",err,err.message);
        return false;
    }
}

// Close socket connection
exports.close = close;
function close() {
    stream.close();
}
