"""Tests for the ``FinalizeCommand`` FinalizeAck handshake and how
``BrowserManagerHandle`` reacts when it fails. No browser is involved.
"""

import logging
import pickle
import socket
import struct
import sys
import threading
import time
from queue import Queue
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple

import pytest

from openwpm import browser_manager
from openwpm.browser_manager import BrowserManagerHandle
from openwpm.command_sequence import CommandSequence
from openwpm.commands import browser_commands
from openwpm.commands.browser_commands import FinalizeAckTimeout, FinalizeCommand
from openwpm.config import BrowserParamsInternal
from openwpm.socket_interface import ClientSocket
from openwpm.types import BrowserId, VisitId

pytestmark = pytest.mark.pyonly

VISIT_ID = 42
BROWSER_ID = 0


@pytest.fixture(autouse=True)
def _no_tab_restart(monkeypatch: pytest.MonkeyPatch) -> None:
    """``FinalizeCommand.execute`` calls ``tab_restart_browser`` first; stub it
    out so the tests need no real webdriver."""
    monkeypatch.setattr(browser_commands, "tab_restart_browser", lambda webdriver: None)


def _make_command() -> FinalizeCommand:
    command = FinalizeCommand(sleep=1)
    command.set_visit_browser_id(VISIT_ID, BROWSER_ID)
    return command


def _run(extension_socket: Any) -> None:
    command = _make_command()
    manager_params = SimpleNamespace(testing=True)  # grace == 0.5s
    browser_params = SimpleNamespace(browser_id=BROWSER_ID)
    command.execute(
        webdriver=object(),
        browser_params=browser_params,
        manager_params=manager_params,
        extension_socket=extension_socket,
    )


class _TimeoutSocket:
    """Never acknowledges: ``receive`` blocks for the requested timeout, then
    raises ``socket.timeout`` -- exactly what a real socket does when nothing
    arrives before the deadline."""

    def __init__(self) -> None:
        self.sent: list = []

    def send(self, msg: Any) -> None:
        self.sent.append(msg)

    def receive(self, timeout: Optional[float] = None) -> Any:
        if timeout and timeout > 0:
            time.sleep(timeout)
        raise socket.timeout()


class _ImmediateTimeoutSocket(_TimeoutSocket):
    """As above, but ``receive`` raises immediately (no blocking)."""

    def receive(self, timeout: Optional[float] = None) -> Any:
        raise socket.timeout()


class _AckSocket:
    """Acknowledges immediately with a matching ``FinalizeAck``."""

    def __init__(self, visit_id: int) -> None:
        self.visit_id = visit_id
        self.sent: list = []

    def send(self, msg: Any) -> None:
        self.sent.append(msg)

    def receive(self, timeout: Optional[float] = None) -> Any:
        return {"action": "FinalizeAck", "visit_id": self.visit_id}


def test_finalize_sends_grace_and_visit_id() -> None:
    sock = _AckSocket(VISIT_ID)
    _run(sock)
    assert len(sock.sent) == 1
    msg = sock.sent[0]
    assert msg["action"] == "Finalize"
    assert msg["visit_id"] == VISIT_ID
    # testing=True forces the grace to 0.5s regardless of sleep
    assert msg["finalize_grace_seconds"] == 0.5


def test_ack_makes_execute_return_normally() -> None:
    # A matching FinalizeAck must let execute return without raising.
    _run(_AckSocket(VISIT_ID))


def test_timeout_raises_finalize_ack_timeout() -> None:
    with pytest.raises(FinalizeAckTimeout):
        _run(_ImmediateTimeoutSocket())


def test_timeout_raises_after_roughly_the_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Shrink the margin so the test stays fast; grace is 0.5s (testing=True),
    # so the deadline is ~0.5 + 0.2 == 0.7s.
    monkeypatch.setattr(browser_commands, "FINALIZE_ACK_MARGIN", 0.2)
    start = time.monotonic()
    with pytest.raises(FinalizeAckTimeout):
        _run(_TimeoutSocket())
    elapsed = time.monotonic() - start
    # Should block for roughly grace + margin before giving up.
    assert 0.5 <= elapsed <= 3.0


