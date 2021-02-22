import asyncio
from typing import Awaitable, Dict

import pytest
from pandas import DataFrame

from openwpm.mp_logger import MPLogger
from openwpm.storage.arrow_storage import CACHE_SIZE
from openwpm.storage.in_memory_storage import MemoryArrowProvider
from openwpm.storage.storage_providers import TableName
from openwpm.types import VisitId
from test.storage.test_values import dt_test_values


@pytest.mark.asyncio
async def test_arrow_cache(mp_logger: MPLogger, test_values: dt_test_values) -> None:
    prov = MemoryArrowProvider()
    await prov.init()
    site_visit = test_values[0][TableName("site_visits")]
    for j in range(5):  # Testing that the cache works repeatedly
        d: Dict[VisitId, Awaitable[None]] = {}
        for i in range(CACHE_SIZE + 1):
            visit_id = VisitId(i + j * 1000)
            site_visit["visit_id"] = visit_id
            await prov.store_record(TableName("site_visits"), visit_id, site_visit)
            d[visit_id] = await prov.finalize_visit_id(visit_id)

        for visit_id in d:
            await d[visit_id]

        await asyncio.sleep(1)
        handle = prov.handle
        # The queue should not be empty at this point
        handle.poll_queue(block=False)

        assert len(handle.storage["site_visits"]) == j + 1
        table = handle.storage["site_visits"][j]

        df: DataFrame = table.to_pandas()
        for row in df.itertuples(index=False):
            del d[row.visit_id]

        assert len(d) == 0
    await prov.shutdown()
