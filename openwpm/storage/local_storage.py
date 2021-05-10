import logging
from pathlib import Path

import pyarrow.parquet as pq
from pyarrow.lib import Table

from .arrow_storage import ArrowProvider
from .storage_providers import TableName, UnstructuredStorageProvider


class LocalArrowProvider(ArrowProvider):
    """Stores Parquet files under storage_path/table_name/n.parquet"""

    def __init__(self, storage_path: Path) -> None:
        super().__init__()
        self.storage_path = storage_path

    async def write_table(self, table_name: TableName, table: Table) -> None:
        pq.write_to_dataset(table, str(self.storage_path / table_name))


class LocalGzipProvider(UnstructuredStorageProvider):
    """Stores files as storage_path/hash.zip"""

    async def init(self) -> None:
        pass

    def __init__(self, storage_path: Path) -> None:
        super().__init__()
        self.storage_path = storage_path
        self.logger = logging.getLogger("openwpm")

    async def store_blob(
        self, filename: str, blob: bytes, overwrite: bool = False
    ) -> None:
        path = self.storage_path / (filename + ".zip")
        if path.exists() and not overwrite:
            self.logger.debug(
                "File %s already exists on disk. Not overwriting", filename
            )
            return
        compressed = self._compress(blob)
        with path.open(mode="wb") as f:
            f.write(compressed.read())

    async def flush_cache(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass
