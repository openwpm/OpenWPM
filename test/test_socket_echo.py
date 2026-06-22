"""Single-process, end-to-end test of the extension->Python wire protocol.

This is the real-code counterpart to ``test/test_socket_interface.py`` (which is
``pyonly`` and re-implements the extension's byte framing in Python). Here we run
the *actual* privileged ``sockets`` API + ``socket.ts`` + ``socket_interface.py``
paths that PR #1180 hardened, without standing up a ``BrowserManager`` or a
``StorageController``.

How it works:
  * The extension's ``echo_mode`` (a test-only ``BrowserParams`` flag) makes the
    WebExtension skip every instrument and instead emit a fixed pair of synthetic
    payloads over its already-connected storage ``SendingSocket``:
      (A) a ``j`` (JSON) record carrying non-ASCII text, and
      (B) an ``n`` (raw byte-string) payload.
  * This test binds two real ``ServerSocket``s in-process (one standing in for the
    StorageController, one for the logger), launches Firefox via
    ``deploy_firefox`` directly, and reads the echoed payloads back off the
    storage server's queue.
  * It then asserts exact round-trip fidelity: the ``j`` record decodes back to
    the same Unicode object; the ``n`` frame comes back as raw ``bytes``
    unchanged. A double-UTF-8-encode regression on the send side (the bug #1180
    fixed) would turn the non-ASCII content into mojibake and fail (A).

The synthetic payloads are defined in ``Extension/src/echo.ts``; the constants
below mirror them and are the source of truth for the assertions.
"""

import json

import pytest
from multiprocess import Queue

from openwpm.config import BrowserParamsInternal, ManagerParamsInternal
from openwpm.deploy_browsers import deploy_firefox
from openwpm.socket_interface import ServerSocket
from openwpm.types import BrowserId

# Mirrors ``ECHO_J_RECORD`` in Extension/src/echo.ts. The extension escapes each
# string through ``escapeString`` (UTF-8 bytes as Latin-1 chars), ``JSON.stringify``s
# it, and sends it with the ``j`` tag; the Python reader decodes the frame as
# UTF-8 and ``json.loads`` returns exactly this object.
ECHO_J_RECORD = [
    "echo",
    {
        "s": "你好 — Привет — 🌍",
        "n": "naïve café λ — 例え",
    },
]

# Mirrors ``ECHO_N_TEXT`` in Extension/src/echo.ts. On the wire this is its UTF-8
# bytes (sent via the ``n`` tag); ``ServerSocket`` returns ``n`` frames as raw
# ``bytes``, untouched.
ECHO_N_TEXT = "café/🌍"
EXPECTED_N_BYTES = ECHO_N_TEXT.encode("utf-8")


@pytest.mark.usefixtures("xpi")
def test_socket_echo_roundtrips_through_real_extension(tmp_path):
    """The extension serializes both a ``j`` and an ``n`` payload through the real
    privileged ``sockets`` API; this test reads them back byte-identical."""
    # Two real Python server sockets -- the same class the live system uses. One
    # stands in for the StorageController, the other for the logger (the
    # extension's ``logAggregator`` connects to it; we just drain it).
    storage_server = ServerSocket(name="echo-storage")
    storage_server.start_accepting()
    logger_server = ServerSocket(name="echo-logger")
    logger_server.start_accepting()

    manager_params = ManagerParamsInternal(num_browsers=1)
    manager_params.testing = True
    manager_params.storage_controller_address = storage_server.sock.getsockname()
    manager_params.logger_address = logger_server.sock.getsockname()

    browser_params = BrowserParamsInternal(
        display_mode="headless",
        echo_mode=True,
        browser_id=BrowserId(0),
        tmp_profile_dir=tmp_path,
    )

    status_queue: Queue = Queue()
    driver = None
    display = None
    try:
        driver, _profile_path, display = deploy_firefox.deploy_firefox(
            status_queue, browser_params, manager_params, crash_recovery=False
        )

        # loggingdb.open() sends ``JSON.stringify("Browser-0")`` to the storage
        # socket first as the client-name handshake; pop it before asserting the
        # echoed payloads. The real StorageController consumes this the same way.
        handshake = storage_server.queue.get(timeout=30)
        assert handshake == "Browser-0"

        # (A) The ``j`` (JSON) record with non-ASCII content. If #1180's
        # no-double-encode fix regresses, this comes back as mojibake, not equal.
        received_j = storage_server.queue.get(timeout=30)
        assert received_j == ECHO_J_RECORD
        # Sanity-check the non-ASCII content survived intact (round-trips cleanly).
        assert json.dumps(received_j, ensure_ascii=False) == json.dumps(
            ECHO_J_RECORD, ensure_ascii=False
        )

        # (B) The ``n`` (raw byte-string) payload. ServerSocket._parse returns
        # ``n`` frames as raw ``bytes``, untouched.
        received_n = storage_server.queue.get(timeout=30)
        assert isinstance(received_n, bytes)
        assert received_n == EXPECTED_N_BYTES
    finally:
        if driver is not None:
            driver.quit()
        if display is not None:
            display.stop()
        storage_server.close()
        logger_server.close()
