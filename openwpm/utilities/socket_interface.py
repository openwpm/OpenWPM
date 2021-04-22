import asyncio
import json
import socket
import struct
import threading
import traceback
from queue import Empty, Queue
from typing import Any, Dict, Literal, Optional

import dill

# TODO - Implement a cleaner shutdown for server socket
# see: https://stackoverflow.com/a/1148237


class AbstractSocket:
    def __init__(
        self, serialization: Optional[Literal["json", "dill"]], verbose: bool
    ) -> None:
        self.verbose = verbose
        if serialization and serialization != "json" and serialization != "dill":
            raise ValueError("Unsupported serialization type: %s" % serialization)
        self.serialization = serialization

    def read_message(self, client: socket.socket) -> Optional[Any]:
        header = recv_chunk(client, 5)
        message_length, serialization = struct.unpack(">Lc", header)
        if self.verbose:
            print(
                "Received message, length %d, serialization %r"
                % (message_length, serialization)
            )
        chunk = recv_chunk(client, message_length)
        try:
            message = _parse(serialization, chunk)
        except (UnicodeDecodeError, ValueError):
            print(
                "Error de-serializing message: %r \n %s"
                % (chunk, traceback.format_exc())
            )
            return None
        return message

    def send_message(self, sock: socket.socket, message: Any) -> None:
        """
        Sends an arbitrary python object to the connected socket. Serializes
        using dill if not string, and prepends message len (4-bytes) and
        serialization type (1-byte).
        """
        if isinstance(message, bytes):
            prefix = b"n"
        elif isinstance(message, str):
            prefix = b"u"
            message = message.encode("utf-8")
        elif self.serialization == "dill":
            message = dill.dumps(message, dill.HIGHEST_PROTOCOL)
            prefix = b"d"
        elif self.serialization == "json":
            message = json.dumps(message).encode("utf-8")
            prefix = b"j"
        else:
            raise ValueError(
                "Unsupported serialization type set: %s" % self.serialization
            )
        if self.verbose:
            print("Sending message with serialization %r" % prefix)

        # prepend with message length
        message = struct.pack(">Lc", len(message), prefix) + message
        total_sent = 0
        while total_sent < len(message):
            sent = sock.send(message[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent = total_sent + sent


class ServerSocket(AbstractSocket):
    """
    A server socket to receive and process string messages
    from client sockets to a central queue
    """

    def __init__(
        self,
        name: Optional[str] = None,
        serialization: Optional[Literal["json", "dill"]] = "json",
        verbose: bool = False,
    ) -> None:
        super().__init__(serialization, verbose)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("localhost", 0))
        self.sock.listen(10)  # queue a max of n connect requests
        self.name = name
        self.recv_msg_queue: Queue[Any] = Queue()
        self.out_msg_queues: Dict[Any, Queue] = {}
        """Maps from address info to queue to the handler thread"""
        if self.verbose:
            print("Server bound to: " + str(self.sock.getsockname()))

    def start_accepting(self):
        """ Start the listener thread """
        thread = threading.Thread(target=self._accept, args=())
        thread.daemon = True  # stops from blocking shutdown
        if self.name is not None:
            thread.name = thread.name + "-" + self.name
        thread.start()

    def _accept(self):
        """ Listen for connections and pass handling to a new thread """
        while True:
            try:
                (client, address) = self.sock.accept()
                queue = Queue()
                self.out_msg_queues[address] = queue
                thread = threading.Thread(
                    target=self._handle_conn, args=(client, address, queue)
                )
                thread.daemon = True
                thread.start()
            except ConnectionAbortedError:
                # Workaround for #278
                print("A connection establish request was performed on a closed socket")
                return

    def _handle_conn(self, client: socket.socket, address: Any, queue: Queue) -> None:
        """
        Receive messages and pass to queue. Messages are prefixed with
        a 4-byte integer to specify the message length and 1-byte character
        to indicate the type of serialization applied to the message.

        Supported serialization formats:
            'n' : no serialization
            'u' : Unicode string in UTF-8
            'd' : dill pickle
            'j' : json
        """
        if self.verbose:
            print("Thread: %s connected to: %s" % (threading.current_thread(), address))
        try:
            while True:
                if (msg := self.read_message(client)) is not None:
                    self.recv_msg_queue.put(msg)
                try:
                    send_msg = queue.get_nowait()
                    self.send_message(self.sock, send_msg)
                except Empty:
                    pass

        except RuntimeError:
            if self.verbose:
                print("Client socket: " + str(address) + " closed")

    def broadcast(self, msg: Any) -> None:
        for queue in self.out_msg_queues.values():
            queue.put(msg)

    def close(self) -> None:
        self.sock.close()


def recv_chunk(client: socket.socket, chunk_length: int) -> bytes:
    chunk = b""
    while len(chunk) < chunk_length:
        part = client.recv(chunk_length - len(chunk))
        if not part:
            raise RuntimeError("socket connection broken")
        chunk = chunk + part
    return chunk


class ClientSocket(AbstractSocket):
    """A client socket for sending messages"""

    def __init__(
        self, serialization: Literal["json", "dill"] = "json", verbose: bool = False
    ) -> None:
        """`serialization` specifies the type of serialization to use for
        non-string messages. Supported formats:
            * 'json' uses the json module. Cross-language support. (default)
            * 'dill' uses the dill pickle module. Python only.
        """
        super().__init__(serialization, verbose)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host: str, port: int) -> None:
        if self.verbose:
            print("Connecting to: %s:%i" % (host, port))
        self.sock.connect((host, port))

    def send(self, msg: Any) -> None:
        self.send_message(self.sock, msg)

    def recv(self) -> Any:
        return self.read_message(self.sock)

    def close(self) -> None:
        self.sock.close()


