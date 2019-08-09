from __future__ import absolute_import

import json
import logging
import logging.handlers
import os
import re
import struct
import sys
import threading
import time

import dill
import sentry_sdk
from multiprocess import JoinableQueue
from sentry_sdk.integrations.logging import BreadcrumbHandler, EventHandler
from six.moves.queue import Empty as EmptyQueue
from six.moves.urllib import parse as urlparse

from .SocketInterface import serversocket

BROWSER_PREFIX = re.compile(r"^BROWSER (-)?\d+:\s*")
NETERROR_RE = re.compile(
    r"WebDriverException: Message: Reached error page: about:neterror\?(.*)\."
)


class ClientSocketHandler(logging.handlers.SocketHandler):
    """
    Make SocketHandler compatible with SocketInterface.py
    """

    def makePickle(self, record):
        """
        Serializes the record via json and prepends a length/serialization
        flag. Returns it ready for transmission across the socket.
        """
        ei = record.exc_info
        if ei:
            # just to get traceback text into record.exc_text ...
            dummy = self.format(record)  # noqa
            record.exc_info = None  # to avoid Unpickleable error
        d = dict(record.__dict__)
        d['msg'] = record.getMessage()
        d['args'] = None
        # s = json.dumps(d).encode('utf-8')
        s = dill.dumps(d)
        if ei:
            record.exc_info = ei  # for next handler
        return struct.pack('>Lc', len(s), b'd') + s


class MPLogger(object):
    """Configure OpenWPM logging across processes"""

    def __init__(self, log_file, crawl_context=None):
        self._crawl_context = crawl_context
        # Configure log handlers
        self._status_queue = JoinableQueue()
        self._log_file = os.path.expanduser(log_file)
        self._initialize_loggers()

        # Configure sentry (if available)
        self._sentry_dsn = os.getenv('SENTRY_DSN', None)
        if self._sentry_dsn:
            self._initialize_sentry()

    def _initialize_loggers(self):
        """Set up console logging and serialized file logging"""
        logger = logging.getLogger('openwpm')
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
        handler.setLevel(logging.DEBUG)
        self._file_handler = handler

        self._listener = threading.Thread(
            target=self._start_listener
        )
        self._listener.daemon = True
        self._listener.start()
        self.logger_address = self._status_queue.get(timeout=60)
        self._status_queue.task_done()

        # Attach console handler to log to console
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(module)-20s - %(levelname)-8s - %(message)s')
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)

        # Attach socket handler to logger to serialize writes to file
        socketHandler = ClientSocketHandler(*self.logger_address)
        socketHandler.setLevel(logging.DEBUG)
        logger.addHandler(socketHandler)

    def _sentry_before_send(self, event, hint):
        """Update sentry events before they are sent

        Note: we want to be very conservative in handling errors here. If this
        method throws an error, Sentry silently discards it and no record is
        sent. It's much better to have Sentry send an unparsed error then no
        error.
        """

        # Strip "BROWSER X: " prefix to clean up logs
        if 'logentry' in event and 'message' in event['logentry']:
            if re.match(BROWSER_PREFIX, event['logentry']['message']):
                event['logentry']['message'] = re.sub(
                    BROWSER_PREFIX, '', event['logentry']['message'])

        # Add traceback info to fingerprint for logs that contain a traceback
        try:
            event['logentry']['message'] = event['extra']['exception'].strip()
        except KeyError:
            pass

        # Combine neterrors of the same type
        try:
            if 'about:neterror' in event['extra']['exception']:
                qs = re.match(
                    NETERROR_RE, event['extra']['exception']).group(1)
                params = urlparse.parse_qs(qs)
                event['fingerprint'] = ['neterror-%s' % '&'.join(params['e'])]
        except Exception:
            pass

        return event

    def _initialize_sentry(self):
        """If running a cloud crawl, we can pull the sentry endpoint
        and related config varibles from the environment"""
        self._breadcrumb_handler = BreadcrumbHandler(level=logging.DEBUG)
        self._event_handler = EventHandler(level=logging.ERROR)
        sentry_sdk.init(
            dsn=self._sentry_dsn,
            before_send=self._sentry_before_send
        )
        with sentry_sdk.configure_scope() as scope:
            if self._crawl_context:
                scope.set_tag(
                    'CRAWL_REFERENCE', '%s/%s' %
                    (self._crawl_context.get('s3_bucket', 'UNKNOWN'),
                     self._crawl_context.get('s3_directory', 'UNKNOWN'))
                )

    def _start_listener(self):
        """Start listening socket for remote logs from extension"""
        socket = serversocket(name="loggingserver")
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
        if len(obj) == 2 and obj[0] == 'EXT':
            self._handle_extension_log(obj)
        else:
            self._handle_serialized_writes(obj)

    def _handle_extension_log(self, obj):
        """Pass messages received from the extension to logger"""
        obj = json.loads(obj[1])
        record = logging.LogRecord(
            name=__name__,
            level=obj['level'],
            pathname=obj['pathname'],
            lineno=obj['lineno'],
            msg=obj['msg'],
            args=obj['args'],
            exc_info=obj['exc_info'],
            func=obj['func']
        )
        logger = logging.getLogger('openwpm')
        logger.handle(record)

    def _handle_serialized_writes(self, obj):
        """Handle records that must be serialized to the main process

        This is currently records that are written to a file on disk
        and those sent to Sentry.
        """
        record = logging.makeLogRecord(obj)
        self._file_handler.emit(record)
        if self._sentry_dsn:
            if record.levelno >= self._breadcrumb_handler.level:
                self._breadcrumb_handler.handle(record)
            if record.levelno >= self._event_handler.level:
                self._event_handler.handle(record)

    def close(self):
        self._status_queue.put("SHUTDOWN")
        self._status_queue.join()
        self._listener.join()
