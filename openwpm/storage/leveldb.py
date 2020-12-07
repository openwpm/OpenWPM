from pathlib import Path
from typing import Optional

import plyvel
from plyvel._plyvel import WriteBatch

from .storage_providers import UnstructuredStorageProvider

LDB_BATCH_SIZE = 100


class LevelDbProvider(UnstructuredStorageProvider):
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ldb_counter = 0
        self._ldb_commit_time = 0
        self.ldb: Optional[plyvel.DB] = None
        self.content_batch: Optional[WriteBatch] = None

    async def init(self) -> None:
        self.ldb = plyvel.DB(
            str(self.db_path),
            create_if_missing=True,
            write_buffer_size=128 * 10 ** 6,
            compression="snappy",
        )
        self.content_batch = self.ldb.write_batch()

    async def flush_cache(self) -> None:
        """Write out content batch to LevelDB database"""
        assert self.content_batch is not None
        assert self.ldb is not None
        self.content_batch.write()
        self.content_batch = self.ldb.write_batch()

    async def shutdown(self) -> None:
        assert self.ldb is not None
        self.ldb.close()
        print("Ldb is closed:", self.ldb.closed)

    async def store_blob(
        self,
        filename: str,
        blob: bytes,
        overwrite: bool = False,
    ) -> None:
        assert self.ldb is not None
        assert self.content_batch is not None

        content_hash = str(filename).encode("ascii")
        if self.ldb.get(content_hash) is not None:
            return
        self.content_batch.put(content_hash, blob)
        self._ldb_counter += 1

        if self._ldb_counter >= LDB_BATCH_SIZE:
            await self.flush_cache()
