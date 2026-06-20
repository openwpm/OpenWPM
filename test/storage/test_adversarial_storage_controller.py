"""Adversarial / chaos tests driving the *real* ``StorageController`` in-process.

These tests assert the central robustness property of the crawl pipeline's
storage tier:

    FORWARD PROGRESS + NO SILENT DATA LOSS
    Every visit_id that is started (a record is stored for it and/or it is
    finalized) MUST eventually reach the ``completion_queue`` exactly once,
    even when the underlying ``StructuredStorageProvider`` misbehaves, and the
    controller must never hang or silently swallow the visit.

The controller is driven exactly like the existing storage-controller tests
(`test/storage/test_storage_controller.py`): a real ``StorageControllerHandle``
spawns the real controller subprocess, and a real ``DataSocket`` feeds records
over a real socket. We then inject adversarial behaviour by subclassing the
in-memory providers to raise at well-defined points.

Scenarios covered (browser-free):
  * S4  - storage provider write/flush faults (transient + permanent)
  * S1/S5 (storage side) - a store_record task that raises must NOT strand the
          visit or tear down the shared connection
  * S6  - malformed / hostile records (huge values, injection-y strings,
          missing visit_id), driven against the real SQLite provider

The G1 / G1b / G2 invariants below were previously confirmed *defects*
(``xfail``); they now hold under the data-failure policy (crosslink #46), which
classifies a record that trips the schema as a CONSTRAINT VIOLATION -> the visit
is failed with an investigable error, the per-record failure is isolated so the
shared connection survives, and every started visit reaches a terminal state
without hanging. See ``docs/developers/Adversarial-Robustness.md`` and crosslink
#46 / #28 / #30.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pytest
from pyarrow import Table

from openwpm.storage.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
)
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_controller import (
    DataSocket,
    StorageControllerHandle,
)
from openwpm.storage.storage_providers import TableName
from openwpm.types import VisitId
from openwpm.utilities import db_utils

pytestmark = pytest.mark.pyonly


# ---------------------------------------------------------------------------
# Adversarial providers
# ---------------------------------------------------------------------------


class RaisingStoreProvider(MemoryStructuredProvider):
    """``store_record`` raises for every record.

    Models a structured-storage backend that throws while persisting a record
    (e.g. a programming error, an unexpected type, or a transient backend
    error that is not caught). Because ``StorageController.store_record``
    fires these off as un-awaited ``asyncio`` tasks, the controller must
    isolate the failure (data-failure policy, crosslink #46): the visit is
    failed, but the connection survives and the visit still reaches a terminal
    state.
    """

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        raise RuntimeError(f"injected store_record failure for visit {visit_id}")


class FailingWriteArrowProvider(MemoryArrowProvider):
    """``write_table`` raises permanently (e.g. disk full / S3 outage)."""

    async def write_table(self, table_name: TableName, table: Table) -> None:
        raise IOError("injected permanent write_table failure")


class TransientFailingStoreProvider(MemoryStructuredProvider):
    """``store_record`` fails the first ``n`` calls then recovers.

    Models a transient backend hiccup. A robust controller should still make
    forward progress for visits stored after the backend recovers.
    """

    def __init__(self, fail_first: int) -> None:
        super().__init__()
        self._remaining_failures = fail_first

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        if self._remaining_failures > 0:
            self._remaining_failures -= 1
            raise RuntimeError("injected transient store_record failure")
        await super().store_record(table, visit_id, record)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _drain_completions(
    handle: StorageControllerHandle, timeout: float = 8.0
) -> List[Tuple[int, bool]]:
    """Poll the completion queue until ``timeout`` and return everything seen."""
    deadline = time.time() + timeout
    seen: List[Tuple[int, bool]] = []
    while time.time() < deadline:
        seen.extend(handle.get_new_completed_visits())
        time.sleep(0.2)
    return seen


def _completed_ids(seen: List[Tuple[int, bool]]) -> Set[int]:
    return {vid for vid, _ in seen}


# ---------------------------------------------------------------------------
# Control: the happy path completes (guards against false negatives below)
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_control_good_visit_completes() -> None:
    """A normal visit reaches the completion queue. Establishes the baseline
    so that the stranding tests below are meaningful (not just slow polling).
    """
    handle = StorageControllerHandle(MemoryStructuredProvider(), None)
    handle.launch()
    assert handle.listener_address is not None
    sock = DataSocket(handle.listener_address, "control")
    vid = VisitId(0xC0FFEE)
    sock.store_record(TableName("site_visits"), vid, {"site_url": "ok"})
    sock.finalize_visit_id(vid, success=True)
    sock.close()

    # The MemoryStructuredProvider only resolves a visit's completion token on
    # flush_cache, which happens on the batch timeout or at shutdown. So we
    # check completions both during the run and after shutdown.
    handle.shutdown()
    seen = handle.get_new_completed_visits()
    assert vid in _completed_ids(seen), f"good visit never completed; seen={seen}"
    assert (vid, True) in seen


# ---------------------------------------------------------------------------
# S4 (transient): forward progress survives a transient store failure
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_transient_store_failure_controller_recovers() -> None:
    """The *controller* recovers from a transient store_record failure: a later
    visit still completes.

    Under the data-failure policy the failing store no longer tears down the
    connection, so the good visit completes on the same controller.
    """
    handle = StorageControllerHandle(TransientFailingStoreProvider(fail_first=1), None)
    handle.launch()
    assert handle.listener_address is not None

    bad = VisitId(1001)  # its store_record will raise (consumes the 1 failure)
    good = VisitId(1002)  # stored after recovery -> must complete

    bad_conn = DataSocket(handle.listener_address, "transient-bad")
    bad_conn.store_record(TableName("site_visits"), bad, {"site_url": "bad"})
    bad_conn.finalize_visit_id(bad, success=False)
    time.sleep(1)  # let the raising store task run
    bad_conn.close()

    good_conn = DataSocket(handle.listener_address, "transient-good")
    good_conn.store_record(TableName("site_visits"), good, {"site_url": "good"})
    good_conn.finalize_visit_id(good, success=True)
    good_conn.close()

    handle.shutdown()
    seen = handle.get_new_completed_visits()
    assert good in _completed_ids(
        seen
    ), f"controller did not recover: later visit did not complete; seen={seen}"


# ---------------------------------------------------------------------------
# G1b: a single failing record must NOT tear down the shared connection
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_raising_store_record_does_not_break_shared_connection() -> None:
    """INVARIANT (data-failure policy): a single failing record must not tear
    down a shared connection and break unrelated later records on it.

    In the real pipeline the TaskManager keeps one long-lived DataSocket for
    site_visits/crawl_history/finalize across ALL visits; one bad record must
    not break the socket for the rest of the crawl [adversarial G1b].
    """
    handle = StorageControllerHandle(TransientFailingStoreProvider(fail_first=1), None)
    handle.launch()
    assert handle.listener_address is not None
    sock = DataSocket(handle.listener_address, "shared-conn")

    bad = VisitId(1101)
    good = VisitId(1102)
    sock.store_record(TableName("site_visits"), bad, {"site_url": "bad"})
    sock.finalize_visit_id(bad, success=False)
    time.sleep(1)  # let the raising store task run; connection must survive
    # Reusing the SAME connection: this must still work under the policy.
    sock.store_record(TableName("site_visits"), good, {"site_url": "good"})
    sock.finalize_visit_id(good, success=True)
    sock.close()

    handle.shutdown()
    seen = handle.get_new_completed_visits()
    assert good in _completed_ids(
        seen
    ), f"good record on shared connection lost; seen={seen}"
    # The bad visit must also reach a terminal state (failed), not vanish.
    assert bad in _completed_ids(seen), f"bad visit stranded; seen={seen}"


# ---------------------------------------------------------------------------
# G1: a raising store task must still let the visit reach a terminal state
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_raising_store_record_visit_still_finalizes() -> None:
    """INVARIANT (data-failure policy): a finalized visit whose store_record
    raised must still reach the completion_queue marked FAILED (not vanish,
    not hang). The browser reported success=True, but a record that could not
    be stored fails the visit so it is surfaced for investigation [G1].
    """
    handle = StorageControllerHandle(RaisingStoreProvider(), None)
    handle.launch()
    assert handle.listener_address is not None
    sock = DataSocket(handle.listener_address, "raising")
    vid = VisitId(2001)
    sock.store_record(TableName("site_visits"), vid, {"site_url": "x"})
    sock.finalize_visit_id(vid, success=True)
    sock.close()

    seen = _drain_completions(handle)
    handle.shutdown()
    seen.extend(handle.get_new_completed_visits())
    assert vid in _completed_ids(
        seen
    ), f"visit stranded - never reached completion queue; seen={seen}"
    # A record that could not be stored fails the visit even though the browser
    # reported success: the visit must be marked FAILED for investigation.
    assert (vid, False) in seen, f"failed visit not marked unsuccessful; seen={seen}"


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_raising_store_record_unfinalized_visit_enqueued_on_shutdown() -> None:
    """INVARIANT (data-failure policy): on shutdown, every visit with pending
    store tasks must be enqueued to the completion_queue even if those tasks
    raised. Models a browser dying mid-visit (no Finalize sent) [G1].
    """
    handle = StorageControllerHandle(RaisingStoreProvider(), None)
    handle.launch()
    assert handle.listener_address is not None
    sock = DataSocket(handle.listener_address, "raising-unfinalized")
    vid = VisitId(2002)
    sock.store_record(TableName("site_visits"), vid, {"site_url": "x"})
    # deliberately NO finalize_visit_id - the client "crashes"
    sock.close()
    time.sleep(1)

    start = time.time()
    handle.shutdown()
    assert time.time() - start < 60, "shutdown hung on the raising visit"
    seen = handle.get_new_completed_visits()
    assert vid in _completed_ids(
        seen
    ), f"unfinalized stranded visit never enqueued on shutdown; seen={seen}"


# ---------------------------------------------------------------------------
# G2: a permanent write_table fault must not strand the visit or hang shutdown
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_permanent_write_table_fault_visit_still_completes() -> None:
    """INVARIANT (data-failure policy): even if persistent storage permanently
    rejects the write, the visit's terminal state must reach the
    completion_queue (marked FAILED) and shutdown must not crash or hang before
    draining it [G2]. The underlying failure is surfaced in the log, not masked
    as a timeout.
    """
    handle = StorageControllerHandle(FailingWriteArrowProvider(), None)
    handle.launch()
    assert handle.listener_address is not None
    sock = DataSocket(handle.listener_address, "write-fault")
    vid = VisitId(3001)
    sock.store_record(
        TableName("site_visits"),
        vid,
        {"site_url": "x", "browser_id": 1, "site_rank": 1},
    )
    sock.finalize_visit_id(vid, success=True)
    sock.close()

    start = time.time()
    handle.shutdown()
    assert time.time() - start < 60, "shutdown hung on the write fault"
    seen = handle.get_new_completed_visits()
    assert vid in _completed_ids(
        seen
    ), f"visit lost on permanent write fault; seen={seen}"
    assert (vid, False) in seen, f"unflushable visit not marked failed; seen={seen}"


# ---------------------------------------------------------------------------
# Constraint violation: a schema-tripping record fails the visit (not dropped)
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_constraint_violation_fails_visit_and_records_incomplete(
    tmp_path: Path,
) -> None:
    """A record that trips the SQLite schema (unknown column) is a CONSTRAINT
    VIOLATION: the visit is failed and recorded in ``incomplete_visits`` for
    investigation, NOT silently dropped (data-failure policy, crosslink #46).

    A subsequent good visit on the same connection must still complete, proving
    the failure was isolated to the offending visit.
    """
    db_path = tmp_path / "constraint.sqlite"
    handle = StorageControllerHandle(SQLiteStorageProvider(db_path), None)
    handle.launch()
    assert handle.listener_address is not None
    sock = DataSocket(handle.listener_address, "constraint")

    bad = VisitId(5001)
    # "nonexistent_column" is not in the site_visits schema -> OperationalError
    # "table site_visits has no column named nonexistent_column".
    sock.store_record(
        TableName("site_visits"),
        bad,
        {"browser_id": 1, "site_url": "ok", "site_rank": 1, "nonexistent_column": "x"},
    )
    sock.finalize_visit_id(bad, success=True)

    good = VisitId(5002)
    sock.store_record(
        TableName("site_visits"),
        good,
        {"browser_id": 1, "site_url": "good", "site_rank": 2},
    )
    sock.finalize_visit_id(good, success=True)
    sock.close()

    start = time.time()
    handle.shutdown()
    assert time.time() - start < 60, "shutdown hung on a constraint violation"

    seen = handle.get_new_completed_visits()
    ids = _completed_ids(seen)
    assert good in ids, f"good visit lost after a constraint violation; seen={seen}"
    # The bad visit reaches a FAILED terminal state ...
    assert (bad, False) in seen, f"constraint-violating visit not failed; seen={seen}"

    # ... and is recorded as incomplete for investigation (not silently dropped).
    incomplete = db_utils.query_db(
        db_path, "SELECT visit_id FROM incomplete_visits;", as_tuple=True
    )
    incomplete_ids = {r[0] for r in incomplete}
    assert (
        bad in incomplete_ids
    ), f"constraint-violating visit not recorded in incomplete_visits; {incomplete_ids}"


# ---------------------------------------------------------------------------
# S6 - malformed / hostile records sent through the real DataSocket
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("adversarial_mp_logger")
def test_malformed_records_do_not_break_controller(tmp_path: Path) -> None:
    """Hostile/malformed records (huge strings, injection-y values, a record
    with no visit_id) must not crash or hang the controller; a subsequent good
    visit must still complete and be persisted.

    Driven against the *real* ``SQLiteStorageProvider`` so the huge value goes
    through the production persistence path (writing to disk), not the
    ``MemoryStructuredProvider`` test queue - a multi-MiB value deadlocks the
    cross-process ``multiprocess.Queue`` the memory provider uses, which is a
    test-harness artifact, not a pipeline property.
    """
    db_path = tmp_path / "malformed.sqlite"
    handle = StorageControllerHandle(SQLiteStorageProvider(db_path), None)
    handle.launch()
    assert handle.listener_address is not None
    sock = DataSocket(handle.listener_address, "malformed")

    huge = "A" * (2 * 1024 * 1024)  # 2 MiB string in a valid TEXT column
    # site_visits.visit_id is the PRIMARY KEY, so each visit gets one record.
    huge_visit = VisitId(4001)
    sock.store_record(
        TableName("site_visits"),
        huge_visit,
        {"browser_id": 1, "site_url": huge, "site_rank": 1},
    )
    sock.finalize_visit_id(huge_visit, success=True)

    # injection-y value as a literal in a valid column on its own visit
    injection_visit = VisitId(4002)
    sock.store_record(
        TableName("site_visits"),
        injection_visit,
        {"browser_id": 1, "site_url": "'; DROP TABLE site_visits;--", "site_rank": 2},
    )
    sock.finalize_visit_id(injection_visit, success=True)

    # A record with no visit_id at all (controller must skip it, not crash).
    # Sent via the raw socket because DataSocket always injects visit_id.
    sock.socket.send((TableName("site_visits"), {"site_url": "no visit id"}))

    # Now a normal visit must still complete -> controller survived.
    good = VisitId(4003)
    sock.store_record(
        TableName("site_visits"),
        good,
        {"browser_id": 1, "site_url": "ok", "site_rank": 3},
    )
    sock.finalize_visit_id(good, success=True)
    sock.close()

    start = time.time()
    handle.shutdown()
    assert time.time() - start < 60, "controller hung on a malformed record"

    seen = handle.get_new_completed_visits()
    ids = _completed_ids(seen)
    assert good in ids, f"controller did not survive malformed records; seen={seen}"
    assert huge_visit in ids, f"huge-value visit lost; seen={seen}"
    assert injection_visit in ids, f"injection-value visit lost; seen={seen}"

    # The injection string is stored as a literal value, table intact.
    rows = db_utils.query_db(
        db_path, "SELECT site_url FROM site_visits;", as_tuple=True
    )
    stored = {r[0] for r in rows}
    assert (
        "'; DROP TABLE site_visits;--" in stored
    ), "injection value not stored literally"
    assert huge in stored, "huge value not persisted"
