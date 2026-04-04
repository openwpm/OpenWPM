"""Conditional PostgreSQL fixtures for test discovery.

pytest_postgresql fixtures must live in conftest.py so pytest can discover
them. They are only defined when the pytest-postgresql package is installed.
"""

try:
    from pytest_postgresql import factories

    postgresql_proc = factories.postgresql_proc()
    postgresql = factories.postgresql("postgresql_proc")
except ImportError:
    pass
