import json
import logging
import os
import sqlite3
from pathlib import Path
from sqlite3 import (
    Connection,
    Cursor,
    IntegrityError,
    InterfaceError,
    OperationalError,
    ProgrammingError,
)
from typing import Any, Dict, List, Tuple

from openwpm.types import VisitId

from .storage_providers import StructuredStorageProvider, TableName

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")


class SQLiteStorageProvider(StructuredStorageProvider):
    db: Connection
    cur: Cursor

    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.db_path = db_path
        self._sql_counter = 0
        self._sql_commit_time = 0
        self.logger = logging.getLogger("openwpm")

    async def init(self) -> None:
        self.db = sqlite3.connect(str(self.db_path))
        self.cur = self.db.cursor()
        self._create_tables()

    def _create_tables(self) -> None:
        """Create tables (if this is a new database)"""
        with open(SCHEMA_FILE, "r") as f:
            self.db.executescript(f.read())
        self.db.commit()

    async def flush_cache(self) -> None:
        self.db.commit()

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        """Submit a record to be stored
        The storing might not happen immediately
        """
        assert self.cur is not None
        statement, args = self._generate_insert(table=table, data=record)
        for i in range(len(args)):
            if isinstance(args[i], bytes):
                args[i] = str(args[i], errors="ignore")
            elif callable(args[i]):
                args[i] = str(args[i])
            elif type(args[i]) == dict:
                args[i] = json.dumps(args[i])
        try:
            self.cur.execute(statement, args)
            self._sql_counter += 1
        except (
            OperationalError,
            ProgrammingError,
            IntegrityError,
            InterfaceError,
        ) as e:
            self.logger.error(
                "Unsupported record:\n%s\n%s\n%s\n%s\n"
                % (type(e), e, statement, repr(args))
            )

    @staticmethod
    def _generate_insert(
        table: TableName, data: Dict[str, Any]
    ) -> Tuple[str, List[Any]]:
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

    def execute_statement(self, statement: str) -> None:
        self.cur.execute(statement)
        self.db.commit()

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> None:
        if interrupted:
            self.logger.warning("Visit with visit_id %d got interrupted", visit_id)
            self.cur.execute("INSERT INTO incomplete_visits VALUES (?)", (visit_id,))
        self.db.commit()

    async def shutdown(self) -> None:
        self.db.commit()
        self.db.close()
