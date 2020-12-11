import asyncio
from typing import Any, Dict, List, Tuple, Union

import pytest
from _pytest.fixtures import FixtureRequest

from openwpm.storage.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)
from openwpm.storage.leveldb import LevelDbProvider
from openwpm.storage.local_storage import LocalGzipProvider
from openwpm.storage.sql_provider import SqlLiteStorageProvider
from openwpm.storage.storage_providers import (
    StructuredStorageProvider,
    TableName,
    UnstructuredStorageProvider,
)
from openwpm.types import VisitId

from ..openwpmtest import OpenWPMTest

memory_structured = "memory_structured"
sqllite = "sqllite"
memory_arrow = "memory_arrow"


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
    assert isinstance(
        request, FixtureRequest
    )  # See https://github.com/pytest-dev/pytest/issues/8073 for why this can't be type annotated
    request.raiseerror("invalid internal test config")


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
class TestStructuredStorageProvider:
    scenarios: List[Tuple[str, Dict[str, Any]]] = [
        (memory_structured, {"structured_provider": memory_structured}),
        (sqllite, {"structured_provider": sqllite}),
        (memory_arrow, {"structured_provider": memory_arrow}),
    ]

    async def test_basic_access(
        self, structured_provider: StructuredStorageProvider
    ) -> None:
        data = {
            "visit_id": 2,
            "browser_id": 3,
            "site_url": "https://example.com",
        }

        await structured_provider.init()

        await structured_provider.store_record(
            TableName("site_visits"), VisitId(2), data
        )
        token = await structured_provider.finalize_visit_id(VisitId(2))
        await structured_provider.flush_cache()
        await token


# Unstructured Providers
memory_unstructured = "memory_unstructured"
leveldb = "leveldb"
local_gzip = "local_gzip"


@pytest.fixture
def unstructured_provider(
    request: Any, tmp_path_factory: Any
) -> UnstructuredStorageProvider:
    if request.param == memory_unstructured:
        return MemoryUnstructuredProvider()
    elif request.param == leveldb:
        tmp_path = tmp_path_factory.mktemp(leveldb)
        return LevelDbProvider(tmp_path / "content.ldb")
    elif request.param == local_gzip:
        tmp_path = tmp_path_factory.mktemp(local_gzip)
        return LocalGzipProvider(tmp_path)
    assert isinstance(
        request, FixtureRequest
    )  # See https://github.com/pytest-dev/pytest/issues/8073 for why this can't be type annotated
    request.raiseerror("invalid internal test config")


@pytest.mark.asyncio
class TestUnstructuredStorageProvide:
    scenarios: List[Tuple[str, Dict[str, Any]]] = [
        (memory_unstructured, {"unstructured_provider": memory_unstructured}),
        (leveldb, {"unstructured_provider": leveldb}),
        (local_gzip, {"unstructured_provider": local_gzip}),
    ]

    async def test_basic_unstructured_storing(
        self, unstructured_provider: UnstructuredStorageProvider
    ) -> None:
        test_string = "This is my test string"
        blob = test_string.encode()
        await unstructured_provider.init()
        await unstructured_provider.store_blob("test", blob)
        await unstructured_provider.flush_cache()
