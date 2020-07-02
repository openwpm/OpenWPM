import os
import sqlite3
from sqlite3 import (
    IntegrityError,
    InterfaceError,
    OperationalError,
    ProgrammingError
)
import time


from .base import (
    RECORD_TYPE_CONTENT,
    RECORD_TYPE_CREATE,
    RECORD_TYPE_SPECIAL,
    BaseAggregator,
    BaseListener,
    BaseParams,
)

SQL_BATCH_SIZE = 1000
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'schema.sql')


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


def handle_create(self, data):
    assert isinstance(data, str)
    self.cur.execute(data)
    self.db.commit()


def write_structured_data(self, table, data, visit_id):
    statement, args = self._generate_insert(
        table=table, data=data)
    for i in range(len(args)):
        if isinstance(args[i], bytes):
            args[i] = str(args[i], errors='ignore')
        elif callable(args[i]):
            args[i] = str(args[i])
        elif type(args[i]) == dict:
            args[i] = json.dumps(args[i])
    try:
        self.cur.execute(statement, args)
        self._sql_counter += 1
    except (OperationalError, ProgrammingError,
            IntegrityError, InterfaceError) as e:
        self.logger.error(
            "Unsupported record:\n%s\n%s\n%s\n%s\n"
            % (type(e), e, statement, repr(args)))


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


def get_next_visit_id(self):
    """Returns the next visit id"""
    self.current_visit_id += 1
    return self.current_visit_id


def get_next_crawl_id(self):
    """Returns the next crawl id"""
    self.current_crawl_id += 1
    return self.current_crawl_id


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


def commit_structured_records(self):
    """Commit records to database if record count or timer is over limit"""

    # Commit SQLite Database inserts
    sql_over_time = (time.time() - self._sql_commit_time) > MIN_TIME
    if self._sql_counter >= SQL_BATCH_SIZE or (
            self._sql_counter > 0 and sql_over_time):
        self.db.commit()
        self._sql_counter = 0
        self._sql_commit_time = time.time()


def run_visit_completion_tasks(self, visit_id: int,
                                interrupted: bool = False):
    if interrupted:
        self.logger.warning(
            "Visit with visit_id %d got interrupted", visit_id)
        self.cur.execute("INSERT INTO incomplete_visits VALUES (?)",
                            (visit_id,))
        self.mark_visit_incomplete(visit_id)
    else:
        self.mark_visit_complete(visit_id)

def init_structured_datasource(self):
    db_path = self.manager_params['database_name']
    if not os.path.exists(manager_params['data_directory']):
        os.mkdir(manager_params['data_directory'])
    self.db = sqlite3.connect(db_path, check_same_thread=False)
    self.cur = self.db.cursor()
    self._create_tables()
    self._get_last_used_ids()
    self._sql_counter = 0
    self._sql_commit_time = 0


def shutdown_structured_datasource(self):
    self.db.commit()
    self.db.close()