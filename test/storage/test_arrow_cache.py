import asyncio
import random
from typing import Awaitable, Dict

import pytest
from pandas import DataFrame
from pyarrow.parquet import ParquetDataset

from openwpm.mp_logger import MPLogger
from openwpm.storage.arrow_storage import CACHE_SIZE
from openwpm.storage.in_memory_storage import MemoryArrowProvider
from openwpm.storage.storage_providers import TableName
from openwpm.types import VisitId
from test.storage.test_values import TEST_VALUES


@pytest.mark.asyncio
async def test_arrow_cache(mp_logger: MPLogger) -> None:
    prov = MemoryArrowProvider()
    await prov.init()
    site_visit = TEST_VALUES["site_visits"]
    d: Dict[VisitId, Awaitable[None]] = {}
    for i in range(CACHE_SIZE + 1):
        visit_id = VisitId(i)
        site_visit["visit_id"] = visit_id
        await prov.store_record(TableName("site_visits"), visit_id, site_visit)
        d[visit_id] = await prov.finalize_visit_id(visit_id)

    for visit_id in d:
        task = d[visit_id]
        await asyncio.wait_for(task, 1)
    await asyncio.sleep(1)
    handle = prov.handle
    # The queue should not be empty at this point
    handle.poll_queue(block=False)

    assert len(handle.storage["site_visits"]) == 1
    table = handle.storage["site_visits"][0]

    df: DataFrame = table.to_pandas()
    for row in df.itertuples(index=False):
        del d[row.visit_id]

    assert len(d) == 0
