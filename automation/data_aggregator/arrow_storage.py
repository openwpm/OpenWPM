from abc import abstractmethod

from pyarrow import Table

from .parquet_schema import PQ_SCHEMAS
from .storage_providers import StructuredStorageProvider


class ArrowAggregator(StructuredStorageProvider):
    """This class implements a StructuredStorage provider that
    serializes records into the arrow format
    """

    def flush_cache(self):
        pass

    def store_record(self, table: str, record: Dict[str, Any], visit_id: int) -> None:
        records = self._records[visit_id]
        # Add nulls
        for item in PQ_SCHEMAS[table].names:
            if item not in record:
                data[item] = None
        # Add instance_id (for partitioning)
        record["instance_id"] = self._instance_id
        records[table].append(record)

    @abstractmethod
    def write_table(self, table: Table) -> None:
        """Write out the table to persistent storage"""
