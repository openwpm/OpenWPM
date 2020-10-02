import gzip
import io
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from automation.types import VisitId

"""
This module contains all base classes of the storage provider hierachy
Any subclass of these classes should be able to be used in OpenWPM
without any changes to the rest of the code base
"""


class StorageProvider(ABC):
    """Base class that defines some general helper methods
    Do not inherit from this class directly
    Inherit from StructuredStorageProvider or UnstructuredStorageProvider instead
    """

    @abstractmethod
    def flush_cache(self) -> None:
        """ Blockingly write out any cached data to the respective storage """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Close all open ressources
        After this method has been called no further calls should be made to the object
        """
        pass


class StructuredStorageProvider(StorageProvider):
    def __init__(self):
        super().__init__()
        self._completed_visit_ids: List[Tuple[VisitId, bool]] = list()

    def saved_visit_ids(self) -> List[Tuple[VisitId, bool]]:
        """Return the list of all visit_ids that have been saved to permanent storage
        since the last time this method was called

        For each visit_id it's also noted whether they were interrupted
        """
        temp = self._completed_visit_ids
        self._completed_visit_ids = list()
        return temp

    @abstractmethod
    def store_record(
        self, table: str, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        """Submit a record to be stored
        The storing might not happen immediately
        """
        pass

    @abstractmethod
    def run_visit_completion_tasks(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> None:
        """This method is invoked to inform the StrucuturedStorageProvider that no more
        records for this visit_id will be submitted
        """
        pass


class UnstructuredStorageProvider(StorageProvider):
    @abstractmethod
    def store_blob(
        self,
        filename: str,
        blob: bytes,
        compressed: bool = True,
        skip_if_exists: bool = True,
    ) -> None:
        """Stores the given bytes under the provided filename"""
        pass

    def _compress(self, blob: bytes) -> io.BytesIO:
        """Takes a byte blob and compresses it with gzip
        The returned BytesIO object is at stream position 0.
        This means it can be treated like a zip file on disk.
        """
        out_f = io.BytesIO()
        with gzip.GzipFile(fileobj=out_f, mode="w") as writer:
            writer.write(blob)
        out_f.seek(0)
        return out_f
