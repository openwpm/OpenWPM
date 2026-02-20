"""Unit tests for the synchronous ``FinalizeCommand`` FinalizeAck handshake.

These are ``pyonly`` tests: they drive ``FinalizeCommand.execute`` directly with
a fake extension socket, no browser or extension involved. The behavior under
test is the refinement introduced on the finalize-ack branch: when the extension
does not acknowledge a ``Finalize`` within ``grace + FINALIZE_ACK_MARGIN``,
``execute`` raises ``FinalizeAckTimeout`` (rather than silently proceeding); a
matching ``FinalizeAck`` instead lets ``execute`` return normally.
"""

import socket
import time
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from openwpm.commands import browser_commands
from openwpm.commands.browser_commands import FinalizeAckTimeout, FinalizeCommand

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
