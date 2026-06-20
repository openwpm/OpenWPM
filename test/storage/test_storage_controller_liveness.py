"""Property-based forward-progress / liveness tests for the StorageController.

Background
----------
In production parquet->S3 crawls, sites were observed to get claimed and
perpetually marked in-progress by the work-queue client while their data never
got committed or pushed out: records were produced and cached in the
StorageController, but the cache never flushed and the visit never reached a
terminal state (neither committed nor explicitly marked incomplete). The visit
was stranded forever and its data lost.

These tests pin down the forward-progress invariant the StorageController must
uphold, expressed as Hypothesis property tests over arbitrary interleavings of
the operations a browser (or watchdog) can drive through the data socket:

  * start a visit by emitting N records across tables,
  * finalize(success),
  * finalize(failure),
  * never-finalize-then-shutdown,
  * concurrent visits,
  * transient storage-provider write failures.

The forward-progress invariants asserted:

  I1  Every visit that emitted records and was finalized(success) appears fully
      in the committed output.
  I2  Every started-but-not-successfully-finalized visit ends in a terminal
      state (recorded incomplete / explicitly dropped) at shutdown - never
      silently stranded.
  I3  Shutdown drains all pending committable data; nothing is left only in the
      provider cache.
  I4  The controller's per-visit cache is bounded: it does not grow without
      bound with perpetually-pending visits while the controller is alive.

To stay fast and browser-free these tests drive the StorageController's async
methods directly in a single event loop, mirroring exactly what the socket
handler does on the wire (``store_record`` for data, ``_handle_meta`` with a
``Finalize`` action for finalize). No subprocess, no socket, no Firefox.
"""

import asyncio
import logging
import queue
from typing import Any, Dict, List, Optional, Tuple

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import openwpm.storage.storage_controller as scmod
from openwpm.storage.arrow_storage import ArrowProvider
from openwpm.storage.storage_controller import (
    SHUTDOWN_FLUSH_RETRIES,
    StorageController,
)
from openwpm.storage.storage_providers import (
    INCOMPLETE_VISITS,
    StructuredStorageProvider,
    TableName,
)
from openwpm.types import VisitId

logging.getLogger("openwpm").addHandler(logging.NullHandler())


@pytest.fixture(autouse=True)
def _fast_controller_intervals(monkeypatch: pytest.MonkeyPatch) -> None:
    """Shrink the controller's poll/retry sleeps so the many shutdown drains
    these property tests perform do not each cost whole seconds. These only
    affect wall-clock latency, never correctness, so shrinking them keeps the
    behaviour faithful while keeping the suite fast."""
    monkeypatch.setattr(scmod, "COMPLETION_QUEUE_INTERVAL", 0.01)
    monkeypatch.setattr(scmod, "SHUTDOWN_FLUSH_RETRY_DELAY", 0.01)


SITE_VISITS = TableName("site_visits")


# ---------------------------------------------------------------------------
# Instrumented providers
# ---------------------------------------------------------------------------
class RecordingArrowProvider(ArrowProvider):
    """An ArrowProvider that captures everything it writes out in-process.

    Uses the real production batching / ``flush_events`` machinery (this is the
    exact code path parquet->S3 crawls exercise), but ``write_table`` records
    into a local dict instead of going to disk/S3 so tests can assert on the
    committed rows.

    ``fail_writes`` makes the first N ``write_table`` calls raise, modelling a
    transient storage backend error (e.g. an S3 PutObject failure).
    """

    def __init__(self, fail_writes: int = 0) -> None:
        super().__init__()
        self.committed: Dict[str, List[Dict[str, Any]]] = {}
        self.write_calls = 0
        self._fail_writes = fail_writes

    async def write_table(self, table_name: TableName, table: Any) -> None:
        self.write_calls += 1
        if self.write_calls <= self._fail_writes:
            raise RuntimeError(
                f"transient write failure #{self.write_calls} for {table_name}"
            )
        rows = table.to_pandas().to_dict("records")
        self.committed.setdefault(table_name, []).extend(rows)

    async def shutdown(self) -> None:
        pass

    # --- helpers for assertions ---
    def committed_visit_ids(self) -> set:
        ids = set()
        for rows in self.committed.values():
            for row in rows:
                vid = row.get("visit_id")
                if vid is not None:
                    ids.add(int(vid))
        return ids

    def incomplete_visit_ids(self) -> set:
        return {
            int(row["visit_id"]) for row in self.committed.get(INCOMPLETE_VISITS, [])
        }

    def committed_row_count(self, table: TableName, visit_id: VisitId) -> int:
        return sum(
            1
            for row in self.committed.get(table, [])
            if row.get("visit_id") == visit_id
        )


