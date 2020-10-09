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
    agg_handle.shutdown()
