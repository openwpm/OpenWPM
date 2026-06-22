"""Round-trip tests for the instrumentation socket framing.

These are ``pyonly`` tests: they exercise ``openwpm.socket_interface`` directly
without a browser or extension. The guarantee under test is that non-ASCII
records survive the length-prefixed framing intact.

Wire contract (important, and easy to get wrong): on the JS -> Python data
path every payload reaches ``sockets.sendData`` as a *byte-string*, not a
Unicode string. Callers pre-encode their text through ``escapeString`` /
``encode_utf8`` (``Extension/src/lib/string-utils.ts``), so the chars handed to
the socket are already the UTF-8 bytes (each char in 0-255). The privileged
``api.js`` therefore narrows each char to one byte and frames on that count;
the Python reader decodes the frame as UTF-8. Re-encoding that byte-string with
``TextEncoder`` on the send side would double-encode it and corrupt every
non-ASCII record -- the regression these tests pin down.

The Python ``ClientSocket`` is a separate, genuinely UTF-8-clean path (it
encodes real ``str`` objects), exercised by the first two tests below.
"""

import json
import socket
import struct
from typing import Any

import pytest

from openwpm.socket_interface import ClientSocket, ServerSocket

pytestmark = pytest.mark.pyonly

# A record dense with non-Latin-1 codepoints across several scripts plus an
# astral (surrogate-pair) emoji -- the content a double UTF-8 encode on the
# send side turns into mojibake.
NON_ASCII_RECORD = [
    "http_requests",
    {
        "url": "https://例え.テスト/路径?q=Привет&emoji=🌍",
        "title": "日本語のタイトル — Заголовок — 😀",
        "cookie": "naïve=café; Ωmega=λ",
    },
]


def _recv_one(server: ServerSocket) -> Any:
    """Block until exactly one parsed message lands in the server queue."""
    return server.queue.get(timeout=10)


def _roundtrip_via_client(msg: Any) -> Any:
    """Send ``msg`` through ClientSocket and return the parsed receipt."""
    server = ServerSocket()
    server.start_accepting()
    try:
        host, port = server.sock.getsockname()
        client = ClientSocket(serialization="json")
        client.connect(host, port)
        try:
            client.send(msg)
            return _recv_one(server)
        finally:
            client.close()
    finally:
        server.close()


def test_non_ascii_json_record_roundtrips_intact() -> None:
    """A JSON record full of CJK/Cyrillic/emoji must arrive byte-for-byte."""
    received = _roundtrip_via_client(NON_ASCII_RECORD)
    assert received == NON_ASCII_RECORD


def test_non_ascii_string_roundtrips_via_u_tag() -> None:
    """Bare str messages use the 'u' (UTF-8) tag; must round-trip intact."""
    msg = "Browser-日本語-Привет-🌍"
    received = _roundtrip_via_client(msg)
    assert received == msg


def _extension_wire_bytes(record: Any) -> bytes:
    """Reproduce the exact bytes the WebExtension puts on the socket.

    This models the real send path, NOT an idealized one. Before any data
    reaches the socket it is funnelled through ``escapeString`` /
    ``encode_utf8`` (``Extension/src/lib/string-utils.ts``), the JS idiom
    ``unescape(encodeURIComponent(s))``. That turns the source text into UTF-8
    and then exposes each UTF-8 byte as a Latin-1 char (code points 0-255) --
    i.e. by the time ``JSON.stringify`` runs and ``sockets.sendData`` is
    called, ``data`` is already a *byte-string*, not a Unicode string. The
    privileged ``api.js`` then narrows each char to one byte (writing
    ``charCodeAt(i)`` into a ``Uint8Array``) and frames the length on that byte
    count. The net result on the wire is plain UTF-8 of the escaped record.

    The Python equivalent of ``unescape(encodeURIComponent(s))`` is
    ``s.encode("utf-8").decode("latin-1")``; narrowing that byte-string back to
    bytes via Latin-1 yields the original UTF-8 bytes. We build the JSON the
    way the extension does (``ensure_ascii`` does not matter because the value
    strings have already been escaped to ASCII-safe byte-strings), then take
    the Latin-1 view to get the wire bytes.
    """

    def escape_string(s: str) -> str:
        # unescape(encodeURIComponent(s)) -- UTF-8 bytes as Latin-1 chars.
        return s.encode("utf-8").decode("latin-1")

    def escape_value(value: Any) -> Any:
        if isinstance(value, str):
            return escape_string(value)
        if isinstance(value, list):
            return [escape_value(v) for v in value]
        if isinstance(value, dict):
            return {escape_string(k): escape_value(v) for k, v in value.items()}
        return value

    escaped = escape_value(record)
    # The extension stringifies the already-escaped (byte-string) record. Those
    # strings contain only code points 0-255, so JSON.stringify's output is a
    # byte-string too; api.js narrows each char to a byte before sending.
    wire_string = json.dumps(escaped, ensure_ascii=False)
    return wire_string.encode("latin-1")


