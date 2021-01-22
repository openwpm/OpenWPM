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


structured_scenarios: List[str] = [
    memory_structured,
    sqllite,
    memory_arrow,
]


@pytest.mark.parametrize("structured_provider", structured_scenarios, indirect=True)
@pytest.mark.asyncio
async def test_basic_access(structured_provider: StructuredStorageProvider) -> None:
    data = {
        "visit_id": 2,
        "browser_id": 3,
        "site_url": "https://example.com",
    }

    await structured_provider.init()

    await structured_provider.store_record(TableName("site_visits"), VisitId(2), data)
    token = await structured_provider.finalize_visit_id(VisitId(2))
    await structured_provider.flush_cache()
    if token is not None:
        await token
    await structured_provider.shutdown()


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


unstructured_scenarios: List[str] = [memory_unstructured, leveldb, local_gzip]


@pytest.mark.parametrize("unstructured_provider", unstructured_scenarios, indirect=True)
@pytest.mark.asyncio
async def test_basic_unstructured_storing(
    unstructured_provider: UnstructuredStorageProvider,
) -> None:
    test_string = "This is my test string"
    blob = test_string.encode()
    await unstructured_provider.init()
    await unstructured_provider.store_blob("test", blob)
    await unstructured_provider.flush_cache()
    await unstructured_provider.shutdown()
