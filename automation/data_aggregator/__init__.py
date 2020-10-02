import base64
import logging
import queue
import random
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from multiprocess import Queue

from automation.utilities.multiprocess_utils import Process

from ..SocketInterface import ServerSocket
from ..types import BrowserId, ManagerParams, VisitId
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


class DataAggregator:
    def __init__(
        self,
        structured_storage: StructuredStorageProvider,
        unstructured_storage: Optional[UnstructuredStorageProvider],
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
        self._last_record_received: Optional[float] = None

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
            if self.unstructured_storage is None:
                self.logger.error(
                    """Tried to save content while not having
                                  provided any unstructured storage provider."""
                )
                return
            content, content_hash = data
            content = base64.b64decode(content)
            self.unstructured_storage.store_blob(filename=content_hash, blob=content)
            return
        if record_type == RECORD_TYPE_META:
            self._handle_meta(data)
            return
        visit_id = VisitId(data["visit_id"])
        self.curent_visit_ids.append(visit_id)
        self.structured_storage.store_record(
            table=record_type, visit_id=visit_id, record=data
        )

    def _handle_meta(self, data: Dict[str, Any]) -> None:
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

    def update_status_queue(self) -> None:
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

    def update_completion_queue(self) -> None:
        for pair in self.structured_storage.saved_visit_ids():
            self.completion_queue.put(pair)
            self.curent_visit_ids.remove(pair[0])

    def drain_queue(self) -> None:
        """ Ensures queue is empty before closing """
        time.sleep(3)  # TODO: the socket needs a better way of closing
        while not self.record_queue.empty():
            self.poll_queue()
        self.logger.info("Queue was flushed completely")

    def shutdown(self) -> None:
        self.structured_storage.flush_cache()
        self.structured_storage.shutdown()
        if self.unstructured_storage is not None:
            self.unstructured_storage.flush_cache()
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


def listener_process_runner(aggregator: DataAggregator) -> None:

    aggregator.startup()

    while not aggregator.should_shutdown():
        aggregator.update_status_queue()
        aggregator.update_completion_queue()
        aggregator.save_batch_if_past_timeout()
        aggregator.poll_queue()

    aggregator.drain_queue()
    aggregator.shutdown()


class DataAggregatorHandle:
    """This class contains all methods relevant for the TaskManager
    to interact with the DataAggregator
    """

    def __init__(
        self,
        structured_storage: StructuredStorageProvider,
        unstructured_storage: UnstructuredStorageProvider,
    ) -> None:

        self.listener_address = None
        self.listener_process: Optional[Process] = None
        self.status_queue = Queue()
        self.completion_queue = Queue()
        self.shutdown_queue = Queue()
        self._last_status = None
        self._last_status_received = None
        self.logger = logging.getLogger("openwpm")
        self.aggregator = DataAggregator(
            structured_storage,
            unstructured_storage,
            status_queue=self.status_queue,
            completion_queue=self.completion_queue,
            shutdown_queue=self.shutdown_queue,
        )

    def get_next_visit_id(self) -> VisitId:
        """Generate visit id as randomly generated positive integer less than 2^53.

        Parquet can support integers up to 64 bits, but Javascript can only
        represent integers up to 53 bits:
        https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER
        Thus, we cap these values at 53 bits.
        """
        return VisitId(random.getrandbits(53))

    def get_next_browser_id(self) -> BrowserId:
        """Generate crawl id as randomly generated positive 32bit integer

        Note: Parquet's partitioned dataset reader only supports integer
        partition columns up to 32 bits.
        """
        return BrowserId(random.getrandbits(32))

    def save_configuration(self, openwpm_version, browser_version):
        # FIXME I need to find a solution for this
        self.logger.error(
            "Can't log config as of yet, because it's still not implemented"
        )

    def launch(self) -> None:
        """Starts the data aggregator"""
        self.listener_process = Process(
            name="DataAggregator",
            target=listener_process_runner,
            args=(self.aggregator,),
        )
        self.listener_process.daemon = True
        self.listener_process.start()

        self.listener_address = self.status_queue.get()

    def get_new_completed_visits(self) -> List[Tuple[int, bool]]:
        """
        Returns a list of all visit ids that have been processed since
        the last time the method was called and whether or not they
        have been interrupted.

        This method will return an empty list in case no visit ids have
        been processed since the last time this method was called
        """
        finished_visit_ids = list()
        while not self.completion_queue.empty():
            finished_visit_ids.append(self.completion_queue.get())
        return finished_visit_ids

    def shutdown(self, relaxed: bool = True) -> None:
        """ Terminate the aggregator listener process"""
        assert isinstance(self.listener_process, Process)
        self.logger.debug(
            "Sending the shutdown signal to the %s listener process..."
            % type(self).__name__
        )
        self.shutdown_queue.put((SHUTDOWN_SIGNAL, relaxed))
        start_time = time.time()
        self.listener_process.join(300)
        self.logger.debug(
            "%s took %s seconds to close."
            % (type(self).__name__, str(time.time() - start_time))
        )
        self.listener_address = None
        self.listener_process = None

    def get_most_recent_status(self):
        """Return the most recent queue size sent from the listener process"""

        # Block until we receive the first status update
        if self._last_status is None:
            return self.get_status()

        # Drain status queue until we receive most recent update
        while not self.status_queue.empty():
            self._last_status = self.status_queue.get()
            self._last_status_received = time.time()

        # Check last status signal
        if (time.time() - self._last_status_received) > STATUS_TIMEOUT:
            raise RuntimeError(
                "No status update from DataAggregator listener process "
                "for %d seconds." % (time.time() - self._last_status_received)
            )

        return self._last_status

    def get_status(self):
        """Get listener process status. If the status queue is empty, block."""
        try:
            self._last_status = self.status_queue.get(
                block=True, timeout=STATUS_TIMEOUT
            )
            self._last_status_received = time.time()
        except queue.Empty:
            raise RuntimeError(
                "No status update from DataAggregator listener process "
                "for %d seconds." % (time.time() - self._last_status_received)
            )
        return self._last_status
