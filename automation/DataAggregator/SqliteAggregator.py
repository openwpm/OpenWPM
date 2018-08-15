from __future__ import absolute_import, print_function

import json
import os
import sqlite3
import time
from sqlite3 import IntegrityError, OperationalError, ProgrammingError

from six.moves import range

from .BaseAggregator import BaseAggregator, BaseListener

COMMIT_BATCH_SIZE = 1000
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')


def listener_process_runner(manager_params, status_queue):
    """SqliteListener runner. Pass to new process"""
    listener = SqliteListener(status_queue, manager_params)
    listener.startup()

    counter = 0  # number of executions made since last commit
    commit_time = 0  # keep track of time since last commit
    while True:
        if listener.should_shutdown():
            break

        if listener.record_queue.empty():
            time.sleep(0.001)

            # commit every five seconds to avoid blocking the db for too long
            if counter > 0 and time.time() - commit_time > 5:
                listener.db.commit()
            continue

        # process record
        record = listener.record_queue.get()
        listener.process_record(record)

        # batch commit if necessary
        counter += 1
        if counter >= COMMIT_BATCH_SIZE:
            counter = 0
            commit_time = time.time()
            listener.db.commit()

    listener.drain_queue()
    listener.shutdown()


class SqliteListener(BaseListener):
    """Listener that interfaces with a local SQLite database."""
    def __init__(self, status_queue, manager_params):
        db_path = manager_params['database_name']
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.cur = self.db.cursor()
        super(SqliteListener, self).__init__(status_queue, manager_params)

    def _generate_insert(self, table, data):
        """Generate a SQL query from `record`"""
        statement = "INSERT INTO %s (" % table
        value_str = "VALUES ("
        values = list()
        first = True
        for field, value in data.items():
            statement += "" if first else ", "
            statement += field
            value_str += "?" if first else ",?"
            values.append(value)
            first = False
        statement = statement + ") " + value_str + ")"
        return statement, values

    def process_record(self, record):
        """Add `record` to database"""
        if len(record) != 2:
            self.logger.error("Query is not the correct length")
            return
        if record[0] == "create_table":
            self.cur.execute(record[1])
            self.db.commit()
            return
        statement, args = self._generate_insert(
            table=record[0], data=record[1])
        import six
        for i in range(len(args)):
            if isinstance(args[i], six.binary_type):
                args[i] = six.text_type(args[i], errors='ignore')
            elif callable(args[i]):
                args[i] = six.text_type(args[i])
        try:
            self.cur.execute(statement, args)
        except (OperationalError, ProgrammingError, IntegrityError) as e:
            self.logger.error(
                "Unsupported record:\n%s\n%s\n%s\n%s\n"
                % (type(e), e, statement, repr(args)))

    def shutdown(self):
        self.db.commit()
        self.db.close()
        super(SqliteListener, self).shutdown()


class SqliteAggregator(BaseAggregator):
    """
    Receives SQL queries from other processes and writes them to the central
    database. Executes queries until being told to die (then it will finish
    work and shut down). Killing this process will result in data loss.
    """
    def __init__(self, manager_params, browser_params):
        super(SqliteAggregator, self).__init__(manager_params, browser_params)
        db_path = self.manager_params['database_name']
        if not os.path.exists(manager_params['data_directory']):
            os.mkdir(manager_params['data_directory'])
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.cur = self.db.cursor()
        self._create_tables()
        self._get_last_used_ids()

    def _create_tables(self):
        """Create tables (if this is a new database)"""
        with open(SCHEMA_FILE, 'r') as f:
            self.db.executescript(f.read())
        self.db.commit()

    def _get_last_used_ids(self):
        """Query max ids from database"""
        self.cur.execute("SELECT MAX(visit_id) from site_visits")
        last_visit_id = self.cur.fetchone()[0]
        if last_visit_id is None:
            last_visit_id = 0
        self.current_visit_id = last_visit_id

        self.cur.execute("SELECT MAX(crawl_id) from crawl")
        last_crawl_id = self.cur.fetchone()[0]
        if last_crawl_id is None:
            last_crawl_id = 0
        self.current_crawl_id = last_crawl_id

    def save_configuration(self, openwpm_version, browser_version):
        """Save configuration details for this crawl to the database"""

        # Record task details
        self.cur.execute(
            "INSERT INTO task "
            "(manager_params, openwpm_version, browser_version) "
            "VALUES (?,?,?)",
            (json.dumps(self.manager_params),
             openwpm_version, browser_version)
        )
        self.db.commit()
        self.task_id = self.cur.lastrowid

        # Record browser details for each brower
        for i in range(self.manager_params['num_browsers']):
            self.cur.execute(
                "INSERT INTO crawl (crawl_id, task_id, browser_params) "
                "VALUES (?,?,?)",
                (self.browser_params[i]['crawl_id'], self.task_id,
                 json.dumps(self.browser_params[i]))
            )
        self.db.commit()

    def get_next_visit_id(self):
        """Returns the next visit id"""
        self.current_visit_id += 1
        return self.current_visit_id

    def get_next_crawl_id(self):
        """Returns the next crawl id"""
        self.current_crawl_id += 1
        return self.current_crawl_id

    def launch(self):
        """Launch the aggregator listener process"""
        super(SqliteAggregator, self).launch(listener_process_runner)

    def shutdown(self):
        """ Terminates the aggregator"""
        self.db.close()
        super(SqliteAggregator, self).shutdown()
