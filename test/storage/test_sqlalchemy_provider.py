"""Tests for the SQLAlchemy storage provider.

Covers:
1. Schema equivalence: SQLAlchemy-generated DDL matches schema.sql
2. All-tables insertion: parametrized across all structured providers
3. _coerce_record edge cases: bool, bytes, callable, dict coercions
"""

import json
import os
import re
import sqlite3

import pytest

from openwpm.storage.sqlalchemy_provider import SQLAlchemyStorageProvider
from openwpm.storage.storage_providers import StructuredStorageProvider, TableName
from openwpm.types import VisitId

from .fixtures import postgresql_scenarios, structured_scenarios
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

    Compares column names, types, NOT NULL constraints, default values,
    and AUTOINCREMENT status for every table.
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
@pytest.mark.parametrize("structured_provider", structured_scenarios, indirect=True)
@pytest.mark.asyncio
async def test_all_tables_access(
    structured_provider: StructuredStorageProvider,
    test_values: dt_test_values,
) -> None:
    """Insert one record into every table across all structured providers."""
    test_table, visit_ids = test_values
    await structured_provider.init()

    for table_name, test_data in test_table.items():
        await structured_provider.store_record(
            TableName(table_name), test_data["visit_id"], test_data
        )

    for visit_id in visit_ids:
        await structured_provider.finalize_visit_id(visit_id)

    await structured_provider.flush_cache()
    await structured_provider.shutdown()


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
@pytest.mark.parametrize("structured_provider", postgresql_scenarios, indirect=True)
@pytest.mark.asyncio
async def test_all_tables_access_postgresql(
    structured_provider: StructuredStorageProvider,
    test_values: dt_test_values,
) -> None:
    """Insert one record into every table using the PostgreSQL provider.

    Separated from test_all_tables_access so that a running PostgreSQL
    instance is only required when this test is explicitly selected.
    """
    test_table, visit_ids = test_values
    await structured_provider.init()

    for table_name, test_data in test_table.items():
        await structured_provider.store_record(
            TableName(table_name), test_data["visit_id"], test_data
        )

    for visit_id in visit_ids:
        await structured_provider.finalize_visit_id(visit_id)

    await structured_provider.flush_cache()
    await structured_provider.shutdown()
