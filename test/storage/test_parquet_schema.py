"""Guard parquet_schema.py against drifting from schema.sql.

Browser tests store via SQLite and the parquet round-trip tests use values
generated from parquet_schema.py itself, so neither notices a misnamed column.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, Set

import pyarrow.parquet as pq
import pytest

from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.local_storage import LocalArrowProvider
from openwpm.storage.parquet_schema import PQ_SCHEMAS
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_providers import StructuredStorageProvider, TableName
from openwpm.task_manager import TaskManager
from openwpm.types import VisitId
from test.utilities import ServerUrls

SCHEMA_SQL = Path(__file__).parents[2] / "openwpm" / "storage" / "schema.sql"

# SQLite-side row ids (navigations.id is never set) and insert timestamps;
# records never carry them.
SQL_ONLY: Dict[str, Set[str]] = {
    **{
        table: {"id"}
        for table in (
            "callstacks",
            "dns_responses",
            "http_redirects",
            "http_requests",
            "http_responses",
            "javascript",
            "javascript_cookies",
            "navigations",
        )
    },
    "task": {"start_time"},
    "crawl": {"start_time"},
    "crawl_history": {"dtg"},
}
# ArrowProvider adds instance_id to every record as the partitioning key.
PARQUET_ONLY: Dict[str, Set[str]] = {table: {"instance_id"} for table in PQ_SCHEMAS}


def sql_columns() -> Dict[str, Set[str]]:
    with sqlite3.connect(":memory:") as db:
        db.executescript(SCHEMA_SQL.read_text())
        tables = [
            name
            for (name,) in db.execute(
                "SELECT name FROM sqlite_master"
                " WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        return {
            table: {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
            for table in tables
        }


@pytest.mark.pyonly
def test_parquet_schema_matches_sql_schema() -> None:
    sql = sql_columns()
    assert sql.keys() == PQ_SCHEMAS.keys()
    for table, columns in sql.items():
        parquet = set(PQ_SCHEMAS[table].names)
        assert columns - parquet == SQL_ONLY.get(table, set()), table
        assert parquet - columns == PARQUET_ONLY[table], table


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_arrow_provider_logs_unknown_fields(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    provider = LocalArrowProvider(tmp_path)
    await provider.init()
    for _ in range(2):
        record = {"visit_id": 1, "browser_id": 1, "site_url": "a", "unknown": 1}
        await provider.store_record(TableName("site_visits"), VisitId(1), record)
    errors = [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(errors) == 1
    assert "site_visits has no column unknown" in errors[0]


PAGES = (
    "/http_test_page.html",  # http_*, dns_responses, iframe navigations
    "/js_cookie.html",  # javascript_cookies
    "/canvas_fingerprinting.html",  # javascript calls with arguments
    "/js_call_stack.html",  # javascript call stacks
)


def crawl(
    data_dir: Path, provider: StructuredStorageProvider, server: ServerUrls
) -> str:
    data_dir.mkdir()
    manager_params = ManagerParams(num_browsers=1)
    manager_params.data_directory = data_dir
    manager_params.log_path = data_dir / "openwpm.log"
    manager_params.testing = True
    browser_params = BrowserParams(display_mode="headless")
    browser_params.http_instrument = True
    browser_params.cookie_instrument = True
    browser_params.navigation_instrument = True
    browser_params.dns_instrument = True
    browser_params.js_instrument = True
    browser_params.js_instrument_settings = ["collection_fingerprinting"]
    with TaskManager(manager_params, [browser_params], provider, None) as manager:
        for page in PAGES:
            manager.get(server.base + page)
    return manager_params.log_path.read_text()


def test_parquet_crawl_matches_sqlite_crawl(
    tmp_path: Path, server: ServerUrls, xpi: None
) -> None:
    sqlite_db = tmp_path / "sqlite" / "crawl-data.sqlite"
    crawl(tmp_path / "sqlite", SQLiteStorageProvider(sqlite_db), server)
    log = crawl(tmp_path / "parquet", LocalArrowProvider(tmp_path / "parquet"), server)

    dropped = [line for line in log.splitlines() if "has no column" in line]

    missing = []
    with sqlite3.connect(sqlite_db) as db:
        for table, columns in sql_columns().items():
            written = {
                column
                for column in columns - SQL_ONLY.get(table, set())
                if db.execute(f"SELECT COUNT({column}) FROM {table}").fetchone()[0]
            }
            if not written:
                continue
            parquet_dir = tmp_path / "parquet" / table
            df = (
                pq.read_table(parquet_dir).to_pandas() if parquet_dir.exists() else None
            )
            for column in sorted(written):
                if df is None or column not in df or df[column].isna().all():
                    missing.append(f"{table}.{column}")
    assert (dropped, missing) == ([], [])
