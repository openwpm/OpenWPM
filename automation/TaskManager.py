import copy
import json
import logging
import os
import pickle
import threading
import time
import traceback
from queue import Empty as EmptyQueue
from typing import Any, Dict, List, Optional, Tuple

import psutil
import tblib

from .BrowserManager import Browser
from .Commands.utils.webdriver_utils import parse_neterror
from .CommandSequence import CommandSequence
from .DataAggregator import BaseAggregator, LocalAggregator, S3Aggregator
from .Errors import CommandExecutionError
from .MPLogger import MPLogger
from .SocketInterface import clientsocket
from .utilities.platform_utils import get_configuration_string, get_version

tblib.pickling_support.install()

SLEEP_CONS = 0.1  # command sleep constant (in seconds)
BROWSER_MEMORY_LIMIT = 1500  # in MB

AGGREGATOR_QUEUE_LIMIT = 10000  # number of records in the queue


def load_default_params(num_browsers: int = 1) \
        -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Loads num_browsers copies of the default browser_params dictionary.
    Also loads a single copy of the default TaskManager params dictionary.
    """
    fp = open(os.path.join(os.path.dirname(__file__),
                           'default_browser_params.json'))
    preferences = json.load(fp)
    fp.close()
    browser_params = [copy.deepcopy(preferences) for i in range(
        0, num_browsers)]

    fp = open(os.path.join(os.path.dirname(__file__),
                           'default_manager_params.json'))
    manager_params = json.load(fp)
    fp.close()
    manager_params['num_browsers'] = num_browsers

    return manager_params, browser_params


class TaskManager:
    """ User-facing Class for interfacing with OpenWPM

    The TaskManager spawns several child processes to run the automation tasks.
        - DataAggregator to aggregate data across browsers and save to the
          database.
        - MPLogger to aggregate logs across processes
        - BrowserManager processes to isolate Browsers in a separate process
    """

    def __init__(self, manager_params: Dict[str, Any],
                 browser_params: List[Dict[str, Any]],
                 process_watchdog: bool = False,
                 logger_kwargs: Dict[Any, Any] = {}) -> None:
        """Initialize the TaskManager with browser and manager config params

        Parameters
        ----------
        manager_params : dict
            Dictionary of TaskManager configuration parameters. See the
            default in `default_manager_params.json`.
        browser_params : list of dict
            Browser configuration parameters. If this is given as a list, it
            includes individual configurations for each browser.
        process_watchdog : bool, optional
            Set to True to monitor Firefox processes for zombie instances or
            instances that exceed a reasonable amount of memory. Any process
            found and not indexed by the TaskManager will be killed.
            (Currently broken: https://github.com/mozilla/OpenWPM/issues/174)
        logger_kwargs : dict, optional
            Keyword arguments to pass to MPLogger on initialization.
        """

        # Make paths absolute in manager_params
        for path in ['data_directory', 'log_directory']:
            if manager_params[path] is not None:
                manager_params[path] = os.path.expanduser(manager_params[path])
        manager_params['database_name'] = os.path.join(
            manager_params['data_directory'], manager_params['database_name'])
        manager_params['log_file'] = os.path.join(
            manager_params['log_directory'], manager_params['log_file'])
        manager_params['screenshot_path'] = os.path.join(
            manager_params['data_directory'], 'screenshots')
        manager_params['source_dump_path'] = os.path.join(
            manager_params['data_directory'], 'sources')
        self.manager_params = manager_params
        self.browser_params = browser_params
        self._logger_kwargs = logger_kwargs

        # Create data directories if they do not exist
        if not os.path.exists(manager_params['screenshot_path']):
            os.makedirs(manager_params['screenshot_path'])
        if not os.path.exists(manager_params['source_dump_path']):
            os.makedirs(manager_params['source_dump_path'])

        # check size of parameter dictionary
        self.num_browsers = manager_params['num_browsers']
        if len(browser_params) != self.num_browsers:
            raise Exception("Number of <browser_params> dicts is not the same "
                            "as manager_params['num_browsers']")

        # Flow control
        self.closing = False
        self.failure_status = None
        self.threadlock = threading.Lock()
        self.failurecount = 0
        if manager_params['failure_limit'] is not None:
            self.failure_limit = manager_params['failure_limit']
        else:
            self.failure_limit = self.num_browsers * 2 + 10

        if process_watchdog:
            raise ValueError(
                "The Process watchdog functionality is currently broken. "
                "See: https://github.com/mozilla/OpenWPM/issues/174.")

        self.process_watchdog = process_watchdog

        # Start logging server thread
        self.logging_server = MPLogger(
            self.manager_params['log_file'],
            self.manager_params,
            **self._logger_kwargs
        )
        self.manager_params[
            'logger_address'] = self.logging_server.logger_address
        self.logger = logging.getLogger('openwpm')

        # Initialize the data aggregators
        self._launch_aggregators()

        # sets up the BrowserManager(s) + associated queues
        self.browsers = self._initialize_browsers(browser_params)
        self._launch_browsers()

        # start the manager watchdog
        thread = threading.Thread(target=self._manager_watchdog, args=())
        thread.daemon = True
        thread.name = "OpenWPM-watchdog"
        thread.start()

        # Save crawl config information to database
        openwpm_v, browser_v = get_version()
        self.data_aggregator.save_configuration(openwpm_v, browser_v)
        self.logger.info(
            get_configuration_string(
                self.manager_params, browser_params, (openwpm_v, browser_v)
            )
        )

    def _initialize_browsers(self, browser_params: List[Dict[str, Any]]) \
            -> List[Browser]:
        """ initialize the browser classes, each its unique set of params """
        browsers = list()
        for i in range(self.num_browsers):
            browser_params[i][
                'crawl_id'] = self.data_aggregator.get_next_crawl_id()
            browsers.append(Browser(self.manager_params, browser_params[i]))

        return browsers

    def _launch_browsers(self) -> None:
        """ launch each browser manager process / browser """
        for browser in self.browsers:
            try:
                success = browser.launch_browser_manager()
            except Exception:
                self._cleanup_before_fail(during_init=True)
                raise

            if not success:
                self.logger.critical("Browser spawn failure during "
                                     "TaskManager initialization, exiting...")
                self.close()
                break

    def _manager_watchdog(self) -> None:
        """
        Periodically checks the following:
        - memory consumption of all browsers every 10 seconds
        - presence of processes that are no longer in use

        TODO: process watchdog needs to be updated since `psutil` won't
              kill browser processes started by Selenium 3 (with `subprocess`)
        """
        while not self.closing:
            time.sleep(10)

            # Check browser memory usage
            for browser in self.browsers:
                try:
                    process = psutil.Process(browser.browser_pid)
                    mem = process.memory_info()[0] / float(2 ** 20)
                    if mem > BROWSER_MEMORY_LIMIT:
                        self.logger.info("BROWSER %i: Memory usage: %iMB"
                                         ", exceeding limit of %iMB" %
                                         (browser.crawl_id, int(mem),
                                          BROWSER_MEMORY_LIMIT))
                        browser.restart_required = True
                except psutil.NoSuchProcess:
                    pass

            # Check for browsers that were not closed correctly
            # 300 second buffer to avoid killing freshly launched browsers
            # TODO This buffer should correspond to the maximum spawn timeout
            if self.process_watchdog:
                browser_pids = set()
                check_time = time.time()
                for browser in self.browsers:
                    if browser.browser_pid is not None:
                        browser_pids.add(browser.browser_pid)
                for process in psutil.process_iter():
                    if process.create_time() + 300 < check_time and (
                            (process.name() == 'firefox' and (
                                process.pid not in browser_pids))):
                        self.logger.debug("Process: %s (pid: %i) with start "
                                          "time %s found running but not in "
                                          "browser process list. Killing." % (
                                              process.name(), process.pid,
                                              process.create_time()))
                        process.kill()

    def _launch_aggregators(self) -> None:
        """Launch the necessary data aggregators"""
        self.data_aggregator: BaseAggregator.BaseAggregator
        if self.manager_params["output_format"] == "local":
            self.data_aggregator = LocalAggregator.LocalAggregator(
                self.manager_params, self.browser_params)
        elif self.manager_params["output_format"] == "s3":
            self.data_aggregator = S3Aggregator.S3Aggregator(
                self.manager_params, self.browser_params)
        else:
            raise Exception("Unrecognized output format: %s" %
                            self.manager_params["output_format"])
        self.data_aggregator.launch()
        self.manager_params[
            'aggregator_address'] = self.data_aggregator.listener_address

        # open connection to aggregator for saving crawl details
        self.sock = clientsocket(serialization='dill')
        self.sock.connect(*self.manager_params['aggregator_address'])

    def _shutdown_manager(self, during_init: bool = False) -> None:
        """
        Wait for current commands to finish, close all child processes and
        threads
        <during_init> flag to indicator if this shutdown is occuring during
                      the TaskManager initialization
        """
        self.closing = True

        for browser in self.browsers:
            browser.shutdown_browser(during_init)

        self.sock.close()  # close socket to data aggregator
        self.data_aggregator.shutdown()
        self.logging_server.close()

    def _cleanup_before_fail(self, during_init: bool = False) -> None:
        """
        Execute shutdown commands before throwing an exception
        This should keep us from having a bunch of hanging processes
        and incomplete data.
        <during_init> flag to indicator if this shutdown is occuring during
                      the TaskManager initialization
        """
        self._shutdown_manager(during_init=during_init)

    def _check_failure_status(self) -> None:
        """ Check the status of command failures. Raise exceptions as necessary

        The failure status property is used by the various asynchronous
        command execution threads which interface with the
        remote browser manager processes. If a failure status is found, the
        appropriate steps are taken to gracefully close the infrastructure
        """
        self.logger.debug("Checking command failure status indicator...")
        if self.failure_status:
            self.logger.debug(
                "TaskManager failure status set, halting command execution.")
            self._cleanup_before_fail()
            if self.failure_status['ErrorType'] == 'ExceedCommandFailureLimit':
                raise CommandExecutionError(
                    "TaskManager exceeded maximum consecutive command "
                    "execution failures.",
                    self.failure_status['CommandSequence']
                )
            elif (self.failure_status['ErrorType'] == ("ExceedLaunch"
                                                       "FailureLimit")):
                raise CommandExecutionError(
                    "TaskManager failed to launch browser within allowable "
                    "failure limit.", self.failure_status['CommandSequence']
                )
            if self.failure_status['ErrorType'] == 'CriticalChildException':
                raise pickle.loads(self.failure_status['Exception'])

    # CRAWLER COMMAND CODE

    def _start_thread(self, browser: Browser,
                      command_sequence: CommandSequence) -> threading.Thread:
        """  starts the command execution thread """

        # Check status flags before starting thread
        if self.closing:
            self.logger.error(
                "Attempted to execute command on a closed TaskManager")
            return
        self._check_failure_status()
        visit_id = self.data_aggregator.get_next_visit_id()
        browser.set_visit_id(visit_id)

        self.sock.send(("site_visits", {
            "visit_id": visit_id,
            "crawl_id": browser.crawl_id,
            "site_url": command_sequence.url,
            "site_rank": command_sequence.site_rank
        }))

        # Start command execution thread
        args = (browser, command_sequence)
        thread = threading.Thread(target=self._issue_command, args=args)
        browser.command_thread = thread
        thread.daemon = True
        thread.start()
        return thread

    def _unpack_picked_error(self, pickled_error: bytes) -> Tuple[str, str]:
        """Unpacks `pickled_error` into and error `message` and `tb` string."""
        exc = pickle.loads(pickled_error)
        message = traceback.format_exception(*exc)[-1]
        tb = json.dumps(tblib.Traceback(exc[2]).to_dict())
        return message, tb

    def _issue_command(self, browser: Browser,
                       command_sequence: CommandSequence) -> None:
        """
        sends command tuple to the BrowserManager
        """
        browser.is_fresh = False

        reset = command_sequence.reset
        if not reset:
            self.logger.warn(
                "BROWSER %i: Browser will not reset after CommandSequence "
                "executes. OpenWPM does not currently support stateful crawls "
                "(see: https://github.com/mozilla/OpenWPM/projects/2). "
                "The next command issued to this browser may or may not "
                "use the same profile (depending on the failure status of "
                "this command). To prevent this warning, initialize the "
                "CommandSequence with `reset` set to `True` to use a fresh "
                "profile for each command." % browser.crawl_id
            )
        start_time = None
        for command_and_timeout in command_sequence.commands_with_timeout:
            command, timeout = command_and_timeout
            if command[0] in ['GET', 'BROWSE',
                              'SAVE_SCREENSHOT',
                              'SCREENSHOT_FULL_PAGE',
                              'DUMP_PAGE_SOURCE',
                              'RECURSIVE_DUMP_PAGE_SOURCE']:
                start_time = time.time()
                command += (browser.curr_visit_id,)
            elif command[0] in ['DUMP_FLASH_COOKIES', 'DUMP_PROFILE_COOKIES']:
                command += (start_time, browser.curr_visit_id,)
            browser.current_timeout = timeout
            # passes off command and waits for a success (or failure signal)
            browser.command_queue.put(command)
            command_arguments = command[1] if len(command) > 1 else None

            # received reply from BrowserManager, either success or failure
            critical_failure = False
            error_text = None
            tb = None
            try:
                status = browser.status_queue.get(
                    True, browser.current_timeout)
                if status == "OK":
                    command_status = 'ok'
                elif status[0] == "CRITICAL":
                    command_status = 'critical'
                    self.logger.critical(
                        "BROWSER %i: Received critical error from browser "
                        "process while executing command %s. Setting failure "
                        "status." % (browser.crawl_id, str(command)))
                    self.failure_status = {
                        'ErrorType': 'CriticalChildException',
                        'CommandSequence': command_sequence,
                        'Exception': status[1]
                    }
                    error_text, tb = self._unpack_picked_error(status[1])
                    critical_failure = True
                elif status[0] == "FAILED":
                    command_status = 'error'
                    error_text, tb = self._unpack_picked_error(status[1])
                    self.logger.info(
                        "BROWSER %i: Received failure status while executing "
                        "command: %s" % (browser.crawl_id, command[0]))
                elif status[0] == 'NETERROR':
                    command_status = 'neterror'
                    error_text, tb = self._unpack_picked_error(status[1])
                    error_text = parse_neterror(error_text)
                    self.logger.info(
                        "BROWSER %i: Received neterror %s while executing "
                        "command: %s" %
                        (browser.crawl_id, error_text, command[0])
                    )
                else:
                    raise ValueError(
                        "Unknown browser status message %s" % status
                    )
            except EmptyQueue:
                command_status = 'timeout'
                self.logger.info(
                    "BROWSER %i: Timeout while executing command, %s, killing "
                    "browser manager" % (browser.crawl_id, command[0]))

            self.sock.send(("crawl_history", {
                "crawl_id": browser.crawl_id,
                "visit_id": browser.curr_visit_id,
                "command": command[0],
                "arguments": str(command_arguments),
                "retry_number": command_sequence.retry_number,
                "command_status": command_status,
                "error": error_text,
                "traceback": tb
            }))

            if critical_failure:
                return

            if command_status != 'ok':
                with self.threadlock:
                    self.failurecount += 1
                if self.failurecount > self.failure_limit:
                    self.logger.critical(
                        "BROWSER %i: Command execution failure pushes failure "
                        "count above the allowable limit. Setting "
                        "failure_status." % browser.crawl_id)
                    self.failure_status = {
                        'ErrorType': 'ExceedCommandFailureLimit',
                        'CommandSequence': command_sequence
                    }
                    return
                browser.restart_required = True
                self.logger.debug("BROWSER %i: Browser restart required" % (
                    browser.crawl_id))
            else:
                with self.threadlock:
                    self.failurecount = 0

            if browser.restart_required:
                break

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
                    "browser launch failures. Setting failure_status." % (
                        browser.crawl_id))
                self.failure_status = {
                    'ErrorType': 'ExceedLaunchFailureLimit',
                    'CommandSequence': command_sequence
                }
                return
            browser.restart_required = False

    def execute_command_sequence(self, command_sequence: CommandSequence,
                                 index: Optional[int] = None) -> None:
        """
        parses command type and issues command(s) to the proper browser
        <index> specifies the type of command this is:
        None  -> first come, first serve
        int  -> index of browser to send command to
        """

        # Block if the aggregator queue is too large
        agg_queue_size = self.data_aggregator.get_most_recent_status()
        if agg_queue_size >= AGGREGATOR_QUEUE_LIMIT:
            while agg_queue_size >= AGGREGATOR_QUEUE_LIMIT:
                self.logger.info(
                    "Blocking command submission until the DataAggregator "
                    "is below the max queue size of %d. Current queue "
                    "length %d. " % (AGGREGATOR_QUEUE_LIMIT, agg_queue_size)
                )
                agg_queue_size = self.data_aggregator.get_status()

        # Distribute command
        if index is None:
            # send to first browser available
            command_executed = False
            while True:
                for browser in self.browsers:
                    if browser.ready():
                        browser.current_timeout = \
                            command_sequence.total_timeout
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
                        index].current_timeout = command_sequence.total_timeout
                    thread = self._start_thread(
                        self.browsers[index], command_sequence)
                    break
                time.sleep(SLEEP_CONS)
        else:
            self.logger.info(
                "Command index type is not supported or out of range")
            return

        if command_sequence.blocking:
            thread.join()
            self._check_failure_status()

    # DEFINITIONS OF HIGH LEVEL COMMANDS
    # NOTE: These wrappers are provided for convenience. To issue sequential
    # commands to the same browser in a single 'visit', use the CommandSequence
    # class directly.

    def get(self, url: str, index: Optional[int] = None,
            timeout: int = 60, sleep: int = 0, reset: bool = False) -> None:
        """ goes to a url """
        command_sequence = CommandSequence(url)
        command_sequence.get(timeout=timeout, sleep=sleep)
        command_sequence.reset = reset
        self.execute_command_sequence(command_sequence, index=index)

    def browse(self, url: str, num_links: int = 2, sleep: int = 0,
               index: Optional[int] = None, timeout: int = 60,
               reset: bool = False) -> None:
        """ browse a website and visit <num_links> links on the page """
        command_sequence = CommandSequence(url)
        command_sequence.browse(
            num_links=num_links, sleep=sleep, timeout=timeout)
        command_sequence.reset = reset
        self.execute_command_sequence(command_sequence, index=index)

    def close(self) -> None:
        """
        Execute shutdown procedure for TaskManager
        """
        if self.closing:
            self.logger.error("TaskManager already closed")
            return
        start_time = time.time()
        self._shutdown_manager()
        # We don't have a logging thread at this time anymore
        print("Shutdown took %s seconds" % str(time.time() - start_time))
