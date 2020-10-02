import pytest

from automation.data_aggregator.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)
from automation.data_aggregator.leveldb import LevelDbProvider
from automation.data_aggregator.sql_provider import SqlLiteStorageProvider
from automation.types import VisitId

from ..openwpmtest import OpenWPMTest

memory_structured = "memory_structured"
sqllite = "sqllite"
memory_arrow = "memory_arrow"

# Unstructured Providers
memory_unstructured = "memory_unstructured"
leveldb = "leveldb"


structured_scenarios = [
    (memory_structured, {"structured_provider": memory_structured}),
    (sqllite, {"structured_provider": sqllite}),
    (memory_arrow, {"structured_provider": memory_arrow}),
]


@pytest.fixture
def structured_provider(request):
    print("Fixture was executed")
    if request.param == memory_structured:
        return MemoryStructuredProvider()
    elif request.param == sqllite:
        return SqlLiteStorageProvider()
    elif request.param == memory_arrow:
        return MemoryArrowProvider()
    else:
        return MemoryStructuredProvider()
        raise ValueError("invalid internal test config")


def pytest_generate_tests(metafunc):
    # Source: https://docs.pytest.org/en/latest/example/parametrize.html#a-quick-port-of-testscenarios  # noqa
    idlist = []
    argvalues = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append([x[1] for x in items])
    print("metafunc called")
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class", indirect=True)


class TestStructuredStorageProvider(OpenWPMTest):
    scenarios = structured_scenarios

    def test_basic_access(self, structured_provider):
        structured_provider.store_record(
            "test", VisitId(2), {"visit_id": 2, "data": "test"}
        )
        structured_provider.run_visit_completion_tasks(VisitId(2))
        structured_provider.flush_cache()
        assert structured_provider.saved_visit_ids() == [(2, False)]
        assert structured_provider.storage == {
            "test": [{"visit_id": 2, "data": "test"}]
        }


class TestUnstructuredStorageProvide(OpenWPMTest):
    scenarios = [(memory_unstructured, {})]

    def test_basic_unstructured_storing(self):
        test_string = "This is my test string"
        blob = test_string.encode()
        prov = MemoryUnstructuredProvider()
        prov.store_blob("test", blob, compressed=False)
