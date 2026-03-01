"""Tests for the SQLAlchemy storage provider.

Covers:
1. Schema equivalence: SQLAlchemy-generated DDL matches schema.sql
2. All-tables insertion: parametrized across all structured providers
3. _coerce_record edge cases: bool, bytes, callable, dict coercions
"""

import asyncio
import json
import logging
import os
import re
import socket
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List

import pyarrow as pa
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import make_url

from openwpm.storage.parquet_schema import PQ_SCHEMAS
from openwpm.storage.sqlalchemy_provider import SQLAlchemyStorageProvider
from openwpm.storage.sqlalchemy_schema import TABLE_MAP
from openwpm.storage.storage_controller import INVALID_VISIT_ID
from openwpm.storage.storage_providers import StructuredStorageProvider, TableName
from openwpm.types import VisitId

from .fixtures import HAS_POSTGRESQL, postgresql_scenarios, structured_scenarios
from .test_values import dt_test_values

SCHEMA_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "..",
    "openwpm",
    "storage",
    "schema.sql",
)


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_schema_equivalence(tmp_path):
    """Verify that SQLAlchemy DDL produces the same schema as schema.sql.

    Compares column names, types, NOT NULL constraints, and AUTOINCREMENT
    status for every table.
    """
    # Create database via schema.sql directly (bypassing SQLiteStorageProvider
    # which now delegates to SQLAlchemy — we need independent comparison).
    legacy_db = tmp_path / "legacy.sqlite"
    legacy_conn_setup = sqlite3.connect(str(legacy_db))
    with open(SCHEMA_FILE, "r") as f:
        legacy_conn_setup.executescript(f.read())
    legacy_conn_setup.commit()
    legacy_conn_setup.close()

    # Create database via SQLAlchemy
    sa_db = tmp_path / "sqlalchemy.sqlite"
    sa_provider = SQLAlchemyStorageProvider(f"sqlite:///{sa_db}")
    await sa_provider.init()
    await sa_provider.shutdown()

    legacy_conn = sqlite3.connect(str(legacy_db))
    sa_conn = sqlite3.connect(str(sa_db))

    try:
        # Get table lists
        legacy_tables = {
            row[0]
            for row in legacy_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name != 'sqlite_sequence'"
            ).fetchall()
        }
        sa_tables = {
            row[0]
            for row in sa_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name != 'sqlite_sequence'"
            ).fetchall()
        }
        assert (
            legacy_tables == sa_tables
        ), f"Table sets differ: legacy={legacy_tables}, sa={sa_tables}"

        # Type normalization: schema.sql uses DATETIME, VARCHAR, STRING
        # which SQLAlchemy normalizes to TEXT. BIGINT (from BigInteger) has
        # INTEGER affinity in SQLite, so treat them as equivalent.
        type_map = {
            "DATETIME": "TEXT",
            "STRING": "TEXT",
            "BIGINT": "INTEGER",
        }

        def normalize_type(t: str) -> str:
            upper = t.upper()
            # Handle VARCHAR(N) -> VARCHAR(N) (both use it)
            if upper in type_map:
                return type_map[upper]
            return upper

        for table_name in sorted(legacy_tables):
            legacy_cols = legacy_conn.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()
            sa_cols = sa_conn.execute(f"PRAGMA table_info({table_name})").fetchall()

            # Verify same number of columns
            assert len(legacy_cols) == len(sa_cols), (
                f"Column count mismatch for {table_name}: "
                f"legacy={len(legacy_cols)}, sa={len(sa_cols)}"
            )

            # PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
            for legacy_col, sa_col in zip(legacy_cols, sa_cols):
                l_cid, l_name, l_type, l_notnull, l_default, l_pk = legacy_col
                s_cid, s_name, s_type, s_notnull, s_default, s_pk = sa_col

                assert (
                    l_name == s_name
                ), f"Column name mismatch in {table_name}: {l_name} vs {s_name}"
                assert normalize_type(l_type) == normalize_type(s_type), (
                    f"Type mismatch for {table_name}.{l_name}: " f"{l_type} vs {s_type}"
                )
                # Skip NOT NULL comparison for primary keys: SQLAlchemy always
                # adds NOT NULL to PKs, while schema.sql may not have it.
                if not l_pk:
                    assert l_notnull == s_notnull, (
                        f"NOT NULL mismatch for {table_name}.{l_name}: "
                        f"{l_notnull} vs {s_notnull}"
                    )
                assert (
                    l_pk == s_pk
                ), f"PK mismatch for {table_name}.{l_name}: {l_pk} vs {s_pk}"

            # Check AUTOINCREMENT via sqlite_master DDL
            def _has_autoincrement(conn, tbl):
                row = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (tbl,),
                ).fetchone()
                return bool(row and re.search(r"AUTOINCREMENT", row[0], re.IGNORECASE))

            legacy_ai = _has_autoincrement(legacy_conn, table_name)
            sa_ai = _has_autoincrement(sa_conn, table_name)
            assert legacy_ai == sa_ai, (
                f"AUTOINCREMENT mismatch for {table_name}: "
                f"legacy={legacy_ai}, sa={sa_ai}"
            )
    finally:
        legacy_conn.close()
        sa_conn.close()


