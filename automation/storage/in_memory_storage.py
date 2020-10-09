from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Tuple

from multiprocess import Queue

from automation.types import VisitId

from .arrow_storage import ArrowProvider
from .storage_providers import StructuredStorageProvider, UnstructuredStorageProvider

"""
This module contains implementations for various kinds of storage providers
that store their results in memory.
These classes are designed to allow for easier parallel testing as there are
no shared resources between tests. It also makes it easier to verify results
by not having to do a round trip to a perstitent storage provider
"""


class MemoryStructuredProvider(StructuredStorageProvider):
    """
    This storage provider passes all it's data to the MemoryStructuredProviderHandle in
    process safe way.
    This makes it ideal for testing and for small crawls where no persistence is required
    """

    def __init__(self) -> None:
        super().__init__()
        self.queue = Queue()
        self.handle = MemoryStructuredProviderHandle(self.queue)

    async def flush_cache(self) -> None:
        pass

    async def store_record(
        self, table: str, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        self.queue.put((table, record))

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> None:
        pass

    async def shutdown(self) -> None:
        pass


class MemoryStructuredProviderHandle:
    """
    Call poll_queue to load all available data into the dict
    at self.storage
    """

    def __init__(self, queue: Queue) -> None:
        self.queue = queue
        self.storage: DefaultDict[str, List[Any]] = defaultdict(list)

    def poll_queue(self) -> None:
        while not self.queue.empty():
            table, record = self.queue.get()
            self.storage[table].append(record)


class MemoryUnstructuredProvider(UnstructuredStorageProvider):
    """This storage provider stores all data in memory under self.storage as a dict
    from filename to content.
    Use this provider for writing tests and for small crawls where no persistence is required
    """

    def __init__(self) -> None:
        self.storage: Dict[str, bytes] = {}

    async def store_blob(
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

    async def flush_cache(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass


class MemoryArrowProvider(ArrowProvider):
    ...
