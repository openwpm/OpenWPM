"""
Workarounds for Selenium headaches.
"""


import errno
import json
import logging
import os
import sys
import tempfile
import threading
import zipfile

from selenium.webdriver.common.service import Service as BaseService
from selenium.webdriver.firefox import webdriver as FirefoxDriverModule
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.firefox_profile import AddonFormatError
from selenium.webdriver.firefox.firefox_profile import \
    FirefoxProfile as BaseFirefoxProfile
from selenium.webdriver.firefox.options import Options

__all__ = ['FirefoxBinary', 'FirefoxProfile', 'FirefoxLogInterceptor',
           'Options']


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
    if hasattr(__builtins__, 'FileExistsError'):
        exc = FileExistsError  # noqa
    else:
        exc = IOError
    raise exc(errno.EEXIST, "No usable fifo name found")


class FirefoxLogInterceptor(threading.Thread):
    """
    Intercept logs from Selenium and/or geckodriver, using a named pipe
    and a detached thread, and feed them to the primary logger for this
    instance.  Also responsible for extracting the _real_ profile location
    from geckodriver's log output (geckodriver copies the profile).
    """

    def __init__(self, crawl_id, profile_path):
        threading.Thread.__init__(self, name="log-interceptor-%i" % crawl_id)
        self.crawl_id = crawl_id
        self.fifo = mktempfifo(suffix=".log", prefix="owpm_driver_")
        self.profile_path = profile_path
        self.daemon = True
        self.logger = logging.getLogger('openwpm')

    def run(self):
        # We might not ever get EOF on the FIFO, so instead we delete
        # it after we receive the first line (which means the other
        # end has actually opened it).
        try:
            with open(self.fifo, "rt") as f:
                for line in f:
                    self.logger.debug("BROWSER %i: driver: %s" %
                                      (self.crawl_id, line.strip()))
                    if "Using profile path" in line:
                        self.profile_path = \
                            line.partition("Using profile path")[-1].strip()

                    if self.fifo is not None:
                        os.unlink(self.fifo)
                        self.fifo = None

        finally:
            if self.fifo is not None:
                os.unlink(self.fifo)
                self.fifo = None


class PatchedGeckoDriverService(BaseService):
    """Object that manages the starting and stopping of the GeckoDriver.
    Modified from the original (selenium.webdriver.firefox.service.Service)
    for Py3 compat in the presence of log FIFOs, and for potential future
    extra flexibility."""

    def __init__(self, executable_path, port=0, service_args=None,
                 log_path="geckodriver.log", env=None):
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
            self, executable_path, port=port, log_file=log_file, env=env)
        self.service_args = service_args or []

    def command_line_args(self):
        return ["--port", "%d" % self.port]

    def send_remote_shutdown_command(self):
        pass


FirefoxDriverModule.Service = PatchedGeckoDriverService


class FirefoxProfile(BaseFirefoxProfile):
    """Hook class for patching bugs in Selenium's FirefoxProfile class"""

    def __init__(self, *args, **kwargs):
        BaseFirefoxProfile.__init__(self, *args, **kwargs)

    def _addon_details(self, addon_path):
        """Selenium 3.4.0 doesn't support loading WebExtensions. See bug:
        https://github.com/SeleniumHQ/selenium/issues/4093. This patch uses
        code from PR: https://github.com/SeleniumHQ/selenium/pull/4790"""
        try:
            return BaseFirefoxProfile._addon_details(self, addon_path)
        except AddonFormatError:
            pass

        # Addon must be a WebExtension, parse details from `manifest.json`
        details = {
            'id': None,
            'unpack': False,
            'name': None,
            'version': None
        }

        def get_namespace_id(doc, url):
            attributes = doc.documentElement.attributes
            namespace = ""
            for i in range(attributes.length):
                if attributes.item(i).value == url:
                    if ":" in attributes.item(i).name:
                        # If the namespace is not the default one remove xlmns:
                        namespace = attributes.item(i).name.split(':')[1] + ":"
                        break
            return namespace

        def get_text(element):
            """Retrieve the text value of a given node"""
            rc = []
            for node in element.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return ''.join(rc).strip()

        if not os.path.exists(addon_path):
            raise IOError('Add-on path does not exist: %s' % addon_path)

        try:
            if zipfile.is_zipfile(addon_path):
                # Bug 944361 - We cannot use 'with' together with zipFile
                # because it will cause an exception thrown in Python 2.6.
                try:
                    compressed_file = zipfile.ZipFile(addon_path, 'r')
                    manifest = compressed_file.read('install.rdf')
                finally:
                    compressed_file.close()
            elif os.path.isdir(addon_path):
                manifest_source = 'manifest.json'
                with open(os.path.join(addon_path, manifest_source), 'r') as f:
                    manifest = f.read()
            else:
                raise IOError("Add-on path is neither an XPI nor a "
                              "directory: %s" % addon_path)
        except (IOError, KeyError) as e:
            raise AddonFormatError(str(e), sys.exc_info()[2])

        doc = json.loads(manifest)

        try:
            details['version'] = doc['version']
            details['name'] = doc['name']
        except KeyError:
            raise AddonFormatError(
                "Add-on manifest.json is missing mandatory fields. "
                "https://developer.mozilla.org/en-US/Add-ons/"
                "WebExtensions/manifest.json")

        try:
            id_ = doc['applications']['gecko']['id']
        except KeyError:
            id_ = "%s@%s" % (doc['name'], doc['version'])
            id_ = ''.join(id_.split())
        finally:
            details["id"] = id_

        return details
