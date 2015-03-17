const {Cc, Ci} = require("chrome");

var bufferpack = require("bufferpack/bufferpack");
var pickle = require("./pickle.js");

// Socket connection handle
var stream = null;
var binStream = null;

// Grab socket transport
var socket_service = Cc["@mozilla.org/network/socket-transport-service;1"]
                          .getService(Ci.nsISocketTransportService);
var binaryStream = Cc["@mozilla.org/binaryoutputstream;1"]
                             .createInstance(Ci.nsIBinaryOutputStream);

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
        var msg = pickle.dumps(query);
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
