import copy
import json
import logging
import logging.handlers
import os
import re
import struct
import sys
import threading
import time
from pathlib import Path
from queue import Empty as EmptyQueue
from typing import Optional

import dill
from multiprocess import JoinableQueue
from tblib import pickling_support

from .commands.utils.webdriver_utils import parse_neterror
from .socket_interface import ServerSocket

pickling_support.install()

BROWSER_PREFIX = re.compile(r"^BROWSER -?\d+:\s*")
EXTENSION_PREFIX = re.compile(r"^Extension-\d+ :\s*")
# These config variable names should name to lowercase kwargs for MPLogger
ENV_CONFIG_VARS = [
    "LOG_LEVEL_CONSOLE",
    "LOG_LEVEL_FILE",
]


def _retrive_log_level_from_env(env_var_name):
    """Retrieve log level from `env_var_name`

    Levels from: https://docs.python.org/3/library/logging.html#levels"""
    level = os.getenv(env_var_name, None)
    if level == "CRITICAL":
        level = logging.CRITICAL
    elif level == "ERROR":
        level = logging.ERROR
    elif level == "WARNING":
        level = logging.WARNING
    elif level == "INFO":
        level = logging.INFO
    elif level == "DEBUG":
        level = logging.DEBUG
    elif level == "NOTSET":
        level = logging.NOTSET
    return level


def parse_config_from_env():
    """Parse the logger config from environment variables"""
    out = dict()
    for env_var_name in ENV_CONFIG_VARS:
        level = _retrive_log_level_from_env(env_var_name)
        if level:
            out[env_var_name.lower()] = level
    return out


class ClientSocketHandler(logging.handlers.SocketHandler):
    """
    Make SocketHandler compatible with SocketInterface.py
    """

    def makePickle(self, record):
        """
        Serializes the record via json and prepends a length/serialization
        flag. Returns it ready for transmission across the socket.
        """
        d = copy.deepcopy(record.__dict__)

        # Pickle fields to so record is safe to send across socket
        if "exc_info" in d and d["exc_info"]:
            try:
                d["exc_info"] = dill.dumps(d["exc_info"])
            except dill.PicklingError:
                d["exc_info"] = None
        if "args" in d and d["args"]:
            try:
                d["args"] = dill.dumps(d["args"])
            except dill.PicklingError:
                d["msg"] = record.getMessage()
                d["args"] = None

        # Serialize logging record so it can be sent to MPLogger
        # s = json.dumps(d).encode('utf-8')
        s = dill.dumps(d)
        return struct.pack(">Lc", len(s), b"d") + s


class MPLogger(object):
    """Configure OpenWPM logging across processes"""

    def __init__(
        self,
        log_file: Path,
        crawl_reference: Optional[str] = None,
        log_level_console=logging.INFO,
        log_level_file=logging.DEBUG,
    ) -> None:
        self._crawl_reference = crawl_reference
        self._log_level_console = log_level_console
        self._log_level_file = log_level_file
        # Configure log handlers
        self._status_queue = JoinableQueue()
        self._log_file = os.path.expanduser(log_file)

        self._initialize_loggers()

    def _initialize_loggers(self):
        """Set up console logging and serialized file logging.

        The logger and socket handler are set to log at the logging.DEBUG level
        and filtering happens at the outputs (console, file)."""
        logger = logging.getLogger("openwpm")
        logger.setLevel(logging.DEBUG)

        # Remove any previous handlers to avoid registering duplicates
        if len(logger.handlers) > 0:
            logger.handlers = list()

        # Start file handler and listener thread (for serialization)
        handler = logging.FileHandler(self._log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(processName)-11s[%(threadName)-10s]"
            "- %(module)-20s - %(levelname)-8s: %(message)s"
        )
        handler.setFormatter(formatter)
        handler.setLevel(self._log_level_file)
        self._file_handler = handler

        self._listener = threading.Thread(target=self._start_listener)
        self._listener.daemon = True
        self._listener.start()
        self.logger_address = self._status_queue.get(timeout=60)
        self._status_queue.task_done()

        # Attach console handler to log to console
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setLevel(self._log_level_console)
        formatter = logging.Formatter("%(module)-20s - %(levelname)-8s - %(message)s")
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)

        # Attach socket handler to logger to serialize writes to file
        socketHandler = ClientSocketHandler(*self.logger_address)
        socketHandler.setLevel(logging.DEBUG)
        logger.addHandler(socketHandler)

    def _start_listener(self):
        """Start listening socket for remote logs from extension"""
        socket = ServerSocket(name="loggingserver")
        self._status_queue.put(socket.sock.getsockname())
        socket.start_accepting()
        self._status_queue.join()  # block to allow parent to retrieve address

        while True:
            # Check for shutdown
            if not self._status_queue.empty():
                self._status_queue.get()
                socket.close()
                time.sleep(3)  # TODO: the socket needs a better way of closing
                while not socket.queue.empty():
                    obj = socket.queue.get()
                    self._process_record(obj)
                self._status_queue.task_done()
                break

            # Process logs
            try:
                obj = socket.queue.get(True, 10)
                self._process_record(obj)
            except EmptyQueue:
                pass

    def _process_record(self, obj):
        if len(obj) == 2 and obj[0] == "EXT":
            self._handle_extension_log(obj)
        else:
            self._handle_serialized_writes(obj)

    def _handle_extension_log(self, obj):
        """Pass messages received from the extension to logger"""
        obj = json.loads(obj[1])
        record = logging.LogRecord(
            name=__name__,
            level=obj["level"],
            pathname=obj["pathname"],
            lineno=obj["lineno"],
            msg=obj["msg"],
            args=obj["args"],
            exc_info=obj["exc_info"],
            func=obj["func"],
        )
        logger = logging.getLogger("openwpm")
        logger.handle(record)

    def _handle_serialized_writes(self, obj):
        """Handle records that must be serialized to the main process

        This is currently records that are written to a file on disk
        """
        if obj["exc_info"]:
            obj["exc_info"] = dill.loads(obj["exc_info"])
        if obj["args"]:
            obj["args"] = dill.loads(obj["args"])
        record = logging.makeLogRecord(obj)
        self._file_handler.emit(record)

    def close(self):
        self._status_queue.put("SHUTDOWN")
        self._status_queue.join()
        self._listener.join()
