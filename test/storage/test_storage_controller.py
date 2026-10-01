from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from openwpm.mp_logger import MPLogger
from openwpm.storage.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
)
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_controller import (
    INVALID_VISIT_ID,
    DataSocket,
    StorageControllerHandle,
)
from openwpm.storage.storage_providers import TableName
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
