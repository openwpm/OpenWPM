class WebSocket {

  // Socket which encodes messages and sends to specified namespace
  constructor(namespaceSuffix) {
    this.namespace = 'openwpm-extension-send-' + namespaceSuffix;
    this.socket = new WebSocket("ws://127.0.0.1:7799/");
  }

  send(record) {
    try {
      this.socket.send(record);
      return true;
    } catch (err) {
      console.error(err, err.message);
      return false;
    }
  }

  close() {
    this.socket.close()
  }
}

export {WebSocket};