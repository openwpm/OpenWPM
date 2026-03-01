import json
import logging
from asyncio import Task
from typing import Any, Dict, Optional

from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.engine import Connection, Engine

from openwpm.types import VisitId

from .sqlalchemy_schema import TABLE_MAP, metadata
from .storage_providers import StructuredStorageProvider, TableName


class SQLAlchemyStorageProvider(StructuredStorageProvider):
    """StructuredStorageProvider backed by any SQLAlchemy-supported database."""

    def __init__(self, db_url: str, **engine_kwargs: Any) -> None:
        super().__init__()
        self.db_url = db_url
        self.engine_kwargs = engine_kwargs
        self.logger = logging.getLogger("openwpm")
        self._engine: Optional[Engine] = None
        self._connection: Optional[Connection] = None
        self._sql_counter = 0
        # Cache for dynamically reflected tables (custom tables not in TABLE_MAP)
        self._reflected_tables: Dict[str, Table] = {}

    async def init(self) -> None:
        self._engine = create_engine(self.db_url, **self.engine_kwargs)
        self._connection = self._engine.connect()
        metadata.create_all(self._engine)

    def _get_table(self, table_name: str) -> Table:
        """Look up a SQLAlchemy Table object by name.

        First checks the static TABLE_MAP (for known schema tables).
        Falls back to reflecting the table from the database (for custom tables
        like 'page_links' created by custom commands).
        """
        if table_name in TABLE_MAP:
            return TABLE_MAP[table_name]
        if table_name in self._reflected_tables:
            return self._reflected_tables[table_name]
        # Reflect unknown table from database (supports custom tables).
        # Use a separate MetaData instance to avoid polluting the canonical
        # metadata with reflected tables. This keeps metadata.create_all()
        # idempotent (only creates known schema tables).
        assert self._engine is not None
        reflected_meta = MetaData()
        reflected_table = Table(table_name, reflected_meta, autoload_with=self._engine)
        self._reflected_tables[table_name] = reflected_table
        return reflected_table

    async def flush_cache(self) -> None:
        assert self._connection is not None
        self._connection.commit()

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        assert self._connection is not None
        record = self._coerce_record(record)
        sa_table = self._get_table(table)
        try:
            self._connection.execute(sa_table.insert(), record)
            self._sql_counter += 1
        except Exception as e:
            self.logger.error(
                "Unsupported record:\n%s\n%s\ntable=%s\n%s\n"
                % (type(e), e, table, repr(record))
            )
            # On PostgreSQL, a failed statement aborts the entire transaction.
            # All subsequent statements would fail with "InFailedSqlTransaction"
            # until a ROLLBACK is issued. We must rollback here so that
            # subsequent inserts can succeed.
            try:
                self._connection.rollback()
            except Exception:
                pass  # Best-effort rollback

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> Optional[Task[None]]:
        assert self._connection is not None
        if interrupted:
            self.logger.warning("Visit with visit_id %d got interrupted", visit_id)
            incomplete = TABLE_MAP["incomplete_visits"]
            self._connection.execute(incomplete.insert(), {"visit_id": visit_id})
        self._connection.commit()
        return None

    async def shutdown(self) -> None:
        if self._connection is not None:
            self._connection.commit()
            self._connection.close()
        if self._engine is not None:
            self._engine.dispose()

    def execute_statement(self, statement: str) -> None:
        """Execute a raw SQL statement and commit.

        This is not part of the StructuredStorageProvider interface.
        It is provided for backward compatibility with code that uses
        SQLiteStorageProvider.execute_statement.
        """
        assert self._connection is not None
        self._connection.execute(text(statement))
        self._connection.commit()

    @staticmethod
    def _coerce_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Apply type coercions to ensure cross-dialect compatibility.

        - bool -> int (defensive for PostgreSQL INTEGER columns)
        - bytes -> str (with errors='ignore')
        - callable -> str(callable)
        - dict -> json.dumps(dict)

        Note: type(value) == dict (not isinstance) is inherited from the
        original SQLiteStorageProvider. This means dict subclasses like
        OrderedDict will NOT be JSON-serialized. This is a known limitation.
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
