"""In-process StorageController for testing.

Runs the StorageController's asyncio event loop in a daemon thread instead of
a subprocess, eliminating subprocess spawn overhead. Uses the same TCP server
and protocol, so the WebExtension connects to it identically.
"""

import asyncio
import logging
import random
import threading
import time
from typing import List, Optional, Tuple

from multiprocess import Queue

from ..types import BrowserId, VisitId
from .storage_controller import StorageController
from .storage_providers import StructuredStorageProvider, UnstructuredStorageProvider


class InProcessStorageControllerHandle:
    """StorageControllerHandle replacement that runs in a thread, not a subprocess.

    Implements the same interface as StorageControllerHandle (satisfies
    StorageInterface protocol) but runs the asyncio event loop in a daemon
    thread within the current process. This avoids subprocess spawn overhead
    for testing.
    """

    def __init__(
        self,
        structured_storage: StructuredStorageProvider,
        unstructured_storage: Optional[UnstructuredStorageProvider],
    ) -> None:
        self.listener_address: Optional[Tuple[str, int]] = None
        self.status_queue: Queue = Queue()
        self.completion_queue: Queue = Queue()
        self.shutdown_queue: Queue = Queue()
        self._last_status: Optional[int] = None
        self._last_status_received: Optional[float] = None
        self.logger = logging.getLogger("openwpm")
        self._storage_controller = StorageController(
            structured_storage,
            unstructured_storage,
            status_queue=self.status_queue,
            completion_queue=self.completion_queue,
            shutdown_queue=self.shutdown_queue,
        )
        self._thread: Optional[threading.Thread] = None

    def get_next_visit_id(self) -> VisitId:
        """Generate visit id as randomly generated positive integer less than 2^53."""
        return VisitId(random.getrandbits(53))

    def get_next_browser_id(self) -> BrowserId:
        """Generate crawl id as randomly generated positive 32bit integer."""
        return BrowserId(random.getrandbits(32))

    def _run_loop(self) -> None:
        """Run the storage controller's asyncio loop in this thread."""
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        asyncio.run(self._storage_controller._run(), debug=True)

    def launch(self) -> None:
        """Start the storage controller in a daemon thread."""
        self._thread = threading.Thread(
            target=self._run_loop, name="InProcessStorageController", daemon=True
        )
        self._thread.start()
        # Wait for the listener address from the status queue
        self.listener_address = self.status_queue.get()

    def get_new_completed_visits(self) -> List[Tuple[int, bool]]:
        """Return visit ids completed since last call."""
        finished_visit_ids = list()
        while not self.completion_queue.empty():
            finished_visit_ids.append(self.completion_queue.get())
        return finished_visit_ids

    def shutdown(self, relaxed: bool = True) -> None:
        """Signal the storage controller to shut down and wait for the thread."""
        assert self._thread is not None
        self.logger.debug("Sending shutdown signal to in-process StorageController...")
        self.shutdown_queue.put(("SHUTDOWN", relaxed))
        start_time = time.time()
        self._thread.join(timeout=60)
        self.logger.debug(
            "%s took %s seconds to close."
            % (type(self).__name__, str(time.time() - start_time))
        )

    def get_most_recent_status(self) -> int:
        """Return the most recent queue size."""
        if self._last_status is None:
            return self.get_status()

        while not self.status_queue.empty():
            self._last_status = self.status_queue.get()
            self._last_status_received = time.time()

        if self._last_status_received is not None and (
            time.time() - self._last_status_received
        ) > 120:
            raise RuntimeError(
                "No status update from the storage controller "
                "for %d seconds." % (time.time() - self._last_status_received)
            )

        return self._last_status

    def get_status(self) -> int:
        """Get listener process status. If the status queue is empty, block."""
        import queue

        try:
            self._last_status = self.status_queue.get(block=True, timeout=120)
            self._last_status_received = time.time()
        except queue.Empty:
            assert self._last_status_received is not None
            raise RuntimeError(
                "No status update from the storage controller "
                "for %d seconds." % (time.time() - self._last_status_received)
            )
        assert isinstance(self._last_status, int)
        return self._last_status

    def save_configuration(
        self,
        manager_params: "ManagerParamsInternal",
        browser_params: "List[BrowserParamsInternal]",
        openwpm_version: str,
        browser_version: str,
    ) -> None:
        """Save configuration - delegates to a DataSocket like StorageControllerHandle."""
        from ..config import BrowserParamsInternal, ManagerParamsInternal  # noqa: F811
        from .storage_controller import INVALID_VISIT_ID, DataSocket
        from .storage_providers import TableName

        assert self.listener_address is not None

        sock = DataSocket(self.listener_address, "StorageControllerHandle")
        task_id = random.getrandbits(32)
        sock.store_record(
            TableName("task"),
            INVALID_VISIT_ID,
            {
                "task_id": task_id,
                "manager_params": manager_params.to_json(),
                "openwpm_version": openwpm_version,
                "browser_version": browser_version,
            },
        )
        for browser_param in browser_params:
            sock.store_record(
                TableName("crawl"),
                INVALID_VISIT_ID,
                {
                    "browser_id": browser_param.browser_id,
                    "task_id": task_id,
                    "browser_params": browser_param.to_json(),
                },
            )
        sock.finalize_visit_id(INVALID_VISIT_ID, success=True)
        sock.close()
