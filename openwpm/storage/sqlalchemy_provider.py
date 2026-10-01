import json
import logging
from asyncio import Task
from collections import defaultdict
from itertools import groupby
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple

from sqlalchemy import MetaData, Table, create_engine, event, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, NoSuchTableError, SQLAlchemyError

from openwpm.types import VisitId

from .sqlalchemy_schema import TABLE_MAP, metadata
from .storage_providers import StructuredStorageProvider, TableName

# Serializes schema creation across crawlers sharing one PostgreSQL database.
_DDL_LOCK_KEY = 0x4F70656E57504D


def _sqlite_disable_autobegin(dbapi_connection: Any, _: Any) -> None:
    dbapi_connection.isolation_level = None


def _sqlite_begin(connection: Connection) -> None:
    connection.exec_driver_sql("BEGIN")


class SQLAlchemyStorageProvider(StructuredStorageProvider):
    """StructuredStorageProvider backed by any SQLAlchemy-supported database.

    Records are buffered in memory and written in one transaction per
    flush_cache/finalize_visit_id/shutdown.
    """

    def __init__(self, db_url: str, **engine_kwargs: Any) -> None:
        super().__init__()
        self.db_url = db_url
        self.engine_kwargs = engine_kwargs
        self.logger = logging.getLogger("openwpm")
        self._engine: Optional[Engine] = None
        self._buffer: DefaultDict[Table, List[Dict[str, Any]]] = defaultdict(list)
        # None marks a table that does not exist.
        self._reflected_tables: Dict[str, Optional[Table]] = {}
        self._reported: Set[Tuple[str, ...]] = set()

    async def init(self) -> None:
        engine = create_engine(
            self.db_url, **{"pool_pre_ping": True, **self.engine_kwargs}
        )
        if engine.dialect.name == "sqlite":
            # pysqlite emits no BEGIN before a SAVEPOINT, so every RELEASE would
            # commit. https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
            event.listen(engine, "connect", _sqlite_disable_autobegin)
            event.listen(engine, "begin", _sqlite_begin)
        with engine.begin() as connection:
            if engine.dialect.name == "postgresql":
                connection.execute(
                    text("SELECT pg_advisory_xact_lock(:key)"), {"key": _DDL_LOCK_KEY}
                )
            metadata.create_all(connection)
        self._engine = engine

    def _get_table(self, table_name: str) -> Optional[Table]:
        """Return the schema table, or reflect a custom one (e.g. page_links)."""
        if table_name in TABLE_MAP:
            return TABLE_MAP[table_name]
        if table_name not in self._reflected_tables:
            assert self._engine is not None
            try:
                # Separate MetaData keeps create_all limited to the known schema.
                self._reflected_tables[table_name] = Table(
                    table_name, MetaData(), autoload_with=self._engine
                )
            except SQLAlchemyError as e:
                if isinstance(e, NoSuchTableError):
                    self._reflected_tables[table_name] = None
                self._report_once(
                    logging.ERROR,
                    "Dropping records for table %s: %s",
                    table_name,
                    repr(e),
                )
                return None
        return self._reflected_tables[table_name]

    def _report_once(self, level: int, msg: str, *args: str) -> None:
        if (msg, *args) not in self._reported:
            self._reported.add((msg, *args))
            self.logger.log(level, msg + " Further occurrences are not logged.", *args)

    async def flush_cache(self) -> None:
        self._flush()

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        sa_table = self._get_table(table)
        if sa_table is None:
            return
        record = self._coerce_record(record)
        for field in record.keys() - sa_table.c.keys():
            self._report_once(
                logging.ERROR,
                "Table %s has no column %s; dropping the field.",
                table,
                field,
            )
            del record[field]
        # One key set per table lets a flush insert rows in arrival order.
        for column in sa_table.c:
            if (
                column.key not in record
                and column.server_default is None
                and column is not sa_table.autoincrement_column
            ):
                record[column.key] = None
        assert self._engine is not None
        if self._engine.dialect.name == "postgresql":
            for field, value in record.items():
                if isinstance(value, str) and "\x00" in value:
                    self._report_once(
                        logging.WARNING,
                        "%s.%s contains NUL, which PostgreSQL text cannot store;"
                        " replacing it with U+FFFD.",
                        table,
                        field,
                    )
                    record[field] = value.replace("\x00", "\ufffd")
        self._buffer[sa_table].append(record)

    def _flush(self) -> None:
        if not self._buffer:
            return
        batch, self._buffer = self._buffer, defaultdict(list)
        size = sum(len(rows) for rows in batch.values())
        try:
            self._write(batch, size)
        except Exception as e:
            self.logger.error("Lost %d records: %r", size, e)

    def _write(self, batch: Dict[Table, List[Dict[str, Any]]], size: int) -> None:
        assert self._engine is not None
        for attempt in (1, 2):
            with self._engine.connect() as connection:
                transaction = connection.begin()
                try:
                    for sa_table, rows in batch.items():
                        for _, run in groupby(rows, key=lambda row: row.keys()):
                            self._insert(connection, sa_table, list(run))
                except DBAPIError as e:
                    if not e.connection_invalidated or attempt == 2:
                        raise
                    self.logger.warning(
                        "Database connection lost, retrying %d records: %r", size, e
                    )
                    continue
                try:
                    transaction.commit()
                except DBAPIError as e:
                    if not e.connection_invalidated:
                        raise
                    # The server may have committed; retrying could duplicate.
                    self.logger.error(
                        "Connection lost during COMMIT; %d records may or may not"
                        " be stored: %r",
                        size,
                        e,
                    )
                return

    def _insert(
        self, connection: Connection, sa_table: Table, rows: List[Dict[str, Any]]
    ) -> None:
        try:
            with connection.begin_nested():
                connection.execute(sa_table.insert(), rows)
            return
        except Exception as e:
            if isinstance(e, DBAPIError) and e.connection_invalidated:
                raise
        # Retry row by row so one bad row does not drop the rest of the batch.
        for row in rows:
            try:
                with connection.begin_nested():
                    connection.execute(sa_table.insert(), row)
            except Exception as e:
                if isinstance(e, DBAPIError) and e.connection_invalidated:
                    raise
                self.logger.error(
                    "Unsupported record:\n%s\n%s\ntable=%s\n%s\n",
                    type(e),
                    e,
                    sa_table.name,
                    repr(row),
                )

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> Optional[Task[None]]:
        if interrupted:
            self.logger.warning("Visit with visit_id %d got interrupted", visit_id)
            await self.store_record(
                TableName("incomplete_visits"), visit_id, {"visit_id": visit_id}
            )
        self._flush()
        return None

    async def shutdown(self) -> None:
        if self._engine is not None:
            self._flush()
            self._engine.dispose()

    def execute_statement(self, statement: str) -> None:
        """Execute a raw SQL statement and commit.

        Not part of the StructuredStorageProvider interface; kept for code that
        used SQLiteStorageProvider.execute_statement.
        """
        assert self._engine is not None
        with self._engine.begin() as connection:
            connection.execute(text(statement))

    @staticmethod
    def _coerce_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert values the database drivers cannot bind.

        - bool -> int: psycopg binds bool as boolean, which an integer column rejects
        - bytes -> str (with errors='ignore')
        - callable -> str(callable)
        - dict -> json.dumps(dict); type() rather than isinstance, as in the
          original SQLiteStorageProvider, so dict subclasses pass through.
        """
        coerced = {}
        for key, value in record.items():
            if isinstance(value, bool):
                value = int(value)
            elif isinstance(value, bytes):
                value = str(value, errors="ignore")
            elif callable(value):
                value = str(value)
            elif type(value) == dict:
                value = json.dumps(value)
            coerced[key] = value
        return coerced
