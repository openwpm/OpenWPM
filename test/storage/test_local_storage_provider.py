import asyncio

import pytest
from pandas import DataFrame
from pyarrow.parquet import ParquetDataset

from openwpm.storage.local_storage import LocalArrowProvider
from openwpm.storage.storage_providers import TableName
from openwpm.types import VisitId


@pytest.mark.asyncio
async def test_local_arrow_storage_provider(tmp_path):
    structured_provider = LocalArrowProvider(tmp_path)
    data = {
        "visit_id": 2,
        "browser_id": 3,
        "site_url": "https://example.com",
        "site_rank": 4,
    }
    await structured_provider.store_record(TableName("site_visits"), VisitId(2), data)
    await asyncio.gather(
        structured_provider.finalize_visit_id(VisitId(2)),
        structured_provider.flush_cache(),
    )
    dataset = ParquetDataset(tmp_path / "site_visits")
    df: DataFrame = dataset.read().to_pandas()
    assert df.shape[0] == 1
    for row in df.itertuples(index=False):
        assert row.visit_id == 2
        assert row.browser_id == 3
        assert row.site_rank == 4
        assert row.site_url == "https://example.com"
