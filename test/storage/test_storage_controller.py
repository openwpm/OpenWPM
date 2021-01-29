import asyncio
import logging
import time

import pandas as pd
import pytest
from multiprocess import Queue
from pandas.testing import assert_frame_equal

from openwpm.mp_logger import MPLogger
from openwpm.socket_interface import ClientSocket
from openwpm.storage.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)
from openwpm.storage.storage_controller import (
    ACTION_TYPE_FINALIZE,
    INVALID_VISIT_ID,
    RECORD_TYPE_META,
    SHUTDOWN_SIGNAL,
    DataSocket,
    StorageController,
    StorageControllerHandle,
)
from test.storage.test_values import TEST_VALUES, TEST_VISIT_IDS


def test_startup_and_shutdown(mp_logger: MPLogger) -> None:
    structured = MemoryStructuredProvider()
    controller_handle = StorageControllerHandle(structured, None)
    controller_handle.launch()
    assert controller_handle.listener_address is not None
    cs = DataSocket(controller_handle.listener_address)
    for table, data in TEST_VALUES.items():
        visit_id = data["visit_id"] if "visit_id" in data else INVALID_VISIT_ID
        cs.store_record(
            table, visit_id, dict(**data)
        )  # cloning to avoid the modifications in store_record

    for visit_id in [*TEST_VISIT_IDS, INVALID_VISIT_ID]:
        cs.finalize_visit_id(visit_id, True)
    cs.close()
    controller_handle.shutdown()

    handle = structured.handle
    handle.poll_queue()
    for table, data in TEST_VALUES.items():
        assert handle.storage[table] == [data]


def test_arrow_provider(mp_logger: MPLogger) -> None:
    structured = MemoryArrowProvider()
    controller_handle = StorageControllerHandle(structured, None)
    controller_handle.launch()

    assert controller_handle.listener_address is not None
    cs = DataSocket(controller_handle.listener_address)

    for table, data in TEST_VALUES.items():
        visit_id = data["visit_id"] if "visit_id" in data else INVALID_VISIT_ID
        cs.store_record(
            table, visit_id, dict(**data)
        )  # cloning to avoid the modifications in store_record

    for visit_id in [*TEST_VISIT_IDS, INVALID_VISIT_ID]:
        cs.finalize_visit_id(visit_id, True)
    cs.close()
    controller_handle.shutdown()

    handle = structured.handle
    handle.poll_queue()
    for table, data in TEST_VALUES.items():

        t1 = handle.storage[table][0].to_pandas().drop(columns=["instance_id"])
        t2 = pd.DataFrame({k: [v] for k, v in data.items()})
        # Since t2 doesn't get created schema the inferred types are different
        assert_frame_equal(t1, t2, check_dtype=False)
