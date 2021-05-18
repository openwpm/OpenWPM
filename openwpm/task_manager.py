import logging
import os
import pickle
import threading
import time
from types import TracebackType
from typing import Any, Dict, List, Optional, Set, Type

import psutil
import tblib

from openwpm.config import (
    BrowserParams,
    BrowserParamsInternal,
    ManagerParams,
    ManagerParamsInternal,
    validate_crawl_configs,
)

from .browser_manager import BrowserManagerHandle
from .command_sequence import CommandSequence
from .errors import CommandExecutionError
from .js_instrumentation import clean_js_instrumentation_settings
from .mp_logger import MPLogger
from .storage.storage_controller import DataSocket, StorageControllerHandle
from .storage.storage_providers import (
    StructuredStorageProvider,
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

        self.num_browsers = manager_params.num_browsers

        # Parse and flesh out js_instrument_settings
        for a_browsers_params in self.browser_params:
            js_settings = a_browsers_params.js_instrument_settings
            cleaned_js_settings = clean_js_instrumentation_settings(js_settings)
            a_browsers_params.cleaned_js_instrument_settings = cleaned_js_settings

        # Flow control
        self.closing = False
        self.failure_status: Optional[Dict[str, Any]] = None
        self.threadlock = threading.Lock()
        self.failure_count = 0

        self.failure_limit = manager_params.failure_limit
        # Start logging server thread
        self.logging_server = MPLogger(
            self.manager_params.log_path,
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
    ) -> List[BrowserManagerHandle]:
        """initialize the browser classes, each with its unique set of params"""
        browsers = list()
        for i in range(self.num_browsers):
            browser_params[
                i
            ].browser_id = self.storage_controller_handle.get_next_browser_id()
            browsers.append(
                BrowserManagerHandle(self.manager_params, browser_params[i])
            )

        return browsers

    def _launch_browsers(self) -> None:
        """launch each browser manager process / browser"""
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
            flag to indicate if this shutdown is occuring during
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
        self, browser: BrowserManagerHandle, command_sequence: CommandSequence
    ) -> threading.Thread:
        """starts the command execution thread"""

        # Check status flags before starting thread
        if self.closing:
            self.logger.error("Attempted to execute command on a closed TaskManager")
            raise RuntimeError("Attempted to execute command on a closed TaskManager")
        self._check_failure_status()
        visit_id = self.storage_controller_handle.get_next_visit_id()
        browser.set_visit_id(visit_id)
        if command_sequence.callback:
            self.unsaved_command_sequences[visit_id] = command_sequence

        # Start command execution thread
        args = (self, command_sequence)
        thread = threading.Thread(target=browser.execute_command_sequence, args=args)
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
        """goes to a url"""
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
        """browse a website and visit <num_links> links on the page"""
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
