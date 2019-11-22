import abc
import logging
import queue
import threading
import time

from multiprocess import Queue

from ..SocketInterface import serversocket
from ..utilities.multiprocess_utils import Process

RECORD_TYPE_CONTENT = 'page_content'
STATUS_TIMEOUT = 120  # seconds
SHUTDOWN_SIGNAL = 'SHUTDOWN'

STATUS_UPDATE_INTERVAL = 5  # seconds


class BaseListener(object):
    """Base class for the data aggregator listener process. This class is used
    alongside the BaseAggregator class to spawn an aggregator process that
    combines data collected in multiple crawl processes and stores it
    persistently as specified in the child class. The BaseListener class
    is instantiated in the remote process, and sets up a listening socket to
    receive data. Classes which inherit from this base class define
    how that data is written to disk.

    Parameters
    ----------
    manager_params : dict
        TaskManager configuration parameters
    browser_params : list of dict
        List of browser configuration dictionaries"""
    __metaclass = abc.ABCMeta

    def __init__(self, status_queue, shutdown_queue, manager_params):
        self.status_queue = status_queue
        self.shutdown_queue = shutdown_queue
        self._shutdown_flag = False
        self._last_update = time.time()  # last status update time
        self.record_queue = None  # Initialized on `startup`
        self.logger = logging.getLogger('openwpm')

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

    def startup(self):
        """Run listener startup tasks

        Note: Child classes should call this method"""
        self.sock = serversocket(name=type(self).__name__)
        self.status_queue.put(self.sock.sock.getsockname())
        self.sock.start_accepting()
        self.record_queue = self.sock.queue

    def should_shutdown(self):
        """Return `True` if the listener has received a shutdown signal"""
        if not self.shutdown_queue.empty():
            self.shutdown_queue.get()
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
            "current number of threads: %d." %
            (qsize, threading.active_count())
        )
        self._last_update = time.time()

    def shutdown(self):
        """Run shutdown tasks defined in the base listener

        Note: Child classes should call this method"""
        self.sock.close()

    def drain_queue(self):
        """ Ensures queue is empty before closing """
        time.sleep(3)  # TODO: the socket needs a better way of closing
        while not self.record_queue.empty():
            record = self.record_queue.get()
            self.process_record(record)


class BaseAggregator(object):
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
        self.shutdown_queue = Queue()
        self._last_status = None
        self._last_status_received = None
        self.logger = logging.getLogger('openwpm')

    @abc.abstractmethod
    def save_configuration(self, openwpm_version, browser_version):
        """Save configuration details to the database"""

    @abc.abstractmethod
    def get_next_visit_id(self):
        """Return a unique visit ID to be used as a key for a single visit"""

    @abc.abstractmethod
    def get_next_crawl_id(self):
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
                block=True, timeout=STATUS_TIMEOUT)
            self._last_status_received = time.time()
        except queue.Empty:
            raise RuntimeError(
                "No status update from DataAggregator listener process "
                "for %d seconds." % (time.time() - self._last_status_received)
            )
        return self._last_status

    def launch(self, listener_process_runner, *args):
        """Launch the aggregator listener process"""
        args = (self.manager_params, self.status_queue,
                self.shutdown_queue) + args
        self.listener_process = Process(
            target=listener_process_runner,
            args=args
        )
        self.listener_process.daemon = True
        self.listener_process.start()
        self.listener_address = self.status_queue.get()

    def shutdown(self):
        """ Terminate the aggregator listener process"""
        self.logger.debug(
            "Sending the shutdown signal to the %s listener process..." %
            type(self).__name__
        )
        self.shutdown_queue.put(SHUTDOWN_SIGNAL)
        start_time = time.time()
        self.listener_process.join(300)
        self.logger.debug(
            "%s took %s seconds to close." % (
                type(self).__name__,
                str(time.time() - start_time)
            )
        )
        self.listener_address = None
        self.listener_process = None
