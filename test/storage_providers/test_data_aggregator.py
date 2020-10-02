from automation.data_aggregator import DataAggregatorHandle
from automation.data_aggregator.in_memory_storage import (
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)


def test_startup_and_shutdown():
    structured = MemoryStructuredProvider()
    unstructured = MemoryUnstructuredProvider()
    agg_handle = DataAggregatorHandle(structured, unstructured)
    agg_handle.launch()
    agg_handle.shutdown()
