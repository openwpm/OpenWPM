import plyvel
from .base import (
    RECORD_TYPE_CONTENT,
    RECORD_TYPE_CREATE,
    RECORD_TYPE_SPECIAL,
)

LDB_BATCH_SIZE = 100
MIN_TIME = 5  # seconds
LDB_NAME = 'content.ldb'

def _write_content_batch(self):
    """Write out content batch to LevelDB database"""
    self.content_batch.write()
    self.content_batch = self.ldb.write_batch()


def process_content(self, record):
    """Add page content to the LevelDB database"""
    table, data = record
    if table != RECORD_TYPE_CONTENT:
        raise ValueError(
            "Incorrect record type passed to `process_content`. Expected "
            "record of type `%s`, received `%s`." % (
                RECORD_TYPE_CONTENT, table)
        )
    if not self.ldb_enabled:
        raise RuntimeError(
            "Attempted to save page content but the LevelDB content "
            "database is not enabled.")
    content, content_hash = data
    content = base64.b64decode(content)
    content_hash = str(content_hash).encode('ascii')
    if self.ldb.get(content_hash) is not None:
        return
    self.content_batch.put(content_hash, content)
    self._ldb_counter += 1


def commit_unstructured_records(self):
    """Commit records to database if record count or timer is over limit"""
    ldb_over_time = (time.time() - self._ldb_commit_time) > MIN_TIME
    if self._ldb_counter >= LDB_BATCH_SIZE or (
            self._ldb_counter > 0 and ldb_over_time):
        self._write_content_batch()
        self._ldb_counter = 0
        self._ldb_commit_time = time.time()


def init_unstructured_datasource(self):
    self.ldb = plyvel.DB(
        os.path.join(self.manager_params['data_directory'], LDB_NAME),
        create_if_missing=True, write_buffer_size=128 * 10 ** 6,
        compression='snappy'
    )
    self.content_batch = self.ldb.write_batch()
    self._ldb_counter = 0
    self._ldb_commit_time = 0


def shutdown_unstructured_datasource(self):
    self._write_content_batch()
    self.ldb.close()