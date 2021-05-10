"""
This module contains all base classes of the storage provider hierarchy
Any subclass of these classes should be able to be used in OpenWPM
without any changes to the rest of the code base
"""
import gzip
import io
from abc import ABC, abstractmethod
from asyncio import Task
from typing import Any, Dict, NewType, Optional

from openwpm.types import VisitId

TableName = NewType("TableName", str)
INCOMPLETE_VISITS = TableName("incomplete_visits")


class StorageProvider(ABC):
    """Base class that defines some general helper methods
    Do not inherit from this class directly
    Inherit from StructuredStorageProvider or UnstructuredStorageProvider instead
    """

    @abstractmethod
    async def init(self) -> None:
        """Initializes the StorageProvider for use

        Guaranteed to be called in the process the
        StorageController runs in.
        """
        pass

    @abstractmethod
    async def flush_cache(self) -> None:
        """Blockingly write out any cached data to the respective storage"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Close all open resources
        After this method has been called no further calls should be made to the object
        """
        pass


class StructuredStorageProvider(StorageProvider):
    """Structured Storage Providers are responsible for handling all structured data
    that OpenWPM emits.
    This includes:
    - All data that is collected by the WebExtension instrumentation
    - Data about browser configuration and
    - Any data that custom commands send to the Storage Controller

    See docs/Schema-Documentation.md to see what an unmodified OpenWPM will attempt
    to store
    """

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        """Submit a record to be stored
        The storing might not happen immediately
        """
        pass

    @abstractmethod
    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> Optional[Task[None]]:
        """This method is invoked to inform the StructuredStorageProvider that no more
        records for this visit_id will be submitted

        This method returns once the data is ready to be written out.
        If the data is immediately written out nothing will be returned.
        Otherwise an awaitable will returned that resolve onces the records have been
        saved out to persistent storage
        """
        pass


class UnstructuredStorageProvider(StorageProvider):
    """Unstructured Storage Providers are responsible for handling the unstructured data
    that OpenWPM emits.
    This is primarily content loaded by websites.
    Don't make any assumptions about the data (especially don't assume it's valid unicode)

    In the future this interface will be expanded to address the needs of https://github.com/mozilla/OpenWPM/issues/232
    """

    @abstractmethod
    async def store_blob(
        self,
        filename: str,
        blob: bytes,
        overwrite: bool = False,
    ) -> None:
        """Stores the given bytes under the provided filename"""
        pass

    @staticmethod
    def _compress(blob: bytes) -> io.BytesIO:
        """Takes a byte blob and compresses it with gzip
        The returned BytesIO object is at stream position 0.
        This means it can be treated like a zip file on disk.
        """
        out_f = io.BytesIO()
        with gzip.GzipFile(fileobj=out_f, mode="w") as writer:
            writer.write(blob)
        out_f.seek(0)
        return out_f
