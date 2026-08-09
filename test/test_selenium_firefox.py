"""Unit tests for FirefoxLogInterceptor.

These exercise the geckodriver log-tailing thread in isolation -- no browser,
no conda -- by writing to the file the way geckodriver does and asserting the
lines reach the logger. They also lock in the leak-proof unlink-on-open
contract that replaced the previous drain-on-stop machinery.
"""

import logging
import os
import time

import pytest

from openwpm.deploy_browsers.selenium_firefox import FirefoxLogInterceptor
from openwpm.types import BrowserId

pytestmark = pytest.mark.pyonly


def _wait_for(predicate, timeout=5.0, interval=0.05):
    """Poll predicate() until truthy or timeout (the tail loop is async)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def test_lines_reach_the_logger(caplog):
    interceptor = FirefoxLogInterceptor(BrowserId(0))
    # Mirror deploy_firefox: open the writer by path, then unlink immediately.
    writer = open(interceptor.logfile, "w")
    path = interceptor.logfile
    interceptor.start()
    os.unlink(path)
    try:
        with caplog.at_level(logging.DEBUG, logger="openwpm"):
            writer.write("hello geckodriver\n")
            writer.flush()
            assert _wait_for(
                lambda: any("hello geckodriver" in r.message for r in caplog.records)
            )
        record = next(r for r in caplog.records if "hello geckodriver" in r.message)
        assert "BROWSER 0: driver:" in record.message
    finally:
        writer.close()


def test_temp_file_is_unlinked_but_still_readable_via_fd(caplog):
    """The path must vanish from $TMPDIR immediately, yet writes/reads on the
    open fds must keep working -- i.e. no /tmp leak, no broken pipe."""
    interceptor = FirefoxLogInterceptor(BrowserId(1))
    path = interceptor.logfile
    writer = open(path, "w")
    interceptor.start()
    os.unlink(path)

    # Path is gone from the filesystem ...
    assert not os.path.exists(path)
    try:
        # ... but the anonymous inode still carries data to the reader.
        with caplog.at_level(logging.DEBUG, logger="openwpm"):
            writer.write("after unlink\n")
            writer.flush()
            assert _wait_for(
                lambda: any("after unlink" in r.message for r in caplog.records)
            )
    finally:
        writer.close()
    # And no temp file was left behind.
    assert not os.path.exists(path)


def test_partial_lines_are_not_fragmented(caplog):
    """A line split across two flushes must be emitted as ONE log line, not
    two -- the regular-file tail buffers until it sees a newline."""
    interceptor = FirefoxLogInterceptor(BrowserId(2))
    writer = open(interceptor.logfile, "w")
    path = interceptor.logfile
    interceptor.start()
    os.unlink(path)
    try:
        with caplog.at_level(logging.DEBUG, logger="openwpm"):
            writer.write("abc")
            writer.flush()
            # Give the tail loop a chance to read the partial fragment.
            time.sleep(0.3)
            writer.write("def\n")
            writer.flush()
            assert _wait_for(lambda: any("abcdef" in r.message for r in caplog.records))
        # "abcdef" must appear whole; the partial "abc" must NOT be its own line.
        driver_lines = [
            r.message for r in caplog.records if "BROWSER 2: driver:" in r.message
        ]
        assert any(m.endswith("abcdef") for m in driver_lines)
        assert not any(m.endswith("driver: abc") for m in driver_lines)
    finally:
        writer.close()
