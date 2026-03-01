import logging
from asyncio import Task
from pathlib import Path
from typing import Any, Dict, Optional

from openwpm.types import VisitId

from .sqlalchemy_provider import SQLAlchemyStorageProvider
from .storage_providers import StructuredStorageProvider, TableName


class SQLiteStorageProvider(StructuredStorageProvider):
    """SQLite-backed StructuredStorageProvider.

    Thin wrapper around SQLAlchemyStorageProvider that preserves the
    original ``__init__(self, db_path: Path)`` constructor signature
    used throughout the codebase.
    """

    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.db_path = db_path
        self._delegate = SQLAlchemyStorageProvider(f"sqlite:///{db_path}")
        self.logger = logging.getLogger("openwpm")

    async def init(self) -> None:
        await self._delegate.init()

    async def flush_cache(self) -> None:
        await self._delegate.flush_cache()

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        await self._delegate.store_record(table, visit_id, record)

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> Optional[Task[None]]:
        return await self._delegate.finalize_visit_id(visit_id, interrupted)

    async def shutdown(self) -> None:
        await self._delegate.shutdown()

    def execute_statement(self, statement: str) -> None:
        self._delegate.execute_statement(statement)
