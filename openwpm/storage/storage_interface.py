"""Protocol defining the interface TaskManager uses to interact with storage.

This decouples TaskManager from the concrete StorageControllerHandle,
allowing tests to use lightweight in-process alternatives.
"""

from typing import List, Optional, Protocol, Tuple

from ..config import BrowserParamsInternal, ManagerParamsInternal
from ..types import BrowserId, VisitId


class StorageInterface(Protocol):
    """Interface for storage controller handles.

    StorageControllerHandle implements this protocol for production use.
    InProcessStorageControllerHandle implements it for testing.

    This mirrors every member of the handle that TaskManager depends on, so
    ``mypy`` rejects a handle that stops honouring the contract.
    """

    listener_address: Optional[Tuple[str, int]]

    def get_next_visit_id(self) -> VisitId: ...

    def get_next_browser_id(self) -> BrowserId: ...

    def save_configuration(
        self,
        manager_params: ManagerParamsInternal,
        browser_params: List[BrowserParamsInternal],
        openwpm_version: str,
        browser_version: str,
    ) -> None: ...

    def launch(self) -> None: ...

    def get_new_completed_visits(self) -> List[Tuple[int, bool]]: ...

    def shutdown(self, relaxed: bool = True) -> None: ...

    def get_most_recent_status(self) -> int: ...

    def get_status(self) -> int: ...
