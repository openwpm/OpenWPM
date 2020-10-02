from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Tuple

from automation.types import VisitId

from .arrow_storage import ArrowProvider
from .storage_providers import StructuredStorageProvider, UnstructuredStorageProvider


class MemoryStructuredProvider(StructuredStorageProvider):
    """This storage provider stores all data in memory under self.storage.
    This makes it ideal for testing and for small crawls where no persistence is required
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

    def shutdown(self) -> None:
        pass


class MemoryUnstructuredProvider(UnstructuredStorageProvider):
    """This storage provider stores all data in memory under self.storage as a dict
    from filename to content.
    Use this provider for writing tests and for small crawls where no persistence is required
    """

    def __init__(self) -> None:
        self.storage: Dict[str, bytes] = {}

    def store_blob(
        self,
        filename: str,
        blob: bytes,
        compressed: bool = True,
        skip_if_exists: bool = True,
    ) -> None:
        if skip_if_exists and filename in self.storage:
            return
        if compressed:
            bytesIO = self._compress(blob)
            blob = bytesIO.getvalue()
        self.storage[filename] = blob

    def flush_cache(self):
        pass

    def shutdown(self):
        pass


class MemoryArrowProvider(ArrowProvider):
    ...
