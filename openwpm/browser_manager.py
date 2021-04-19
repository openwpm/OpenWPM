import errno
import json
import logging
import os
import pickle
import shutil
import signal
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path
from queue import Empty as EmptyQueue
from typing import TYPE_CHECKING, Optional, Tuple, Union

import psutil
from multiprocess import Queue
from selenium.common.exceptions import WebDriverException
from tblib import Traceback, pickling_support

from .command_sequence import CommandSequence
from .commands.browser_commands import FinalizeCommand
from .commands.profile_commands import dump_profile
from .commands.types import BaseCommand, ShutdownSignal
from .commands.utils.webdriver_utils import parse_neterror
from .config import BrowserParamsInternal, ManagerParamsInternal
from .deploy_browsers import deploy_firefox
from .errors import BrowserConfigError, BrowserCrashError, ProfileLoadError
from .socket_interface import ClientSocket
from .storage.storage_providers import TableName
from .types import BrowserId, VisitId
from .utilities.multiprocess_utils import (
    Process,
    kill_process_and_children,
    parse_traceback_for_sentry,
)

pickling_support.install()

if TYPE_CHECKING:
    from .task_manager import TaskManager


class BrowserManagerHandle:
    """
    The BrowserManagerHandle class is responsible for holding all of the
    configuration and status information on BrowserManager process
    it corresponds to. It also includes a set of methods for managing
    the BrowserManager process and its child processes/threads.
    <manager_params> are the TaskManager configuration settings.
    <browser_params> are per-browser parameter settings (e.g. whether
                     this browser is headless, etc.)
    """

    def __init__(
        self,
        manager_params: ManagerParamsInternal,
        browser_params: BrowserParamsInternal,
    ) -> None:
        # Constants
        self._SPAWN_TIMEOUT = 120  # seconds
        self._UNSUCCESSFUL_SPAWN_LIMIT = 4

        # manager parameters
        self.current_profile_path: Optional[Path] = None
        self.db_socket_address = manager_params.storage_controller_address
        assert browser_params.browser_id is not None
        self.browser_id: BrowserId = browser_params.browser_id
        self.curr_visit_id: Optional[VisitId] = None
        self.browser_params = browser_params
        self.manager_params = manager_params

        # Queues and process IDs for BrowserManager

        # thread to run commands issued from TaskManager
        self.command_thread: Optional[threading.Thread] = None
        # queue for passing command tuples to BrowserManager
        self.command_queue: Optional[Queue] = None
        # queue for receiving command execution status from BrowserManager
        self.status_queue: Optional[Queue] = None
        # pid for browser instance controlled by BrowserManager
        self.geckodriver_pid: Optional[int] = None
        # the pid of the display for the Xvfb display (if it exists)
        self.display_pid: Optional[int] = None
        # the port of the display for the Xvfb display (if it exists)
        self.display_port: Optional[int] = None

        # boolean that says if the BrowserManager is new (to optimize restarts)
        self.is_fresh = True
        # boolean indicating if the browser should be restarted
        self.restart_required = False

        self.current_timeout: Optional[int] = None  # timeout of the current command
        self.browser_manager: Optional[Process] = None  # process that controls browser

        self.logger = logging.getLogger("openwpm")

    def ready(self):
        """ return if the browser is ready to accept a command """
        return self.command_thread is None or not self.command_thread.is_alive()

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
            tempdir = tempfile.mkdtemp(prefix="openwpm_profile_archive_")
            tar_path = Path(tempdir) / "profile.tar"

            dump_profile(
                browser_profile_path=self.current_profile_path,
                tar_path=tar_path,
                compress=False,
                browser_params=self.browser_params,
            )

            # make sure browser loads crashed profile
            self.browser_params.recovery_tar = tar_path

            crash_recovery = True
        else:
            tempdir = None
            crash_recovery = False

        self.logger.info("BROWSER %i: Launching browser..." % self.browser_id)
        self.is_fresh = not crash_recovery

        # Try to spawn the browser within the timelimit
        unsuccessful_spawns = 0
        success = False

        def check_queue(launch_status):
            result = self.status_queue.get(True, self._SPAWN_TIMEOUT)
            if result[0] == "STATUS":
                launch_status[result[1]] = True
                return result[2]
            elif result[0] == "CRITICAL":
                _, exc, tb = pickle.loads(result[1])
                raise exc.with_traceback(tb)
            elif result[0] == "FAILED":
                raise BrowserCrashError("Browser spawn returned failure status")

        while not success and unsuccessful_spawns < self._UNSUCCESSFUL_SPAWN_LIMIT:
            self.logger.debug(
                "BROWSER %i: Spawn attempt %i " % (self.browser_id, unsuccessful_spawns)
            )
            # Resets the command/status queues
            (self.command_queue, self.status_queue) = (Queue(), Queue())

            # builds and launches the browser_manager
            args = (
                self.command_queue,
                self.status_queue,
                self.browser_params,
                self.manager_params,
                crash_recovery,
            )
            self.browser_manager = Process(target=BrowserManager, args=args)
            self.browser_manager.daemon = True
            self.browser_manager.start()

            # Read success status of browser manager
            launch_status = dict()
            try:
                # 1. Browser profile created
                browser_profile_path = check_queue(launch_status)
                # 2. Profile tar loaded (if necessary)
                check_queue(launch_status)
                # 3. Display launched (if necessary)
                self.display_pid, self.display_port = check_queue(launch_status)
                # 4. Browser launch attempted
                check_queue(launch_status)
                # 5. Browser launched
                self.geckodriver_pid = check_queue(launch_status)

                ready = check_queue(launch_status)
                if ready != "READY":
                    self.logger.error(
                        "BROWSER %i: Mismatch of status queue return values, "
                        "trying again..." % self.browser_id
                    )
                    unsuccessful_spawns += 1
                    continue
                success = True
            except (EmptyQueue, BrowserCrashError):
                unsuccessful_spawns += 1
                error_string = ""
                status_strings = [
                    "Profile Created",
                    "Profile Tar",
                    "Display",
                    "Launch Attempted",
                    "Browser Launched",
                    "Browser Ready",
                ]
                for string in status_strings:
                    error_string += " | %s: %s " % (
                        string,
                        launch_status.get(string, False),
                    )
                self.logger.error(
                    "BROWSER %i: Spawn unsuccessful %s"
                    % (self.browser_id, error_string)
                )
                self.close_browser_manager()
                if "Profile Created" in launch_status:
                    shutil.rmtree(browser_profile_path, ignore_errors=True)

        # If the browser spawned successfully, we should update the
        # current profile path class variable and clean up the tempdir
        # and previous profile path.
        if success:
            self.logger.debug("BROWSER %i: Browser spawn successful!" % self.browser_id)
            previous_profile_path = self.current_profile_path
            self.current_profile_path = browser_profile_path
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
        self.logger.info(
            "BROWSER %i: BrowserManager restart initiated. "
            "Clear profile? %s" % (self.browser_id, clear_profile)
        )
        if self.is_fresh:  # Return success if browser is fresh
            self.logger.info(
                "BROWSER %i: Skipping restart since the browser "
                "is a fresh instance already" % self.browser_id
            )
            return True

        self.close_browser_manager()

        # if crawl should be stateless we can clear profile
        if clear_profile and self.current_profile_path is not None:
            shutil.rmtree(self.current_profile_path, ignore_errors=True)
            self.current_profile_path = None
            self.browser_params.recovery_tar = None

        return self.launch_browser_manager()

    def close_browser_manager(self, force: bool = False):
        """Attempt to close the webdriver and browser manager processes
        from this thread.
        If the browser manager process is unresponsive, the process is killed.
        """
        self.logger.debug("BROWSER %i: Closing browser..." % self.browser_id)
        assert self.status_queue is not None

        if force:
            self.kill_browser_manager()
            return

        # Join current command thread (if it exists)
        in_command_thread = threading.current_thread() == self.command_thread
        if not in_command_thread and self.command_thread is not None:
            self.logger.debug("BROWSER %i: Joining command thread" % self.browser_id)
            start_time = time.time()
            if self.current_timeout is not None:
                self.command_thread.join(self.current_timeout + 10)
            else:
                self.command_thread.join(60)

            # If command thread is still alive, process is locked
            if self.command_thread.is_alive():
                self.logger.debug(
                    "BROWSER %i: command thread failed to join during close. "
                    "Assuming the browser process is locked..." % self.browser_id
                )
                self.kill_browser_manager()
                return

            self.logger.debug(
                "BROWSER %i: %f seconds to join command thread"
                % (self.browser_id, time.time() - start_time)
            )

        # If command queue doesn't exist, this likely means the browser
        # failed to launch properly. Let's kill any child processes that
        # we can find.
        if self.command_queue is None:
            self.logger.debug(
                "BROWSER %i: Command queue not found while closing." % self.browser_id
            )
            self.kill_browser_manager()
            return

        # Send the shutdown command
        command = ShutdownSignal()
        self.command_queue.put(command)

        # Verify that webdriver has closed (30 second timeout)
        try:
            status = self.status_queue.get(True, 30)
        except EmptyQueue:
            self.logger.debug(
                "BROWSER %i: Status queue timeout while closing browser."
                % self.browser_id
            )
            self.kill_browser_manager()
            return
        if status != "OK":
            self.logger.debug(
                "BROWSER %i: Command failure while closing browser." % self.browser_id
            )
            self.kill_browser_manager()
            return

        # Verify that the browser process has closed (30 second timeout)
        if self.browser_manager is not None:
            self.browser_manager.join(30)
            if self.browser_manager.is_alive():
                self.logger.debug(
                    "BROWSER %i: Browser manager process still alive 30 seconds "
                    "after executing shutdown command." % self.browser_id
                )
                self.kill_browser_manager()
                return

        self.logger.debug(
            "BROWSER %i: Browser manager closed successfully." % self.browser_id
        )

    def execute_command_sequence(
        self,
        # Quoting to break cyclic import, see https://stackoverflow.com/a/39757388
        task_manager: "TaskManager",
        command_sequence: CommandSequence,
    ) -> None:
        """
        Sends CommandSequence to the BrowserManager one command at a time
        """
        assert self.browser_id is not None
        assert self.curr_visit_id is not None
        task_manager.sock.store_record(
            TableName("site_visits"),
            self.curr_visit_id,
            {
                "visit_id": self.curr_visit_id,
                "browser_id": self.browser_id,
                "site_url": command_sequence.url,
                "site_rank": command_sequence.site_rank,
            },
        )
        self.is_fresh = False

        reset = command_sequence.reset
        self.logger.info(
            "Starting to work on CommandSequence with "
            "visit_id %d on browser with id %d",
            self.curr_visit_id,
            self.browser_id,
        )
        assert self.command_queue is not None
        assert self.status_queue is not None

        for command_and_timeout in command_sequence.get_commands_with_timeout():
            command, timeout = command_and_timeout
            command.set_visit_browser_id(self.curr_visit_id, self.browser_id)
            command.set_start_time(time.time())
            self.current_timeout = timeout

            # Adding timer to track performance of commands
            t1 = time.time_ns()

            # passes off command and waits for a success (or failure signal)
            self.command_queue.put(command)

            # received reply from BrowserManager, either success or failure
            error_text = None
            tb = None
            status = None
            try:
                status = self.status_queue.get(True, self.current_timeout)
            except EmptyQueue:
                self.logger.info(
                    "BROWSER %i: Timeout while executing command, %s, killing "
                    "browser manager" % (self.browser_id, repr(command))
                )

            if status is None:
                # allows us to skip this entire block without having to bloat
                # every if statement
                command_status = "timeout"
                pass
            elif status == "OK":
                command_status = "ok"
            elif status[0] == "CRITICAL":
                command_status = "critical"
                self.logger.critical(
                    "BROWSER %i: Received critical error from browser "
                    "process while executing command %s. Setting failure "
                    "status." % (self.browser_id, str(command))
                )
                task_manager.failure_status = {
                    "ErrorType": "CriticalChildException",
                    "CommandSequence": command_sequence,
                    "Exception": status[1],
                }
                error_text, tb = self._unpack_pickled_error(status[1])
            elif status[0] == "FAILED":
                command_status = "error"
                error_text, tb = self._unpack_pickled_error(status[1])
                self.logger.info(
                    "BROWSER %i: Received failure status while executing "
                    "command: %s" % (self.browser_id, repr(command))
                )
            elif status[0] == "NETERROR":
                command_status = "neterror"
                error_text, tb = self._unpack_pickled_error(status[1])
                error_text = parse_neterror(error_text)
                self.logger.info(
                    "BROWSER %i: Received neterror %s while executing "
                    "command: %s" % (self.browser_id, error_text, repr(command))
                )
            else:
                raise ValueError("Unknown browser status message %s" % status)

            task_manager.sock.store_record(
                TableName("crawl_history"),
                self.curr_visit_id,
                {
                    "browser_id": self.browser_id,
                    "visit_id": self.curr_visit_id,
                    "command": type(command).__name__,
                    "arguments": json.dumps(
                        command.__dict__, default=lambda x: repr(x)
                    ).encode("utf-8"),
                    "retry_number": command_sequence.retry_number,
                    "command_status": command_status,
                    "error": error_text,
                    "traceback": tb,
                    "duration": int((time.time_ns() - t1) / 1000000),
                },
            )

            if command_status == "critical":
                task_manager.sock.finalize_visit_id(
                    success=False,
                    visit_id=self.curr_visit_id,
                )
                return

            if command_status != "ok":
                with task_manager.threadlock:
                    task_manager.failure_count += 1
                if task_manager.failure_count > task_manager.failure_limit:
                    self.logger.critical(
                        "BROWSER %i: Command execution failure pushes failure "
                        "count above the allowable limit. Setting "
                        "failure_status." % self.browser_id
                    )
                    task_manager.failure_status = {
                        "ErrorType": "ExceedCommandFailureLimit",
                        "CommandSequence": command_sequence,
                    }
                    return
                self.restart_required = True
                self.logger.debug(
                    "BROWSER %i: Browser restart required" % self.browser_id
                )
            # Reset failure_count at the end of each successful command sequence
            elif type(command) is FinalizeCommand:
                with task_manager.threadlock:
                    task_manager.failure_count = 0

            if self.restart_required:
                task_manager.sock.finalize_visit_id(
                    success=False, visit_id=self.curr_visit_id
                )
                break

        self.logger.info(
            "Finished working on CommandSequence with "
            "visit_id %d on browser with id %d",
            self.curr_visit_id,
            self.browser_id,
        )
        # Sleep after executing CommandSequence to provide extra time for
        # internal buffers to drain. Stopgap in support of #135
        time.sleep(2)

        if task_manager.closing:
            return

        if self.restart_required or reset:
            success = self.restart_browser_manager(clear_profile=reset)
            if not success:
                self.logger.critical(
                    "BROWSER %i: Exceeded the maximum allowable consecutive "
                    "browser launch failures. Setting failure_status." % self.browser_id
                )
                task_manager.failure_status = {
                    "ErrorType": "ExceedLaunchFailureLimit",
                    "CommandSequence": command_sequence,
                }
                return
            self.restart_required = False

    def _unpack_pickled_error(self, pickled_error: bytes) -> Tuple[str, str]:
        """Unpacks `pickled_error` into an error `message` and `tb` string."""
        exc = pickle.loads(pickled_error)
        message = traceback.format_exception(*exc)[-1]
        tb = json.dumps(Traceback(exc[2]).to_dict())
        return message, tb

    def kill_browser_manager(self):
        """Kill the BrowserManager process and all of its children"""
        self.logger.debug(
            "BROWSER %i: Attempting to kill BrowserManager with pid %i. "
            "Browser PID: %s"
            % (self.browser_id, self.browser_manager.pid, self.geckodriver_pid)
        )
        if self.display_pid is not None:
            self.logger.debug(
                "BROWSER {browser_id}: Attempting to kill display "
                "with pid {display_pid}, port {display_port}".format(
                    browser_id=self.browser_id,
                    display_pid=self.display_pid,
                    display_port=self.display_port,
                )
            )

        if self.browser_manager is not None and self.browser_manager.pid is not None:
            try:
                os.kill(self.browser_manager.pid, signal.SIGKILL)
            except OSError:
                self.logger.debug(
                    "BROWSER %i: Browser manager process does "
                    "not exist" % self.browser_id
                )
                pass

        if self.display_pid is not None:
            try:
                os.kill(self.display_pid, signal.SIGKILL)
            except OSError:
                self.logger.debug(
                    "BROWSER %i: Display process does not exit" % self.browser_id
                )
                pass
            except TypeError:
                self.logger.error(
                    "BROWSER %i: PID may not be the correct "
                    "type %s" % (self.browser_id, str(self.display_pid))
                )
        if self.display_port is not None:  # xvfb display lock
            lockfile = "/tmp/.X%s-lock" % self.display_port
            try:
                os.remove(lockfile)
            except OSError:
                self.logger.debug(
                    "BROWSER %i: Screen lockfile (%s) already "
                    "removed" % (self.browser_id, lockfile)
                )
                pass

        if self.geckodriver_pid is not None:
            """`geckodriver_pid` is the geckodriver process. We first kill
            the child processes (i.e. firefox) and then kill the geckodriver
            process."""
            try:
                geckodriver_process = psutil.Process(pid=self.geckodriver_pid)
            except psutil.NoSuchProcess:
                self.logger.debug(
                    "BROWSER %i: geckodriver process with pid %i has already"
                    " exited" % (self.browser_id, self.geckodriver_pid)
                )
                return
            kill_process_and_children(geckodriver_process, self.logger)

    def shutdown_browser(self, during_init: bool, force: bool = False) -> None:
        """ Runs the closing tasks for this Browser/BrowserManager """
        # Close BrowserManager process and children
        self.logger.debug("BROWSER %i: Closing browser manager..." % self.browser_id)
        self.close_browser_manager(force=force)

        # Archive browser profile (if requested)
        self.logger.debug(
            "BROWSER %i: during_init=%s | profile_archive_dir=%s"
            % (
                self.browser_id,
                str(during_init),
                self.browser_params.profile_archive_dir,
            )
        )
        if not during_init and self.browser_params.profile_archive_dir is not None:
            self.logger.debug(
                "BROWSER %i: Archiving browser profile directory to %s"
                % (self.browser_id, self.browser_params.profile_archive_dir)
            )
            tar_path = self.browser_params.profile_archive_dir / "profile.tar.gz"
            assert self.current_profile_path is not None
            dump_profile(
                browser_profile_path=self.current_profile_path,
                tar_path=tar_path,
                compress=True,
                browser_params=self.browser_params,
            )

        # Clean up temporary files
        if self.current_profile_path is not None:
            shutil.rmtree(self.current_profile_path, ignore_errors=True)


