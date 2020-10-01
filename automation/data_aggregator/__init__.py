import base64
import logging
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from multiprocess import Queue

from ..SocketInterface import ServerSocket
from ..types import ManagerParams, VisitId
from .storage_providers import StructuredStorageProvider, UnstructuredStorageProvider

RECORD_TYPE_CONTENT = "page_content"
RECORD_TYPE_META = "meta_information"
ACTION_TYPE_FINALIZE = "Finalize"
ACTION_TYPE_INITIALIZE = "Initialize"
RECORD_TYPE_CREATE = "create_table"
STATUS_TIMEOUT = 120  # seconds
SHUTDOWN_SIGNAL = "SHUTDOWN"
BATCH_COMMIT_TIMEOUT = 30  # commit a batch if no new records for N seconds


STATUS_UPDATE_INTERVAL = 5  # seconds


def listener_process_runner(
    status_queue: Queue,
    completion_queue: Queue,
    shutdown_queue: Queue,
    structured_storage: StructuredStorageProvider,
    unstructured_storage: UnstructuredStorageProvider,
) -> None:
    aggregator = DataAggregator(
        structured_storage,
        unstructured_storage,
        status_queue=status_queue,
        completion_queue=completion_queue,
        shutdown_queue=shutdown_queue,
    )
    aggregator.startup()

    while not aggregator.should_shutdown():
        aggregator.update_status_queue()
        aggregator.save_batch_if_past_timeout()
        aggregator.poll_queue()

    aggregator.drain_queue()
    aggregator.shutdown()


class DataAggregator:
    def __init__(
        self,
        structured_storage: StructuredStorageProvider,
        unstructured_storage: UnstructuredStorageProvider,
        status_queue: Queue,
        completion_queue: Queue,
        shutdown_queue: Queue,
    ) -> None:
        """
        Creates a BaseListener instance

        Parameters
        ----------
        status_queue
            queue that the current amount of records to be processed will
            be sent to
            also used for initialization
        completion_queue
            queue containing the visitIDs of saved records
        shutdown_queue
            queue that the main process can use to shut down the listener
        """
        self.status_queue = status_queue
        self.completion_queue = completion_queue
        self.shutdown_queue = shutdown_queue
        self._shutdown_flag = False
        self._relaxed = False
        self._last_update = time.time()  # last status update time
        self.record_queue: Queue = None  # Initialized on `startup`
        self.logger = logging.getLogger("openwpm")
        self.curent_visit_ids: List[VisitId] = list()  # All visit_ids in flight
        self.sock: Optional[ServerSocket] = None
        self.structured_storage = structured_storage
        self.unstructured_storage = unstructured_storage

    def startup(self):
        """Puts the DataAggregator into a runable state
        by starting up the ServerSocket"""
        self.sock = ServerSocket(name=type(self).__name__)
        self.status_queue.put(self.sock.sock.getsockname())
        self.sock.start_accepting()
        self.record_queue = self.sock.queue

    def poll_queue(self) -> None:
        assert self.record_queue is not None
        try:
            record: Tuple[str, Any] = self.record_queue.get(block=True, timeout=5)
        except queue.Empty:
            return
        if len(record) != 2:
            self.logger.error("Query is not the correct length %s", repr(record))
            return
        self._last_record_received = time.time()
        record_type, data = record
        if record_type == RECORD_TYPE_CREATE:
            raise RuntimeError(
                f"""{RECORD_TYPE_CREATE} is no longer supported.
                since the user now has access to the DB before it
                goes into use, they should set up all schemas before
                launching the DataAggregator
                """
            )
            return
        if record_type == RECORD_TYPE_CONTENT:
            assert isinstance(data, tuple)
            assert len(data) == 2
            content, content_hash = data
            content = base64.b64decode(content)
            self.unstructured_storage.store_blob(filename=content_hash, blob=content)
            return
        if record_type == RECORD_TYPE_META:
            self.handle_meta(data)
            return

        self.structured_storage.store_record

    def handle_meta(self, data: Dict[str, Any]) -> None:
        """
        Messages for the table RECORD_TYPE_SPECIAL are metainformation
        communicated to the aggregator
        Supported message types:
        - finalize: A message sent by the extension to
                    signal that a visit_id is complete.
        """
        if data["action"] == ACTION_TYPE_INITIALIZE:
            self.curent_visit_ids.append(data["visit_id"])
        elif data["action"] == ACTION_TYPE_FINALIZE:
            try:
                self.curent_visit_ids.remove(data["visit_id"])
            except ValueError:
                self.logger.error(
                    "Trying to remove visit_id %i " "from current_visit_ids failed",
                    data["visit_id"],
                )

            self.structured_storage.run_visit_completion_tasks(
                data["visit_id"], interrupted=not data["success"]
            )
        else:
            raise ValueError(
                "Unexpected meta " "information type: %s" % data["meta_type"]
            )

    def update_status_queue(self):
        """Send manager process a status update."""
        if (time.time() - self._last_update) < STATUS_UPDATE_INTERVAL:
            return
        qsize = self.record_queue.qsize()
        self.status_queue.put(qsize)
        self.logger.debug(
            "Status update; current record queue size: %d. "
            "current number of threads: %d." % (qsize, threading.active_count())
        )
        self._last_update = time.time()

    def drain_queue(self) -> None:
        """ Ensures queue is empty before closing """
        time.sleep(3)  # TODO: the socket needs a better way of closing
        while not self.record_queue.empty():
            self.poll_queue()
        self.logger.info("Queue was flushed completely")

    def shutdown(self) -> None:
        self.structured_storage.flush_cache()
        self.unstructured_storage.flush_cache()
        self.structured_storage.shutdown()
        self.unstructured_storage.shutdown()

    def should_shutdown(self):
        """Return `True` if the listener has received a shutdown signal
        Sets `self._relaxed` and `self.shutdown_flag`
        `self._relaxed means this shutdown is
        happening after all visits have completed and
        all data can be seen as complete
        """
        if not self.shutdown_queue.empty():
            _, relaxed = self.shutdown_queue.get()
            self._relaxed = relaxed
            self._shutdown_flag = True
            self.logger.info("Received shutdown signal!")
            return True
        return False

    def save_batch_if_past_timeout(self):
        """Save the current batch of records if no new data has been received.

        If we aren't receiving new data for this batch we commit early
        regardless of the current batch size."""
        if self._last_record_received is None:
            return
        if time.time() - self._last_record_received < BATCH_COMMIT_TIMEOUT:
            return
        self.logger.debug(
            "Saving current record batches to S3 since no new data has "
            "been written for %d seconds." % (time.time() - self._last_record_received)
        )
        self.drain_queue()
        self._last_record_received = None


class DataAggregatorHandle:
    """This class contains all methods relevant for the TaskManager
    to interact with the DataAggregator
    """

    ...