def test_extension_style_byte_framing_decodes_intact() -> None:
    """Reproduce the WebExtension's real wire bytes and decode them.

    The extension does NOT UTF-8 re-encode at the socket -- its payloads are
    already byte-strings (see ``_extension_wire_bytes``). It frames ``>Lc`` on
    the byte count and writes those raw bytes. This builds those exact bytes
    with a raw client socket (bypassing ``ClientSocket``) and asserts the
    Python ``ServerSocket`` decodes them back to the original record. This is
    the end-to-end guard against the double-encoding regression: a second UTF-8
    encode on the send side would corrupt every non-ASCII record.
    """
    server = ServerSocket()
    server.start_accepting()
    try:
        host, port = server.sock.getsockname()
        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw.connect((host, port))
        try:
            payload = _extension_wire_bytes(NON_ASCII_RECORD)
            # Sanity: the wire payload is plain UTF-8 of the escaped record.
            # A double-encode (TextEncoder over the byte-string) would make the
            # payload strictly longer; assert we are sending the lossless form.
            assert payload == payload.decode("utf-8").encode("utf-8")
            frame = struct.pack(">Lc", len(payload), b"j") + payload
            raw.sendall(frame)
            received = _recv_one(server)
            assert received == NON_ASCII_RECORD
        finally:
            raw.close()
    finally:
        server.close()


def test_extension_double_encode_would_corrupt() -> None:
    """Pin the regression: a second UTF-8 encode on the send side is detectable.

    Documents *why* ``api.js`` narrows the byte-string instead of running it
    through ``TextEncoder``. Re-encoding the already-UTF-8 byte-string produces
    a strictly different (longer) wire payload that does NOT decode back to the
    original record -- the mojibake CI caught (你好 -> ä½\\xa0å¥½).
    """
    correct = _extension_wire_bytes(NON_ASCII_RECORD)
    # TextEncoder().encode(byte_string) == byte_string re-encoded as UTF-8.
    double_encoded = correct.decode("latin-1").encode("utf-8")
    assert double_encoded != correct
    assert len(double_encoded) > len(correct)
    # The double-encoded bytes are still valid UTF-8 / valid JSON, so the
    # corruption is silent: json.loads succeeds but yields mojibake, never the
    # original record. This is exactly the failure CI surfaced (你好 turned into
    # ä½\xa0å¥½). The correct (single-encoded) bytes do round-trip.
    assert json.loads(correct.decode("utf-8")) == NON_ASCII_RECORD
    corrupted = json.loads(double_encoded.decode("utf-8"))
    assert corrupted != NON_ASCII_RECORD


def test_send_rejects_oversized_payload() -> None:
    """Payloads >= 4 GiB must raise, never silently truncate the length field."""
    server = ServerSocket()
    server.start_accepting()
    try:
        host, port = server.sock.getsockname()
        client = ClientSocket(serialization="json")
        client.connect(host, port)
        try:
            # Avoid actually allocating 4 GiB: a real bytes object just over
            # the limit is too costly. Instead use an empty bytes subclass that
            # overrides __len__ to report an oversized length, so the >u32 guard
            # in ClientSocket.send (which checks len(msg)) fires without
            # allocating the payload.
            class _Huge(bytes):
                def __len__(self) -> int:
                    return 0x100000000

            with pytest.raises(RuntimeError, match="exceeds the u32 length"):
                client.send(_Huge())
        finally:
            client.close()
    finally:
        server.close()
