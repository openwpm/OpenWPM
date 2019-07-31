""" Support for logging with the multiprocessing module """
from __future__ import absolute_import, print_function

import json
import logging
import logging.handlers
import os
import queue
import re
import struct
import sys
import threading
import time

import sentry_sdk
from sentry_sdk.integrations.logging import BreadcrumbHandler, EventHandler
from six.moves.queue import Empty as EmptyQueue
# from .SocketInterface import serversocket
from SocketInterface import serversocket

BROWSER_PREFIX = re.compile(r"^BROWSER (-)?\d+:")


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
        s = json.dumps(d).encode('utf-8')
        if ei:
            record.exc_info = ei  # for next handler
        return struct.pack('>Lc', len(s), b'j') + s


class MPLogger(object):
    """Configure OpenWPM logging across processes"""

    def __init__(self, log_file):
        self._status_queue = queue.Queue()
        self._log_file = os.path.expanduser(log_file)
        self._initialize_loggers()

        # Configure sentry (if available)
        self._sentry_dsn = os.getenv('SENTRY_DSN', None)
        if self._sentry_dsn:
            self._initialize_sentry()

    def _initialize_loggers(self):
        """Set up console logging and serialized file logging"""

        # Start file handler and listener thread (for serialization)
        handler = logging.FileHandler(self._log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(processName)-11s[%(threadName)-10s]"
            "- %(module)-20s - %(levelname)-8s: %(message)s"
        )
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        self._file_handler = handler

        self._listener = threading.Thread(
            target=self._start_listener,
            args=(self._status_queue,)
        )
        self._listener.daemon = True
        self._listener.start()
        self._listener_address = self._status_queue.get()

        # Attach console handler to log to console
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(module)-20s - %(levelname)-8s - %(message)s')
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)

        # Attach socket handler to logger to serialize writes to file
        socketHandler = ClientSocketHandler(*self._listener_address)
        socketHandler.setLevel(logging.DEBUG)
        logger.addHandler(socketHandler)

    def _sentry_before_send(self, event, hint):
        """Update sentry events before they are sent"""
        # Strip browser ID prefix for better grouping
        if re.match(BROWSER_PREFIX, event['message']):
            event['message'] = re.sub(BROWSER_PREFIX, '', event['message'])
        return event

    def _initialize_sentry(self):
        """If running a cloud crawl, we can pull the sentry endpoint
        and related config varibles from the environment"""
        print("**********")
        self._breadcrumb_handler = BreadcrumbHandler(level=logging.DEBUG)
        self._event_handler = EventHandler(level=logging.ERROR)

        # sentry_logging = LoggingIntegration(
        #     level=logging.DEBUG,
        #     event_level=logging.ERROR
        # )
        sentry_sdk.init(
            dsn=self._sentry_dsn,
            # integrations=[sentry_logging],
            # before_send=self._sentry_before_send
        )

        with sentry_sdk.configure_scope() as scope:
            # tags generate breakdown charts and search filters
            S3_BUCKET = os.getenv('S3_BUCKET', 'openwpm-crawls')
            CRAWL_DIRECTORY = os.getenv('CRAWL_DIRECTORY', 'crawl-data')
            scope.set_tag(
                'NUM_BROWSERS',
                int(os.getenv('NUM_BROWSERS', '1'))
            )
            scope.set_tag(
                'CRAWL_DIRECTORY', CRAWL_DIRECTORY
            )
            scope.set_tag(
                'S3_BUCKET', S3_BUCKET
            )
            scope.set_tag(
                'HTTP_INSTRUMENT',
                os.getenv('HTTP_INSTRUMENT', '1') == '1'
            )
            scope.set_tag(
                'COOKIE_INSTRUMENT',
                os.getenv('COOKIE_INSTRUMENT', '1') == '1'
            )
            scope.set_tag(
                'NAVIGATION_INSTRUMENT',
                os.getenv('NAVIGATION_INSTRUMENT', '1') == '1'
            )
            scope.set_tag(
                'JS_INSTRUMENT',
                os.getenv('JS_INSTRUMENT', '1') == '1'
            )
            scope.set_tag(
                'SAVE_JAVASCRIPT',
                os.getenv('SAVE_JAVASCRIPT', '0') == '1'
            )
            scope.set_tag(
                'DWELL_TIME',
                int(os.getenv('DWELL_TIME', '10'))
            )
            scope.set_tag(
                'TIMEOUT',
                int(os.getenv('TIMEOUT', '60'))
            )
            scope.set_tag(
                'CRAWL_REFERENCE', '%s/%s' %
                (S3_BUCKET, CRAWL_DIRECTORY)
            )
            # context adds addition information that may be of interest
            scope.set_context("crawl_config", {
                'REDIS_QUEUE_NAME': os.getenv(
                    'REDIS_QUEUE_NAME', 'crawl-queue'),
            })
        sentry_sdk.capture_message("[MPLogger] Crawl started.")

    def _start_listener(self, status_queue):
        """Start listening socket for remote logs from extension"""
        socket = serversocket(name="loggingserver")
        status_queue.put(socket.sock.getsockname())
        socket.start_accepting()

        while True:
            # Check for shutdown
            if not self._status_queue.empty():
                self._status_queue.get()
                socket.close()
                time.sleep(3)  # TODO: the socket needs a better way of closing
                while not socket.queue.empty():
                    obj = socket.queue.get()
                    self._process_record(obj)
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
        logger = logging.getLogger()
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
        if self._sentry_dsn:
            sentry_sdk.capture_message("[MPLogger] Crawl finished.")
        self._status_queue.put("SHUTDOWN")
        self._listener.join()


def main():
    import logging
    import multiprocess as mp

    # Set up loggingserver
    log_file = '~/mplogger.log'
    openwpm_logger = MPLogger(log_file)

    # Connect a child process to the server
    def child_proc(index):
        logging.info('Child %d - Test1' % index)
        logging.info('Child %d - Test2' % index)
        logging.info('Child %d - Test3' % index)
        logging.info('Child %d - Test4' % index)
        logging.debug('Child %d - Test5' % index)
        time.sleep(1)
        logging.error('Child %d - Test6' % index)
        logging.critical('Child %d - Test7' % index)
        logging.warning('Child %d - Test8' % index)
        return
    child_process_1 = mp.Process(
        target=child_proc,
        args=(1,)
    )
    child_process_1.daemon = True
    child_process_1.start()
    child_process_2 = mp.Process(
        target=child_proc,
        args=(2,)
    )
    child_process_2.daemon = True
    child_process_2.start()

    # Send some sample logs
    logging.info('Test1')
    logging.error('Test2')
    logging.critical('Test3')
    logging.debug('Test4')
    logging.warning('Test5')

    logger1 = logging.getLogger('test1')
    logger2 = logging.getLogger('test2')
    logger1.info('asdfasdfsa')
    logger2.info('1234567890')

    # Close the logging server
    openwpm_logger.close()
    child_process_1.join()
    child_process_2.join()
    print("Server closed, exiting...")


if __name__ == '__main__':
    main()