def test_non_matching_message_is_discarded_then_ack_accepted() -> None:
    # A stale ack for a different visit must not end the wait; the matching
    # ack that follows should.
    class _StaleThenAckSocket:
        def __init__(self) -> None:
            self.sent: list = []
            self._responses = [
                {"action": "FinalizeAck", "visit_id": VISIT_ID + 999},
                {"action": "FinalizeAck", "visit_id": VISIT_ID},
            ]

        def send(self, msg: Any) -> None:
            self.sent.append(msg)

        def receive(self, timeout: Optional[float] = None) -> Any:
            return self._responses.pop(0)

    _run(_StaleThenAckSocket())


@pytest.mark.parametrize(
    "reply",
    [
        None,  # extension closes the connection
        struct.pack(">Lc", 2, b"j") + b"\xff\xfe",  # not UTF-8
        struct.pack(">Lc", 2, b"x") + b"{}",  # unknown serialization tag
    ],
    ids=["closed", "non-utf8", "unknown-tag"],
)
def test_unreadable_ack_raises(reply: Optional[bytes]) -> None:
    client = ClientSocket()
    peer, client.sock = socket.socketpair()
    try:
        if reply is None:
            peer.shutdown(socket.SHUT_WR)
        else:
            peer.sendall(reply)
        with pytest.raises((RuntimeError, ValueError)):
            _run(client)
    finally:
        peer.close()
        client.close()


class _RecordingDataSocket:
    def __init__(self) -> None:
        self.finalized: List[Tuple[int, bool]] = []

    def store_record(self, table_name: Any, visit_id: int, data: Any) -> None:
        pass

    def finalize_visit_id(self, visit_id: int, success: bool) -> None:
        self.finalized.append((visit_id, success))


def _exc_status(exc: Exception) -> Tuple[str, bytes]:
    try:
        raise exc
    except Exception:
        return ("FAILED", pickle.dumps(sys.exc_info()))


def _execute_sequence(
    monkeypatch: pytest.MonkeyPatch,
    finalize_status: Any,
    failure_count: int = 0,
) -> Tuple[BrowserManagerHandle, SimpleNamespace, List[bool]]:
    """Run one CommandSequence (Initialize, Finalize) on a handle whose
    browser process is replaced by pre-seeded status replies."""
    monkeypatch.setattr(browser_manager.time, "sleep", lambda _: None)
    handle = BrowserManagerHandle.__new__(BrowserManagerHandle)
    handle.browser_id = BrowserId(BROWSER_ID)
    handle.curr_visit_id = VisitId(VISIT_ID)
    handle.browser_params = BrowserParamsInternal()
    handle.restart_required = False
    handle.logger = logging.getLogger("openwpm")
    handle.command_queue = Queue()
    handle.status_queue = Queue()
    handle.status_queue.put("OK")  # InitializeCommand
    handle.status_queue.put(finalize_status)
    restarts: List[bool] = []

    def restart_browser_manager(clear_profile: bool = False) -> bool:
        restarts.append(clear_profile)
        return True

    handle.restart_browser_manager = restart_browser_manager  # type: ignore
    task_manager = SimpleNamespace(
        sock=_RecordingDataSocket(),
        threadlock=threading.Lock(),
        failure_count=failure_count,
        failure_limit=10,
        failure_status=None,
        closing=False,
    )
    handle.execute_command_sequence(
        task_manager, CommandSequence("http://example.com")  # type: ignore
    )
    return handle, task_manager, restarts


@pytest.mark.parametrize(
    "exc",
    [FinalizeAckTimeout("no ack"), RuntimeError("socket connection broken")],
    ids=["ack-timeout", "connection-broken"],
)
def test_failed_finalize_restarts_browser(
    monkeypatch: pytest.MonkeyPatch, exc: Exception
) -> None:
    # A browser whose extension did not ack must not serve the next visit: a
    # still-pending Finalize there would clear that visit's visit_id.
    handle, task_manager, restarts = _execute_sequence(monkeypatch, _exc_status(exc))
    assert restarts == [False]
    assert not handle.restart_required
    assert task_manager.sock.finalized == [(VISIT_ID, False)]
    assert task_manager.failure_count == 1
    assert task_manager.failure_status is None


def test_failed_finalize_counts_toward_failure_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, task_manager, restarts = _execute_sequence(
        monkeypatch, _exc_status(FinalizeAckTimeout("no ack")), failure_count=10
    )
    assert task_manager.failure_status["ErrorType"] == "ExceedCommandFailureLimit"
    assert restarts == []


def test_acked_finalize_keeps_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    _, task_manager, restarts = _execute_sequence(monkeypatch, "OK", failure_count=3)
    assert restarts == []
    assert task_manager.sock.finalized == []
    assert task_manager.failure_count == 0
