/* eslint-disable max-classes-per-file */

export type RespondFn = (msg: any) => void;

const DataReceiver = {
  callbacks: new Map(),
  onDataReceived: (
    aSocketId: number,
    aData: string,
    aJSON: boolean,
    aConnectionId: number,
  ): void => {
    if (!DataReceiver.callbacks.has(aSocketId)) {
      return;
    }
    if (aJSON) {
      aData = JSON.parse(aData);
    }
    const respond: RespondFn = (msg: any) => {
      browser.sockets.sendResponse(aConnectionId, JSON.stringify(msg), true);
    };
    DataReceiver.callbacks.get(aSocketId)(aData, respond);
  },
};

browser.sockets.onDataReceived.addListener(DataReceiver.onDataReceived);

export class ListeningSocket {
  callback: any;
  port: number;
  constructor(callback) {
    this.callback = callback;
  }

  async startListening() {
    this.port = await browser.sockets.createServerSocket();
    DataReceiver.callbacks.set(this.port, this.callback);
    browser.sockets.startListening(this.port);
    console.log("Listening on port " + this.port);
  }
}

export class SendingSocket {
  id: number;

  async connect(host: string, port: number) {
    this.id = await browser.sockets.createSendingSocket();
    browser.sockets.connect(this.id, host, port);
    console.log(`Connected to ${host}:${port}`);
  }

  send(aData: string, aJSON = true): boolean {
    try {
      browser.sockets.sendData(this.id, aData, !!aJSON);
      return true;
    } catch (err) {
      console.error(err, err.message);
      return false;
    }
  }

  close(): void {
    browser.sockets.close(this.id);
  }
}
