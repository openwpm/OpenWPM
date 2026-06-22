import asyncio
import json
import socket
import struct
import threading
import traceback
from queue import Queue
from typing import Any

import dill


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
        # Track the accept thread and per-connection handler threads so that
        # shutdown() can deterministically wait for all in-flight messages to be
        # drained into `queue` instead of relying on a fixed-duration sleep.
        self._accept_thread = None
        self._conn_threads = []
        self._conn_lock = threading.Lock()
        # Live client sockets, so shutdown() can force blocked recv() calls to
        # return and let the handler threads exit promptly.
        self._clients = set()
        # Set by shutdown() so the accept loop stops instead of treating the
        # wakeup connection as a real client.
        self._shutting_down = False
        if self.verbose:
            print("Server bound to: " + str(self.sock.getsockname()))

    def start_accepting(self):
        """Start the listener thread"""
        thread = threading.Thread(target=self._accept, args=())
        thread.daemon = True  # stops from blocking shutdown
        if self.name is not None:
            thread.name = thread.name + "-" + self.name
        self._accept_thread = thread
        thread.start()

    def _accept(self):
        """Listen for connections and pass handling to a new thread"""
        while True:
            try:
                client, address = self.sock.accept()
            except (ConnectionAbortedError, OSError):
                # The listening socket was closed (shutdown) or a connection
                # request hit an already-closed socket (#278). Stop accepting.
                if self.verbose:
                    print("Listening socket closed; accept loop exiting")
                return
            if self._shutting_down:
                # This is the wakeup connection made by shutdown() to unblock
                # accept(); it carries no log records. Close it and stop.
                try:
                    client.close()
                except OSError:
                    pass
                return
            with self._conn_lock:
                self._clients.add(client)
            thread = threading.Thread(target=self._handle_conn, args=(client, address))
            thread.daemon = True
            with self._conn_lock:
                self._conn_threads.append(thread)
            thread.start()

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
        except (RuntimeError, OSError):
            if self.verbose:
                print("Client socket: " + str(address) + " closed")
        finally:
            with self._conn_lock:
                self._clients.discard(client)
            try:
                client.close()
            except OSError:
                pass

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

    def shutdown(self, timeout=None):
        """Deterministically stop the server and drain in-flight messages.

        Closes the listening socket so no new connections are accepted, then
        shuts down every live client socket so that any handler thread blocked
        in ``recv()`` returns and exits. Finally joins all handler threads.

        Once this returns, every message a client fully sent has been parsed
        into ``self.queue``; callers can drain the queue with no risk of losing
        a tail record and without waiting a fixed duration.
        """
        # Tell the accept loop to stop, then unblock it. Closing the listening
        # socket alone does not reliably wake a thread blocked in accept(), so
        # make a throwaway connection to it: accept() returns, sees the flag,
        # and exits. This must happen while the socket is still listening.
        self._shutting_down = True
        if self._accept_thread is not None:
            try:
                wakeup = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                wakeup.connect(self.sock.getsockname())
                wakeup.close()
            except OSError:
                # Listener already gone; nothing left to wake.
                pass
            self._accept_thread.join(timeout)

        # Now no new connections can be accepted; close the listening socket.
        self.close()

        # Force any handler thread blocked in recv() to wake up and exit by
        # shutting down the read side of each live client socket.
        with self._conn_lock:
            clients = list(self._clients)
        for client in clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                # Already closed / disconnected by the peer.
                pass

        # Wait for all handler threads to finish. Each handler appends every
        # fully-received message to self.queue before it exits, so after these
        # joins the queue holds every such message.
        with self._conn_lock:
            threads = list(self._conn_threads)
        for thread in threads:
            thread.join(timeout)


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
    """Reads a message from the StreamReader
    To safely use this method, you should guard against the exception
    like this:

    .. code-block:: Python

        try:
            record: Tuple[str, Any] = await get_message_from_reader(reader)
        except IncompleteReadError as e:
            print("The underlying socket closed", repr(e))

    :raises:
      IncompleteReadError: If the underlying socket is closed
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
