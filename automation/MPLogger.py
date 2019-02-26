""" Support for logging with the multiprocessing module """
from __future__ import absolute_import, print_function

import json
import logging
import logging.handlers
import os
import struct
import sys
import time

from six.moves.queue import Empty as EmptyQueue

from .SocketInterface import serversocket


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
            dummy = self.format(record) # noqa
            record.exc_info = None  # to avoid Unpickleable error
        d = dict(record.__dict__)
        d['msg'] = record.getMessage()
        d['args'] = None
        s = json.dumps(d).encode('utf-8')
        if ei:
            record.exc_info = ei  # for next handler
        return struct.pack('>Lc', len(s), b'j') + s


def loggingclient(logger_address, logger_port, level=logging.DEBUG):
    """ Establishes a logger that sends log records to loggingserver """
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # Logger object shared, so we only want to connect handlers once
    if not len(logger.handlers):

        # Set up the SocketHandler - formatted server-side
        socketHandler = ClientSocketHandler(logger_address, logger_port)
        socketHandler.setLevel(level)
        logger.addHandler(socketHandler)

        # Set up logging to console
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(module)-20s - %(levelname)-8s - %(message)s')
        consoleHandler.setFormatter(formatter)
        logger.addHandler(consoleHandler)

    return logger


def loggingserver(log_file, status_queue):
    """
    A logging server to serialize writes to the log file from multiple
    processes.

    <log_file> location of the log file on disk
    <status_queue> is a queue connect to the TaskManager used for communication
    """
    # Configure the log file
    logging.basicConfig(
        filename=os.path.expanduser(log_file),
        format='%(asctime)s - %(processName)-11s[%(threadName)-10s]' +
        ' - %(module)-20s - %(levelname)-8s: %(message)s',
        level=logging.INFO)

    # Sets up the serversocket to start accepting connections
    sock = serversocket(name="loggingserver")
    status_queue.put(sock.sock.getsockname())  # let TM know location
    sock.start_accepting()

    while True:
        # Check for KILL command from TaskManager
        if not status_queue.empty():
            status_queue.get()
            sock.close()
            _drain_queue(sock.queue)
            break

        # Process logs
        try:
            obj = sock.queue.get(True, 10)
            _handleLogRecord(obj)
        except EmptyQueue:
            pass


def _handleLogRecord(obj):
    """ Handle log, logs everything sent. Should filter client-side """

    # Log message came from browser extension: requires special handling
    if len(obj) == 2 and obj[0] == 'EXT':
        obj = json.loads(obj[1])
        record = logging.LogRecord(name=__name__,
                                   level=obj['level'],
                                   pathname=obj['pathname'],
                                   lineno=obj['lineno'],
                                   msg=obj['msg'],
                                   args=obj['args'],
                                   exc_info=obj['exc_info'],
                                   func=obj['func'])
    else:
        record = logging.makeLogRecord(obj)
    logger = logging.getLogger(record.name)
    logger.handle(record)


def _drain_queue(sock_queue):
    """ Ensures queue is empty before closing """
    time.sleep(3)  # TODO: the socket needs a better way of closing
    while not sock_queue.empty():
        obj = sock_queue.get()
        _handleLogRecord(obj)


def main():
    # Some tests
    import logging
    import logging.handlers
    import multiprocess as mp

    # Set up loggingserver
    log_file = '~/mplogger.log'
    status_queue = mp.Queue()
    lserver_process = mp.Process(target=loggingserver,
                                 args=(log_file, status_queue))
    lserver_process.daemon = True
    lserver_process.start()
    server_address = status_queue.get()

    # Connect main process to logging server
    rootLogger = logging.getLogger('')
    rootLogger.setLevel(logging.DEBUG)
    socketHandler = ClientSocketHandler(*server_address)
    rootLogger.addHandler(socketHandler)

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
    status_queue.put('DIE')
    lserver_process.join()
    print("Server closed, exiting...")


if __name__ == '__main__':
    main()
