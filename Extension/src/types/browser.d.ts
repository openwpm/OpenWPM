declare namespace browser.profileDirIO {
  export function readFile(filename: string): Promise<string>;
  export function writeFile(filename: string, content: string): void;
}

declare namespace browser.sockets {
  export type ConnectionId = number;
  export const onDataReceived: {
    // `data` is a UTF-8 string for the "j"/"u" tags (isJson is true only for
    // "j") and a raw Uint8Array for the "n" (no-serialization) tag, mirroring
    // the Python reader (socket_interface._parse).
    addListener(
      receiver: (
        socketId: number,
        data: string | Uint8Array,
        isJson: boolean,
        connectionId: ConnectionId,
      ) => void,
    ): void;
  };
  export type ServerSocketId = number;
  export function createServerSocket(): Promise<ServerSocketId>;
  export function startListening(id: ServerSocketId): void;
  export type SendingSocketId = number;
  export function createSendingSocket(): Promise<SendingSocketId>;
  export function connect(
    id: SendingSocketId,
    host: string,
    port: number,
  ): void;
  // Returns true on a successful framed write, false if the write failed
  // (e.g. the connection dropped) or the socket id is unknown.
  export function sendData(
    id: SendingSocketId,
    data: string,
    json: boolean,
  ): boolean;
  export function sendResponse(
    connectionId: ConnectionId,
    data: string,
    json: boolean,
  ): boolean;
  export function close(id: SendingSocketId | ServerSocketId): void;
}
