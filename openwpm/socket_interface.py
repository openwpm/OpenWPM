import asyncio
import json
import socket
import struct
import threading
import traceback
from queue import Queue
from typing import Any

import dill

# TODO - Implement a cleaner shutdown for server socket
# see: https://stackoverflow.com/a/1148237


class ServerSocket:
    """
    A server socket to receive and process string messages
    from client sockets to a central queue
    """

    def __init__(self, name=None, verbose=False):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("localhost", 0))
        self.sock.listen(10)  # queue a max of n connect requests
        self.verbose = verbose
        self.name = name
        self.queue = Queue()
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
                thread = threading.Thread(
                    target=self._handle_conn, args=(client, address)
                )
                thread.daemon = True
                thread.start()
            except ConnectionAbortedError:
                # Workaround for #278
                print("A connection establish request was performed on a closed socket")
                return

    def _handle_conn(self, client, address):
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
                msg = self.receive_msg(client, 5)
                msglen, serialization = struct.unpack(">Lc", msg)
                if self.verbose:
                    print(
                        "Received message, length %d, serialization %r"
                        % (msglen, serialization)
                    )
                msg = self.receive_msg(client, msglen)
                try:
                    msg = _parse(serialization, msg)
                except (UnicodeDecodeError, ValueError) as e:
                    print(
                        "Error de-serializing message: %s \n %s"
                        % (msg, traceback.format_exc(e))
                    )
                    continue
                self._put_into_queue(msg)
        except RuntimeError:
            if self.verbose:
                print("Client socket: " + str(address) + " closed")

    def _put_into_queue(self, msg):
        """Put the parsed message into a queue from where it can be read by consumers"""
        self.queue.put(msg)

    def receive_msg(self, client, msglen):
        msg = b""
        while len(msg) < msglen:
            chunk = client.recv(msglen - len(msg))
            if not chunk:
                raise RuntimeError("socket connection broken")
            msg = msg + chunk
        return msg

    def close(self):
        self.sock.close()


class ClientSocket:
    """A client socket for sending messages"""

    def __init__(self, serialization="json", verbose=False):
        """`serialization` specifies the type of serialization to use for
        non-string messages. Supported formats:
            * 'json' uses the json module. Cross-language support. (default)
            * 'dill' uses the dill pickle module. Python only.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if serialization != "json" and serialization != "dill":
            raise ValueError("Unsupported serialization type: %s" % serialization)
        self.serialization = serialization
        self.verbose = verbose

    def connect(self, host, port):
        if self.verbose:
            print("Connecting to: %s:%i" % (host, port))
        self.sock.connect((host, port))

    def send(self, msg):
        """
        Sends an arbitrary python object to the connected socket. Serializes
        using dill if not string, and prepends msg len (4-bytes) and
        serialization type (1-byte).
        """
        if isinstance(msg, bytes):
            serialization = b"n"
        elif isinstance(msg, str):
            serialization = b"u"
            msg = msg.encode("utf-8")
        elif self.serialization == "dill":
            msg = dill.dumps(msg, dill.HIGHEST_PROTOCOL)
            serialization = b"d"
        elif self.serialization == "json":
            msg = json.dumps(msg).encode("utf-8")
            serialization = b"j"
        else:
            raise ValueError(
                "Unsupported serialization type set: %s" % self.serialization
            )
        if self.verbose:
            print("Sending message with serialization %s" % serialization)

        # prepend with message length
        msg = struct.pack(">Lc", len(msg), serialization) + msg
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def close(self):
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
    msg = await reader.readexactly(5)
    msglen, serialization = struct.unpack(">Lc", msg)
    msg = await reader.readexactly(msglen)
    return _parse(serialization, msg)


def _parse(serialization: bytes, msg: bytes) -> Any:
    if serialization == b"n":
        return msg
    if serialization == b"d":  # dill serialization
        return dill.loads(msg)
    if serialization == b"j":  # json serialization
        return json.loads(msg.decode("utf-8"))
    if serialization == b"u":  # utf-8 serialization
        return msg.decode("utf-8")
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
        sock = ClientSocket(serialization=serialization)
        sock.connect(host, int(port))
        msg = None

        # some predefined messages
        tuple_msg = ("hello", "world")
        list_msg = ["hello", "world"]
        dict_msg = {"hello": "world"}

        def function_msg(x):
            return x

        # read user input
        while msg != "quit":
            msg = input("Enter a message to send:\n")
            if msg == "tuple":
                sock.send(tuple_msg)
            elif msg == "list":
                sock.send(list_msg)
            elif msg == "dict":
                sock.send(dict_msg)
            elif msg == "function":
                sock.send(function_msg)
            else:
                sock.send(msg)
        sock.close()


if __name__ == "__main__":
    main()
