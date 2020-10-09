from automation.SocketInterface import ClientSocket
from automation.storage.in_memory_storage import (
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)
from automation.storage.storage_controller import StorageControllerHandle


def test_startup_and_shutdown() -> None:
    structured = MemoryStructuredProvider()
    unstructured = MemoryUnstructuredProvider()
    agg_handle = StorageControllerHandle(structured, unstructured)
    agg_handle.launch()
    print(agg_handle.listener_address)
    cs = ClientSocket()
    cs.connect(*agg_handle.listener_address)
    cs.send(("test", {"asd": "dfg"}))
    agg_handle.shutdown()
    handle = structured.handle
    handle.poll_queue()
    assert handle.storage["test"] == {"asd": "dfg"}
