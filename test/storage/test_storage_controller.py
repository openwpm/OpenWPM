import asyncio
import threading
import time
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import pyarrow.parquet as pq
import pytest
from multiprocess import Queue
from pandas.testing import assert_frame_equal

from openwpm.mp_logger import MPLogger
from openwpm.storage.arrow_storage import CACHE_SIZE
from openwpm.storage.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
)
from openwpm.storage.local_storage import LocalArrowProvider
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_controller import (
    ACTION_TYPE_FINALIZE,
    INVALID_VISIT_ID,
    DataSocket,
    StorageController,
    StorageControllerHandle,
)
from openwpm.storage.storage_providers import StructuredStorageProvider, TableName
from openwpm.types import VisitId
from openwpm.utilities import db_utils
from test.storage.fixtures import dt_test_values


def test_startup_and_shutdown(mp_logger: MPLogger, test_values: dt_test_values) -> None:
    test_table, visit_ids = test_values
    structured = MemoryStructuredProvider()
    controller_handle = StorageControllerHandle(structured, None)
    controller_handle.launch()
    assert controller_handle.listener_address is not None
    cs = DataSocket(controller_handle.listener_address, "Test")
    for table, data in test_table.items():
        visit_id = data["visit_id"]
        cs.store_record(
            table, visit_id, data
        )  # cloning to avoid the modifications in store_record

    for visit_id in visit_ids:
        cs.finalize_visit_id(visit_id, True)
    cs.close()
    controller_handle.shutdown()

    handle = structured.handle
    handle.poll_queue()
    for table, data in test_table.items():
        if data["visit_id"] == INVALID_VISIT_ID:
            del data["visit_id"]
        assert handle.storage[table] == [data]


def test_arrow_provider(mp_logger: MPLogger, test_values: dt_test_values) -> None:
    test_table, visit_ids = test_values
    structured = MemoryArrowProvider()
    controller_handle = StorageControllerHandle(structured, None)
    controller_handle.launch()

    assert controller_handle.listener_address is not None
    cs = DataSocket(controller_handle.listener_address, "Test")

    for table, data in test_table.items():
        visit_id = data["visit_id"]
        cs.store_record(table, visit_id, data)

    for visit_id in visit_ids:
        cs.finalize_visit_id(visit_id, True)
    cs.close()
    controller_handle.shutdown()

    handle = structured.handle
    handle.poll_queue()
    for table, data in test_table.items():
        t1 = handle.storage[table][0].to_pandas().drop(columns=["instance_id"])
        if data["visit_id"] == INVALID_VISIT_ID:
            del data["visit_id"]
        t2 = pd.DataFrame({k: [v] for k, v in data.items()})
        # Since t2 doesn't get created schema the inferred types are different
        assert_frame_equal(t1, t2, check_dtype=False)


@pytest.mark.pyonly
def test_unencodable_string_is_stored(mp_logger: MPLogger, tmp_path: Path) -> None:
    """A lone surrogate (e.g. from a page-chosen JS string) cannot be encoded as
    UTF-8. It must not drop the producer's connection, losing later records."""
    db = tmp_path / "crawl-data.sqlite"
    controller_handle = StorageControllerHandle(SQLiteStorageProvider(db), None)
    controller_handle.launch()
    assert controller_handle.listener_address is not None
    cs = DataSocket(controller_handle.listener_address, "Test")
    for visit_id, call_stack in [(1, "lone\ud800name"), (2, "after")]:
        cs.store_record(
            TableName("callstacks"),
            VisitId(visit_id),
            {"request_id": 1, "browser_id": 1, "call_stack": call_stack},
        )
        cs.finalize_visit_id(VisitId(visit_id), True)
    cs.close()
    controller_handle.shutdown()

    rows = db_utils.query_db(
        db, "SELECT visit_id, call_stack FROM callstacks ORDER BY visit_id"
    )
    assert [tuple(row) for row in rows] == [(1, "lone\ufffdname"), (2, "after")]


