"""Unit tests for the framed-message reading in ``ClientSocket.receive``.

These exercise the wire framing against a plain TCP peer, so no browser,
extension xpi, or storage server is needed.
"""

import json
import socket
import struct
import threading

import pytest

from openwpm.socket_interface import ClientSocket

pytestmark = pytest.mark.pyonly


def frame(obj: object, serialization: bytes = b"j") -> bytes:
    """Encode ``obj`` the way the extension's socket API frames a reply."""
    payload = json.dumps(obj).encode("utf-8")
    return struct.pack(">Lc", len(payload), serialization) + payload


@pytest.fixture
def connected_pair():
    """Yield ``(peer_conn, client)`` for a connected localhost TCP pair."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("localhost", 0))
    listener.listen(1)
    host, port = listener.getsockname()

    client = ClientSocket(serialization="json")
    client.connect(host, port)
    peer_conn, _ = listener.accept()
    listener.close()
    try:
        yield peer_conn, client
    finally:
        peer_conn.close()
        client.close()


def test_receive_single_frame(connected_pair):
    peer, client = connected_pair
    peer.sendall(frame({"action": "FinalizeAck", "visit_id": 7}))
    assert client.receive(timeout=2.0) == {"action": "FinalizeAck", "visit_id": 7}


def test_receive_two_frames_in_one_chunk(connected_pair):
    """A read that overshoots into the next frame keeps the surplus buffered."""
    peer, client = connected_pair
    peer.sendall(frame({"visit_id": 1}) + frame({"visit_id": 2}))
    assert client.receive(timeout=2.0) == {"visit_id": 1}
    assert client.receive(timeout=2.0) == {"visit_id": 2}


def test_partial_frame_timeout_does_not_desync(connected_pair):
    """A timeout part-way through a frame must not corrupt the next read."""
    peer, client = connected_pair
    full = frame({"action": "FinalizeAck", "visit_id": 9})

    peer.sendall(full[:3])  # only part of the 5-byte header
    with pytest.raises(socket.timeout):
        client.receive(timeout=0.2)

    peer.sendall(full[3:])  # the remainder arrives later
    assert client.receive(timeout=2.0) == {"action": "FinalizeAck", "visit_id": 9}


def test_receive_restores_prior_socket_timeout(connected_pair):
    peer, client = connected_pair
    client.sock.settimeout(3.5)
    peer.sendall(frame({"ok": True}))
    client.receive(timeout=1.0)
    assert client.sock.gettimeout() == 3.5


def test_receive_raises_when_peer_closes(connected_pair):
    peer, client = connected_pair
    peer.close()
    with pytest.raises(RuntimeError):
        client.receive(timeout=2.0)


def test_receive_handles_frame_split_across_recv_calls(connected_pair):
    """A frame delivered in trickled writes is reassembled into one message."""
    peer, client = connected_pair
    full = frame({"action": "FinalizeAck", "visit_id": 42})

    def trickle():
        for byte in full:
            peer.sendall(bytes([byte]))

    sender = threading.Thread(target=trickle)
    sender.start()
    try:
        assert client.receive(timeout=5.0) == {
            "action": "FinalizeAck",
            "visit_id": 42,
        }
    finally:
        sender.join()
