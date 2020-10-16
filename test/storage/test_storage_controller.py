import logging
import time

import pytest

from automation.MPLogger import MPLogger
from automation.SocketInterface import ClientSocket
from automation.storage.in_memory_storage import (
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)
from automation.storage.storage_controller import StorageControllerHandle


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
    data = {"visit_id": 1, "asd": "dfg"}
    structured = MemoryStructuredProvider()
    unstructured = MemoryUnstructuredProvider()
    agg_handle = StorageControllerHandle(structured, unstructured)
    agg_handle.launch()
    assert agg_handle.listener_address is not None
    cs = ClientSocket()
    cs.connect(*agg_handle.listener_address)
    cs.send(("test", data))
    agg_handle.shutdown()
    handle = structured.handle
    handle.poll_queue()
    assert handle.storage["test"] == [data]
