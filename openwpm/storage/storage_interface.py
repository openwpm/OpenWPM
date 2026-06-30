"""Protocol defining the interface TaskManager uses to interact with storage.

This decouples TaskManager from the concrete StorageControllerHandle,
allowing tests to use lightweight in-process alternatives.
"""

from typing import List, Optional, Protocol, Tuple

from ..types import BrowserId, VisitId


class StorageInterface(Protocol):
    """Interface for storage controller handles.

    StorageControllerHandle implements this protocol for production use.
    InProcessStorageControllerHandle implements it for testing.
    """

    def get_next_visit_id(self) -> VisitId: ...

    def get_next_browser_id(self) -> BrowserId: ...

    def get_most_recent_status(self) -> int: ...

    def get_new_completed_visits(self) -> List[Tuple[int, bool]]: ...

    def launch(self) -> None: ...

    listener_address: Optional[Tuple[str, int]]

    def shutdown(self, relaxed: bool = True) -> None: ...
