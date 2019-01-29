from __future__ import absolute_import

import errno
import os
import shutil
import signal
import sys
import tempfile
import time
import traceback

import psutil
from multiprocess import Process, Queue
from six import reraise
from six.moves import cPickle as pickle
from six.moves.queue import Empty as EmptyQueue
from tblib import pickling_support

from .Commands import command_executor, profile_commands
from .DeployBrowsers import deploy_browser
from .Errors import BrowserConfigError, BrowserCrashError, ProfileLoadError
from .MPLogger import loggingclient
from .SocketInterface import clientsocket

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
        self.logger_address = manager_params['logger_address']
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
        # the pid of the display for the headless browser (if it exists)
        self.display_pid = None
        # the port of the display for the headless browser (if it exists)
        self.display_port = None

        # boolean that says if the BrowserManager new (to optimize restarts)
        self.is_fresh = True
        # boolean indicating if the browser should be restarted
        self.restart_required = False

        self.current_timeout = None  # timeout of the current command
        # dict of additional browser profile settings (e.g. screen_res)
        self.browser_settings = None
        self.browser_manager = None  # process that controls browser
        self.logger = loggingclient(*self.logger_address)

    def ready(self):
        """ return if the browser is ready to accept a command """
        return (self.command_thread is None or
                not self.command_thread.is_alive())

    def set_visit_id(self, visit_id):
        self.curr_visit_id = visit_id

    def launch_browser_manager(self):
        """
        sets up the BrowserManager and gets the process id, browser pid and,
        if applicable, screen pid. loads associated user profile if necessary
        """
        # if this is restarting from a crash, update the tar location
        # to be a tar of the crashed browser's history
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
                reraise(*pickle.loads(result[1]))
            elif result[0] == 'FAILED':
                raise BrowserCrashError(
                    'Browser spawn returned failure status')

        while (not success and
                unsuccessful_spawns < self._UNSUCCESSFUL_SPAWN_LIMIT):
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
                # 3. Display launched
                (self.display_pid, self.display_port) = check_queue(
                    launch_status)
                # 4. Browser launch attempted
                check_queue(launch_status)
                # 5. Browser launched
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
                self.kill_browser_manager()
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

        self.kill_browser_manager()

        # if crawl should be stateless we can clear profile
        if clear_profile and self.current_profile_path is not None:
            shutil.rmtree(self.current_profile_path, ignore_errors=True)
            self.current_profile_path = None
            self.browser_params['profile_tar'] = None

        return self.launch_browser_manager()

    def kill_browser_manager(self):
        """Kill the BrowserManager process and all of its children"""
        self.logger.debug(
            "BROWSER %i: Attempting to kill BrowserManager with pid %i. "
            "Display PID: %s | Display Port: %s | Browser PID: %s" % (
                self.crawl_id, self.browser_manager.pid, self.display_pid,
                self.display_port, self.browser_pid)
        )
        if (self.browser_manager is not None and
                self.browser_manager.pid is not None):
            try:
                os.kill(self.browser_manager.pid, signal.SIGKILL)
            except OSError:
                self.logger.debug("BROWSER %i: Browser manager process does "
                                  "not exist" % self.crawl_id)
                pass
        if self.display_pid is not None:
            try:
                os.kill(self.display_pid, signal.SIGKILL)
            except OSError:
                self.logger.debug("BROWSER %i: Display process does not "
                                  "exit" % self.crawl_id)
                pass
            except TypeError:
                self.logger.error("BROWSER %i: PID may not be the correct "
                                  "type %s" % (self.crawl_id,
                                               str(self.display_pid)))
        if self.display_port is not None:  # xvfb diplay lock
            lockfile = "/tmp/.X%s-lock" % self.display_port
            try:
                os.remove(lockfile)
            except OSError:
                self.logger.debug("BROWSER %i: Screen lockfile (%s) already "
                                  "removed" % (self.crawl_id, lockfile))
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
        # Join command thread
        if self.command_thread is not None:
            self.logger.debug(
                "BROWSER %i: Joining command thread" % self.crawl_id)
            start_time = time.time()
            if self.current_timeout is not None:
                self.command_thread.join(self.current_timeout + 10)
            else:
                self.command_thread.join(60)
            self.logger.debug(
                "BROWSER %i: %f seconds to join command thread" % (
                    self.crawl_id, time.time() - start_time))

        # Kill BrowserManager process and children
        self.logger.debug(
            "BROWSER %i: Killing browser manager..." % self.crawl_id)
        self.kill_browser_manager()

        # Archive browser profile (if requested)
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
    try:
        logger = loggingclient(*manager_params['logger_address'])

        # Start the virtualdisplay (if necessary), webdriver, and browser
        driver, prof_folder, browser_settings = deploy_browser.deploy_browser(
            status_queue, browser_params, manager_params, crash_recovery)
        if prof_folder[-1] != '/':
            prof_folder += '/'

        # Read the extension port -- if extension is enabled
        # TODO: Initial communication from extension to TM should use sockets
        if (browser_params['browser'] == 'firefox' and
                browser_params['extension_enabled']):
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

        # passes the profile folder, WebDriver pid and display pid back to the
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
            logger.info("BROWSER %i: EXECUTING COMMAND: %s" % (
                browser_params['crawl_id'], str(command)))
            # attempts to perform an action and return an OK signal
            # if command fails for whatever reason, tell the TaskManager to
            # kill and restart its worker processes
            command_executor.execute_command(
                command, driver, browser_settings,
                browser_params, manager_params, extension_socket)
            status_queue.put("OK")

    except (ProfileLoadError, BrowserConfigError, AssertionError) as e:
        logger.info("BROWSER %i: %s thrown, informing parent and raising" % (
            browser_params['crawl_id'], e.__class__.__name__))
        err_info = sys.exc_info()
        status_queue.put(('CRITICAL', pickle.dumps(err_info)))
        return
    except Exception:
        excp = traceback.format_exception(*sys.exc_info())
        logger.info("BROWSER %i: Crash in driver, restarting browser manager "
                    "\n %s" % (browser_params['crawl_id'], ''.join(excp)))
        status_queue.put(('FAILED', None))
        return
