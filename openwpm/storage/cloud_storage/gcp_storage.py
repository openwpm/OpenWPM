import logging
from typing import Set

import pyarrow.parquet as pq
from gcsfs import GCSFileSystem
from pyarrow.lib import Table

from ..arrow_storage import ArrowProvider
from ..storage_providers import TableName, UnstructuredStorageProvider


class GcsStructuredProvider(ArrowProvider):
    """This class allows you to upload Parquet files to GCS.
    This might not actually be the thing that we want to do
    long term but seeing as GCS is the S3 equivalent of GCP
    it is the easiest way forward.

    Inspired by the old S3Aggregator structure the GcsStructuredProvider
    will by default store into
    base_path/visits/table_name in the given bucket.

    Pass a different sub_dir to change this.
    """

    file_system: GCSFileSystem

    def __init__(
        self,
        project: str,
        bucket_name: str,
        base_path: str,
        token: str = None,
        sub_dir: str = "visits",
    ) -> None:
        super().__init__()
        self.project = project
        self.token = token
        self.base_path = f"{bucket_name}/{base_path}/{sub_dir}/{{table_name}}"

    def __str__(self) -> str:
        return f"GCS:{self.base_path.removesuffix('/{table_name}')}"

    async def init(self) -> None:
        await super(GcsStructuredProvider, self).init()
        self.file_system = GCSFileSystem(
            project=self.project, token=self.token, access="read_write"
        )

    async def write_table(self, table_name: TableName, table: Table) -> None:
        pq.write_to_dataset(
            table,
            self.base_path.format(table_name=table_name),
            filesystem=self.file_system,
        )

    async def shutdown(self) -> None:
        pass


class GcsUnstructuredProvider(UnstructuredStorageProvider):
    """This class allows you to upload arbitrary bytes to GCS.
    They will be stored under bucket_name/base_path/filename
    """

    file_system: GCSFileSystem

    def __init__(
        self,
        project: str,
        bucket_name: str,
        base_path: str,
        token: str = None,
    ) -> None:
        super().__init__()
        self.project = project
        self.bucket_name = bucket_name
        self.base_path = base_path
        self.token = token
        self.base_path = f"{bucket_name}/{base_path}/{{filename}}"

        self.file_name_cache: Set[str] = set()
        """The set of all filenames ever uploaded, checked before uploading"""
        self.logger = logging.getLogger("openwpm")

    async def init(self) -> None:
        await super(GcsUnstructuredProvider, self).init()
        self.file_system = GCSFileSystem(
            project=self.project, token=self.token, access="read_write"
        )

    async def store_blob(
        self, filename: str, blob: bytes, overwrite: bool = False
    ) -> None:
        target_path = self.base_path.format(filename=filename)
        if not overwrite and (
            filename in self.file_name_cache or self.file_system.exists(target_path)
        ):
            self.logger.info("Not saving out file %s as it already exists", filename)
            return

        with self.file_system.open(target_path, mode="wb") as f:
            f.write(blob)

        self.file_name_cache.add(filename)

    async def flush_cache(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass
