from ..SocketInterface import serversocket
from ..MPLogger import loggingclient
import plyvel
import mmh3
import zlib
import time
import os


def LevelDBAggregator(manager_params, status_queue, batch_size=100):
    """
     Receives <key, value> pairs from other processes and writes them to the central database.
     Executes queries until being told to die (then it will finish work and shut down).
     This process should never be terminated un-gracefully.

     <manager_params> TaskManager configuration parameters
     <status_queue> is a queue connect to the TaskManager used for communication
     <batch_size> is the size of the write batch
    """

    # sets up logging connection
    logger = loggingclient(*manager_params['logger_address'])

    # sets up the serversocket to start accepting connections
    sock = serversocket()
    status_queue.put(sock.sock.getsockname())  # let TM know location
    sock.start_accepting()

    # sets up DB connection
    db_path = os.path.join(manager_params['data_directory'], 'javascript.ldb')
    db = plyvel.DB(db_path,
            create_if_missing = True,
            lru_cache_size = 10**9,
            write_buffer_size = 128*10**4,
            compression = None)
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
            time.sleep(0.1)

            # commit every five seconds to avoid blocking the db for too long
            if counter > 0 and time.time() - commit_time > 5:
                batch.write()
                batch = db.write_batch()
            continue

        # process record
        script = sock.queue.get()
        counter = process_script(script, batch, db, counter, logger)

        # batch commit if necessary
        if counter >= batch_size:
            counter = 0
            commit_time = time.time()
            batch.write()
            batch = db.write_batch()

    # finishes work and gracefully stops
    batch.write()
    db.close()

def process_script(script, batch, db, counter, logger):
    """
    adds a script to the batch
    """
    # Hash script for deduplication on disk
    hasher = mmh3.hash128
    script_hash = str(hasher(script) >> 64)

    if db.get(script_hash) is not None:
        return counter

    compressed_script = zlib.compress(script)

    batch.put(script_hash, compressed_script)
    return counter + 1

def drain_queue(sock_queue, batch, db, counter, logger):
    """ Ensures queue is empty before closing """
    time.sleep(3)  # TODO: the socket needs a better way of closing
    while not sock_queue.empty():
        script = sock_queue.get()
        counter = process_script(script, batch, db, counter, logger)
