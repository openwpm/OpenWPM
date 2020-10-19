import asyncio
from typing import Any, Dict, List, Tuple

import pytest

from automation.storage.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)
from automation.storage.leveldb import LevelDbProvider
from automation.storage.sql_provider import SqlLiteStorageProvider
from automation.storage.storage_providers import StructuredStorageProvider, TableName
from automation.types import VisitId

from ..openwpmtest import OpenWPMTest

memory_structured = "memory_structured"
sqllite = "sqllite"
memory_arrow = "memory_arrow"

# Unstructured Providers
memory_unstructured = "memory_unstructured"
leveldb = "leveldb"


structured_scenarios: List[Tuple[str, Dict[str, Any]]] = [
    (memory_structured, {"structured_provider": memory_structured}),
    (sqllite, {"structured_provider": sqllite}),
    (memory_arrow, {"structured_provider": memory_arrow}),
]


@pytest.fixture
def structured_provider(
    request: Any, tmp_path_factory: Any
) -> StructuredStorageProvider:
    if request.param == memory_structured:
        return MemoryStructuredProvider()
    elif request.param == sqllite:
        tmp_path = tmp_path_factory.mktemp("sqllite")
        return SqlLiteStorageProvider(tmp_path / "test_db.sqllite")
    elif request.param == memory_arrow:
        return MemoryArrowProvider()
    raise ValueError("invalid internal test config")


def pytest_generate_tests(metafunc: Any) -> Any:
    # Source: https://docs.pytest.org/en/latest/example/parametrize.html#a-quick-port-of-testscenarios  # noqa
    idlist = []
    argvalues = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append([x[1] for x in items])
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class", indirect=True)


@pytest.mark.asyncio
class TestStructuredStorageProvider(OpenWPMTest):
    scenarios = structured_scenarios

    async def test_basic_access(
        self, structured_provider: StructuredStorageProvider
    ) -> None:
        data = {
            "visit_id": 2,
            "browser_id": 3,
            "instance_id": 4,
            "site_url": "https://example.com",
        }

        await structured_provider.store_record(
            TableName("site_visits"), VisitId(2), data
        )
        await structured_provider.finalize_visit_id(VisitId(2))
        await structured_provider.flush_cache()


@pytest.mark.asyncio
class TestUnstructuredStorageProvide(OpenWPMTest):
    scenarios: List[Tuple[str, Dict[str, Any]]] = [(memory_unstructured, {})]

    async def test_basic_unstructured_storing(self) -> None:
        test_string = "This is my test string"
        blob = test_string.encode()
        prov = MemoryUnstructuredProvider()
        prov.store_blob("test", blob, compressed=False)
