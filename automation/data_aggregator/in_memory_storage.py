from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Tuple

from automation.types import VisitId

from .storage_providers import StructuredStorageProvider, UnstructuredStorageProvider


class MemoryStructuredProvider(StructuredStorageProvider):
    """This storage provider stores all data in memory under
    self.storage.
    This makes it ideal for testing and for small crawls where no persitence is required
    """

    def __init__(self):
        super().__init__()
        self.storage: DefaultDict[str, List[Any]] = defaultdict(list)
        self._completed_visit_ids: List[Tuple[VisitId, bool]] = list()

    def flush_cache(self) -> None:
        pass

    def store_record(
        self, table: str, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        self.storage[table].append(record)
        pass

    def run_visit_completion_tasks(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> None:
        self._completed_visit_ids.append((visit_id, interrupted))
        pass

    def saved_visit_ids(self) -> List[Tuple[VisitId, bool]]:
        temp = self._completed_visit_ids
        self._completed_visit_ids = list()
        return temp

    def shutdown(self) -> None:
        pass
