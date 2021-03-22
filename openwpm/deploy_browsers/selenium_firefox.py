"""
Workarounds for Selenium headaches.
"""


import errno
import logging
import os
import tempfile
import threading

from selenium.webdriver.common.service import Service as BaseService
from selenium.webdriver.firefox import webdriver as FirefoxDriverModule
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options

__all__ = ["FirefoxBinary", "FirefoxLogInterceptor", "Options"]


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
            os.mkfifo(file, 384)  # 0600
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

    def __init__(self, browser_id):
        threading.Thread.__init__(self, name="log-interceptor-%i" % browser_id)
        self.browser_id = browser_id
        self.fifo = mktempfifo(suffix=".log", prefix="owpm_driver_")
        self.daemon = True
        self.logger = logging.getLogger("openwpm")

    def run(self):
        # We might not ever get EOF on the FIFO, so instead we delete
        # it after we receive the first line (which means the other
        # end has actually opened it).
        try:
            with open(self.fifo, "rt") as f:
                for line in f:
                    self.logger.debug(
                        "BROWSER %i: driver: %s" % (self.browser_id, line.strip())
                    )
                    if self.fifo is not None:
                        os.unlink(self.fifo)
                        self.fifo = None

        finally:
            if self.fifo is not None:
                os.unlink(self.fifo)
                self.fifo = None


class PatchedGeckoDriverService(FirefoxDriverModule.Service):
    """Object that manages the starting and stopping of the GeckoDriver.
    Modified from the original (selenium.webdriver.firefox.service.Service)
    for Py3 compat in the presence of log FIFOs, and for potential future
    extra flexibility."""

    def __init__(
        self,
        executable_path,
        port=0,
        service_args=None,
        log_path="geckodriver.log",
        env=None,
    ):
        """Creates a new instance of the GeckoDriver remote service proxy.

        GeckoDriver provides a HTTP interface speaking the W3C WebDriver
        protocol to Marionette.

        :param executable_path: Path to the GeckoDriver binary.
        :param port: Run the remote service on a specified port.
            Defaults to 0, which binds to a random open port of the
            system's choosing.
        :param service_args: Optional list of arguments to pass to the
            GeckoDriver binary.
        :param log_path: Optional path for the GeckoDriver to log to.
            Defaults to _geckodriver.log_ in the current working directory.
        :param env: Optional dictionary of output variables to expose
            in the services' environment.

        """
        log_file = None
        if log_path:
            try:
                log_file = open(log_path, "a")
            except OSError as e:
                if e.errno != errno.ESPIPE:
                    raise
                log_file = open(log_path, "w")

        BaseService.__init__(
            self, executable_path, port=port, log_file=log_file, env=env
        )
        self.service_args = service_args or []


FirefoxDriverModule.Service = PatchedGeckoDriverService
