
import base64
import json
import os
import sqlite3
import time
from sqlite3 import (IntegrityError, InterfaceError, OperationalError,
                     ProgrammingError)

import plyvel

from .BaseAggregator import RECORD_TYPE_CONTENT, BaseAggregator, BaseListener

SQL_BATCH_SIZE = 1000
LDB_BATCH_SIZE = 100
MIN_TIME = 5  # seconds
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'schema.sql')
LDB_NAME = 'content.ldb'


def listener_process_runner(
        manager_params, status_queue, shutdown_queue, ldb_enabled):
    """LocalListener runner. Pass to new process"""
    listener = LocalListener(
        status_queue, shutdown_queue, manager_params, ldb_enabled)
    listener.startup()

    while True:
        listener.update_status_queue()
        if listener.should_shutdown():
            break

        if listener.record_queue.empty():
            time.sleep(1)
            listener.maybe_commit_records()
            continue

        # Process record
        record = listener.record_queue.get()
        listener.process_record(record)

        # batch commit if necessary
        listener.maybe_commit_records()

    listener.drain_queue()
    listener.shutdown()


class LocalListener(BaseListener):
    """Listener that interfaces with a local SQLite database."""

    def __init__(
            self, status_queue, shutdown_queue, manager_params, ldb_enabled):
        db_path = manager_params['database_name']
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.cur = self.db.cursor()
        self.ldb_enabled = ldb_enabled
        if self.ldb_enabled:
            self.ldb = plyvel.DB(
                os.path.join(manager_params['data_directory'], LDB_NAME),
                create_if_missing=True, write_buffer_size=128 * 10 ** 6,
                compression='snappy'
            )
            self.content_batch = self.ldb.write_batch()
        self._ldb_counter = 0
        self._ldb_commit_time = 0
        self._sql_counter = 0
        self._sql_commit_time = 0
        super(LocalListener, self).__init__(
            status_queue, shutdown_queue, manager_params)

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
        elif record[0] == RECORD_TYPE_CONTENT:
            self.process_content(record)
            return
        statement, args = self._generate_insert(
            table=record[0], data=record[1])
        for i in range(len(args)):
            if isinstance(args[i], bytes):
                args[i] = str(args[i], errors='ignore')
            elif callable(args[i]):
                args[i] = str(args[i])
            elif type(args[i]) == dict:
                print(args[i])
                args[i] = json.dumps(args[i])
        try:
            self.cur.execute(statement, args)
            self._sql_counter += 1
        except (OperationalError, ProgrammingError,
                IntegrityError, InterfaceError) as e:
            self.logger.error(
                "Unsupported record:\n%s\n%s\n%s\n%s\n"
                % (type(e), e, statement, repr(args)))

    def process_content(self, record):
        """Add page content to the LevelDB database"""
        if record[0] != RECORD_TYPE_CONTENT:
            raise ValueError(
                "Incorrect record type passed to `process_content`. Expected "
                "record of type `%s`, received `%s`." % (
                    RECORD_TYPE_CONTENT, record[0])
            )
        if not self.ldb_enabled:
            raise RuntimeError(
                "Attempted to save page content but the LevelDB content "
                "database is not enabled.")
        content, content_hash = record[1]
        content = base64.b64decode(content)
        content_hash = str(content_hash).encode('ascii')
        if self.ldb.get(content_hash) is not None:
            return
        self.content_batch.put(content_hash, content)
        self._ldb_counter += 1

    def _write_content_batch(self):
        """Write out content batch to LevelDB database"""
        self.content_batch.write()
        self.content_batch = self.ldb.write_batch()

    def maybe_commit_records(self):
        """Commit records to database if record count or timer is over limit"""

        # Commit SQLite Database inserts
        sql_over_time = (time.time() - self._sql_commit_time) > MIN_TIME
        if self._sql_counter >= SQL_BATCH_SIZE or (
                self._sql_counter > 0 and sql_over_time):
            self.db.commit()
            self._sql_counter = 0
            self._sql_commit_time = time.time()

        # Write LevelDB batch to DB
        if not self.ldb_enabled:
            return
        ldb_over_time = (time.time() - self._ldb_commit_time) > MIN_TIME
        if self._ldb_counter >= LDB_BATCH_SIZE or (
                self._ldb_counter > 0 and ldb_over_time):
            self._write_content_batch()
            self._ldb_counter = 0
            self._ldb_commit_time = time.time()

    def shutdown(self):
        self.db.commit()
        self.db.close()
        if self.ldb_enabled:
            self._write_content_batch()
            self.ldb.close()
        super(LocalListener, self).shutdown()


class LocalAggregator(BaseAggregator):
    """
    Receives SQL queries from other processes and writes them to the central
    database. Executes queries until being told to die (then it will finish
    work and shut down). Killing this process will result in data loss.

    If content saving is enabled, we write page content to a LevelDB database.
    """

    def __init__(self, manager_params, browser_params):
        super(LocalAggregator, self).__init__(manager_params, browser_params)
        db_path = self.manager_params['database_name']
        if not os.path.exists(manager_params['data_directory']):
            os.mkdir(manager_params['data_directory'])
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.cur = self.db.cursor()
        self._create_tables()
        self._get_last_used_ids()

        # Mark if LDBAggregator is needed
        # (if content saving is enabled on any browser)
        self.ldb_enabled = False
        for params in browser_params:
            if params['save_content']:
                self.ldb_enabled = True
                break

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
        super(LocalAggregator, self).launch(
            listener_process_runner, self.ldb_enabled)

    def shutdown(self):
        """ Terminates the aggregator"""
        self.db.close()
        super(LocalAggregator, self).shutdown()
