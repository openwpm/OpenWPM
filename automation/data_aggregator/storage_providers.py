from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

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
    @abstractmethod
    def store_record(self, table: str, record: Dict[str, Any]) -> None:
        """Submit a record to be stored
        The storing might not happen immediately
        """
        pass

    @abstractmethod
    def run_visit_completion_tasks(
        self, visit_id: int, interrupted: bool = False
    ) -> None:
        """This method is invoked to inform the StrucuturedStorageProvider that no more
        records for this visit_id will be submitted
        """
        pass

    @abstractmethod
    def saved_visit_ids(self) -> List[Tuple[int, bool]]:
        """Return the list of all visit_ids that have been saved to permanent storage
        since the last time this method was called

        For each visit_id it's also noted whether they were interrupted
        """
        pass


class UnstructuredStorageProvider(StorageProvider):
    def store_blob(self, blob: str) -> None:
        """Stores the data passed in as an base64 encoded string"""
        pass
