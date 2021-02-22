import json
import logging
import os
import pickle
import sys
import threading
import time
import traceback
from queue import Empty as EmptyQueue
from types import TracebackType
from typing import Any, Dict, List, Optional, Set, Tuple, Type

import psutil
import tblib

from openwpm.config import (
    BrowserParams,
    BrowserParamsInternal,
    ManagerParams,
    ManagerParamsInternal,
    validate_browser_params,
    validate_crawl_configs,
    validate_manager_params,
)

from .browser_manager import Browser
from .command_sequence import CommandSequence
from .commands.browser_commands import FinalizeCommand
from .commands.utils.webdriver_utils import parse_neterror
from .errors import CommandExecutionError
from .js_instrumentation import clean_js_instrumentation_settings
from .mp_logger import MPLogger
from .storage.storage_controller import DataSocket, StorageControllerHandle
from .storage.storage_providers import (
    StructuredStorageProvider,
    TableName,
    UnstructuredStorageProvider,
)
from .utilities.multiprocess_utils import kill_process_and_children
from .utilities.platform_utils import get_configuration_string, get_version

tblib.pickling_support.install()

SLEEP_CONS = 0.1  # command sleep constant (in seconds)
BROWSER_MEMORY_LIMIT = 1500  # in MB

STORAGE_CONTROLLER_JOB_LIMIT = 10000  # number of records in the queue


