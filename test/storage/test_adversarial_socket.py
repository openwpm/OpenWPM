"""Adversarial wire-protocol tests against the real StorageController server.

The StorageController exposes an ``asyncio`` TCP server speaking the
length-prefixed framing of ``openwpm/socket_interface.py`` (4-byte big-endian
length + 1-byte serialization tag + body). Untrusted/buggy clients (a crashing
extension, a half-open connection, a corrupted frame) can send arbitrary bytes
at it.

PROPERTY: the server must degrade gracefully - a hostile or truncated frame may
kill *that one connection*, but the server must keep accepting new connections,
must not hang, and must not lose data for well-behaved clients.

All of these are browser-free: we open raw sockets to the controller's listen
address and verify a subsequent good visit still completes.
"""

import json
import socket
import struct
import time
from typing import List, Tuple

import pytest

from openwpm.storage.in_memory_storage import MemoryStructuredProvider
from openwpm.storage.storage_controller import DataSocket, StorageControllerHandle
from openwpm.storage.storage_providers import TableName
from openwpm.types import VisitId

pytestmark = pytest.mark.pyonly


def _send_raw(addr: Tuple[str, int], payload: bytes) -> None:
    """Open a raw socket, dump ``payload``, briefly wait, then close."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(addr)
    try:
        s.sendall(payload)
    except OSError:
        # The server may close on us for some payloads; that is acceptable.
        pass
    time.sleep(0.3)
    s.close()


def _hostile_frames() -> List[Tuple[str, bytes]]:
    one_tuple = json.dumps(["only_one_element"]).encode("utf-8")
    return [
        # Unknown serialization tag 'X' with a 3-byte body.
        ("unknown_serialization", struct.pack(">Lc", 3, b"X") + b"abc"),
        # Length prefix claims 100 bytes but only 2 are sent, then EOF.
        ("truncated_body", struct.pack(">Lc", 100, b"j") + b"ab"),
        # Absurd length prefix (2 GiB) with no body - must not allocate/hang.
        ("oversized_length_prefix", struct.pack(">Lc", 2**31, b"j")),
        # Fewer than the 5 header bytes, then EOF.
        ("short_header", b"\x01\x02"),
        # Valid JSON frame but the record is a 1-element list (wrong arity);
        # the controller logs "Query is not the correct length" and skips.
        ("wrong_arity_record", struct.pack(">Lc", len(one_tuple), b"j") + one_tuple),
        # Valid JSON frame whose body is not even a sequence.
        (
            "non_sequence_record",
            (lambda b: struct.pack(">Lc", len(b), b"j") + b)(b"42"),
        ),
    ]


@pytest.mark.usefixtures("adversarial_mp_logger")
@pytest.mark.parametrize(
    "name,payload", _hostile_frames(), ids=[n for n, _ in _hostile_frames()]
)
def test_server_survives_hostile_frame(name: str, payload: bytes) -> None:
    """After a single hostile frame on its own connection, the controller must
    still accept a new connection and complete a good visit.
    """
    handle = StorageControllerHandle(MemoryStructuredProvider(), None)
    handle.launch()
    assert handle.listener_address is not None
    addr = handle.listener_address

    _send_raw(addr, payload)

    sock = DataSocket(addr, f"good-after-{name}")
    good = VisitId(0xBEEF)
    sock.store_record(TableName("site_visits"), good, {"site_url": "ok"})
    sock.finalize_visit_id(good, success=True)
    sock.close()

    start = time.time()
    handle.shutdown()
    elapsed = time.time() - start
    assert elapsed < 60, f"shutdown hung after hostile frame {name} ({elapsed:.1f}s)"

    seen = handle.get_new_completed_visits()
    assert good in {vid for vid, _ in seen}, (
        f"server did not survive hostile frame {name}; good visit lost; " f"seen={seen}"
    )


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_server_survives_abrupt_disconnect_mid_message() -> None:
    """A client that connects, sends its name, sends a partial record header,
    then drops the connection must not wedge the controller.
    """
    handle = StorageControllerHandle(MemoryStructuredProvider(), None)
    handle.launch()
    assert handle.listener_address is not None
    addr = handle.listener_address

    # Send a valid client-name frame, then half of a record header, then close.
    name_body = json.dumps("evil-client").encode("utf-8")
    payload = struct.pack(">Lc", len(name_body), b"j") + name_body
    payload += b"\x00\x00"  # 2 of the 5 header bytes of the next message
    _send_raw(addr, payload)

    sock = DataSocket(addr, "good-after-disconnect")
    good = VisitId(0xD00D)
    sock.store_record(TableName("site_visits"), good, {"site_url": "ok"})
    sock.finalize_visit_id(good, success=True)
    sock.close()

    handle.shutdown()
    seen = handle.get_new_completed_visits()
    assert good in {vid for vid, _ in seen}, f"controller wedged; seen={seen}"
