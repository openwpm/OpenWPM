"""Fixtures shared by the storage-tier tests.

The project-wide ``mp_logger`` fixture (in ``test/conftest.py``) asserts that
no ``ERROR`` line was logged during the test. That is the right default for the
happy-path storage tests, but the *adversarial* storage tests in this directory
deliberately provoke error logging (a provider that raises, a hostile socket
frame, a malformed record). For those we need a logger that captures output the
same way but does not fail the test on the expected ERROR lines.
"""

import logging
from typing import Any, Generator

import pytest

from openwpm.mp_logger import MPLogger


@pytest.fixture(scope="module")
def adversarial_mp_logger(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[MPLogger, Any, None]:
    """An ``MPLogger`` for tests that intentionally log ERRORs.

    Like ``mp_logger`` but without the post-test assertion that no ERROR was
    logged - the adversarial tests *expect* ERROR lines and assert on
    observable pipeline behaviour (forward progress / no data loss / no hang)
    instead. Module-scoped because ``MPLogger.close`` takes ~13s.
    """
    log_path = tmp_path_factory.mktemp("adversarial") / "openwpm.log"
    logger = MPLogger(log_path, log_level_console=logging.DEBUG)
    yield logger
    logger.close()
