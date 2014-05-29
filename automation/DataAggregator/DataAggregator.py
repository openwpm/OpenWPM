from ..SocketInterface import serversocket
from sqlite3 import OperationalError
from sqlite3 import ProgrammingError
import sqlite3
import time


def DataAggregator(db_loc, status_queue, commit_batch_size=1000):
    """
     Receives SQL queries from other processes and writes them to the central database
     Executes queries until being told to die (then it will finish work and shut down)
     This process should never be terminated un-gracefully
     Currently uses SQLite but may move to different platform

     <db_loc> is the absolute path of the DB's current location
     <status_queue> is a queue connect to the TaskManager used for communication
     <commit_batch_size> is the number of execution statements that should be made before a commit (used for speedup)
    """

    # sets up DB connection
    db = sqlite3.connect(db_loc, check_same_thread=False)
    curr = db.cursor()

    # sets up the serversocket to start accepting connections
    sock = serversocket()
    status_queue.put(sock.sock.getsockname())  # let TM know location
    sock.start_accepting()

    counter = 0  # number of executions made since last commit
    commit_time = 0  # keep track of time since last commit
    while True:
        # received KILL command from TaskManager
        if not status_queue.empty():
            status_queue.get()
            drain_queue(sock, curr)
            break

        # no command for now -> sleep to avoid pegging CPU on blocking get
        if sock.queue.empty():
            time.sleep(0.001)

            # commit every five seconds to avoid blocking the db for too long
            if counter > 0 and time.time() - commit_time > 5:
                db.commit()
            continue

        # process query
        query = sock.queue.get()
        process_query(query, curr)

        # batch commit if necessary
        counter += 1
        if counter >= commit_batch_size:
            counter = 0
            commit_time = time.time()
            db.commit()

    # finishes work and gracefully stops
    db.commit()
    db.close()
    sock.close()


def process_query(query, curr):
    """
    executes a query of form (template_string, arguments)
    query is of form (template_string, arguments)
    """
    try:
        curr.execute(query[0], query[1])
    except OperationalError:
        print "ERROR: Unsupported query"
        pass
    except ProgrammingError:
        print "ERROR: Unsupported query"
        pass


def drain_queue(sock, curr):
    """ Ensures queue is empty before closing """
    time.sleep(3)  # TODO: the socket needs a better way of closing
    while not sock.queue.empty():
        query = sock.queue.get()
        process_query(query, curr)
