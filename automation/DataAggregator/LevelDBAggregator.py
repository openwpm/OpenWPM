from __future__ import absolute_import
from ..SocketInterface import serversocket
from ..MPLogger import loggingclient
import plyvel
import time
import os

DB_NAME = 'content.ldb'


def LevelDBAggregator(manager_params, status_queue, batch_size=100):
    """
     Receives <key, value> pairs from other processes and writes them to the
     central database. Executes queries until being told to die (then it will
     finish work and shut down).This process should never be terminated
     un-gracefully.

     <manager_params> TaskManager configuration parameters
     <status_queue> queue connect to the TaskManager used for communication
     <batch_size> is the size of the write batch
    """

    # sets up logging connection
    logger = loggingclient(*manager_params['logger_address'])

    # sets up the serversocket to start accepting connections
    sock = serversocket()
    status_queue.put(sock.sock.getsockname())  # let TM know location
    sock.start_accepting()

    # sets up DB connection
    db_path = os.path.join(manager_params['data_directory'], DB_NAME)
    db = plyvel.DB(db_path,
                   create_if_missing=True,
                   write_buffer_size=128*10**6,
                   compression='snappy')
    batch = db.write_batch()

    counter = 0  # number of executions made since last write
    commit_time = 0  # keep track of time since last write
    while True:
        # received KILL command from TaskManager
        if not status_queue.empty():
            status_queue.get()
            sock.close()
            drain_queue(sock.queue, batch, db, counter, logger)
            break

        # no command for now -> sleep to avoid pegging CPU on blocking get
        if sock.queue.empty():
            time.sleep(1)
            # commit every five seconds to avoid blocking the db for too long
            if counter > 0 and (time.time() - commit_time) > 5:
                counter = 0
                commit_time = time.time()
                batch.write()
                batch = db.write_batch()
            continue

        # process record
        content, content_hash = sock.queue.get()
        counter = process_content(
            content, content_hash, batch, db, counter, logger)

        # batch commit if necessary
        if counter >= batch_size:
            counter = 0
            commit_time = time.time()
            batch.write()
            batch = db.write_batch()

    # finishes work and gracefully stops
    batch.write()
    db.close()


def process_content(content, content_hash, batch, db, counter, logger):
    """
    adds content to the batch
    """
    content = content.encode('utf-8')
    content_hash = str(content_hash).encode('ascii')
    if db.get(content_hash) is not None:
        return counter

    batch.put(content_hash, content)
    return counter + 1


def drain_queue(sock_queue, batch, db, counter, logger):
    """ Ensures queue is empty before closing """
    time.sleep(3)  # TODO: the socket needs a better way of closing
    while not sock_queue.empty():
        content, content_hash = sock_queue.get()
        counter = process_content(
            content, content_hash, batch, db, counter, logger)
