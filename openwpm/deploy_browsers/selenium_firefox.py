"""
Workarounds for Selenium headaches.
"""

import logging
import os
import tempfile
import threading
import time
from typing import IO, Optional

from openwpm.types import BrowserId

__all__ = ["FirefoxLogInterceptor"]


class FirefoxLogInterceptor(threading.Thread):
    """
    Intercept logs from Selenium and/or geckodriver, using a regular log
    file and a detached thread, and feed them to the primary logger for
    this instance.

    A regular file (rather than a FIFO) is deliberate: geckodriver writes
    its log to this path's write end, and a FIFO whose read end has closed
    would make those writes fail with EPIPE -- which geckodriver escalates
    to a panic and SIGABRT. A regular file never raises EPIPE, so the
    driver is unaffected by interceptor/teardown ordering.

    The read end is opened in ``start()`` (before the writer opens the file
    by path), so the caller can unlink the path immediately afterwards. On
    Linux the open read/write fds keep the now-anonymous inode alive, and it
    is reclaimed automatically when the process exits -- leak-proof under
    ``os._exit()`` and SIGKILL alike, with no teardown hook required.
    """

    def __init__(self, browser_id: BrowserId) -> None:
        threading.Thread.__init__(
            self,
            name=f"log-interceptor-{browser_id}",
        )
        self.browser_id = browser_id
        fd, self.logfile = tempfile.mkstemp(suffix=".log", prefix="owpm_driver_")
        os.close(fd)
        self.daemon = True
        self.logger = logging.getLogger("openwpm")
        self._reader: Optional[IO[str]] = None

    def start(self) -> None:
        # Open the read end before the thread runs (and before the caller lets
        # geckodriver open the file by path), so the path can be unlinked while
        # both fds keep the anonymous inode alive.
        self._reader = open(self.logfile, "rt")
        super().start()

    def run(self) -> None:
        assert self._reader is not None, "start() must be called before run()"
        try:
            with self._reader as f:
                # Tail the log file: read newly written lines as they appear.
                # A regular-file readline() can return a partial line if the
                # writer flushed mid-line or our poll landed mid-write, so we
                # accumulate fragments and only emit once we see a newline --
                # otherwise a single driver line would be split across two log
                # entries.
                buf = ""
                while True:
                    chunk = f.readline()
                    if not chunk:
                        # EOF: nothing more written yet. Wait without flushing
                        # the partial buffer -- the rest of the line is coming.
                        time.sleep(0.1)
                        continue
                    buf += chunk
                    if buf.endswith("\n"):
                        self.logger.debug(
                            "BROWSER %i: driver: %s" % (self.browser_id, buf.strip())
                        )
                        buf = ""
        except Exception:
            self.logger.error("Error in LogInterceptor", exc_info=True)
