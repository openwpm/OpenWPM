declare namespace browser.profileDirIO {
  export function readFile(filename: string): Promise<string>;
  export function writeFile(filename: string, content: string): void;
}

declare namespace browser.sockets {
  export const onDataReceived: {
    addListener(
      receiver: (socketId: number, data: string, isJson: boolean) => void,
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
  export function sendData(
    id: SendingSocketId,
    data: string,
    json: boolean,
  ): void;
  export function close(id: SendingSocketId | ServerSocketId): void;
}
