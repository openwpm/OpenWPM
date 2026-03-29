---
title: "Add PostgreSQL tests for SQLAlchemyStorageProvider"
tags: [design-doc]
sources: []
contributors: [claude]
created: 2026-03-29
updated: 2026-03-29
---


## Design Specification

### Summary

PR #1149 implements `SQLAlchemyStorageProvider` with PostgreSQL URL support but only tests against SQLite. The missing AC from issue #1143 is tests against a real PostgreSQL instance. This adds `pytest-postgresql` to spin up a local PostgreSQL process in CI, adds `psycopg2` as a hard dependency, and extends the existing parametrized all-tables insertion test to cover a `postgresql` scenario.

### Requirements

- REQ-1: `psycopg2` and `pytest-postgresql` must be added to `environment.yaml` following the existing conda-forge pattern, making PostgreSQL testing available in all environments without optional imports.
- REQ-2: `test/storage/fixtures.py` must include a `postgresql` scenario in `structured_scenarios` backed by a `SQLAlchemyStorageProvider` initialized with a `pytest-postgresql` connection URL.
- REQ-3: The existing all-tables insertion test (13 tables, all record types from `test/storage/test_values.py`) must pass when parametrized with the `postgresql` scenario.
- REQ-4: No new test logic is required beyond adding the scenario — the existing parametrized tests cover all 13 tables and `_coerce_record` edge cases.

### Acceptance Criteria

- [ ] AC-1 (REQ-1): `environment.yaml` contains `psycopg2` and `pytest-postgresql` under `conda-forge` dependencies (same section/style as existing entries). `pip install -e .` succeeds in a fresh env. No `pytest.importorskip` guard needed.
- [ ] AC-2 (REQ-2): `test/storage/fixtures.py` imports `pytest_postgresql` and defines a `postgresql` fixture scenario. The `structured_provider` fixture's if-elif chain handles `request.param == "postgresql"` by constructing `SQLAlchemyStorageProvider(pg_url)` where `pg_url` is derived from the `pytest-postgresql` connection.
- [ ] AC-3 (REQ-2): `"postgresql"` is added to `structured_scenarios` list in `test/storage/fixtures.py` so all existing `@pytest.mark.parametrize("structured_provider", structured_scenarios)` tests automatically run against PostgreSQL.
- [ ] AC-4 (REQ-3): All 13-table insertion tests pass against PostgreSQL — verified by `pytest test/storage/ -k postgresql -v` with no errors or skips.

### Architecture

**Files changed:**
- `environment.yaml` — add `psycopg2` and `pytest-postgresql` to the `conda-forge` channel dependencies block (lines 1–48), following the alphabetical ordering convention.
- `test/storage/fixtures.py` — add `postgresql` string constant, extend `structured_provider` fixture with a `pytest-postgresql`-backed `SQLAlchemyStorageProvider`, add `"postgresql"` to `structured_scenarios`.

**`pytest-postgresql` pattern:**
```python
from pytest_postgresql import factories

postgresql_proc = factories.postgresql_proc()
postgresql = factories.postgresql("postgresql_proc")

@pytest.fixture
def structured_provider(request, tmp_path_factory, postgresql):
    ...
    elif request.param == "postgresql":
        from openwpm.storage.sqlalchemy_provider import SQLAlchemyStorageProvider
        dsn = postgresql.info.dsn  # or equivalent connection URL
        return SQLAlchemyStorageProvider(f"postgresql+psycopg2://...")
```

`pytest-postgresql` starts a real PostgreSQL process on a random port, creates a test database, and tears it down after the test. No Docker or external service required.

**No schema equivalence test for PostgreSQL** — asserting all 13 tables insert successfully is the acceptance bar. PostgreSQL type differences (e.g. `TEXT` vs `VARCHAR`) are handled by SQLAlchemy's dialect layer and covered implicitly by the insertion tests.

**`sqlalchemy>=2.0`** must also be in `environment.yaml` (added by PR #1149 but not yet in master's `environment.yaml` — verify it's present on the PR branch and carry it forward).

### Out of Scope

- PostgreSQL schema DDL equivalence test (type mapping differences are dialect concerns, not bugs)
- Testing batch inserts or connection pooling
- Docker-based PostgreSQL in CI
- Any changes to `openwpm/storage/sqlalchemy_provider.py` or `sqlalchemy_schema.py`
- Async SQLAlchemy engine support