@pytest.mark.parametrize("first_success", [False, True])
def test_duplicate_finalize_is_ignored(
    mp_logger: MPLogger, first_success: bool
) -> None:
    """After a failed FinalizeCommand both the TaskManager and the extension
    may finalize the same visit; only the first may reach the callback."""
    visit_id = VisitId(1000)
    controller_handle = StorageControllerHandle(MemoryStructuredProvider(), None)
    controller_handle.launch()
    assert controller_handle.listener_address is not None
    task_manager_sock = DataSocket(controller_handle.listener_address, "TaskManager")
    extension_sock = DataSocket(controller_handle.listener_address, "Extension")
    try:
        task_manager_sock.store_record(
            TableName("site_visits"), visit_id, {"site_url": "x"}
        )
        task_manager_sock.finalize_visit_id(visit_id, first_success)
        completed: List[Tuple[int, bool]] = []
        deadline = time.monotonic() + 30
        while not completed and time.monotonic() < deadline:
            completed += controller_handle.get_new_completed_visits()
            time.sleep(0.1)
        extension_sock.finalize_visit_id(visit_id, not first_success)
    finally:
        task_manager_sock.close()
        extension_sock.close()
        controller_handle.shutdown()
    completed += controller_handle.get_new_completed_visits()
    assert completed == [(visit_id, first_success)]


def _read_crawl(provider: str, path: Path) -> Tuple[List[str], int]:
    """Returns the stored crawl_history commands and incomplete_visits count"""
    if provider == "sqlite":
        db = path / "crawl.sqlite"
        commands = db_utils.query_db(
            db, "SELECT command FROM crawl_history", as_tuple=True
        )
        incomplete = db_utils.query_db(db, "SELECT * FROM incomplete_visits")
        return sorted(c for (c,) in commands), len(incomplete)
    incomplete_dir = path / "incomplete_visits"
    return (
        sorted(pq.read_table(path / "crawl_history").column("command").to_pylist()),
        pq.read_table(incomplete_dir).num_rows if incomplete_dir.exists() else 0,
    )


@pytest.mark.parametrize("provider", ["sqlite", "arrow"])
@pytest.mark.parametrize("second_finalize", [False, True])
@pytest.mark.parametrize("first_success", [False, True])
def test_records_after_finalize_are_flushed(
    mp_logger: MPLogger,
    tmp_path: Path,
    first_success: bool,
    second_finalize: bool,
    provider: str,
) -> None:
    """Records can follow a visit's finalize: the TaskManager's crawl_history
    row after the extension's finalize, or extension stragglers (and a second
    finalize) after the TaskManager's failure finalize. They must be stored
    without marking the visit interrupted again or completing it twice."""
    visit_id = VisitId(1000)
    structured: StructuredStorageProvider = (
        SQLiteStorageProvider(tmp_path / "crawl.sqlite")
        if provider == "sqlite"
        else LocalArrowProvider(tmp_path)
    )
    controller_handle = StorageControllerHandle(structured, None)
    controller_handle.launch()
    assert controller_handle.listener_address is not None
    first_sock = DataSocket(controller_handle.listener_address, "First")
    late_sock = DataSocket(controller_handle.listener_address, "Late")
    completed: List[Tuple[int, bool]] = []
    try:
        first_sock.store_record(
            TableName("crawl_history"), visit_id, {"browser_id": 1, "command": "early"}
        )
        first_sock.finalize_visit_id(visit_id, first_success)
        if provider == "sqlite":
            # Arrow completes only once the file is written, i.e. at shutdown.
            deadline = time.monotonic() + 30
            while not completed and time.monotonic() < deadline:
                completed += controller_handle.get_new_completed_visits()
                time.sleep(0.1)
        late_sock.store_record(
            TableName("crawl_history"), visit_id, {"browser_id": 1, "command": "late"}
        )
        if second_finalize:
            late_sock.finalize_visit_id(visit_id, not first_success)
    finally:
        first_sock.close()
        late_sock.close()
        controller_handle.shutdown()
    completed += controller_handle.get_new_completed_visits()
    assert completed == [(visit_id, first_success)]
    assert _read_crawl(provider, tmp_path) == (
        ["early", "late"],
        0 if first_success else 1,
    )


