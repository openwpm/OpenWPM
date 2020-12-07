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
    RECORD_TYPE_META,
    SHUTDOWN_SIGNAL,
    StorageController,
    StorageControllerHandle,
)
from test.storage.test_values import TEST_VALUES, TEST_VISIT_IDS


@pytest.fixture(scope="session")
def logger() -> MPLogger:
    """PyTest only captures logging events in the Main Process
    so we need to log everything to console to have it show
    up in our tests
    """
    return MPLogger(
        "/dev/null",
        None,  # We have no manager params here
        log_level_console=logging.DEBUG,
    )


def test_startup_and_shutdown(logger: MPLogger) -> None:

    structured = MemoryStructuredProvider()
    unstructured = MemoryUnstructuredProvider()
    agg_handle = StorageControllerHandle(structured, unstructured)
    agg_handle.launch()
    assert agg_handle.listener_address is not None
    cs = ClientSocket()
    cs.connect(*agg_handle.listener_address)
    for table, data in TEST_VALUES.items():
        cs.send((table, data))

    for visit_id in TEST_VISIT_IDS:
        cs.send(
            (
                RECORD_TYPE_META,
                {"action": ACTION_TYPE_FINALIZE, "visit_id": visit_id, "success": True},
            )
        )
    agg_handle.shutdown()
    handle = structured.handle
    handle.poll_queue()
    for table, data in TEST_VALUES.items():
        assert handle.storage[table] == [data]


@pytest.mark.asyncio
async def test_arrow_provider(logger: MPLogger) -> None:
    structured = MemoryArrowProvider()
    status_queue = Queue()
    completion_queue = Queue()
    shutdown_queue = Queue()

    storage_controller = StorageController(
        structured,
        None,
        status_queue=status_queue,
        completion_queue=completion_queue,
        shutdown_queue=shutdown_queue,
    )
    task = asyncio.create_task(storage_controller._run())
    cs = ClientSocket()
    while status_queue.empty():
        await asyncio.sleep(5)

    cs.connect(*status_queue.get())

    for table, data in TEST_VALUES.items():
        cs.send((table, data))

    # This sleep needs to be here because otherwise it is executing blockingly on the single thread,
    # so the server doesn't ever wake up
    await asyncio.sleep(1)
    shutdown_queue.put((SHUTDOWN_SIGNAL, True))
    await task

    handle = structured.handle
    handle.poll_queue()
    for table, data in TEST_VALUES.items():
        if table == "incomplete_visits":
            # We currently mark all of them as failed, because we don't bother sending a finalize command
            continue
        t1 = handle.storage[table][0].to_pandas().drop(columns=["instance_id"])
        t2 = pd.DataFrame({k: [v] for k, v in data.items()})
        # Since t2 doesn't get created schema the inferred types are different
        assert_frame_equal(t1, t2, check_dtype=False)
