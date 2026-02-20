from typing import Any, Type, Union

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from openwpm.mp_logger import MPLogger
from openwpm.storage.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
)
from openwpm.storage.in_process_storage import InProcessStorageControllerHandle
from openwpm.storage.storage_controller import (
    INVALID_VISIT_ID,
    DataSocket,
    StorageControllerHandle,
)
from test.storage.test_values import dt_test_values

HandleCls = Type[Union[StorageControllerHandle, InProcessStorageControllerHandle]]


@pytest.fixture(params=["subprocess", "in_process"])
def controller_handle_cls(request: Any) -> HandleCls:
    if request.param == "subprocess":
        return StorageControllerHandle
    else:
        return InProcessStorageControllerHandle


def test_startup_and_shutdown(
    mp_logger: MPLogger, test_values: dt_test_values, controller_handle_cls: HandleCls
) -> None:
    test_table, visit_ids = test_values
    structured = MemoryStructuredProvider()
    controller_handle = controller_handle_cls(structured, None)
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


def test_arrow_provider(
    mp_logger: MPLogger, test_values: dt_test_values, controller_handle_cls: HandleCls
) -> None:
    test_table, visit_ids = test_values
    structured = MemoryArrowProvider()
    controller_handle = controller_handle_cls(structured, None)
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