def site_visit_record(visit_id: int, browser_id: int = 1) -> Dict[str, Any]:
    """A schema-valid ``site_visits`` record."""
    return {
        "visit_id": visit_id,
        "browser_id": browser_id,
        "site_url": f"https://example-{visit_id}.test",
        "site_rank": None,
    }


# ---------------------------------------------------------------------------
# In-process driver that faithfully mirrors the socket handler's behaviour
# ---------------------------------------------------------------------------
class ControllerDriver:
    """Drives a StorageController's async API directly, as the socket handler does.

    The real ``handler`` loop turns every wire message into exactly one of:
      * ``store_record(table, visit_id, data)``  (data records)
      * ``_handle_meta(visit_id, {action: Finalize, success: ...})``  (finalize)
    and lets the resulting ``store_record`` tasks run on the event loop. This
    driver does the same, so it exercises the identical controller code path
    without a socket or subprocess.
    """

    def __init__(self, provider: StructuredStorageProvider) -> None:
        self.provider = provider
        # Use synchronous in-process queues instead of multiprocess.Queue.
        # multiprocess.Queue has a background feeder thread, so ``.empty()``
        # immediately after ``.put()`` can race the feeder and spuriously report
        # empty -- which would make these single-shot drain assertions flaky.
        # The controller only calls .put/.get/.empty, so queue.Queue is a
        # drop-in synchronous replacement and makes the tests deterministic.
        self.status_queue: queue.Queue = queue.Queue()
        self.completion_queue: queue.Queue = queue.Queue()
        self.shutdown_queue: queue.Queue = queue.Queue()
        self.sc = StorageController(
            provider,
            None,
            self.status_queue,
            self.completion_queue,
            self.shutdown_queue,
        )
        self._timeout_task: Optional[asyncio.Task] = None

    async def init(self) -> None:
        await self.provider.init()

    async def emit(
        self, table: TableName, visit_id: int, record: Dict[str, Any]
    ) -> None:
        await self.sc.store_record(table, VisitId(visit_id), dict(record))

    async def finalize(self, visit_id: int, success: bool) -> None:
        # Mirror the handler: store tasks for this visit must be awaited before
        # finalize, which is exactly what finalize_visit_id does internally.
        await self.sc._handle_meta(
            VisitId(visit_id),
            {"visit_id": visit_id, "action": "Finalize", "success": success},
        )

    async def settle(self) -> None:
        """Let all currently-scheduled store_record tasks run to completion."""
        pending = [
            t
            for tasks in self.sc.store_record_tasks.values()
            for t in tasks
            if not t.done()
        ]
        if pending:
            await asyncio.gather(*pending)

    def start_timeout_flush(self) -> None:
        self._timeout_task = asyncio.create_task(
            self.sc.save_batch_if_past_timeout(), name="TimeoutCheck"
        )

    async def run_shutdown(self) -> None:
        """Run the controller's real shutdown/drain path to completion."""
        self.sc._shutdown_flag = True
        ucq = asyncio.create_task(self.sc.update_completion_queue())
        if self._timeout_task is not None:
            self._timeout_task.cancel()
        await asyncio.wait_for(self.sc.shutdown(ucq), timeout=30)

    def drain_completion_queue(self) -> List[Tuple[int, bool]]:
        out: List[Tuple[int, bool]] = []
        while not self.completion_queue.empty():
            out.append(self.completion_queue.get())
        return out


# A plan is a list of (visit_id, n_records, outcome) where outcome is one of
# "success", "failure", "never" (never finalized -> relies on shutdown drain).
visit_plan = st.lists(
    st.tuples(
        st.integers(min_value=1, max_value=20),  # visit_id
        st.integers(min_value=0, max_value=4),  # records emitted
        st.sampled_from(["success", "failure", "never"]),
    ),
    min_size=1,
    max_size=8,
    # unique visit_ids so plans are unambiguous (no re-use of a visit_id)
    unique_by=lambda t: t[0],
)


