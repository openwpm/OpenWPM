import random
from abc import abstractmethod
from typing import Any, Dict, List

from pyarrow import Table

from automation.types import VisitId

from .parquet_schema import PQ_SCHEMAS
from .storage_providers import StructuredStorageProvider


class ArrowProvider(StructuredStorageProvider):
    """This class implements a StructuredStorage provider that
    serializes records into the arrow format
    """

    def __init__(self) -> None:
        super().__init__()
        self._records: Dict[VisitId, Dict[str, List[Dict[str, Any]]]] = {}
        self._instance_id = random.getrandbits(32)

    async def store_record(
        self, table: str, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        records = self._records[visit_id]
        # Add nulls
        for item in PQ_SCHEMAS[table].names:
            if item not in record:
                record[item] = None
        # Add instance_id (for partitioning)
        record["instance_id"] = self._instance_id
        records[table].append(record)

    @abstractmethod
    async def write_table(self, table: Table) -> None:
        """Write out the table to persistent storage"""