def test_late_records_keep_arrow_file_count(
    mp_logger: MPLogger, tmp_path: Path
) -> None:
    """In a crawl every visit's FinalizeCommand row follows its finalize.
    Those late rows must not make the Arrow cache flush more often."""
    visits = 2 * CACHE_SIZE + 100
    controller_handle = StorageControllerHandle(LocalArrowProvider(tmp_path), None)
    controller_handle.launch()
    assert controller_handle.listener_address is not None
    sock = DataSocket(controller_handle.listener_address, "TaskManager")
    try:
        for i in range(1, visits + 1):
            visit_id = VisitId(i)
            sock.store_record(
                TableName("site_visits"), visit_id, {"browser_id": 1, "site_url": "x"}
            )
            sock.store_record(
                TableName("crawl_history"),
                visit_id,
                {"browser_id": 1, "command": "GetCommand"},
            )
            sock.finalize_visit_id(visit_id, True)
            sock.store_record(
                TableName("crawl_history"),
                visit_id,
                {"browser_id": 1, "command": "FinalizeCommand"},
            )
    finally:
        sock.close()
        # Drain completions while shutting down, or the controller process
        # blocks on a full completion queue.
        closer = threading.Thread(target=controller_handle.shutdown)
        closer.start()
        completed: List[Tuple[int, bool]] = []
        while closer.is_alive():
            completed += controller_handle.get_new_completed_visits()
            closer.join(0.1)
    completed += controller_handle.get_new_completed_visits()
    assert sorted(completed) == [(i, True) for i in range(1, visits + 1)]
    for table in ("site_visits", "crawl_history"):
        # Cache-full flushes after CACHE_SIZE + 1 visits, twice; then shutdown.
        assert len(list((tmp_path / table).rglob("*.parquet"))) == 3, table
    assert pq.read_table(tmp_path / "site_visits").num_rows == visits
    assert pq.read_table(tmp_path / "crawl_history").num_rows == 2 * visits


LATE_ROW = {"browser_id": 1, "visit_id": 1000}


async def _finalized_controller(
    success: bool,
) -> Tuple[StorageController, MemoryArrowProvider]:
    """A controller whose visit 1000 was finalized after one record"""
    provider = MemoryArrowProvider()
    await provider.init()
    controller = StorageController(provider, None, Queue(), Queue(), Queue())
    await controller.store_record(
        TableName("crawl_history"), VisitId(1000), {**LATE_ROW, "command": "early"}
    )
    await controller._handle_meta(
        VisitId(1000),
        {"action": ACTION_TYPE_FINALIZE, "success": success},
        writer=None,  # type: ignore[arg-type]
    )
    return controller, provider


@pytest.mark.asyncio
async def test_late_records_are_flushed_together(mp_logger: MPLogger) -> None:
    """A stalled extension's backlog after the visit was finalized must not
    become one batch per record."""
    controller, provider = await _finalized_controller(success=False)
    for i in range(1200):
        await controller.store_record(
            TableName("crawl_history"),
            VisitId(1000),
            {**LATE_ROW, "command": f"late{i}"},
        )
    await asyncio.gather(*controller._late_flush_tasks)
    batches = provider._batches[TableName("crawl_history")]
    assert sum(b.num_rows for b in batches) == 1201
    assert len(batches) == 2
    assert [(v, s) for v, _, s in controller.finalize_tasks] == [(1000, False)]


@pytest.mark.asyncio
async def test_completion_waits_for_late_records(mp_logger: MPLogger) -> None:
    """A visit whose finalize filled the Arrow cache is written right away, but
    its late records land in the next file. Its completion must wait for it."""
    controller, provider = await _finalized_controller(success=True)
    await provider.flush_cache()
    await controller.store_record(
        TableName("crawl_history"), VisitId(1000), {**LATE_ROW, "command": "late"}
    )
    await asyncio.gather(*controller._late_flush_tasks)
    ((_, token, _),) = controller.finalize_tasks
    assert token is not None and not token.done()
    await provider.flush_cache()
    await asyncio.sleep(0)
    assert token.done()
