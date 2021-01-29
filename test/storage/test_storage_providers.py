import asyncio

import pytest
from pandas import DataFrame
from pyarrow.parquet import ParquetDataset

from openwpm.storage.local_storage import LocalArrowProvider
from openwpm.storage.storage_controller import INVALID_VISIT_ID
from openwpm.storage.storage_providers import (
    StructuredStorageProvider,
    TableName,
    UnstructuredStorageProvider,
)
from openwpm.types import VisitId

from .fixtures import structured_scenarios, unstructured_scenarios
from .test_values import TEST_VALUES


@pytest.mark.asyncio
async def test_local_arrow_storage_provider(tmp_path, mp_logger):
    structured_provider = LocalArrowProvider(tmp_path)
    await structured_provider.init()
    visit_ids = set()
    for table_name, test_data in TEST_VALUES.items():
        try:
            visit_id = VisitId(test_data["visit_id"])
        except KeyError:
            visit_id = INVALID_VISIT_ID
        visit_ids.add(visit_id)
        await structured_provider.store_record(
            TableName(table_name), visit_id, test_data
        )
    token_list = []
    for i in visit_ids:
        token_list.append(await structured_provider.finalize_visit_id(i))
    await structured_provider.flush_cache()
    await asyncio.gather(*token_list)
    for table_name, test_data in TEST_VALUES.items():
        dataset = ParquetDataset(tmp_path / table_name)
        df: DataFrame = dataset.read().to_pandas()
        assert df.shape[0] == 1
        for row in df.itertuples(index=False):
            assert row._asdict() == test_data


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
