import pytest

from automation.data_aggregator.in_memory_storage import (
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)
from automation.types import VisitId

pytestmark = pytest.mark.pyonly


def test_structured_construction():
    assert MemoryStructuredProvider()


def test_basic_access():
    prov = MemoryStructuredProvider()
    prov.store_record("test", VisitId(2), {"visit_id": 2, "data": "test"})
    prov.run_visit_completion_tasks(VisitId(2))
    assert prov.saved_visit_ids() == [(2, False)]
    assert prov.storage == {"test": [{"visit_id": 2, "data": "test"}]}


def test_unstructured_construction():
    assert MemoryUnstructuredProvider()


def test_basic_unstructured_storing():
    test_string = "This is my test string"
    blob = test_string.encode()
    prov = MemoryUnstructuredProvider()
    prov.store_blob("test", blob, compressed=False)
