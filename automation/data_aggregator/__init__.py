import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from multiprocess import Queue

from ..SocketInterface import ServerSocket


class DataAggregator:
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
        self.sock: Optional[ServerSocket] = None

    def startup(self):
        """Run listener startup tasks

        Note: Child classes should call this method"""
        self.sock = ServerSocket(name=type(self).__name__)
        self.status_queue.put(self.sock.sock.getsockname())
        self.sock.start_accepting()
        self.record_queue = self.sock.queue