def BrowserManager(
    command_queue, status_queue, browser_params, manager_params, crash_recovery
):
    """
    The BrowserManager function runs in each new browser process.
    It is responsible for listening to command instructions from
    the Task Manager and passing them to the command module to execute
    and interface with Selenium. Command execution status is sent back
    to the TaskManager.
    """
    logger = logging.getLogger("openwpm")
    display = None
    try:
        # Start Xvfb (if necessary), webdriver, and browser
        driver, browser_profile_path, display = deploy_firefox.deploy_firefox(
            status_queue, browser_params, manager_params, crash_recovery
        )

        # Read the extension port -- if extension is enabled
        # TODO: Initial communication from extension to TM should use sockets
        if browser_params.extension_enabled:
            logger.debug(
                "BROWSER %i: Looking for extension port information "
                "in %s" % (browser_params.browser_id, browser_profile_path)
            )
            elapsed = 0
            port = None
            ep_filename = browser_profile_path / "extension_port.txt"
            while elapsed < 5:
                try:
                    with open(ep_filename, "rt") as f:
                        port = int(f.read().strip())
                        break
                except IOError as e:
                    if e.errno != errno.ENOENT:
                        raise
                time.sleep(0.1)
                elapsed += 0.1
            if port is None:
                # try one last time, allowing all exceptions to propagate
                with open(ep_filename, "rt") as f:
                    port = int(f.read().strip())

            logger.debug(
                "BROWSER %i: Connecting to extension on port %i"
                % (browser_params.browser_id, port)
            )
            extension_socket = ClientSocket(serialization="json")
            extension_socket.connect("127.0.0.1", int(port))
        else:
            extension_socket = None

        logger.debug("BROWSER %i: BrowserManager ready." % browser_params.browser_id)

        # passes "READY" to the TaskManager to signal a successful startup
        status_queue.put(("STATUS", "Browser Ready", "READY"))
        browser_params.profile_path = browser_profile_path

        # starts accepting arguments until told to die
        while True:
            # no command for now -> sleep to avoid pegging CPU on blocking get
            if command_queue.empty():
                time.sleep(0.001)
                continue

            command: Union[ShutdownSignal, BaseCommand] = command_queue.get()

            if type(command) is ShutdownSignal:
                driver.quit()
                status_queue.put("OK")
                return

            logger.info(
                "BROWSER %i: EXECUTING COMMAND: %s"
                % (browser_params.browser_id, str(command))
            )

            # attempts to perform an action and return an OK signal
            # if command fails for whatever reason, tell the TaskManager to
            # kill and restart its worker processes
            try:
                command.execute(
                    driver,
                    browser_params,
                    manager_params,
                    extension_socket,
                )
                status_queue.put("OK")
            except WebDriverException:
                # We handle WebDriverExceptions separately here because they
                # are quite common, and we often still have a handle to the
                # browser, allowing us to run the SHUTDOWN command.
                tb = traceback.format_exception(*sys.exc_info())
                if "about:neterror" in tb[-1]:
                    status_queue.put(("NETERROR", pickle.dumps(sys.exc_info())))
                    continue
                extra = parse_traceback_for_sentry(tb)
                extra["exception"] = tb[-1]
                logger.error(
                    "BROWSER %i: WebDriverException while executing command"
                    % browser_params.browser_id,
                    exc_info=True,
                    extra=extra,
                )
                status_queue.put(("FAILED", pickle.dumps(sys.exc_info())))

    except (ProfileLoadError, BrowserConfigError, AssertionError) as e:
        logger.error(
            "BROWSER %i: %s thrown, informing parent and raising"
            % (browser_params.browser_id, e.__class__.__name__)
        )
        status_queue.put(("CRITICAL", pickle.dumps(sys.exc_info())))
    except Exception:
        tb = traceback.format_exception(*sys.exc_info())
        extra = parse_traceback_for_sentry(tb)
        extra["exception"] = tb[-1]
        logger.error(
            "BROWSER %i: Crash in driver, restarting browser manager"
            % browser_params.browser_id,
            exc_info=True,
            extra=extra,
        )
        status_queue.put(("FAILED", pickle.dumps(sys.exc_info())))
    finally:
        if display is not None:
            display.stop()
        return
