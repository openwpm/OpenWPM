"""
Workarounds for Selenium headaches.
"""

import errno
import logging
import os
import tempfile
import threading

from openwpm.types import BrowserId

__all__ = ["FirefoxLogInterceptor"]


def mktempfifo(suffix="", prefix="tmp", dir=None):
    """
    Same as 'tempfile.mkdtemp' but creates a fifo instead of a
    directory.
    """
    if dir is None:
        dir = tempfile.gettempdir()
    names = tempfile._get_candidate_names()
    for seq in range(tempfile.TMP_MAX):
        name = next(names)
        file = os.path.join(dir, prefix + name + suffix)
        try:
            os.mkfifo(file, 0o600)
            return file
        except OSError as e:
            if e.errno == errno.EEXIST:
                continue
            raise
    if hasattr(__builtins__, "FileExistsError"):
        exc = FileExistsError  # noqa
    else:
        exc = IOError
    raise exc(errno.EEXIST, "No usable fifo name found")


class FirefoxLogInterceptor(threading.Thread):
    """
    Intercept logs from Selenium and/or geckodriver, using a named pipe
    and a detached thread, and feed them to the primary logger for this
    instance.
    """

    def __init__(self, browser_id: BrowserId) -> None:
        threading.Thread.__init__(
            self,
            name=f"log-interceptor-{browser_id}",
        )
        self.browser_id = browser_id
        self.fifo = mktempfifo(suffix=".log", prefix="owpm_driver_")
        self.daemon = True
        self.logger = logging.getLogger("openwpm")
        assert self.fifo is not None

    def run(self) -> None:
        # We might not ever get EOF on the FIFO, so instead we delete
        # it after we receive the first line (which means the other
        # end has actually opened it).
        assert self.fifo is not None
        try:
            with open(self.fifo, "rt") as f:
                for line in f:
                    self.logger.debug(
                        "BROWSER %i: driver: %s" % (self.browser_id, line.strip())
                    )
                    if self.fifo is not None:
                        os.unlink(self.fifo)
                        self.fifo = None
        except Exception:
            self.logger.error("Error in LogInterceptor", exc_info=True)
        finally:
            if self.fifo is not None:
                os.unlink(self.fifo)
                self.fifo = None
