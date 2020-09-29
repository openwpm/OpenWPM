from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Tuple

from .storage_providers import StructuredStorageProvider, UnstructuredStorageProvider


class MemoryStructuredProvider(StructuredStorageProvider):
    def __init__(self):
        super().__init__()
        self._storage: DefaultDict[str, List[Any]] = defaultdict(list)
        self._completed_visit_ids: List[Tuple[int, bool]] = list()

    def flush_cache(self) -> None:
        pass

    def store_record(self, table: str, record: Dict[str, Any]) -> None:
        self._storage[table].append(record)
        pass

    def run_visit_completion_tasks(
        self, visit_id: int, interrupted: bool = False
    ) -> None:
        self._completed_visit_ids.append((visit_id, interrupted))
        pass

    def saved_visit_ids(self) -> List[Tuple[int, bool]]:
        temp = self._completed_visit_ids
        self._completed_visit_ids = list()
        return temp

    def shutdown(self) -> None:
        pass
