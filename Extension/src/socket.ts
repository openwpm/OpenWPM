/* eslint-disable max-classes-per-file */

const DataReceiver = {
  callbacks: new Map(),
  onDataReceived: (
    aSocketId: number,
    aData: string | Uint8Array,
    aJSON: boolean,
  ): void => {
    if (!DataReceiver.callbacks.has(aSocketId)) {
      return;
    }
    // aJSON is only ever true for the "j" tag, whose payload is a UTF-8
    // string; "n" arrives as a raw Uint8Array and is handed through untouched.
    const data = aJSON ? JSON.parse(aData as string) : aData;
    DataReceiver.callbacks.get(aSocketId)(data);
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
      // sendData resolves to false (rather than throwing) when the framed
      // write fails, e.g. the StorageController connection dropped. Surface
      // that instead of swallowing it: there is no reconnect, so a silent
      // false here is permanent per-browser data loss for the rest of the
      // visit. We log rather than throw to avoid breaking fire-and-forget
      // callers; the browser console error is the observability hook.
      const ok = browser.sockets.sendData(this.id, aData, !!aJSON);
      if (ok === false) {
        console.error(
          `SendingSocket.send: framed write failed on socket ${this.id}; ` +
            `record dropped (no reconnect).`,
        );
        return false;
      }
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
