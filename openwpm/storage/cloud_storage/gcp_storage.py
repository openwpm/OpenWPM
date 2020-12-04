from pyarrow.lib import Table

from ..arrow_storage import ArrowProvider
from ..storage_providers import TableName, UnstructuredStorageProvider


class GcsStructuredProvider(ArrowProvider):
    """This class allows you to upload Parquet files to GCS.
    This might not actually be the thing that we want to do
    long term but seeing as GCS is the S3 equivalent of GCP
    it is the easiest way forward.
    """

    def __init__(self):
        super().__init__()

    async def write_table(self, table_name: TableName, table: Table) -> None:
        pass

    async def shutdown(self) -> None:
        pass
