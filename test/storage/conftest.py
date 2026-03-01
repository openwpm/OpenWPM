"""pytest-postgresql fixtures; they must live in conftest.py to be discovered.

OPENWPM_TEST_POSTGRESQL_URL points them at an existing server (as in CI);
otherwise they start one from the binaries found via pg_config.
"""

import os

try:
    from pytest_postgresql import factories
    from sqlalchemy.engine import make_url

    if os.environ.get("OPENWPM_TEST_POSTGRESQL_URL"):
        _url = make_url(os.environ["OPENWPM_TEST_POSTGRESQL_URL"])
        postgresql_noproc = factories.postgresql_noproc(
            host=_url.host, port=_url.port, user=_url.username, password=_url.password
        )
        postgresql = factories.postgresql("postgresql_noproc")
    else:
        postgresql_proc = factories.postgresql_proc()
        postgresql = factories.postgresql("postgresql_proc")
except ImportError:
    # Excluded via HAS_POSTGRESQL in fixtures.py.
    pass