@pytest.mark.pyonly
@pytest.mark.parametrize(
    "structured_provider", structured_scenarios + postgresql_scenarios, indirect=True
)
@pytest.mark.asyncio
async def test_all_tables_access(
    structured_provider: StructuredStorageProvider,
    test_values: dt_test_values,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Insert one record into every table across all structured providers."""
    test_table, visit_ids = test_values
    await structured_provider.init()

    for table_name, test_data in test_table.items():
        visit_id = test_data["visit_id"]
        if visit_id == INVALID_VISIT_ID:
            # task and crawl have no visit_id column. Mirror StorageController,
            # which strips the sentinel visit_id before handing the record to
            # the provider; otherwise the unknown column makes the insert fail
            # (silently, since store_record swallows exceptions).
            del test_data["visit_id"]
        await structured_provider.store_record(
            TableName(table_name), visit_id, test_data
        )

    for visit_id in visit_ids:
        await structured_provider.finalize_visit_id(visit_id)

    await structured_provider.flush_cache()
    await structured_provider.shutdown()
    # Failed inserts and unknown fields are logged and swallowed.
    assert [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR] == []


@pytest.mark.pyonly
def test_coerce_record_edge_cases():
    """Unit test for SQLAlchemyStorageProvider._coerce_record."""
    coerce = SQLAlchemyStorageProvider._coerce_record

    # bool -> int
    assert coerce({"flag": True}) == {"flag": 1}
    assert coerce({"flag": False}) == {"flag": 0}

    # bytes -> str (using str(bytes_val, errors="ignore"))
    result = coerce({"data": b"hello"})
    assert result["data"] == "hello"
    assert isinstance(result["data"], str)

    # callable -> str
    result = coerce({"func": len})
    assert isinstance(result["func"], str)
    assert "len" in result["func"]

    # dict -> json
    d = {"key": "value", "num": 42}
    result = coerce({"nested": d})
    assert result["nested"] == json.dumps(d)

    # passthrough: str, int, None
    assert coerce({"s": "hello", "n": 42, "x": None}) == {
        "s": "hello",
        "n": 42,
        "x": None,
    }


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_store_record_persists_values(tmp_path: Path) -> None:
    """store_record must actually persist rows; read them back and verify values.

    Guards against a store_record that silently no-ops (e.g. swallowing every
    insert exception and rolling the batch back) — such a regression would still
    pass a test that only checks store_record does not raise.
    """
    db = tmp_path / "readback.sqlite"
    provider = SQLAlchemyStorageProvider(f"sqlite:///{db}")
    await provider.init()
    await provider.store_record(
        TableName("site_visits"),
        VisitId(42),
        {"visit_id": 42, "browser_id": 7, "site_url": "https://example.com"},
    )
    await provider.finalize_visit_id(VisitId(42))
    await provider.flush_cache()
    await provider.shutdown()

    conn = sqlite3.connect(str(db))
    try:
        rows = conn.execute(
            "SELECT visit_id, browser_id, site_url FROM site_visits"
        ).fetchall()
    finally:
        conn.close()
    assert rows == [(42, 7, "https://example.com")]


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_bad_row_does_not_drop_batched_good_rows(tmp_path: Path) -> None:
    """A single failing insert must not discard the rest of the batch.

    The flush inserts the batch at once; when that fails (here: a duplicate
    primary key) it retries row by row, each in a SAVEPOINT, so only the bad
    row is dropped.
    """
    db = tmp_path / "batch.sqlite"
    provider = SQLAlchemyStorageProvider(f"sqlite:///{db}")
    await provider.init()
    # Good row buffered before the failure.
    await provider.store_record(
        TableName("site_visits"),
        VisitId(1),
        {"visit_id": 1, "browser_id": 1, "site_url": "https://a.example"},
    )
    # Bad row: duplicate primary key.
    await provider.store_record(
        TableName("site_visits"),
        VisitId(1),
        {"visit_id": 1, "browser_id": 1, "site_url": "https://dup.example"},
    )
    # Good row buffered after the failure.
    await provider.store_record(
        TableName("site_visits"),
        VisitId(3),
        {"visit_id": 3, "browser_id": 1, "site_url": "https://c.example"},
    )
    await provider.flush_cache()  # commit the batch
    await provider.shutdown()

    conn = sqlite3.connect(str(db))
    try:
        rows = {
            row[0]: row[1]
            for row in conn.execute("SELECT visit_id, site_url FROM site_visits")
        }
    finally:
        conn.close()
    # Both good rows survived; only the duplicate is absent. The pre-failure row
    # keeps its original value (the duplicate did not overwrite it).
    assert rows == {1: "https://a.example", 3: "https://c.example"}


@pytest.mark.pyonly
def test_postgresql_integer_widths() -> None:
    """PostgreSQL INTEGER is 4 bytes. Every column the parquet schema stores wider
    (e.g. browser_id: uint32 from getrandbits(32)) must be BIGINT there, and so
    must every surrogate key."""
    pg = postgresql.dialect()
    wide = {pa.int64(), pa.uint32(), pa.uint64()}
    narrow = [
        f"{name}.{field.name}"
        for name, table in TABLE_MAP.items()
        for field in PQ_SCHEMAS[name]
        if field.type in wide
        and field.name in table.c
        and table.c[field.name].type.compile(dialect=pg) != "BIGINT"
    ]
    assert not narrow
    for table in TABLE_MAP.values():
        col = table.autoincrement_column
        if col is not None:
            assert col.type.compile(dialect=pg) == "BIGINT", table.name
            assert col.type.compile(dialect=sqlite.dialect()) == "INTEGER", table.name


def _site_visit(visit_id: int) -> Dict[str, Any]:
    return {"visit_id": visit_id, "browser_id": 2**32 - 1, "site_url": "https://x"}


def _count(db: Path, table: str) -> int:
    conn = sqlite3.connect(str(db))
    try:
        return int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_records_not_committed_before_flush(tmp_path: Path) -> None:
    db = tmp_path / "tx.sqlite"
    provider = SQLAlchemyStorageProvider(f"sqlite:///{db}")
    await provider.init()
    for i in range(5):
        await provider.store_record(
            TableName("site_visits"), VisitId(i), _site_visit(i)
        )
    assert _count(db, "site_visits") == 0
    await provider.flush_cache()
    assert _count(db, "site_visits") == 5
    await provider.shutdown()


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_flush_batches_statements(tmp_path: Path) -> None:
    """A flush is one transaction with one INSERT per table, not one per row."""
    db = tmp_path / "batch.sqlite"
    provider = SQLAlchemyStorageProvider(f"sqlite:///{db}")
    await provider.init()
    statements: List[str] = []
    event.listen(
        provider._engine,
        "before_cursor_execute",
        lambda conn, cursor, stmt, *args: statements.append(stmt.split()[0].upper()),
    )
    for i in range(1000):
        await provider.store_record(
            TableName("site_visits"), VisitId(i), _site_visit(i)
        )
    await provider.flush_cache()
    await provider.shutdown()
    assert statements.count("INSERT") == 1
    assert len(statements) <= 5
    assert _count(db, "site_visits") == 1000


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_bad_row_isolation_stays_in_one_transaction(tmp_path: Path) -> None:
    """pysqlite does not BEGIN before a SAVEPOINT, which turns every RELEASE into
    a commit. The bad-row fallback must run inside an explicit transaction."""
    db = tmp_path / "savepoint.sqlite"
    provider = SQLAlchemyStorageProvider(f"sqlite:///{db}")
    await provider.init()
    in_tx: List[bool] = []
    event.listen(
        provider._engine,
        "after_cursor_execute",
        lambda conn, *args: in_tx.append(
            conn.connection.dbapi_connection.in_transaction
        ),
    )
    for i in (1, 1, 2):
        await provider.store_record(
            TableName("site_visits"), VisitId(i), _site_visit(i)
        )
    await provider.flush_cache()
    await provider.shutdown()
    assert in_tx and all(in_tx)
    assert _count(db, "site_visits") == 2


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_unknown_fields_are_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    db = tmp_path / "unknown.sqlite"
    provider = SQLAlchemyStorageProvider(f"sqlite:///{db}")
    await provider.init()
    record = _site_visit(1)
    record["brand_new_field"] = "x"
    await provider.store_record(TableName("site_visits"), VisitId(1), record)
    await provider.flush_cache()
    await provider.shutdown()
    assert any(
        "brand_new_field" in r.getMessage()
        for r in caplog.records
        if r.levelno >= logging.ERROR
    )
    assert _count(db, "site_visits") == 1


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_missing_table_is_logged_not_raised(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    provider = SQLAlchemyStorageProvider(f"sqlite:///{tmp_path / 'missing.sqlite'}")
    await provider.init()
    await provider.store_record(TableName("page_links"), VisitId(1), {"visit_id": 1})
    await provider.finalize_visit_id(VisitId(1))
    await provider.shutdown()
    assert any(
        "page_links" in r.getMessage()
        for r in caplog.records
        if r.levelno >= logging.ERROR
    )


def _js(event_ordinal: int, value: Any) -> Dict[str, Any]:
    return {
        "browser_id": 1,
        "visit_id": 1,
        "event_ordinal": event_ordinal,
        "time_stamp": "",
        "value": value,
    }


def _http_request(request_id: int, **extra: Any) -> Dict[str, Any]:
    return {
        "browser_id": 1,
        "visit_id": 1,
        "url": f"u{request_id}",
        "method": "GET",
        "referrer": "",
        "headers": "",
        "request_id": request_id,
        "resource_type": "",
        "time_stamp": "",
        **extra,
    }


def _scalar(url: str, query: str) -> Any:
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            return conn.execute(text(query)).scalar_one()
    finally:
        engine.dispose()


async def _store_one_unbindable_row(
    url: str, table: str, good: Any, bad: Dict[str, Any]
) -> None:
    provider = SQLAlchemyStorageProvider(url)
    await provider.init()
    for i in range(3):
        await provider.store_record(TableName(table), VisitId(1), good(i))
    await provider.store_record(TableName(table), VisitId(1), bad)
    await provider.store_record(TableName(table), VisitId(1), good(4))
    await provider.finalize_visit_id(VisitId(1))
    await provider.shutdown()


# What json.loads makes of a JSON "\ud800" escape; no driver can encode it.
LONE_SURROGATE = "abc\ud800def"


@pytest.mark.pyonly
@pytest.mark.parametrize(
    "table,good,bad",
    [
        ("javascript", lambda i: _js(i, "ok"), _js(3, LONE_SURROGATE)),
        # sqlite3 raises OverflowError, which SQLAlchemy does not wrap.
        ("http_requests", _http_request, _http_request(3, frame_id=2**64)),
    ],
    ids=["surrogate", "int-overflow"],
)
@pytest.mark.asyncio
async def test_unbindable_row_drops_only_itself(
    tmp_path: Path, table: str, good: Any, bad: Dict[str, Any]
) -> None:
    url = f"sqlite:///{tmp_path / 'unbindable.sqlite'}"
    await _store_one_unbindable_row(url, table, good, bad)
    assert _scalar(url, f"SELECT count(*) FROM {table}") == 4


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_flush_never_raises(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: Any
) -> None:
    provider = SQLAlchemyStorageProvider(f"sqlite:///{tmp_path / 'raise.sqlite'}")
    await provider.init()

    def broken(*args: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(provider, "_insert", broken)
    await provider.store_record(TableName("site_visits"), VisitId(1), _site_visit(1))
    await provider.finalize_visit_id(VisitId(1))
    await provider.shutdown()
    assert any(
        "Lost 1 records" in r.getMessage()
        for r in caplog.records
        if r.levelno >= logging.ERROR
    )


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_missing_table_is_looked_up_once(tmp_path: Path) -> None:
    provider = SQLAlchemyStorageProvider(f"sqlite:///{tmp_path / 'missing.sqlite'}")
    await provider.init()
    statements: List[str] = []
    event.listen(
        provider._engine,
        "before_cursor_execute",
        lambda conn, cursor, stmt, *args: statements.append(stmt),
    )
    await provider.store_record(TableName("page_links"), VisitId(1), {"visit_id": 1})
    lookup = len(statements)
    for _ in range(100):
        await provider.store_record(
            TableName("page_links"), VisitId(1), {"visit_id": 1}
        )
    await provider.shutdown()
    assert lookup > 0
    assert len(statements) == lookup


@pytest.mark.pyonly
@pytest.mark.asyncio
async def test_ids_follow_arrival_order(tmp_path: Path) -> None:
    """The extension omits some keys (e.g. javascript.arguments) on some records;
    that must not reorder the surrogate ids."""
    url = f"sqlite:///{tmp_path / 'order.sqlite'}"
    provider = SQLAlchemyStorageProvider(url)
    await provider.init()
    for i in range(6):
        record = _js(i, "v")
        if i % 2:
            record["arguments"] = "[]"
        await provider.store_record(TableName("javascript"), VisitId(1), record)
    await provider.finalize_visit_id(VisitId(1))
    await provider.shutdown()
    engine = create_engine(url)
    with engine.connect() as conn:
        ordinals: list[int] = list(
            conn.execute(
                text("SELECT event_ordinal FROM javascript ORDER BY id")
            ).scalars()
        )
    engine.dispose()
    assert ordinals == list(range(6))


requires_postgresql = pytest.mark.skipif(
    not HAS_POSTGRESQL, reason="needs PostgreSQL (see test/storage/conftest.py)"
)


@pytest.mark.pyonly
@requires_postgresql
@pytest.mark.asyncio
async def test_postgresql_stores_production_values(postgresql_url: str) -> None:
    """Values SQLite accepts must survive on PostgreSQL: uint32 ids as drawn by
    StorageControllerHandle, URLs over 500 chars and NUL in text."""
    provider = SQLAlchemyStorageProvider(postgresql_url)
    await provider.init()
    big = 2**32 - 1
    long_url = "https://example.com/?" + "a" * 600
    await provider.store_record(
        TableName("task"),
        INVALID_VISIT_ID,
        {
            "task_id": big,
            "manager_params": "",
            "openwpm_version": "",
            "browser_version": "",
        },
    )
    await provider.store_record(
        TableName("crawl"),
        INVALID_VISIT_ID,
        {"browser_id": big, "task_id": big, "browser_params": ""},
    )
    await provider.store_record(
        TableName("site_visits"),
        VisitId(2**53 - 1),
        {
            "visit_id": 2**53 - 1,
            "browser_id": big,
            "site_url": long_url,
            "site_rank": big,
        },
    )
    await provider.store_record(
        TableName("javascript"),
        VisitId(2**53 - 1),
        {"visit_id": 2**53 - 1, "browser_id": big, "value": "a\x00b", "time_stamp": ""},
    )
    await provider.finalize_visit_id(VisitId(2**53 - 1))
    await provider.shutdown()

    engine = create_engine(postgresql_url)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT task_id FROM task")).all() == [(big,)]
        assert conn.execute(text("SELECT browser_id, task_id FROM crawl")).all() == [
            (big, big)
        ]
        assert conn.execute(
            text("SELECT browser_id, site_url, site_rank FROM site_visits")
        ).all() == [(big, long_url, big)]
        assert conn.execute(text("SELECT value FROM javascript")).all() == [
            ("a\ufffdb",)
        ]
    engine.dispose()


def _terminate_other_backends(url: str) -> int:
    engine = create_engine(url)
    with engine.begin() as conn:
        killed: int = conn.execute(
            text(
                "SELECT count(pg_terminate_backend(pid)) FROM pg_stat_activity"
                " WHERE datname = current_database() AND pid <> pg_backend_pid()"
            )
        ).scalar_one()
    engine.dispose()
    return killed


@pytest.mark.pyonly
@requires_postgresql
@pytest.mark.asyncio
async def test_postgresql_survives_connection_loss(
    postgresql_url: str, caplog: pytest.LogCaptureFixture
) -> None:
    """A server-side disconnect, between flushes or in the middle of one, must
    neither lose the buffered batch nor raise into the StorageController."""
    provider = SQLAlchemyStorageProvider(postgresql_url)
    await provider.init()

    def store(url: str) -> Any:
        return provider.store_record(
            TableName("http_requests"),
            VisitId(1),
            {
                "browser_id": 1,
                "visit_id": 1,
                "url": url,
                "method": "GET",
                "referrer": "",
                "headers": "",
                "request_id": 1,
                "resource_type": "",
                "time_stamp": "",
            },
        )

    await store("before")
    await provider.flush_cache()

    await store("idle-kill")
    assert _terminate_other_backends(postgresql_url) >= 1
    await provider.flush_cache()

    killed: List[int] = []

    def kill_mid_flush(conn: Any, cursor: Any, statement: str, *args: Any) -> None:
        if statement.startswith("INSERT") and not killed:
            killed.append(_terminate_other_backends(postgresql_url))

    assert provider._engine is not None
    event.listen(provider._engine, "before_cursor_execute", kill_mid_flush)
    await store("mid-flush-kill")
    await provider.finalize_visit_id(VisitId(1), interrupted=True)
    event.remove(provider._engine, "before_cursor_execute", kill_mid_flush)

    await store("after")
    await provider.shutdown()
    assert killed and killed[0] >= 1

    engine = create_engine(postgresql_url)
    with engine.connect() as conn:
        urls: List[str] = list(
            conn.execute(text("SELECT url FROM http_requests ORDER BY id")).scalars()
        )
        assert urls == ["before", "idle-kill", "mid-flush-kill", "after"]
        assert conn.execute(text("SELECT visit_id FROM incomplete_visits")).all() == [
            (1,)
        ]
    engine.dispose()
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert any("retrying" in r.getMessage() for r in caplog.records)


@pytest.mark.pyonly
@requires_postgresql
def test_postgresql_concurrent_init(postgresql_url: str) -> None:
    """Crawlers started together against an empty database must all come up."""
    n = 8
    barrier = threading.Barrier(n)
    errors: List[BaseException] = []

    def start() -> None:
        provider = SQLAlchemyStorageProvider(postgresql_url)
        barrier.wait()
        try:
            asyncio.run(provider.init())
        except BaseException as e:
            errors.append(e)
        asyncio.run(provider.shutdown())

    threads = [threading.Thread(target=start) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []


@pytest.mark.pyonly
@requires_postgresql
@pytest.mark.asyncio
async def test_postgresql_unbindable_row_drops_only_itself(postgresql_url: str) -> None:
    await _store_one_unbindable_row(
        postgresql_url, "javascript", lambda i: _js(i, "ok"), _js(3, LONE_SURROGATE)
    )
    assert _scalar(postgresql_url, "SELECT count(*) FROM javascript") == 4


@pytest.mark.pyonly
@requires_postgresql
@pytest.mark.asyncio
async def test_postgresql_lost_commit_reply_is_not_retried(
    postgresql_url: str, caplog: pytest.LogCaptureFixture
) -> None:
    """The server commits but its reply is lost: a retry would duplicate the batch."""
    upstream_url = make_url(postgresql_url)
    armed = threading.Event()
    listener = socket.create_server(("127.0.0.1", 0))

    def pipe(
        src: socket.socket, dst: socket.socket, to_server: bool, state: Any
    ) -> None:
        try:
            while data := src.recv(65536):
                if to_server and armed.is_set() and b"COMMIT" in data:
                    state["commit_sent"] = True
                elif not to_server and state.get("commit_sent"):
                    armed.clear()
                    src.shutdown(socket.SHUT_RDWR)
                    dst.shutdown(socket.SHUT_RDWR)
                    return
                dst.sendall(data)
        except OSError:
            pass

    def serve() -> None:
        while True:
            try:
                client, _ = listener.accept()
            except OSError:
                return
            upstream = socket.create_connection((upstream_url.host, upstream_url.port))
            state: Dict[str, bool] = {}
            for args in (
                (client, upstream, True, state),
                (upstream, client, False, state),
            ):
                threading.Thread(target=pipe, args=args, daemon=True).start()

    threading.Thread(target=serve, daemon=True).start()
    proxy_url = upstream_url.set(
        host="127.0.0.1", port=listener.getsockname()[1]
    ).render_as_string(hide_password=False)
    try:
        provider = SQLAlchemyStorageProvider(proxy_url)
        await provider.init()
        for i in range(5):
            await provider.store_record(
                TableName("http_requests"), VisitId(1), _http_request(i)
            )
        armed.set()
        await provider.finalize_visit_id(VisitId(1))
        await provider.shutdown()
    finally:
        listener.shutdown(socket.SHUT_RDWR)
        listener.close()
    assert not armed.is_set(), "the proxy never saw COMMIT"
    assert _scalar(postgresql_url, "SELECT count(*) FROM http_requests") == 5
    assert any(
        "during COMMIT" in r.getMessage()
        for r in caplog.records
        if r.levelno >= logging.ERROR
    )
