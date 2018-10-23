import io from 'socket.io-client';

const getSocketIoInstance = function(namespace) {
  return io('http://localhost:7331/' + namespace, {
    transports: ['websocket'] // https://github.com/socketio/socket.io-client/blob/master/docs/API.md#with-websocket-transport-only
  });
};

class ListeningSocket {

  // Socket which feeds incoming messages to a queue
  constructor(namespaceSuffix) {
    this.namespace = 'openwpm-extension-listen-' + namespaceSuffix;
    this.queue = []; // stores messages sent to socket
  }

  startListening() {
    console.log('Listening for incoming web socket messages...');
    this.socket = getSocketIoInstance(this.namespace);
    /*
    this.socket.on('ping', (data) => {
      console.log(this.namespace + " - socket ping", data);
    });
    this.socket.emit('ping', 'foo');
    */
    this.socket.on('message', this._updateQueue);
  }

  _updateQueue(data) {
    console.log(this.namespace + '_updateQueue data', data);
    this.queue.push(data);
  }
}

class SendingSocket {

  // Socket which encodes messages and sends to specified namespace
  constructor(namespaceSuffix) {
    this.namespace = 'openwpm-extension-send-' + namespaceSuffix;
  }

  connect() {
    this.socket = getSocketIoInstance(this.namespace);
    return this.socket;
  }

  send(record) {
    try {
      this.socket.emit('record', record);
      return true;
    } catch (err) {
      console.error(err,err.message);
      return false;
    }
  }

  close() {
    this.socket.close()
  }
}
export { ListeningSocket, SendingSocket };
