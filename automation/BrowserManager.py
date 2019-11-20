
import errno
import logging
import os
import pickle
import shutil
import signal
import sys
import threading
import time
import traceback
from queue import Empty as EmptyQueue

import psutil
from multiprocess import Queue
from selenium.common.exceptions import WebDriverException
from tblib import pickling_support

from .Commands import command_executor
from .DeployBrowsers import deploy_browser
from .Errors import BrowserConfigError, BrowserCrashError, ProfileLoadError
from .SocketInterface import clientsocket
from .utilities.multiprocess_utils import Process, parse_traceback_for_sentry

pickling_support.install()


class Browser:
    """
     The Browser class is responsbile for holding all of the
     configuration and status information on BrowserManager process
     it corresponds to. It also includes a set of methods for managing
     the BrowserManager process and its child processes/threads.
     <manager_params> are the TaskManager configuration settings.
     <browser_params> are per-browser parameter settings (e.g. whether
                      this browser is headless, etc.)
     """

    def __init__(self, manager_params, browser_params):
        # Constants
        self._SPAWN_TIMEOUT = 120  # seconds
        self._UNSUCCESSFUL_SPAWN_LIMIT = 4

        # manager parameters
        self.current_profile_path = None
        self.db_socket_address = manager_params['aggregator_address']
        self.crawl_id = browser_params['crawl_id']
        self.curr_visit_id = None
        self.browser_params = browser_params
        self.manager_params = manager_params

        # Queues and process IDs for BrowserManager

        # thread to run commands issues from TaskManager
        self.command_thread = None
        # queue for passing command tuples to BrowserManager
        self.command_queue = None
        # queue for receiving command execution status from BrowserManager
        self.status_queue = None
        # pid for browser instance controlled by BrowserManager
        self.browser_pid = None

        # boolean that says if the BrowserManager new (to optimize restarts)
        self.is_fresh = True
        # boolean indicating if the browser should be restarted
        self.restart_required = False

        self.current_timeout = None  # timeout of the current command
        # dict of additional browser profile settings (e.g. screen_res)
        self.browser_settings = None
        self.browser_manager = None  # process that controls browser

        self.logger = logging.getLogger('openwpm')

    def ready(self):
        """ return if the browser is ready to accept a command """
        return self.command_thread is None or \
            not self.command_thread.is_alive()

    def set_visit_id(self, visit_id):
        self.curr_visit_id = visit_id

    def launch_browser_manager(self):
        """
        sets up the BrowserManager and gets the process id, browser pid and,
        if applicable, screen pid. loads associated user profile if necessary
        """
        # Unsupported. See https://github.com/mozilla/OpenWPM/projects/2
        # if this is restarting from a crash, update the tar location
        # to be a tar of the crashed browser's history
        """
        if self.current_profile_path is not None:
            # tar contents of crashed profile to a temp dir
            tempdir = tempfile.mkdtemp(prefix="owpm_profile_archive_") + "/"
            profile_commands.dump_profile(
                self.current_profile_path,
                self.manager_params,
                self.browser_params,
                tempdir,
                close_webdriver=False,
                browser_settings=self.browser_settings
            )
            # make sure browser loads crashed profile
            self.browser_params['profile_tar'] = tempdir
            # don't re-randomize attributes
            self.browser_params['random_attributes'] = False
            crash_recovery = True
        else:
        """
        self.logger.info(
            "BROWSER %i: Launching browser..." % self.crawl_id
        )
        tempdir = None
        crash_recovery = False
        self.is_fresh = not crash_recovery

        # Try to spawn the browser within the timelimit
        unsuccessful_spawns = 0
        success = False

        def check_queue(launch_status):
            result = self.status_queue.get(True, self._SPAWN_TIMEOUT)
            if result[0] == 'STATUS':
                launch_status[result[1]] = True
                return result[2]
            elif result[0] == 'CRITICAL':
                raise pickle.loads(result[1])
            elif result[0] == 'FAILED':
                raise BrowserCrashError(
                    'Browser spawn returned failure status')

        while not success and \
                unsuccessful_spawns < self._UNSUCCESSFUL_SPAWN_LIMIT:
            self.logger.debug("BROWSER %i: Spawn attempt %i " % (
                self.crawl_id, unsuccessful_spawns))
            # Resets the command/status queues
            (self.command_queue, self.status_queue) = (Queue(), Queue())

            # builds and launches the browser_manager
            args = (self.command_queue, self.status_queue, self.browser_params,
                    self.manager_params, crash_recovery)
            self.browser_manager = Process(target=BrowserManager, args=args)
            self.browser_manager.daemon = True
            self.browser_manager.start()

            # Read success status of browser manager
            launch_status = dict()
            try:
                # 1. Selenium profile created
                spawned_profile_path = check_queue(launch_status)
                # 2. Profile tar loaded (if necessary)
                check_queue(launch_status)
                # 3. Browser launch attempted
                check_queue(launch_status)
                # 4. Browser launched
                (self.browser_pid, self.browser_settings) = check_queue(
                    launch_status)

                (driver_profile_path, ready) = check_queue(launch_status)
                if ready != 'READY':
                    self.logger.error(
                        "BROWSER %i: Mismatch of status queue return values, "
                        "trying again..." % self.crawl_id
                    )
                    unsuccessful_spawns += 1
                    continue
                success = True
            except (EmptyQueue, BrowserCrashError):
                unsuccessful_spawns += 1
                error_string = ''
                status_strings = [
                    'Proxy Ready', 'Profile Created', 'Profile Tar', 'Display',
                    'Launch Attempted', 'Browser Launched', 'Browser Ready']
                for string in status_strings:
                    error_string += " | %s: %s " % (
                        string, launch_status.get(string, False))
                self.logger.error(
                    "BROWSER %i: Spawn unsuccessful %s" % (self.crawl_id,
                                                           error_string))
                self.close_browser_manager()
                if 'Profile Created' in launch_status:
                    shutil.rmtree(spawned_profile_path, ignore_errors=True)

        # If the browser spawned successfully, we should update the
        # current profile path class variable and clean up the tempdir
        # and previous profile path.
        if success:
            self.logger.debug(
                "BROWSER %i: Browser spawn sucessful!" % self.crawl_id)
            previous_profile_path = self.current_profile_path
            self.current_profile_path = driver_profile_path
            if driver_profile_path != spawned_profile_path:
                shutil.rmtree(spawned_profile_path, ignore_errors=True)
            if previous_profile_path is not None:
                shutil.rmtree(previous_profile_path, ignore_errors=True)
            if tempdir is not None:
                shutil.rmtree(tempdir, ignore_errors=True)

        return success

    def restart_browser_manager(self, clear_profile=False):
        """
        kill and restart the two worker processes
        <clear_profile> marks whether we want to wipe the old profile
        """
        self.logger.info("BROWSER %i: BrowserManager restart initiated. "
                         "Clear profile? %s" % (self.crawl_id, clear_profile))
        if self.is_fresh:  # Return success if browser is fresh
            self.logger.info("BROWSER %i: Skipping restart since the browser "
                             "is a fresh instance already" % self.crawl_id)
            return True

        self.close_browser_manager()

        # if crawl should be stateless we can clear profile
        if clear_profile and self.current_profile_path is not None:
            shutil.rmtree(self.current_profile_path, ignore_errors=True)
            self.current_profile_path = None
            self.browser_params['profile_tar'] = None

        return self.launch_browser_manager()

    def close_browser_manager(self):
        """Attempt to close the webdriver and browser manager processes.

        If the browser manager process is unresponsive, the process is killed.
        """
        self.logger.debug(
            "BROWSER %i: Closing browser..." % self.crawl_id
        )

        # Join current command thread (if it exists)
        in_command_thread = threading.current_thread() == self.command_thread
        if not in_command_thread and self.command_thread is not None:
            self.logger.debug(
                "BROWSER %i: Joining command thread" % self.crawl_id)
            start_time = time.time()
            if self.current_timeout is not None:
                self.command_thread.join(self.current_timeout + 10)
            else:
                self.command_thread.join(60)

            # If command thread is still alive, process is locked
            if self.command_thread.is_alive():
                self.logger.debug(
                    "BROWSER %i: command thread failed to join during close. "
                    "Assuming the browser process is locked..." %
                    self.crawl_id
                )
                self.kill_browser_manager()
                return

            self.logger.debug(
                "BROWSER %i: %f seconds to join command thread" % (
                    self.crawl_id, time.time() - start_time))

        # If command queue doesn't exist, this likely means the browser
        # failed to launch properly. Let's kill any child processes that
        # we can find.
        if self.command_queue is None:
            self.logger.debug(
                "BROWSER %i: Command queue not found while closing." %
                self.crawl_id
            )
            self.kill_browser_manager()
            return

        # Send the shutdown command
        self.command_queue.put(("SHUTDOWN",))

        # Verify that webdriver has closed (30 second timeout)
        try:
            status = self.status_queue.get(True, 30)
        except EmptyQueue:
            self.logger.debug(
                "BROWSER %i: Status queue timeout while closing browser." %
                self.crawl_id
            )
            self.kill_browser_manager()
            return
        if status != "OK":
            self.logger.debug(
                "BROWSER %i: Command failure while closing browser." %
                self.crawl_id
            )
            self.kill_browser_manager()
            return

        # Verify that the browser process has closed (30 second timeout)
        if self.browser_manager is not None:
            self.browser_manager.join(30)
        if self.browser_manager.is_alive():
            self.logger.debug(
                "BROWSER %i: Browser manager process still alive 30 seconds "
                "after executing shutdown command." %
                self.crawl_id
            )
            self.kill_browser_manager()
            return

        self.logger.debug(
            "BROWSER %i: Browser manager closed successfully." %
            self.crawl_id
        )

    def kill_browser_manager(self):
        """Kill the BrowserManager process and all of its children"""
        self.logger.debug(
            "BROWSER %i: Attempting to kill BrowserManager with pid %i. "
            "Browser PID: %s" % (
                self.crawl_id, self.browser_manager.pid,
                self.browser_pid)
        )

        if self.browser_manager is not None and \
                self.browser_manager.pid is not None:
            try:
                os.kill(self.browser_manager.pid, signal.SIGKILL)
            except OSError:
                self.logger.debug("BROWSER %i: Browser manager process does "
                                  "not exist" % self.crawl_id)
                pass

        if self.browser_pid is not None:
            """`browser_pid` is the geckodriver process. We first kill
            the child processes (i.e. firefox) and then kill the geckodriver
            process."""
            try:
                geckodriver = psutil.Process(pid=self.browser_pid)
                for child in geckodriver.children():
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        self.logger.debug(
                            "BROWSER %i: Geckodriver child process already "
                            "killed (pid=%i)." % (self.crawl_id, child.pid))
                        pass
                geckodriver.kill()
                geckodriver.wait(timeout=20)
                for child in geckodriver.children():
                    child.wait(timeout=20)
            except psutil.NoSuchProcess:
                self.logger.debug("BROWSER %i: Geckodriver process already "
                                  "killed." % self.crawl_id)
                pass
            except psutil.TimeoutExpired:
                self.logger.debug("BROWSER %i: Timeout while waiting for "
                                  "geckodriver or browser process to close " %
                                  self.crawl_id)
                pass

    def shutdown_browser(self, during_init):
        """ Runs the closing tasks for this Browser/BrowserManager """
        # Close BrowserManager process and children
        self.logger.debug(
            "BROWSER %i: Closing browser manager..." % self.crawl_id)
        self.close_browser_manager()

        # Archive browser profile (if requested)
        if not during_init and \
                self.browser_params['profile_archive_dir'] is not None:
            self.logger.warning(
                "BROWSER %i: Archiving the browser profile directory is "
                "currently unsupported. "
                "See: https://github.com/mozilla/OpenWPM/projects/2" %
                self.crawl_id
            )
        """
        self.logger.debug(
            "BROWSER %i: during_init=%s | profile_archive_dir=%s" % (
                self.crawl_id, str(during_init),
                self.browser_params['profile_archive_dir'])
        )
        if (not during_init and
                self.browser_params['profile_archive_dir'] is not None):
            self.logger.debug(
                "BROWSER %i: Archiving browser profile directory to %s" % (
                    self.crawl_id, self.browser_params['profile_archive_dir']))
            profile_commands.dump_profile(
                self.current_profile_path,
                self.manager_params,
                self.browser_params,
                self.browser_params['profile_archive_dir'],
                close_webdriver=False,
                browser_settings=self.browser_settings,
                compress=True,
                save_flash=self.browser_params['disable_flash'] is False
            )
        """

        # Clean up temporary files
        if self.current_profile_path is not None:
            shutil.rmtree(self.current_profile_path, ignore_errors=True)


