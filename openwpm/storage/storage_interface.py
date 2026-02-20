"""Protocol defining the interface TaskManager uses to interact with storage.

This decouples TaskManager from the concrete StorageControllerHandle,
allowing tests to use lightweight in-process alternatives.
"""

from typing import Any, List, Optional, Protocol, Tuple

from multiprocess import Queue

from ..config import BrowserParamsInternal, ManagerParamsInternal
from ..types import BrowserId, VisitId


class StorageInterface(Protocol):
    """Interface for storage controller handles.

    StorageControllerHandle implements this protocol for production use.
    InProcessStorageControllerHandle implements it for testing.
    """

    listener_address: Optional[Tuple[str, int]]
    completion_queue: Queue

    def get_next_visit_id(self) -> VisitId: ...

    def get_next_browser_id(self) -> BrowserId: ...

    def get_most_recent_status(self) -> int: ...

    def get_status(self) -> int: ...

    def get_new_completed_visits(self) -> List[Tuple[int, bool]]: ...

    def launch(self) -> None: ...

    def shutdown(self, relaxed: bool = True) -> None: ...

    def save_configuration(
        self,
        manager_params: ManagerParamsInternal,
        browser_params: List[BrowserParamsInternal],
        openwpm_version: str,
        browser_version: str,
    ) -> None: ...
