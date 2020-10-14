import logging
import random
from abc import abstractmethod
from typing import Any, DefaultDict, Dict, List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow import Table

from automation.types import VisitId

from .parquet_schema import PQ_SCHEMAS
from .storage_providers import StructuredStorageProvider, TableName

SITE_VISITS_INDEX = TableName("_site_visits_index")
INCOMPLETE_VISITS = TableName("incomplete_visits")
CACHE_SIZE = 500


class ArrowProvider(StructuredStorageProvider):
    """This class implements a StructuredStorage provider that
    serializes records into the arrow format
    """

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger("openwpm")

        def factory_function() -> DefaultDict[TableName, List[Dict[str, Any]]]:
            return DefaultDict(list)

        # Raw records per VisitId and Table
        self._records: DefaultDict[
            VisitId, DefaultDict[TableName, List[Dict[str, Any]]]
        ] = DefaultDict(factory_function)

        # Record batches by TableName
        self._batches: DefaultDict[TableName, List[pa.RecordBatch]] = DefaultDict(list)
        self._signals = list()

        self._instance_id = random.getrandbits(32)

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
                "Trying to create batch for visit_id %d" "when one was already created",
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
            # We construct a special index file from the site_visits data
            # to make it easier to query the dataset
            if table_name == "site_visits":
                for item in data:
                    self._batches[SITE_VISITS_INDEX].append(item)

        del self._records[visit_id]

    @abstractmethod
    async def write_table(self, table: Table) -> None:
        """Write out the table to persistent storage"""

    def _is_cache_full(self) -> bool:
        for batches in self._batches.values():
            if len(batches) > CACHE_SIZE:
                return True
        return False

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> None:
        if interrupted:
            await self.store_record(INCOMPLETE_VISITS, visit_id, {"visit_id": visit_id})

        self._create_batch(visit_id)
        if self._is_cache_full():
            await self.flush_cache()

        raise NotImplementedError()

    async def flush_cache(self) -> None:
        raise NotImplementedError()
