import pytest

from automation.data_aggregator.in_memory_storage import MemoryStructuredProvider

pytestmark = pytest.mark.pyonly


def test_construction():
    assert MemoryStructuredProvider()


def test_basic_acess():
    prov = MemoryStructuredProvider()
    prov.store_record("test", {"visit_id": 2, "data": "test"})
    prov.run_visit_completion_tasks(2)
    assert prov.saved_visit_ids() == [(2, False)]
    assert prov.storage == {"test": [{"visit_id": 2, "data": "test"}]}
