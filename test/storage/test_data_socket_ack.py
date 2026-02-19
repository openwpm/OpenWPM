"""Unit tests for ``DataSocket.finalize_visit_id_with_ack``."""

import logging
import socket
import struct
import threading
import time
from typing import Any, Dict, List, Optional

import pytest

from openwpm.mp_logger import MPLogger
from openwpm.socket_interface import ClientSocket
from openwpm.storage.in_memory_storage import MemoryStructuredProvider
from openwpm.storage.storage_controller import DataSocket, StorageControllerHandle
from openwpm.storage.storage_providers import StructuredStorageProvider, TableName
from openwpm.types import VisitId
from test.storage.fixtures import structured_scenarios

VISIT_ID = VisitId(42)


class _FakeSocket:
    """Replays ``responses`` in order; an exception instance is raised instead
    of returned. Once exhausted, behaves like a socket that times out."""

    def __init__(self, responses: List[Any]) -> None:
        self.sent: List[Any] = []
        self._responses = list(responses)

    def send(self, msg: Any) -> None:
        self.sent.append(msg)

    def receive(self, timeout: Optional[float] = None) -> Any:
        if not self._responses:
            if timeout and timeout > 0:
                time.sleep(timeout)
            raise socket.timeout()
        response = self._responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def _data_socket(fake: Any) -> DataSocket:
    ds = DataSocket.__new__(DataSocket)
    ds.socket = fake
    ds.logger = logging.getLogger("openwpm")
    ds._send_lock = threading.Lock()
    ds._ack_lock = threading.Lock()
    return ds


def _ack(visit_id: int, finalized: bool = True) -> dict:
    return {"action": "finalize_ack", "visit_id": visit_id, "finalized": finalized}


@pytest.mark.pyonly
def test_matching_ack_returns_true() -> None:
    fake = _FakeSocket([_ack(VISIT_ID)])
    assert _data_socket(fake).finalize_visit_id_with_ack(VISIT_ID, True) is True
    ((record_type, data),) = fake.sent
    assert data["visit_id"] == VISIT_ID
    assert data["want_ack"] is True


@pytest.mark.pyonly
def test_stale_ack_for_previous_visit_is_discarded() -> None:
    fake = _FakeSocket([_ack(VISIT_ID - 1), _ack(VISIT_ID)])
    assert _data_socket(fake).finalize_visit_id_with_ack(VISIT_ID, True) is True
    assert fake._responses == []


@pytest.mark.pyonly
def test_only_stale_ack_times_out() -> None:
    fake = _FakeSocket([_ack(VISIT_ID - 1)])
    start = time.monotonic()
    assert (
        _data_socket(fake).finalize_visit_id_with_ack(VISIT_ID, True, timeout=0.3)
        is None
    )
    assert time.monotonic() - start < 3.0


@pytest.mark.pyonly
def test_timeout_returns_none() -> None:
    fake = _FakeSocket([])
    start = time.monotonic()
    assert (
        _data_socket(fake).finalize_visit_id_with_ack(VISIT_ID, True, timeout=0.3)
        is None
    )
    elapsed = time.monotonic() - start
    assert 0.25 <= elapsed < 3.0


@pytest.mark.pyonly
@pytest.mark.parametrize(
    "frame",
    [
        struct.pack(">Lc", 2, b"x") + b"{}",  # unknown serialization
        struct.pack(">Lc", 3, b"j") + b"{{{",  # invalid JSON
    ],
)
def test_malformed_frame_returns_none(frame: bytes) -> None:
    client = ClientSocket()
    server_end, client.sock = socket.socketpair()
    try:
        server_end.sendall(frame)
        ds = _data_socket(client)
        assert ds.finalize_visit_id_with_ack(VISIT_ID, True, timeout=1.0) is None
    finally:
        server_end.close()
        client.close()


@pytest.mark.pyonly
def test_broken_connection_returns_none() -> None:
    fake = _FakeSocket([RuntimeError("socket connection broken")])
    assert _data_socket(fake).finalize_visit_id_with_ack(VISIT_ID, True) is None


@pytest.mark.pyonly
def test_skipped_visit_ack_returns_false() -> None:
    fake = _FakeSocket([_ack(VISIT_ID, finalized=False)])
    assert _data_socket(fake).finalize_visit_id_with_ack(VISIT_ID, True) is False


@pytest.mark.parametrize("structured_provider", structured_scenarios, indirect=True)
def test_ack_round_trip_through_storage_controller(
    mp_logger: MPLogger, structured_provider: StructuredStorageProvider
) -> None:
    controller_handle = StorageControllerHandle(structured_provider, None)
    controller_handle.launch()
    assert controller_handle.listener_address is not None
    ds = DataSocket(controller_handle.listener_address, "Test")
    try:
        for visit_id, success in ((VisitId(1), True), (VisitId(2), False)):
            ds.store_record(
                TableName("crawl_history"), visit_id, {"browser_id": 1, "command": "x"}
            )
            assert ds.finalize_visit_id_with_ack(visit_id, success) is True
        # Already finalized: acked, but reported as skipped.
        assert ds.finalize_visit_id_with_ack(VisitId(2), True) is False
    finally:
        ds.close()
        controller_handle.shutdown()


def test_concurrent_threads_share_one_socket(mp_logger: MPLogger) -> None:
    """The TaskManager shares one DataSocket across browser threads: every
    caller must get its own ack while other threads keep storing records."""
    controller_handle = StorageControllerHandle(MemoryStructuredProvider(), None)
    controller_handle.launch()
    assert controller_handle.listener_address is not None
    ds = DataSocket(controller_handle.listener_address, "Test")
    threads, visits_per_thread = 4, 20
    results: Dict[int, List[Optional[bool]]] = {}
    errors: List[BaseException] = []

    def browser_thread(index: int) -> None:
        try:
            for i in range(visits_per_thread):
                visit_id = VisitId(index * 1000 + i + 1)
                ds.store_record(TableName("site_visits"), visit_id, {"site_url": "x"})
                results.setdefault(index, []).append(
                    ds.finalize_visit_id_with_ack(visit_id, True)
                )
        except BaseException as e:
            errors.append(e)

    workers = [
        threading.Thread(target=browser_thread, args=(i,)) for i in range(threads)
    ]
    try:
        for w in workers:
            w.start()
        for w in workers:
            w.join(120)
        assert not any(w.is_alive() for w in workers)
        assert errors == []
        assert results == {i: [True] * visits_per_thread for i in range(threads)}
    finally:
        ds.close()
        controller_handle.shutdown()
