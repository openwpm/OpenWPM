import logging
from typing import Any, Set

import pyarrow.parquet as pq
from pyarrow.lib import Table
from s3fs import S3FileSystem

from ..arrow_storage import ArrowProvider
from ..storage_providers import TableName, UnstructuredStorageProvider


class S3StructuredProvider(ArrowProvider):
    """This class allows you to upload Parquet files to S3.

    S3StructuredProvider will by default store into
    base_path/visits/table_name in the given bucket.
    Pass a different sub_dir to change this.

    **kwargs get passed on to S3FileSystem.__init__
    Please look at https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem
    for further information
    """

    file_system: S3FileSystem

    def __init__(
        self, bucket_name: str, base_path: str, sub_dir: str = "visits", **kwargs: Any
    ) -> None:
        super().__init__()
        self.kwargs = kwargs
        self.base_path = f"{bucket_name}/{base_path}/{sub_dir}/{{table_name}}"

    def __str__(self) -> str:
        return f"S3FS:{self.base_path.removesuffix('/{table_name}')}"

    async def init(self) -> None:
        await super(S3StructuredProvider, self).init()
        self.file_system = S3FileSystem(**self.kwargs)

    async def write_table(self, table_name: TableName, table: Table) -> None:
        self.file_system.start_transaction()
        pq.write_to_dataset(
            table,
            self.base_path.format(table_name=table_name),
            filesystem=self.file_system,
        )
        self.file_system.end_transaction()


class S3UnstructuredProvider(UnstructuredStorageProvider):
    """This class allows you to upload arbitrary bytes to S3.
    They will be stored under bucket_name/base_path/filename

    **kwargs get passed on to S3FileSystem.__init__
    Please look at https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem
    for further information
    """

    file_system: S3FileSystem

    def __init__(self, bucket_name: str, base_path: str, **kwargs: Any) -> None:
        super().__init__()
        self.kwargs = kwargs
        self.bucket_name = bucket_name
        self.base_path = base_path
        self.base_path = f"{bucket_name}/{base_path}/{{filename}}"

        self.file_name_cache: Set[str] = set()
        """The set of all filenames ever uploaded, checked before uploading"""
        self.logger = logging.getLogger("openwpm")

    async def init(self) -> None:
        await super(S3UnstructuredProvider, self).init()
        self.file_system = S3FileSystem(**self.kwargs)

    async def store_blob(
        self, filename: str, blob: bytes, overwrite: bool = False
    ) -> None:
        target_path = self.base_path.format(filename=filename)
        if not overwrite and (
            filename in self.file_name_cache or self.file_system.exists(target_path)
        ):
            self.logger.info("Not saving out file %s as it already exists", filename)
            return
        self.file_system.start_transaction()

        with self.file_system.open(target_path, mode="wb") as f:
            f.write(blob)

        self.file_system.end_transaction()

        self.file_name_cache.add(filename)

    async def flush_cache(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass
