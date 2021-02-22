import asyncio
import logging
import random
from abc import abstractmethod
from asyncio import Task
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List

import pandas as pd
import pyarrow as pa
from pyarrow import Table

from openwpm.types import VisitId

from .parquet_schema import PQ_SCHEMAS
from .storage_providers import INCOMPLETE_VISITS, StructuredStorageProvider, TableName

CACHE_SIZE = 500


class ArrowProvider(StructuredStorageProvider):
    """This class implements a StructuredStorage provider that
    serializes records into the arrow format
    """

    storing_lock: asyncio.Lock

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger("openwpm")

        def factory_function() -> DefaultDict[TableName, List[Dict[str, Any]]]:
            return defaultdict(list)

        # Raw records per VisitId and Table
        self._records: DefaultDict[
            VisitId, DefaultDict[TableName, List[Dict[str, Any]]]
        ] = defaultdict(factory_function)

        # Record batches by TableName
        self._batches: DefaultDict[TableName, List[pa.RecordBatch]] = defaultdict(list)
        self._instance_id = random.getrandbits(32)

        self.flush_events: List[asyncio.Event] = list()

    async def init(self) -> None:
        # Used to synchronize the finalizing and the flushing
        self.storing_lock = asyncio.Lock()

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        records = self._records[visit_id]
        # Add nulls
        for item in PQ_SCHEMAS[table].names:
            if item not in record:
                record[item] = None
        # Add instance_id (for partitioning)
        record["instance_id"] = self._instance_id
        records[table].append(record)

    def _create_batch(self, visit_id: VisitId) -> None:
        """Create record batches for all records from `visit_id`"""
        if visit_id not in self._records:
            # The batch for this `visit_id` was already created, skip
            self.logger.error(
                "Trying to create batch for visit_id %d when one was already created",
                visit_id,
            )
            return
        for table_name, data in self._records[visit_id].items():
            try:
                df = pd.DataFrame(data)
                batch = pa.RecordBatch.from_pandas(
                    df, schema=PQ_SCHEMAS[table_name], preserve_index=False
                )
                self._batches[table_name].append(batch)
                self.logger.debug(
                    "Successfully created batch for table %s and "
                    "visit_id %s" % (table_name, visit_id)
                )
            except pa.lib.ArrowInvalid:
                self.logger.error(
                    "Error while creating record batch for table %s\n" % table_name,
                    exc_info=True,
                )
                pass

        del self._records[visit_id]

    def _is_cache_full(self) -> bool:
        for batches in self._batches.values():
            if len(batches) > CACHE_SIZE:
                return True
        return False

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> Task[None]:
        """This method is the reason the finalize_visit_id interface returns a task.
        This was necessary as we needed to enable the following pattern.
        ```
            token = await structured_storage.finalize_visit_id(1)
            structured_storage.flush_cache()
            await token
        ```
        If there was no task returned and the method would just block/yield after turning the
        record into a batch, there would be no way to know, when it's safe to flush_cache as
        I couldn't find a way to run a coroutine until it yields and then run a different one.

        With the current setup `token` aka a `wait_on_condition` coroutine will only return once
        it's respective event has been set.
        """
        if interrupted:
            await self.store_record(INCOMPLETE_VISITS, visit_id, {"visit_id": visit_id})
        # This code is pretty tricky as there are a number of things going on
        # 1. The awaitable returned by finalize_visit_id should only
        #    resolve once the data is saved to persistent storage
        # 2. No new batches should be created while saving out all the batches
        async with self.storing_lock:
            self._create_batch(visit_id)

            event = asyncio.Event()
            self.flush_events.append(event)

            if self._is_cache_full():
                await self.flush_cache(self.storing_lock)

            async def wait_on_condition(e: asyncio.Event) -> None:
                await e.wait()

            return asyncio.create_task(wait_on_condition(event))

    @abstractmethod
    async def write_table(self, table_name: TableName, table: Table) -> None:
        """Write out the table to persistent storage
        This should only return once it's actually saved out
        """

    async def flush_cache(self, lock: asyncio.Lock = None) -> None:
        """We need to hack around the fact that asyncio has no reentrant lock
        So we either grab the storing_lock ourselves or the caller needs
        to pass us the locked storing_lock
        """
        has_lock_arg = lock is not None
        if not has_lock_arg:
            lock = self.storing_lock
            await lock.acquire()

        assert lock == self.storing_lock and lock.locked()

        for table_name, batches in self._batches.items():
            table = pa.Table.from_batches(batches)
            await self.write_table(table_name, table)
        self._batches.clear()

        for event in self.flush_events:
            event.set()
        self.flush_events.clear()

        if not has_lock_arg:
            lock.release()

    async def shutdown(self) -> None:
        for table_name, batches in self._batches.items():
            if len(batches) != 0:
                self.logger.error(
                    "While shutting down there were %d cached entries for table %s",
                    len(batches),
                    table_name,
                )
