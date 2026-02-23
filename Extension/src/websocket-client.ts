/**
 * WebSocket client for communicating with the Python WebSocket bridge.
 *
 * Replaces the old 3-socket setup (SendingSocket→StorageController,
 * SendingSocket→MPLogger, ListeningSocket for commands) with a single
 * bidirectional WebSocket connection.
 */

type CommandCallback = (data: any) => void;

export class OpenWPMWebSocket {
  private ws: WebSocket | null = null;
  private commandCallback: CommandCallback | null = null;
  private url: string = "";
  private connected: boolean = false;

  constructor(commandCallback: CommandCallback) {
    this.commandCallback = commandCallback;
  }

  connect(port: number): Promise<void> {
    this.url = `ws://127.0.0.1:${port}`;
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log(`WebSocket connected to ${this.url}`);
        this.connected = true;
        resolve();
      };

      this.ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        if (!this.connected) {
          reject(new Error(`WebSocket connection failed to ${this.url}`));
        }
      };

      this.ws.onclose = () => {
        console.log("WebSocket connection closed");
        this.connected = false;
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "command" && this.commandCallback) {
            this.commandCallback(msg);
          } else {
            console.warn("Unknown WebSocket message type:", msg.type);
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      };
    });
  }

  /**
   * Send a data record to be stored by the StorageController.
   */
  sendRecord(table: string, record: any): boolean {
    return this._send({ type: "data", table, record });
  }

  /**
   * Send a log message to the Python logging system.
   */
  sendLog(level: number, msg: string): boolean {
    return this._send({ type: "log", level, msg });
  }

  private _send(msg: object): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected, cannot send");
      return false;
    }
    try {
      this.ws.send(JSON.stringify(msg));
      return true;
    } catch (err) {
      console.error("WebSocket send error:", err);
      return false;
    }
  }

  close(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connected = false;
  }
}
