import asyncio

import pytest
from pandas import DataFrame
from pyarrow.parquet import ParquetDataset

from openwpm.storage.local_storage import LocalArrowProvider
from openwpm.storage.storage_providers import TableName
from openwpm.types import VisitId

from .test_values import TEST_VALUES


@pytest.mark.asyncio
async def test_local_arrow_storage_provider(tmp_path, mp_logger):
    structured_provider = LocalArrowProvider(tmp_path)
    visit_ids = set()
    for table_name, test_data in TEST_VALUES.items():
        visit_id = VisitId(test_data["visit_id"])
        visit_ids.add(visit_id)
        await structured_provider.store_record(
            TableName(table_name), visit_id, test_data
        )
    task_list = list(structured_provider.finalize_visit_id(i) for i in visit_ids)
    task_list.append(structured_provider.flush_cache())
    ret_vals = await asyncio.gather(*task_list)
    for table_name, test_data in TEST_VALUES.items():
        dataset = ParquetDataset(tmp_path / table_name)
        df: DataFrame = dataset.read().to_pandas()
        assert df.shape[0] == 1
        for row in df.itertuples(index=False):
            assert row._asdict() == test_data
