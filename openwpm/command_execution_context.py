"""Protocol for the context needed by BrowserManagerHandle to execute commands.

This decouples BrowserManagerHandle from the concrete TaskManager class,
allowing tests to provide lightweight mock implementations.
"""

from typing import Any, Dict, Protocol

from .failure_tracker import FailureTracker
from .storage.storage_providers import TableName
from .types import VisitId


class CommandExecutionContext(Protocol):
    """Interface that BrowserManagerHandle needs from the TaskManager.

    TaskManager implements this protocol. Tests can provide a lightweight
    mock with a real FailureTracker but no storage/browser infrastructure.
    """

    closing: bool
    failure_tracker: FailureTracker

    def store_record(
        self, table: TableName, visit_id: VisitId, data: Dict[str, Any]
    ) -> None:
        """Send a record to the StorageController."""
        ...

    def finalize_visit_id(self, visit_id: VisitId, success: bool) -> None:
        """Signal that all data for a visit_id has been sent."""
        ...
