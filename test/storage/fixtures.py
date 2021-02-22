from typing import Any, List

import pytest
from _pytest.fixtures import FixtureRequest

from openwpm.storage.in_memory_storage import (
    MemoryArrowProvider,
    MemoryStructuredProvider,
    MemoryUnstructuredProvider,
)
from openwpm.storage.leveldb import LevelDbProvider
from openwpm.storage.local_storage import LocalGzipProvider
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_controller import INVALID_VISIT_ID
from openwpm.storage.storage_providers import (
    StructuredStorageProvider,
    UnstructuredStorageProvider,
)
from test.storage.test_values import dt_test_values, generate_test_values

memory_structured = "memory_structured"
sqlite = "sqlite"
memory_arrow = "memory_arrow"


@pytest.fixture
def structured_provider(
    request: Any, tmp_path_factory: Any
) -> StructuredStorageProvider:
    if request.param == memory_structured:
        return MemoryStructuredProvider()
    elif request.param == sqlite:
        tmp_path = tmp_path_factory.mktemp("sqlite")
        return SQLiteStorageProvider(tmp_path / "test_db.sqlite")
    elif request.param == memory_arrow:
        return MemoryArrowProvider()
    assert isinstance(
        request, FixtureRequest
    )  # See https://github.com/pytest-dev/pytest/issues/8073 for why this can't be type annotated
    request.raiseerror("invalid internal test config")


structured_scenarios: List[str] = [
    memory_structured,
    sqlite,
    memory_arrow,
]

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


@pytest.fixture
def test_values() -> dt_test_values:
    data, visit_ids = generate_test_values()
    for table in data.values():
        table["visit_id"] = (
            table["visit_id"] if "visit_id" in table else INVALID_VISIT_ID
        )
    visit_ids.add(INVALID_VISIT_ID)
    return data, visit_ids