async def get_message_from_reader(reader: asyncio.StreamReader) -> Any:
    """
    Reads a message from the StreamReader
    :exception IncompleteReadError if the underlying socket is closed

    To safely use this method, you should guard against the exception
    like this:
    ```
        try:
            record: Tuple[str, Any] = await get_message_from_reader(reader)
        except IncompleteReadError as e:
            print("The underlying socket closed", repr(e))
    ```
    """
    message = await reader.readexactly(5)
    message_length, serialization = struct.unpack(">Lc", message)
    message = await reader.readexactly(message_length)
    return _parse(serialization, message)


def _parse(serialization: bytes, message: bytes) -> Any:
    if serialization == b"n":
        return message
    if serialization == b"d":  # dill serialization
        return dill.loads(message)
    if serialization == b"j":  # json serialization
        return json.loads(message.decode("utf-8"))
    if serialization == b"u":  # utf-8 serialization
        return message.decode("utf-8")
    raise ValueError("Unknown Encoding")


def main():
    import sys

    # Just for testing
    if sys.argv[1] == "s":
        ssock = ServerSocket(verbose=True)
        ssock.start_accepting()
        input("Press enter to exit...")
        ssock.close()
    elif sys.argv[1] == "c":
        host = input("Enter the host name:\n")
        port = input("Enter the port:\n")
        serialization = input("Enter the serialization type (default: 'json'):\n")
        if serialization == "":
            serialization = "json"
        assert serialization
        sock = ClientSocket(serialization=serialization, verbose=True)
        sock.connect(host, int(port))
        message = None

        # some predefined messages
        tuple_message = ("hello", "world")
        list_message = ["hello", "world"]
        dict_message = {"hello": "world"}

        def function_message(x):
            return x

        # read user input
        while message != "quit":
            message = input("Enter a message to send:\n")
            if message == "tuple":
                sock.send(tuple_message)
            elif message == "list":
                sock.send(list_message)
            elif message == "dict":
                sock.send(dict_message)
            elif message == "function":
                sock.send(function_message)
            else:
                sock.send(message)
        sock.close()


if __name__ == "__main__":
    main()
