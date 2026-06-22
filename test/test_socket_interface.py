"""Unit tests for openwpm.socket_interface.

Focus on ServerSocket.shutdown()'s deterministic drain: after shutdown()
returns, every message a client fully sent must already be in the queue, with
no fixed-duration sleep involved (Phase-3 R5 of the socket-reliability thread).
"""

from queue import Empty

import pytest

from openwpm.socket_interface import ClientSocket, ServerSocket


def _make_connected_pair():
    server = ServerSocket(name="test")
    server.start_accepting()
    host, port = server.sock.getsockname()
    client = ClientSocket(serialization="json")
    client.connect(host, port)
    return server, client


def test_shutdown_drains_all_sent_records():
    """All messages a client fully sent are queued after shutdown() returns."""
    server, client = _make_connected_pair()

    n = 500
    for i in range(n):
        client.send({"i": i})
    # Client has finished sending and closes its end, mirroring a child process
    # that has logged everything and exited before MPLogger.close().
    client.close()

    # Deterministic drain: bounded join so a wedged handler can't hang the test.
    server.shutdown(timeout=30)

    received = []
    while not server.queue.empty():
        received.append(server.queue.get())

    assert len(received) == n
    assert sorted(r["i"] for r in received) == list(range(n))


def test_shutdown_with_open_client_connection():
    """shutdown() still completes promptly when the client never closes.

    The handler thread is blocked in recv(); shutdown() must force it to exit by
    shutting down the client socket, then join it. This mirrors the parent
    process's own still-attached socket handler at MPLogger.close() time.
    """
    server, client = _make_connected_pair()

    for i in range(10):
        client.send({"i": i})

    # Note: client connection left open on purpose.
    server.shutdown(timeout=30)

    received = []
    while not server.queue.empty():
        received.append(server.queue.get())
    assert sorted(r["i"] for r in received) == list(range(10))

    # The accept thread and all handler threads must have exited.
    assert not server._accept_thread.is_alive()
    for thread in server._conn_threads:
        assert not thread.is_alive()

    client.close()


def test_shutdown_no_clients():
    """shutdown() is a no-op-safe drain when nothing ever connected."""
    server = ServerSocket(name="test")
    server.start_accepting()
    server.shutdown(timeout=30)
    with pytest.raises(Empty):
        server.queue.get_nowait()
