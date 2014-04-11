from ..SocketInterface import serversocket
import sqlite3
import time

# Receives SQL queries from other processes and writes them to the central database
# Executes queries until being told to die (then it will finish work and shut down)
# This process should never be terminated un-gracefully
# Currently uses SQLite but may move to different platform
# TODO: add killing of the serversocket once supported

# <db_loc> is the absolute path of the DB's current location
# <query_queue> is data input queue: for now, passed query strings (TODO: more involved data manipulations)
# <status_queue> is a queue connect to the TaskManager used for
# <commit_loop> is the number of execution statements that should be made before a commit (used for speedup)

def DataAggregator(db_loc, status_queue, commit_loop=1000):
    # sets up DB connection
    db = sqlite3.connect(db_loc, check_same_thread=False)
    curr = db.cursor()

    # sets up the serversocket to start accepting connections
    sock = serversocket()
    status_queue.put(sock.sock.getsockname()) #let TM know location
    sock.start_accepting()

    counter = 0  # number of executions made since last commit
    while True:
        # received KILL command from TaskManager
        if not status_queue.empty():
            status_queue.get()
            break

        # no command for now -> sleep to avoid pegging CPU on blocking get
        if sock.queue.empty():
            time.sleep(0.001)
            continue

        # executes a query of form (template_string, arguments)
        # query is of form (template_string, arguments)
        query = sock.queue.get()
        curr.execute(query[0], query[1])

        # batch commit if necessary
        counter += 1
        if counter >= commit_loop:
            counter = 0
            db.commit()

    # finishes work and gracefully stops
    db.commit()
    db.close()
