"""
This module contains implementations for various kinds of storage providers
that store their results in memory.
These classes are designed to allow for easier parallel testing as there are
no shared resources between tests. It also makes it easier to verify results
by not having to do a round trip through a persistent storage provider
"""

import asyncio
import logging
from asyncio import Event, Lock, Task
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List

from multiprocess import Queue
from pyarrow import Table

from openwpm.types import VisitId

from .arrow_storage import ArrowProvider
from .storage_providers import (
    StructuredStorageProvider,
    TableName,
    UnstructuredStorageProvider,
)


class MemoryStructuredProvider(StructuredStorageProvider):
    """
    This storage provider passes all it's data to the MemoryStructuredProviderHandle in a
    process safe way.

    This makes it ideal for testing

    It also aims to only save out data as late as possible to ensure that storage_controller
    only relies on the guarantees given in the interface.
    """

    lock: Lock

    def __init__(self) -> None:
        super().__init__()
        self.queue = Queue()
        self.handle = MemoryProviderHandle(self.queue)
        self.logger = logging.getLogger("openwpm")
        self.cache1: DefaultDict[
            VisitId, DefaultDict[TableName, List[Dict[str, Any]]]
        ] = defaultdict(lambda: defaultdict(list))
        """The cache for entries before they are finalized"""
        self.cache2: DefaultDict[TableName, List[Dict[str, Any]]] = defaultdict(list)
        """For all entries that have been finalized but not yet flushed out to the queue"""
        self.signal_list: List[Event] = []

    async def init(self) -> None:
        self.lock = asyncio.Lock()

    async def flush_cache(self) -> None:
        async with self.lock as _:
            self.logger.info("Flushing cache")

            for table, record_list in self.cache2.items():
                self.logger.info(f"Saving out {len(record_list)} entries for {table}")
                for record in record_list:
                    self.queue.put((table, record))
            self.cache2.clear()
            for ev in self.signal_list:
                ev.set()

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        self.logger.info(
            "Saving into table %s for visit_id %d record %r", table, visit_id, record
        )
        self.cache1[visit_id][table].append(record)

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> Task[None]:
        async with self.lock as _:
            self.logger.info(
                f"Finalizing visit_id {visit_id} which was {'' if interrupted else 'not'} interrupted"
            )
            for table, record_list in self.cache1[visit_id].items():
                self.cache2[table].extend(record_list)

            del self.cache1[visit_id]

            async def wait(signal: Event) -> None:
                await signal.wait()

            ev = Event()
            self.signal_list.append(ev)
            return asyncio.create_task(wait(ev))

    async def shutdown(self) -> None:
        if self.cache1 != {} or self.cache2 != {}:
            self.logger.error("Shutting down with unsaved records")


class MemoryProviderHandle:
    """
    Call poll_queue to load all available data into the dict
    at self.storage
    """

    def __init__(self, queue: Queue) -> None:
        self.queue = queue
        self.storage: DefaultDict[str, List[Any]] = defaultdict(list)

    def poll_queue(self, *args: Any, **kwargs: Any) -> None:
        while not self.queue.empty():
            table, record = self.queue.get(*args, **kwargs)
            self.storage[table].append(record)


class MemoryUnstructuredProvider(UnstructuredStorageProvider):
    """This storage provider stores all data in memory under self.storage as a dict
    from filename to content.
    Use this provider for writing tests and for small crawls where no persistence is required
    """

    async def init(self) -> None:
        pass

    def __init__(self) -> None:
        self.storage: Dict[str, bytes] = {}
        self.queue = Queue()
        self.handle = MemoryProviderHandle(self.queue)

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
        self.queue.put((filename, blob))

    async def flush_cache(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass


class MemoryArrowProvider(ArrowProvider):
    def __init__(self) -> None:
        super().__init__()
        self.queue = Queue()
        self.handle = MemoryProviderHandle(self.queue)

    async def write_table(self, table_name: TableName, table: Table) -> None:
        self.queue.put((table_name, table))

    async def shutdown(self) -> None:
        pass
