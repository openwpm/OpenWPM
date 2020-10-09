import json
import logging
import os
import sqlite3
from os import PathLike
from sqlite3 import IntegrityError, InterfaceError, OperationalError, ProgrammingError
from typing import Any, Dict, List, Tuple

from automation.types import VisitId

from .storage_providers import StructuredStorageProvider

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")


class SqlLiteStorageProvider(StructuredStorageProvider):
    def __init__(self, db_path: PathLike) -> None:
        super().__init__()
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.cur = self.db.cursor()
        self._sql_counter = 0
        self._sql_commit_time = 0
        self.logger = logging.getLogger("openwpm")
        self._create_tables()

    def _create_tables(self) -> None:
        """Create tables (if this is a new database)"""
        with open(SCHEMA_FILE, "r") as f:
            self.db.executescript(f.read())
        self.db.commit()

    async def flush_cache(self) -> None:
        self.db.commit()

    async def store_record(
        self, table: str, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        """Submit a record to be stored
        The storing might not happen immediately
        """
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

    def _generate_insert(
        self, table: str, data: Dict[str, Any]
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

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> None:
        if interrupted:
            self.logger.warning("Visit with visit_id %d got interrupted", visit_id)
            self.cur.execute("INSERT INTO incomplete_visits VALUES (?)", (visit_id,))

    async def shutdown(self) -> None:
        self.db.commit()
        self.db.close()
