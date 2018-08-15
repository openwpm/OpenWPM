import abc
import time

from multiprocess import Process, Queue

from ..MPLogger import loggingclient
from ..SocketInterface import serversocket


class BaseListener(object):
    """Base class for the data aggregator listener process. This class is used
    alongside the BaseAggregator class to spawn an aggregator process that
    combines data collected in multiple crawl processes and write it to disk as
    specified in the child class. The BaseListener class is instantiated in the
    remote process, and sets up a listening socket to receive data. Classes
    which inherit from this base class define how that data is written to disk.

    Parameters
    ----------
    manager_params : dict
        TaskManager configuration parameters
    browser_params : list of dict
        List of browser configuration dictionaries"""
    __metaclass = abc.ABCMeta

    def __init__(self, status_queue, manager_params):
        self.status_queue = status_queue
        self.logger = loggingclient(*manager_params['logger_address'])

    @abc.abstractmethod
    def process_record(self, record):
        """Parse and save `record` to persistent storage.

        Parameters
        ----------
        record : tuple
            2-tuple in format (table_name, data). `data` is a dict which maps
            column name to the record for that column"""

    def startup(self):
        """Run listener startup tasks

        Note: Child classes should call this method"""
        self.sock = serversocket(name=type(self).__name__)
        self.status_queue.put(self.sock.sock.getsockname())
        self.sock.start_accepting()
        self.record_queue = self.sock.queue

    def should_shutdown(self):
        """Check if we should shut down this listener process"""
        if not self.status_queue.empty():
            self.status_queue.get()
            return True
        return False

    def shutdown(self):
        """Run shutdown tasks defined in the base listener

        Note: Child classes should call this method"""
        self.sock.close()

    def drain_queue(self):
        """ Ensures queue is empty before closing """
        self.sock.close()
        time.sleep(3)  # TODO: the socket needs a better way of closing
        while not self.sock.queue.empty():
            record = self.sock.queue.get()
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
        self.logger = loggingclient(*manager_params['logger_address'])
        self.listener_address = None
        self.listener_process = None

    @abc.abstractmethod
    def save_configuration(self, openwpm_version, browser_version):
        """Save configuration details to the database"""

    @abc.abstractmethod
    def get_next_visit_id(self):
        """Return a unique visit ID to be used as a key for a single visit"""

    @abc.abstractmethod
    def get_next_crawl_id(self):
        """Return a unique crawl ID used as a key for a browser instance"""

    def launch(self, listener_process_runner):
        """Launch the aggregator listener process"""
        self.status_queue = Queue()
        self.listener_process = Process(
            target=listener_process_runner,
            args=(self.manager_params, self.status_queue))
        self.listener_process.daemon = True
        self.listener_process.start()
        self.listener_address = self.status_queue.get()

    def shutdown(self):
        """ Terminate the aggregator listener process"""
        self.logger.debug(
            "Sending the shutdown signal to the %s listener process..." %
            type(self).__name__
        )
        self.status_queue.put("SHUTDOWN")
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
