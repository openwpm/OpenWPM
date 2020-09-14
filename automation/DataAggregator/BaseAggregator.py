import abc
import logging
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from multiprocess import Queue

from ..SocketInterface import serversocket
from ..utilities.multiprocess_utils import Process

RECORD_TYPE_CONTENT = "page_content"
RECORD_TYPE_SPECIAL = "meta_information"
ACTION_TYPE_FINALIZE = "Finalize"
ACTION_TYPE_INITIALIZE = "Initialize"
RECORD_TYPE_CREATE = "create_table"
STATUS_TIMEOUT = 120  # seconds
SHUTDOWN_SIGNAL = "SHUTDOWN"

STATUS_UPDATE_INTERVAL = 5  # seconds

BaseParams = Tuple[Queue, Queue, Queue]


class BaseListener:
    """Base class for the data aggregator listener process. This class is used
    alongside the BaseAggregator class to spawn an aggregator process that
    combines data collected in multiple crawl processes and stores it
    persistently as specified in the child class. The BaseListener class
    is instantiated in the remote process, and sets up a listening socket to
    receive data. Classes which inherit from this base class define
    how that data is written to disk.
    """

    __metaclass = abc.ABCMeta

    def __init__(
        self, status_queue: Queue, completion_queue: Queue, shutdown_queue: Queue
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
        self.curent_visit_ids: List[int] = list()  # All visit_ids in flight
        self.sock: Optional[serversocket] = None

    @abc.abstractmethod
    def process_record(self, record):
        """Parse and save `record` to persistent storage.

        Parameters
        ----------
        record : tuple
            2-tuple in format (table_name, data). `data` is a dict which maps
            column name to the record for that column"""

    @abc.abstractmethod
    def process_content(self, record):
        """Parse and save page content `record` to persistent storage.

        Parameters
        ----------
        record : tuple
            2-tuple in format (table_name, data). `data` is a 2-tuple of the
            for (content, content_hash)"""

    @abc.abstractmethod
    def run_visit_completion_tasks(self, visit_id: int, interrupted: bool = False):
        """Will be called once a visit_id will receive no new records

        Parameters
        ----------
        visit_id
            the id that will receive no more updates
        interrupted
           whether a visit is unfinished"""

    def startup(self):
        """Run listener startup tasks

        Note: Child classes should call this method"""
        self.sock = serversocket(name=type(self).__name__)
        self.status_queue.put(self.sock.sock.getsockname())
        self.sock.start_accepting()
        self.record_queue = self.sock.queue

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

    def handle_special(self, data: Dict[str, Any]) -> None:
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

            self.run_visit_completion_tasks(
                data["visit_id"], interrupted=not data["success"]
            )
        else:
            raise ValueError(
                "Unexpected meta " "information type: %s" % data["meta_type"]
            )

    def mark_visit_complete(self, visit_id: int) -> None:
        """This function should be called to indicate that all records
        relating to a certain visit_id have been saved"""
        self.completion_queue.put((visit_id, False))

    def mark_visit_incomplete(self, visit_id: int):
        """This function should be called to indicate that a certain visit
        has been interrupted and will forever be incomplete
        """
        self.completion_queue.put((visit_id, True))

    def shutdown(self):
        """Run shutdown tasks defined in the base listener

        Note: Child classes should call this method"""
        self.sock.close()
        for visit_id in self.curent_visit_ids:
            self.run_visit_completion_tasks(visit_id, interrupted=not self._relaxed)

    def drain_queue(self):
        """ Ensures queue is empty before closing """
        time.sleep(3)  # TODO: the socket needs a better way of closing
        while not self.record_queue.empty():
            record = self.record_queue.get()
            self.process_record(record)
        self.logger.info("Queue was flushed completely")


class BaseAggregator:
    """Base class for the data aggregator interface. This class is used
    alongside the BaseListener class to spawn an aggregator process that
    combines data from multiple crawl processes. The BaseAggregator class
    manages the child listener process.

    Parameters
    ----------
    manager_params : dict
        TaskManager configuration parameters
    browser_params : list of dict
        List of browser configuration dictionaries"""

    __metaclass__ = abc.ABCMeta

    def __init__(self, manager_params, browser_params):
        self.manager_params = manager_params
        self.browser_params = browser_params
        self.listener_address = None
        self.listener_process = None
        self.status_queue = Queue()
        self.completion_queue = Queue()
        self.shutdown_queue = Queue()
        self._last_status = None
        self._last_status_received = None
        self.logger = logging.getLogger("openwpm")

    @abc.abstractmethod
    def save_configuration(self, openwpm_version, browser_version):
        """Save configuration details to the database"""

    @abc.abstractmethod
    def get_next_visit_id(self):
        """Return a unique visit ID to be used as a key for a single visit"""

    @abc.abstractmethod
    def get_next_browser_id(self):
        """Return a unique crawl ID used as a key for a browser instance"""

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

    def launch(self, listener_process_runner, *args):
        """Launch the aggregator listener process"""
        args = ((self.status_queue, self.completion_queue, self.shutdown_queue),) + args
        self.listener_process = Process(target=listener_process_runner, args=args)
        self.listener_process.daemon = True
        self.listener_process.start()
        self.listener_address = self.status_queue.get()

    def shutdown(self, relaxed: bool = True):
        """ Terminate the aggregator listener process"""
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
