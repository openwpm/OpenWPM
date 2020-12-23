import gzip
import io
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Awaitable, Dict, List, NewType, Optional, Tuple

from openwpm.types import VisitId

"""
This module contains all base classes of the storage provider hierachy
Any subclass of these classes should be able to be used in OpenWPM
without any changes to the rest of the code base
"""

TableName = NewType("TableName", str)


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
        """ Blockingly write out any cached data to the respective storage """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Close all open resources
        After this method has been called no further calls should be made to the object
        """
        pass


class StructuredStorageProvider(StorageProvider):
    def __init__(self) -> None:
        super().__init__()

    # TODO: Discuss if we want visit_id here
    # It will always be part of the record and make the interface bigger
    # than it needs to be
    # But not having to access the data is also convenient
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
    ) -> Awaitable[None]:
        """This method is invoked to inform the StructuredStorageProvider that no more
        records for this visit_id will be submitted

        This method returns an awaitable that will resolve once the records have been
        saved out to persistent storage
        """
        pass


class UnstructuredStorageProvider(StorageProvider):
    @abstractmethod
    async def store_blob(
        self, filename: str, blob: bytes, overwrite: bool = False,
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