class TaskManager:
    """User-facing Class for interfacing with OpenWPM

    The TaskManager spawns several child processes to run the automation tasks.
        - StorageController to receive data from across browsers and save it to
          the provided StorageProviders
        - MPLogger to aggregate logs across processes
        - BrowserManager processes to isolate Browsers in a separate process
    """

    def __init__(
        self,
        manager_params_temp: ManagerParams,
        browser_params_temp: List[BrowserParams],
        structured_storage_provider: StructuredStorageProvider,
        unstructured_storage_provider: Optional[UnstructuredStorageProvider],
        logger_kwargs: Dict[Any, Any] = {},
    ) -> None:
        """Initialize the TaskManager with browser and manager config params

        Parameters
        ----------
        manager_params_temp : ManagerParams
            TaskManager configuration parameters
        browser_params_temp : list of BrowserParams
            Browser configuration parameters. It is a list which
            includes individual configurations for each browser.
        logger_kwargs : dict, optional
            Keyword arguments to pass to MPLogger on initialization.
        """

        validate_crawl_configs(manager_params_temp, browser_params_temp)
        manager_params = ManagerParamsInternal.from_dict(manager_params_temp.to_dict())
        browser_params = [
            BrowserParamsInternal.from_dict(bp.to_dict()) for bp in browser_params_temp
        ]

        # Make paths absolute in manager_params
        if manager_params.data_directory:
            manager_params.data_directory = manager_params.data_directory.expanduser()

        if manager_params.log_directory:
            manager_params.log_directory = manager_params.log_directory.expanduser()

        manager_params.log_file = (
            manager_params.log_directory / manager_params.log_file.name
        )
        manager_params.screenshot_path = manager_params.data_directory / "screenshots"

        manager_params.source_dump_path = manager_params.data_directory / "sources"

        self.manager_params = manager_params
        self.browser_params = browser_params
        self._logger_kwargs = logger_kwargs

        # Create data directories if they do not exist
        if not os.path.exists(manager_params.screenshot_path):
            os.makedirs(manager_params.screenshot_path)
        if not os.path.exists(manager_params.source_dump_path):
            os.makedirs(manager_params.source_dump_path)

        # Check size of parameter dictionary
        self.num_browsers = manager_params.num_browsers

        # Parse and flesh out js_instrument_settings
        for a_browsers_params in self.browser_params:
            js_settings = a_browsers_params.js_instrument_settings
            cleaned_js_settings = clean_js_instrumentation_settings(js_settings)
            a_browsers_params.js_instrument_settings = cleaned_js_settings

        # Flow control
        self.closing = False
        self.failure_status: Optional[Dict[str, Any]] = None
        self.threadlock = threading.Lock()
        self.failure_count = 0

        self.failure_limit = manager_params.failure_limit
        # Start logging server thread
        self.logging_server = MPLogger(
            self.manager_params.log_file,
            str(structured_storage_provider),
            **self._logger_kwargs
        )
        self.manager_params.logger_address = self.logging_server.logger_address
        self.logger = logging.getLogger("openwpm")

        # Initialize the storage controller
        self._launch_storage_controller(
            structured_storage_provider, unstructured_storage_provider
        )

        # Sets up the BrowserManager(s) + associated queues
        self.browsers = self._initialize_browsers(browser_params)
        self._launch_browsers()

        # Start the manager watchdog
        thread = threading.Thread(target=self._manager_watchdog, args=())
        thread.daemon = True
        thread.name = "OpenWPM-watchdog"
        thread.start()

        # Save crawl config information to database
        openwpm_v, browser_v = get_version()
        self.storage_controller_handle.save_configuration(
            manager_params, browser_params, openwpm_v, browser_v
        )
        self.logger.info(
            get_configuration_string(
                self.manager_params, browser_params, (openwpm_v, browser_v)
            )
        )
        self.unsaved_command_sequences: Dict[int, CommandSequence] = dict()
        self.callback_thread = threading.Thread(
            target=self._mark_command_sequences_complete, args=()
        )
        self.callback_thread.name = "OpenWPM-completion_handler"
        self.callback_thread.start()

    def __enter__(self):
        """
        Execute starting procedure for TaskManager
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        Execute shutdown procedure for TaskManager
        """
        self.close()

    def _initialize_browsers(
        self, browser_params: List[BrowserParamsInternal]
    ) -> List[Browser]:
        """ initialize the browser classes, each its unique set of params """
        browsers = list()
        for i in range(self.num_browsers):
            browser_params[
                i
            ].browser_id = self.storage_controller_handle.get_next_browser_id()
            browsers.append(Browser(self.manager_params, browser_params[i]))

        return browsers

    def _launch_browsers(self) -> None:
        """ launch each browser manager process / browser """
        for browser in self.browsers:
            try:
                success = browser.launch_browser_manager()
            except Exception:
                self._shutdown_manager(during_init=True)
                raise

            if not success:
                self.logger.critical(
                    "Browser spawn failure during "
                    "TaskManager initialization, exiting..."
                )
                self.close()
                break

    def _manager_watchdog(self) -> None:
        """
        Periodically checks the following:
        - memory consumption of all browsers every 10 seconds
        - presence of processes that are no longer in use
        """
        while not self.closing:
            time.sleep(10)

            # Check browser memory usage
            if self.manager_params.memory_watchdog:
                for browser in self.browsers:
                    try:
                        # Sum the memory used by the geckodriver process, the
                        # main Firefox process and all its child processes.
                        # Use the USS metric for child processes, to avoid
                        # double-counting memory shared with their parent.
                        geckodriver = psutil.Process(browser.geckodriver_pid)
                        mem_bytes = geckodriver.memory_info().rss
                        children = geckodriver.children()
                        if children:
                            firefox = children[0]
                            mem_bytes += firefox.memory_info().rss
                            for child in firefox.children():
                                mem_bytes += child.memory_full_info().uss
                        mem = mem_bytes / 2 ** 20
                        if mem > BROWSER_MEMORY_LIMIT:
                            self.logger.info(
                                "BROWSER %i: Memory usage: %iMB"
                                ", exceeding limit of %iMB"
                                % (browser.browser_id, int(mem), BROWSER_MEMORY_LIMIT)
                            )
                            browser.restart_required = True
                    except psutil.NoSuchProcess:
                        pass

            # Check for browsers or displays that were not closed correctly
            # 300 second buffer to avoid killing freshly launched browsers
            # TODO This buffer should correspond to the maximum spawn timeout
            if self.manager_params.process_watchdog:
                geckodriver_pids: Set[int] = set()
                display_pids: Set[int] = set()
                check_time = time.time()
                for browser in self.browsers:
                    if browser.geckodriver_pid is not None:
                        geckodriver_pids.add(browser.geckodriver_pid)
                    if browser.display_pid is not None:
                        display_pids.add(browser.display_pid)
                for process in psutil.process_iter():
                    if process.create_time() + 300 < check_time and (
                        (
                            process.name() == "geckodriver"
                            and (process.pid not in geckodriver_pids)
                        )
                        or (
                            process.name() == "Xvfb"
                            and (process.pid not in display_pids)
                        )
                    ):
                        self.logger.debug(
                            "Process %s (pid: %i) with start "
                            "time %s isn't controlled by any BrowserManager."
                            "Killing it now."
                            % (process.name(), process.pid, process.create_time())
                        )
                        kill_process_and_children(process, self.logger)

    def _launch_storage_controller(
        self,
        structured_storage_provider: StructuredStorageProvider,
        unstructured_storage_provider: Optional[UnstructuredStorageProvider],
    ) -> None:
        self.storage_controller_handle = StorageControllerHandle(
            structured_storage_provider, unstructured_storage_provider
        )
        self.storage_controller_handle.launch()
        self.manager_params.storage_controller_address = (
            self.storage_controller_handle.listener_address
        )
        assert self.manager_params.storage_controller_address is not None
        # open connection to storage controller for saving crawl details
        self.sock = DataSocket(self.manager_params.storage_controller_address)

    def _shutdown_manager(
        self, during_init: bool = False, relaxed: bool = True
    ) -> None:
        """
        Wait for current commands to finish, close all child processes and
        threads

        Parameters
        ----------
        during_init :
            flag to indicator if this shutdown is occuring during
          the TaskManager initialization
        relaxed :
            If `True` the function will wait for all active
            `CommandSequences` to finish before shutting down
        """
        if self.closing:
            return
        self.closing = True

        for browser in self.browsers:
            if (
                relaxed is True
                and browser.command_thread
                and browser.command_thread.is_alive()
            ):
                # Waiting for the command_sequence to be finished
                browser.command_thread.join()
            browser.shutdown_browser(during_init, force=not relaxed)

        self.sock.close()  # close socket to storage controller
        self.storage_controller_handle.shutdown(relaxed=relaxed)
        self.logging_server.close()
        if hasattr(self, "callback_thread"):
            self.callback_thread.join()

    def _check_failure_status(self) -> None:
        """Check the status of command failures. Raise exceptions as necessary

        The failure status property is used by the various asynchronous
        command execution threads which interface with the
        remote browser manager processes. If a failure status is found, the
        appropriate steps are taken to gracefully close the infrastructure
        """
        self.logger.debug("Checking command failure status indicator...")
        if not self.failure_status:
            return

        self.logger.debug("TaskManager failure status set, halting command execution.")
        self._shutdown_manager()
        if self.failure_status["ErrorType"] == "ExceedCommandFailureLimit":
            raise CommandExecutionError(
                "TaskManager exceeded maximum consecutive command "
                "execution failures.",
                self.failure_status["CommandSequence"],
            )
        elif self.failure_status["ErrorType"] == "ExceedLaunchFailureLimit":
            raise CommandExecutionError(
                "TaskManager failed to launch browser within allowable "
                "failure limit.",
                self.failure_status["CommandSequence"],
            )
        if self.failure_status["ErrorType"] == "CriticalChildException":
            _, exc, tb = pickle.loads(self.failure_status["Exception"])
            raise exc.with_traceback(tb)

    # CRAWLER COMMAND CODE

    def _start_thread(
        self, browser: Browser, command_sequence: CommandSequence
    ) -> threading.Thread:
        """  starts the command execution thread """

        # Check status flags before starting thread
        if self.closing:
            self.logger.error("Attempted to execute command on a closed TaskManager")
            raise RuntimeError("Attempted to execute command on a closed TaskManager")
        self._check_failure_status()
        visit_id = self.storage_controller_handle.get_next_visit_id()
        browser.set_visit_id(visit_id)
        if command_sequence.callback:
            self.unsaved_command_sequences[visit_id] = command_sequence

        self.sock.store_record(
            TableName("site_visits"),
            visit_id,
            {
                "visit_id": visit_id,
                "browser_id": browser.browser_id,
                "site_url": command_sequence.url,
                "site_rank": command_sequence.site_rank,
            },
        )

        # Start command execution thread
        args = (browser, command_sequence)
        thread = threading.Thread(target=self._issue_command, args=args)
        browser.command_thread = thread
        thread.daemon = True
        thread.start()
        return thread

    def _mark_command_sequences_complete(self) -> None:
        """Polls the storage controller for saved records
        and calls their callbacks
        """
        while True:
            if self.closing and not self.unsaved_command_sequences:
                # we're shutting down and have no unprocessed callbacks
                break

            visit_id_list = self.storage_controller_handle.get_new_completed_visits()
            if not visit_id_list:
                time.sleep(1)
                continue

            for visit_id, successful in visit_id_list:
                self.logger.debug("Invoking callback of visit_id %d", visit_id)
                cs = self.unsaved_command_sequences.pop(visit_id, None)
                if cs:
                    cs.mark_done(successful)

    def _unpack_pickled_error(self, pickled_error: bytes) -> Tuple[str, str]:
        """Unpacks `pickled_error` into an error `message` and `tb` string."""
        exc = pickle.loads(pickled_error)
        message = traceback.format_exception(*exc)[-1]
        tb = json.dumps(tblib.Traceback(exc[2]).to_dict())
        return message, tb

    def _issue_command(
        self, browser: Browser, command_sequence: CommandSequence
    ) -> None:
        """
        Sends CommandSequence to the BrowserManager one command at a time
        """
        browser.is_fresh = False
        assert browser.browser_id is not None
        assert browser.curr_visit_id is not None
        reset = command_sequence.reset
        if not reset:
            self.logger.warning(
                "BROWSER %i: Browser will not reset after CommandSequence "
                "executes. OpenWPM does not currently support stateful crawls "
                "(see: https://github.com/mozilla/OpenWPM/projects/2). "
                "The next command issued to this browser may or may not "
                "use the same profile (depending on the failure status of "
                "this command). To prevent this warning, initialize the "
                "CommandSequence with `reset` set to `True` to use a fresh "
                "profile for each command." % browser.browser_id
            )
        self.logger.info(
            "Starting to work on CommandSequence with "
            "visit_id %d on browser with id %d",
            browser.curr_visit_id,
            browser.browser_id,
        )
        assert browser.command_queue is not None
        assert browser.status_queue is not None

        for command_and_timeout in command_sequence.get_commands_with_timeout():
            command, timeout = command_and_timeout
            command.set_visit_browser_id(browser.curr_visit_id, browser.browser_id)
            command.set_start_time(time.time())
            browser.current_timeout = timeout

            # Adding timer to track performance of commands
            t1 = time.time_ns()

            # passes off command and waits for a success (or failure signal)
            browser.command_queue.put(command)

            # received reply from BrowserManager, either success or failure
            error_text = None
            tb = None
            status = None
            try:
                status = browser.status_queue.get(True, browser.current_timeout)
            except EmptyQueue:
                self.logger.info(
                    "BROWSER %i: Timeout while executing command, %s, killing "
                    "browser manager" % (browser.browser_id, repr(command))
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
                    "status." % (browser.browser_id, str(command))
                )
                self.failure_status = {
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
                    "command: %s" % (browser.browser_id, repr(command))
                )
            elif status[0] == "NETERROR":
                command_status = "neterror"
                error_text, tb = self._unpack_pickled_error(status[1])
                error_text = parse_neterror(error_text)
                self.logger.info(
                    "BROWSER %i: Received neterror %s while executing "
                    "command: %s" % (browser.browser_id, error_text, repr(command))
                )
            else:
                raise ValueError("Unknown browser status message %s" % status)

            self.sock.store_record(
                TableName("crawl_history"),
                browser.curr_visit_id,
                {
                    "browser_id": browser.browser_id,
                    "visit_id": browser.curr_visit_id,
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
                self.sock.finalize_visit_id(
                    success=False,
                    visit_id=browser.curr_visit_id,
                )
                return

            if command_status != "ok":
                with self.threadlock:
                    self.failure_count += 1
                if self.failure_count > self.failure_limit:
                    self.logger.critical(
                        "BROWSER %i: Command execution failure pushes failure "
                        "count above the allowable limit. Setting "
                        "failure_status." % browser.browser_id
                    )
                    self.failure_status = {
                        "ErrorType": "ExceedCommandFailureLimit",
                        "CommandSequence": command_sequence,
                    }
                    return
                browser.restart_required = True
                self.logger.debug(
                    "BROWSER %i: Browser restart required" % (browser.browser_id)
                )
            # Reset failure_count at the end of each successful command sequence
            elif type(command) is FinalizeCommand:
                with self.threadlock:
                    self.failure_count = 0

            if browser.restart_required:
                self.sock.finalize_visit_id(
                    success=False, visit_id=browser.curr_visit_id
                )
                break

        self.logger.info(
            "Finished working on CommandSequence with "
            "visit_id %d on browser with id %d",
            browser.curr_visit_id,
            browser.browser_id,
        )
        # Sleep after executing CommandSequence to provide extra time for
        # internal buffers to drain. Stopgap in support of #135
        time.sleep(2)

        if self.closing:
            return

        if browser.restart_required or reset:
            success = browser.restart_browser_manager(clear_profile=reset)
            if not success:
                self.logger.critical(
                    "BROWSER %i: Exceeded the maximum allowable consecutive "
                    "browser launch failures. Setting failure_status."
                    % (browser.browser_id)
                )
                self.failure_status = {
                    "ErrorType": "ExceedLaunchFailureLimit",
                    "CommandSequence": command_sequence,
                }
                return
            browser.restart_required = False

    def execute_command_sequence(
        self, command_sequence: CommandSequence, index: Optional[int] = None
    ) -> None:
        """
        parses command type and issues command(s) to the proper browser
        <index> specifies the type of command this is:
        None  -> first come, first serve
        int  -> index of browser to send command to
        """

        # Block if the storage controller has too many unfinished records
        agg_queue_size = self.storage_controller_handle.get_most_recent_status()
        if agg_queue_size >= STORAGE_CONTROLLER_JOB_LIMIT:
            while agg_queue_size >= STORAGE_CONTROLLER_JOB_LIMIT:
                self.logger.info(
                    "Blocking command submission until the storage controller "
                    "is below the max queue size of %d. Current queue "
                    "length %d. " % (STORAGE_CONTROLLER_JOB_LIMIT, agg_queue_size)
                )
                agg_queue_size = self.storage_controller_handle.get_status()

        # Distribute command
        if index is None:
            # send to first browser available
            command_executed = False
            while True:
                for browser in self.browsers:
                    if browser.ready():
                        browser.current_timeout = command_sequence.total_timeout
                        thread = self._start_thread(browser, command_sequence)
                        command_executed = True
                        break
                if command_executed:
                    break
                time.sleep(SLEEP_CONS)
        elif 0 <= index < len(self.browsers):
            # send the command to this specific browser
            while True:
                if self.browsers[index].ready():
                    self.browsers[
                        index
                    ].current_timeout = command_sequence.total_timeout
                    thread = self._start_thread(self.browsers[index], command_sequence)
                    break
                time.sleep(SLEEP_CONS)
        else:
            self.logger.info("Command index type is not supported or out of range")
            return

        if command_sequence.blocking:
            thread.join()
            self._check_failure_status()

    # DEFINITIONS OF HIGH LEVEL COMMANDS
    # NOTE: These wrappers are provided for convenience. To issue sequential
    # commands to the same browser in a single 'visit', use the CommandSequence
    # class directly.

    def get(
        self,
        url: str,
        index: Optional[int] = None,
        timeout: int = 60,
        sleep: int = 0,
        reset: bool = False,
    ) -> None:
        """ goes to a url """
        command_sequence = CommandSequence(url)
        command_sequence.get(timeout=timeout, sleep=sleep)
        command_sequence.reset = reset
        self.execute_command_sequence(command_sequence, index=index)

    def browse(
        self,
        url: str,
        num_links: int = 2,
        sleep: int = 0,
        index: Optional[int] = None,
        timeout: int = 60,
        reset: bool = False,
    ) -> None:
        """ browse a website and visit <num_links> links on the page """
        command_sequence = CommandSequence(url)
        command_sequence.browse(num_links=num_links, sleep=sleep, timeout=timeout)
        command_sequence.reset = reset
        self.execute_command_sequence(command_sequence, index=index)

    def close(self, relaxed: bool = True) -> None:
        """
        Execute shutdown procedure for TaskManager
        """
        if self.closing:
            self.logger.error("TaskManager already closed")
            return
        start_time = time.time()
        self._shutdown_manager(relaxed=relaxed)
        # We don't have a logging thread at this time anymore
        print("Shutdown took %s seconds" % str(time.time() - start_time))