HSETTINGS = settings(
    max_examples=40,
    deadline=None,  # async event-loop scheduling timing is not deterministic
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


# ---------------------------------------------------------------------------
# I1 + I2 + I3: forward progress with a healthy provider
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.pyonly
@HSETTINGS
@given(plan=visit_plan)
async def test_every_visit_reaches_a_terminal_state(
    plan: List[Tuple[int, int, str]],
) -> None:
    """With a healthy provider, every started visit must reach a terminal state.

    * finalize(success) visits with records -> fully committed (I1)
    * every other started visit -> committed-and/or-marked-incomplete, never
      silently stranded (I2)
    * shutdown drains everything; nothing left only in cache (I3)
    """
    provider = RecordingArrowProvider()
    driver = ControllerDriver(provider)
    await driver.init()

    emitted_counts: Dict[int, int] = {}
    outcomes: Dict[int, str] = {}
    for visit_id, n, outcome in plan:
        outcomes[visit_id] = outcome
        emitted_counts[visit_id] = n
        for i in range(n):
            await driver.emit(SITE_VISITS, visit_id, site_visit_record(visit_id))
        await driver.settle()
        if outcome == "success":
            await driver.finalize(visit_id, success=True)
        elif outcome == "failure":
            await driver.finalize(visit_id, success=False)
        # "never" -> no finalize; shutdown must clean it up

    await driver.run_shutdown()
    completed = dict(driver.drain_completion_queue())

    # I3: shutdown must leave nothing in the per-visit record cache.
    assert not provider._records, (
        f"records left uncommitted in provider cache after shutdown: "
        f"{dict(provider._records)}"
    )
    assert not provider._batches, (
        f"batches left unflushed in provider cache after shutdown: "
        f"{dict(provider._batches)}"
    )

    for visit_id, outcome in outcomes.items():
        n = emitted_counts[visit_id]
        observed = n > 0 or outcome in ("success", "failure")
        if not observed:
            # CONTRACT BOUNDARY: a visit the controller never observed (no record
            # ever arrived AND no finalize was sent) is invisible to the
            # StorageController - there is nothing it could key on. Driving such a
            # claimed-but-silent visit to a terminal state is the work-queue
            # client's responsibility (e.g. via its own visit-claim timeout), not
            # the controller's. See the module docstring / PR write-up.
            continue
        # I2: every visit the controller observed must appear in the completion
        # queue (terminal), never silently stranded.
        assert visit_id in completed, (
            f"visit {visit_id} (outcome={outcome}, records={n}) never reached the "
            f"completion queue - it is silently stranded"
        )
        if outcome == "success" and n > 0:
            # I1: a successfully finalized visit's records must all be committed.
            assert provider.committed_row_count(SITE_VISITS, VisitId(visit_id)) == n, (
                f"visit {visit_id} finalized(success) but committed "
                f"{provider.committed_row_count(SITE_VISITS, VisitId(visit_id))} of "
                f"{n} records"
            )


# ---------------------------------------------------------------------------
# I2: a started-but-never-finalized visit must NOT be silently stranded
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.pyonly
@HSETTINGS
@given(
    n_visits=st.integers(min_value=1, max_value=6),
    records_each=st.integers(min_value=1, max_value=3),
)
async def test_never_finalized_visits_drained_at_shutdown(
    n_visits: int, records_each: int
) -> None:
    """Browser crash: records arrive, finalize never does. Shutdown must mark
    them terminal (completion queue) - not leave them stranded."""
    provider = RecordingArrowProvider()
    driver = ControllerDriver(provider)
    await driver.init()

    visit_ids = list(range(1, n_visits + 1))
    for visit_id in visit_ids:
        for _ in range(records_each):
            await driver.emit(SITE_VISITS, visit_id, site_visit_record(visit_id))
    await driver.settle()

    await driver.run_shutdown()
    completed = dict(driver.drain_completion_queue())

    for visit_id in visit_ids:
        assert (
            visit_id in completed
        ), f"never-finalized visit {visit_id} was not drained at shutdown"
        assert (
            completed[visit_id] is False
        ), f"never-finalized visit {visit_id} reported success={completed[visit_id]}"
    # All such visits must be marked incomplete (terminal, recoverable).
    incomplete = provider.incomplete_visit_ids()
    for visit_id in visit_ids:
        assert (
            visit_id in incomplete
        ), f"never-finalized visit {visit_id} not recorded in incomplete_visits"


# ---------------------------------------------------------------------------
# I1/I2 under transient provider write failures -- the production bug
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.pyonly
@HSETTINGS
@given(
    plan=visit_plan,
    # A transient outage that recovers within the controller's shutdown retry
    # budget (SHUTDOWN_FLUSH_RETRIES). The live-crawl periodic flusher retries
    # indefinitely; the shutdown drain is bounded by design so it can never hang.
    fail_writes=st.integers(min_value=1, max_value=SHUTDOWN_FLUSH_RETRIES - 1),
)
async def test_forward_progress_survives_transient_write_failures(
    plan: List[Tuple[int, int, str]], fail_writes: int
) -> None:
    """A transient storage-backend write failure (e.g. an S3 PutObject error)
    must NOT permanently strand visits.

    This reproduces the observed production liveness bug: the first few
    ``write_table`` calls fail, and the controller must still eventually drive
    every started visit to a terminal state (committed or incomplete) and not
    leave records stuck only in the cache.
    """
    provider = RecordingArrowProvider(fail_writes=fail_writes)
    driver = ControllerDriver(provider)
    await driver.init()

    observed: List[int] = []
    for visit_id, n, outcome in plan:
        # The controller can only key on visits it has observed: a 0-record,
        # never-finalized visit is invisible to it (that is the work-queue
        # client's responsibility, see test_every_visit_reaches_a_terminal_state).
        if n > 0 or outcome in ("success", "failure"):
            observed.append(visit_id)
        for _ in range(n):
            await driver.emit(SITE_VISITS, visit_id, site_visit_record(visit_id))
        await driver.settle()
        if outcome == "success":
            await driver.finalize(visit_id, success=True)
        elif outcome == "failure":
            await driver.finalize(visit_id, success=False)

    await driver.run_shutdown()
    completed = dict(driver.drain_completion_queue())

    for visit_id in observed:
        assert visit_id in completed, (
            f"visit {visit_id} never reached a terminal state after a transient "
            f"write failure -- it is perpetually in-progress (stranded)"
        )

    # I3: nothing may remain only in the provider cache.
    assert not provider._records, (
        f"records stranded in provider cache after transient failure + shutdown: "
        f"{dict(provider._records)}"
    )
    assert not provider._batches, (
        f"batches stranded in provider cache after transient failure + shutdown: "
        f"{dict(provider._batches)}"
    )


# ---------------------------------------------------------------------------
# I4: the per-visit cache is bounded -- no unbounded growth of pending visits
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.pyonly
@HSETTINGS
@given(n_visits=st.integers(min_value=5, max_value=40))
async def test_finalized_visits_do_not_accumulate_unboundedly(n_visits: int) -> None:
    """Finalizing a visit must release its per-visit bookkeeping.

    A correct controller drops the visit from ``store_record_tasks`` on finalize,
    so the number of tracked visits cannot grow without bound as visits are
    finalized one after another.
    """
    provider = RecordingArrowProvider()
    driver = ControllerDriver(provider)
    await driver.init()

    max_tracked = 0
    for visit_id in range(1, n_visits + 1):
        await driver.emit(SITE_VISITS, visit_id, site_visit_record(visit_id))
        await driver.settle()
        await driver.finalize(visit_id, success=True)
        max_tracked = max(max_tracked, len(driver.sc.store_record_tasks))

    # Each visit is finalized immediately after it is started, so at most a
    # small constant number of visits should ever be tracked simultaneously -
    # never O(n_visits).
    assert max_tracked <= 2, (
        f"per-visit cache grew to {max_tracked} tracked visits for {n_visits} "
        f"sequentially-finalized visits -- finalize is not releasing bookkeeping"
    )

    await driver.run_shutdown()