def BrowserManager(command_queue, status_queue, browser_params,
                   manager_params, crash_recovery):
    """
    The BrowserManager function runs in each new browser process.
    It is responsible for listening to command instructions from
    the Task Manager and passing them to the command module to execute
    and interface with Selenium. Command execution status is sent back
    to the TaskManager.
    """
    logger = logging.getLogger('openwpm')
    try:
        # Start webdriver and browser
        driver, prof_folder, browser_settings = deploy_browser.deploy_browser(
            status_queue, browser_params, manager_params, crash_recovery)
        if prof_folder[-1] != '/':
            prof_folder += '/'

        # Read the extension port -- if extension is enabled
        # TODO: Initial communication from extension to TM should use sockets
        if browser_params['browser'] == 'firefox' and \
                browser_params['extension_enabled']:
            logger.debug("BROWSER %i: Looking for extension port information "
                         "in %s" % (browser_params['crawl_id'], prof_folder))
            elapsed = 0
            port = None
            ep_filename = os.path.join(prof_folder, 'extension_port.txt')
            while elapsed < 5:
                try:
                    with open(ep_filename, 'rt') as f:
                        port = int(f.read().strip())
                        break
                except IOError as e:
                    if e.errno != errno.ENOENT:
                        raise
                time.sleep(0.1)
                elapsed += 0.1
            if port is None:
                # try one last time, allowing all exceptions to propagate
                with open(ep_filename, 'rt') as f:
                    port = int(f.read().strip())

            logger.debug("BROWSER %i: Connecting to extension on port %i" % (
                browser_params['crawl_id'], port))
            extension_socket = clientsocket(serialization='json')
            extension_socket.connect('127.0.0.1', int(port))
        else:
            extension_socket = None

        logger.debug(
            "BROWSER %i: BrowserManager ready." % browser_params['crawl_id'])

        # passes the profile folder, WebDriver pid back to the
        # TaskManager to signal a successful startup
        status_queue.put(('STATUS', 'Browser Ready', (prof_folder, 'READY')))
        browser_params['profile_path'] = prof_folder

        # starts accepting arguments until told to die
        while True:
            # no command for now -> sleep to avoid pegging CPU on blocking get
            if command_queue.empty():
                time.sleep(0.001)
                continue

            # reads in the command tuple of form:
            # (command, arg0, arg1, arg2, ..., argN) where N is variable
            command = command_queue.get()

            if command[0] == "SHUTDOWN":
                # Geckodriver creates a copy of the profile (and the original
                # temp file created by FirefoxProfile() is deleted).
                # We clear the profile attribute here to prevent prints from:
                # https://github.com/SeleniumHQ/selenium/blob/4e4160dd3d2f93757cafb87e2a1c20d6266f5554/py/selenium/webdriver/firefox/webdriver.py#L193-L199
                if driver.profile and not os.path.isdir(driver.profile.path):
                    driver.profile = None
                driver.quit()
                status_queue.put("OK")
                return

            logger.info("BROWSER %i: EXECUTING COMMAND: %s" % (
                browser_params['crawl_id'], str(command)))

            # attempts to perform an action and return an OK signal
            # if command fails for whatever reason, tell the TaskManager to
            # kill and restart its worker processes
            try:
                command_executor.execute_command(
                    command, driver, browser_settings,
                    browser_params, manager_params, extension_socket)
                status_queue.put("OK")
            except WebDriverException:
                # We handle WebDriverExceptions separately here because they
                # are quite common, and we often still have a handle to the
                # browser, allowing us to run the SHUTDOWN command.
                tb = traceback.format_exception(*sys.exc_info())
                if 'about:neterror' in tb[-1]:
                    status_queue.put(
                        ('NETERROR', pickle.dumps(sys.exc_info()))
                    )
                    continue
                extra = parse_traceback_for_sentry(tb)
                extra['exception'] = tb[-1]
                logger.error(
                    "BROWSER %i: WebDriverException while executing command" %
                    browser_params['crawl_id'], exc_info=True, extra=extra
                )
                status_queue.put(('FAILED', pickle.dumps(sys.exc_info())))

    except (ProfileLoadError, BrowserConfigError, AssertionError) as e:
        logger.error("BROWSER %i: %s thrown, informing parent and raising" % (
            browser_params['crawl_id'], e.__class__.__name__))
        status_queue.put(('CRITICAL', pickle.dumps(sys.exc_info())))
        return
    except Exception:
        tb = traceback.format_exception(*sys.exc_info())
        extra = parse_traceback_for_sentry(tb)
        extra['exception'] = tb[-1]
        logger.error(
            "BROWSER %i: Crash in driver, restarting browser manager" %
            browser_params['crawl_id'], exc_info=True, extra=extra
        )
        status_queue.put(('FAILED', pickle.dumps(sys.exc_info())))
        return
