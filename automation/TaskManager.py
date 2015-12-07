from BrowserManager import Browser
from DataAggregator import DataAggregator, LevelDBAggregator
from SocketInterface import clientsocket
from PostProcessing import post_processing
from Errors import CommandExecutionError
import MPLogger

from multiprocessing import Process, Queue
from Queue import Empty as EmptyQueue
from sqlite3 import OperationalError
import threading
import copy
import os
import sqlite3
import time
import json
import psutil
import shutil
import sys

SLEEP_CONS = 0.1  # command sleep constant (in seconds)
BROWSER_MEMORY_LIMIT = 1500 # in MB

def load_default_params(num_browsers=1):
    """
    Loads num_browsers copies of the default browser_params dictionary.
    Also loads a single copy of the default TaskManager params dictionary.
    """
    fp = open(os.path.join(os.path.dirname(__file__), 'default_browser_params.json'))
    preferences = json.load(fp)
    fp.close()
    browser_params = [copy.deepcopy(preferences) for i in xrange(0, num_browsers)]
    
    fp = open(os.path.join(os.path.dirname(__file__), 'default_manager_params.json'))
    manager_params = json.load(fp)
    fp.close()
    manager_params['num_browsers'] = num_browsers
    
    return manager_params, browser_params

class TaskManager:
    """
    User-facing Class for interfacing with OpenWPM
    The TaskManager spawns several child processes to run the automation tasks.
        - DataAggregator to aggregate data in a SQLite database
        - MPLogger to aggregate logs across processes
        - BrowserManager processes to isolate Browsers in a separate process
    <manager_params> dict of TaskManager configuration parameters
    <browser_params> is a list of (or a single) dictionaries that specify preferences for browsers to instantiate
    <process_watchdog> will monitor firefox and Xvfb processes, killing any not indexed in TaskManager's browser list.
        NOTE: Only run this in isolated environments. It kills processes by name, indiscriminately.
    <task_description> is an optional description string for a particular crawl (primarily for logging)
    """

    def __init__(self, manager_params, browser_params, process_watchdog=False, task_description=None):
        # Make paths absolute in manager_params
        manager_params['data_directory'] = os.path.expanduser(manager_params['data_directory'])
        manager_params['log_directory'] = os.path.expanduser(manager_params['log_directory'])
        manager_params['database_name'] = os.path.join(manager_params['data_directory'],manager_params['database_name'])
        manager_params['log_file'] = os.path.join(manager_params['log_directory'],manager_params['log_file'])
        self.manager_params = manager_params
        
        # Flow control
        self.closing = False
        self.failure_flag = False
        self.threadlock = threading.Lock()
        self.failurecount = 0
        
        self.desc = task_description
        self.process_watchdog = process_watchdog

        # sets up the crawl data database
        db_path = manager_params['database_name']
        if not os.path.exists(manager_params['data_directory']):
            os.mkdir(manager_params['data_directory'])
        self.db = sqlite3.connect(db_path)
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
            self.db.executescript(f.read())
        
        # check size of parameter dictionary
        self.num_browsers = manager_params['num_browsers']
        if len(browser_params) != self.num_browsers:
            raise Exception("Number of <browser_params> dicts is not the same as manager_params['num_browsers']")

        # sets up logging server + connect a client
        self.logging_status_queue = None
        self.loggingserver = self._launch_loggingserver()
        # socket location: (address, port)
        self.manager_params['logger_address'] = self.logging_status_queue.get()
        self.logger = MPLogger.loggingclient(*self.manager_params['logger_address'])

        # Mark if LDBAggregator is needed (if js is enabled on any browser)
        self.ldb_enabled = False
        for params in browser_params:
            if params['save_javascript']:
                self.ldb_enabled = True
                break

        # Initialize the data aggregators
        self._launch_aggregators()
        
        # open client socket
        self.sock = clientsocket()
        self.sock.connect(*self.manager_params['aggregator_address'])

        # update task table
        cur = self.db.cursor()
        cur.execute("INSERT INTO task (description) VALUES (?)", (self.desc,))
        self.db.commit()
        self.task_id = cur.lastrowid

        # read the last used site visit id
        cur = self.db.cursor()
        last_visit_id = 0
        query_successful = False
        while not query_successful:
            try:
                cur.execute("SELECT MAX(visit_id) from site_visits")
                self.db.commit()
                last_visit_id = cur.fetchone()[0]
                if last_visit_id is None:
                    last_visit_id = 0
                query_successful = True
            except OperationalError:
                time.sleep(0.1)
                pass
        self.next_visit_id = last_visit_id + 1

        # sets up the BrowserManager(s) + associated queues
        self.browsers = self._initialize_browsers(browser_params)  # List of the Browser(s)
        self._launch_browsers()

        # start the manager watchdog
        thread = threading.Thread(target=self._manager_watchdog, args=())
        thread.daemon = True
        thread.start()

    def _initialize_browsers(self, browser_params):
        """ initialize the browser classes, each with a unique set of parameters """
        browsers = list()
        for i in xrange(self.num_browsers):
            # update crawl table
            # TODO: update DB with browser.browser_settings for each browser manager initialized
            cur = self.db.cursor()
            query_successful = False
            crawl_id = -1
            while not query_successful:
                try:
                    cur.execute("INSERT INTO crawl (task_id, profile, browser, headless, proxy, debugging, "
                                "disable_flash) VALUES (?,?,?,?,?,?,?)",
                                (self.task_id, browser_params[i]['profile_tar'], browser_params[i]['browser'],
                                 browser_params[i]['headless'], browser_params[i]['proxy'],
                                 browser_params[i]['debugging'], browser_params[i]['disable_flash']))
                    self.db.commit()
                    crawl_id = cur.lastrowid
                    query_successful = True
                except OperationalError:
                    time.sleep(0.1)
                    pass

            browser_params[i]['crawl_id'] = crawl_id
            browsers.append(Browser(self.manager_params, browser_params[i]))

        return browsers
    
    def _launch_browsers(self):
        """ launch each browser manager process / browser """
        for browser in self.browsers:
            success = browser.launch_browser_manager()
            if not success:
                self.logger.critical("Browser spawn failure during TaskManager initialization, exiting...")
                self.close(post_process=False)
                break

            # Update our DB with the random browser settings
            # These are found within the scope of each instance of Browser in the browsers list
            screen_res = str(browser.browser_settings['screen_res'])
            ua_string = str(browser.browser_settings['ua_string'])
            self.sock.send(("UPDATE crawl SET screen_res = ?, ua_string = ? \
                             WHERE crawl_id = ?", (screen_res, ua_string, browser.crawl_id)))

    def _manager_watchdog(self):
        """ 
        Periodically checks the following:
        - memory consumption of all browsers every 10 seconds
        - presence of processes that are no longer in use
        """
        while not self.closing:
            time.sleep(10)

            # Check browser memory usage
            for browser in self.browsers:
                try:
                    process = psutil.Process(browser.browser_pid)
                    mem = process.memory_info()[0] / float(2 ** 20)
                    if mem > BROWSER_MEMORY_LIMIT:
                        self.logger.info("BROWSER %i: Memory usage: %iMB, exceeding limit of %iMB"
                            % (browser.crawl_id, int(mem), BROWSER_MEMORY_LIMIT))
                        browser.restart_required = True
                except psutil.NoSuchProcess as e:
                    pass
            
            # Check for browsers or displays that were not closed correctly
            # Provide a 300 second buffer to avoid killing freshly launched browsers
            # TODO This buffer should correspond to the maximum browser spawn timeout
            if self.process_watchdog:
                browser_pids = set()
                display_pids = set()
                check_time = time.time()
                for browser in self.browsers:
                    if browser.browser_pid is not None:
                        browser_pids.add(browser.browser_pid)
                    if browser.display_pid is not None:
                        display_pids.add(browser.display_pid)
                for process in psutil.process_iter():
                    if (process.create_time() + 300 < check_time and
                            ((process.name() == 'firefox' and process.pid not in browser_pids) or
                            (process.name() == 'Xvfb' and process.pid not in display_pids))):
                        self.logger.debug("Process: %s (pid: %i) with start time %s found running but not in browser process list. Killing."
                                % (process.name(), process.pid, process.create_time()))
                        process.kill()

    def _launch_aggregators(self):
        """
        Launches the various data aggregators, which serialize data from all processes.
        * DataAggregator - sqlite database for crawl data
        * LevelDBAggregator - leveldb database for javascript files
        """
        # DataAggregator
        self.aggregator_status_queue = Queue()
        self.data_aggregator = Process(target=DataAggregator.DataAggregator,
                             args=(self.manager_params, self.aggregator_status_queue))
        self.data_aggregator.daemon = True
        self.data_aggregator.start()
        self.manager_params['aggregator_address'] = self.aggregator_status_queue.get()  # socket location: (address, port)

        # LevelDB Aggregator
        if self.ldb_enabled:
            self.ldb_status_queue = Queue()
            self.ldb_aggregator = Process(target=LevelDBAggregator.LevelDBAggregator,
                                 args=(self.manager_params, self.ldb_status_queue))
            self.ldb_aggregator.daemon = True
            self.ldb_aggregator.start()
            self.manager_params['ldb_address'] = self.ldb_status_queue.get()  # socket location: (address, port)

    def _kill_aggregators(self):
        """ Terminates the aggregators gracefully """
        # DataAggregator
        self.logger.debug("Telling the DataAggregator to shut down...")
        self.aggregator_status_queue.put("DIE")
        start_time = time.time()
        self.data_aggregator.join(300)
        self.logger.debug("DataAggregator took " + str(time.time() - start_time) + " seconds to close")
        
        # LevelDB Aggregator
        if self.ldb_enabled:
            self.logger.debug("Telling the LevelDBAggregator to shut down...")
            self.ldb_status_queue.put("DIE")
            start_time = time.time()
            self.ldb_aggregator.join(300)
            self.logger.debug("LevelDBAggregator took " + str(time.time() - start_time) + " seconds to close")
    
    def _launch_loggingserver(self):
        """ sets up logging server """
        self.logging_status_queue = Queue()
        loggingserver = Process(target=MPLogger.loggingserver,
                             args=(self.manager_params['log_file'], self.logging_status_queue, ))
        loggingserver.daemon = True
        loggingserver.start()
        return loggingserver

    def _kill_loggingserver(self):
        """ terminates logging server gracefully """
        self.logging_status_queue.put("DIE")
        self.loggingserver.join(300)

    def _shutdown_manager(self, failure=False):
        """
        Wait for current commands to finish, close all child processes and
        threads
        <failure> flag to indicate manager failure (True) or end of crawl (False)
        """
        self.closing = True
        
        for i in range(len(self.browsers)):
            browser = self.browsers[i]
            if browser.command_thread is not None:
                self.logger.debug("BROWSER %i: Joining command thread" % browser.crawl_id)
                start_time = time.time()
                if browser.current_timeout is not None:
                    browser.command_thread.join(browser.current_timeout + 10)
                else:
                    browser.command_thread.join(60)
                self.logger.debug("BROWSER %i: %f seconds to join command thread" % (browser.crawl_id, time.time() - start_time))
            self.logger.debug("BROWSER %i: Killing browser manager..." % browser.crawl_id)
            browser.kill_browser_manager()
            if browser.current_profile_path is not None:
                shutil.rmtree(browser.current_profile_path, ignore_errors = True)
            if failure:
                self.sock.send(("UPDATE crawl SET finished = -1 WHERE crawl_id = ?",
                                (browser.crawl_id,)))
            else:
                self.sock.send(("UPDATE crawl SET finished = 1 WHERE crawl_id = ?",
                                (browser.crawl_id,)))
        self.db.close()  # close db connection
        self.sock.close()  # close socket to data aggregator
        self._kill_aggregators()
        self._kill_loggingserver()

    def _gracefully_fail(self, msg, command_sequence):
        """
        Execute shutdown commands before throwing error
        <msg>: an Exception will be raised with this message
        """
        self._shutdown_manager(failure=True)
        raise CommandExecutionError(msg, command_sequence)

    # CRAWLER COMMAND CODE

    def _distribute_command(self, command_sequence, index=None):
        """
        parses command type and issues command(s) to the proper browser
        <index> specifies the type of command this is:
        = None  -> first come, first serve
        =  #    -> index of browser to send command to
        = *     -> sends command to all browsers
        = **    -> sends command to all browsers (synchronized)
        """
        if index is None:
            #send to first browser available
            command_executed = False
            while True:
                for browser in self.browsers:
                    if browser.ready():
                        browser.current_timeout = command_sequence.total_timeout
                        self._start_thread(browser, command_sequence)
                        command_executed = True
                        break
                if command_executed:
                    break
                time.sleep(SLEEP_CONS)

        elif 0 <= index < len(self.browsers):
            #send the command to this specific browser
            while True:
                if self.browsers[index].ready():
                    self.browsers[index].current_timeout = command_sequence.total_timeout
                    self._start_thread(self.browsers[index], command_sequence)
                    break
                time.sleep(SLEEP_CONS)
        elif index == '*':
            #send the command to all browsers
            command_executed = [False] * len(self.browsers)
            while False in command_executed:
                for i in xrange(len(self.browsers)):
                    if self.browsers[i].ready() and not command_executed[i]:
                        self.browsers[i].current_timeout = command_sequence.total_timeout
                        self._start_thread(self.browsers[i], command_sequence)
                        command_executed[i] = True
                time.sleep(SLEEP_CONS)
        elif index == '**':
            #send the command to all browsers and sync it
            condition = threading.Condition()  # Used to block threads until ready
            command_executed = [False] * len(self.browsers)
            while False in command_executed:
                for i in xrange(len(self.browsers)):
                    if self.browsers[i].ready() and not command_executed[i]:
                        self.browsers[i].current_timeout = command_sequence.total_timeout
                        self._start_thread(self.browsers[i], command_sequence, condition)
                        command_executed[i] = True
                time.sleep(SLEEP_CONS)
            with condition:
                condition.notifyAll()  # All browsers loaded, tell them to start
        else:
            self.logger.info("Command index type is not supported or out of range")

    def _start_thread(self, browser, command_sequence, condition=None):
        """  starts the command execution thread """

        # Check status flags before starting thread
        if self.closing:
            self.logger.error("Attempted to execute command on a closed TaskManager")
            return
        if self.failure_flag:
            self.logger.debug("TaskManager failure threshold exceeded, raising CommandExecutionError")
            self._gracefully_fail("TaskManager failure threshold exceeded", command_sequence)

        browser.set_visit_id(self.next_visit_id)
        self.sock.send(("INSERT INTO site_visits (visit_id, crawl_id, site_url) VALUES (?,?,?)",
                        (self.next_visit_id, browser.crawl_id, command_sequence.url)))
        self.next_visit_id += 1

        # Start command execution thread
        args = (browser, command_sequence, condition)
        thread = threading.Thread(target=self._issue_command, args=args)
        browser.command_thread = thread
        thread.daemon = True
        thread.start()

    def _issue_command(self, browser, command_sequence, condition=None):
        """
        sends command tuple to the BrowserManager
        """
        browser.is_fresh = False  # since we are issuing a command, the BrowserManager is no longer a fresh instance

        # if this is a synced call, block on condition
        if condition is not None:
            with condition:
                condition.wait()

        reset = command_sequence.reset
        start_time = None
        commands = command_sequence.commands
        for command_tuple in commands:
            command, timeout = command_tuple
            if command[0] == 'GET' or command[0] == 'BROWSE':
                start_time = time.time()
                command += (browser.curr_visit_id,)
            elif command[0] == 'DUMP_STORAGE_VECTORS':
                command += (start_time, browser.curr_visit_id,)
            browser.current_timeout = timeout
            # passes off command and waits for a success (or failure signal)
            browser.command_queue.put(command)
            command_succeeded = 0 #1 success, 0 failure from error, -1 timeout
            command_arguments = command[1] if len(command) > 1 else None

            # received reply from BrowserManager, either success signal or failure notice
            try:
                status = browser.status_queue.get(True, browser.current_timeout)
                if status == "OK":
                    command_succeeded = 1
                else:
                    command_succeeded = 0
                    self.logger.info("BROWSER %i: Received failure status while executing command: %s" % (browser.crawl_id, command[0]))
            except EmptyQueue:
                command_succeeded = -1
                self.logger.info("BROWSER %i: Timeout while executing command, %s, killing browser manager" % (browser.crawl_id, command[0]))

            self.sock.send(("INSERT INTO CrawlHistory (crawl_id, command, arguments, bool_success)"
                            " VALUES (?,?,?,?)",
                            (browser.crawl_id, command[0], command_arguments, command_succeeded)))

            if command_succeeded != 1:
                with self.threadlock:
                    self.failurecount += 1
                if self.failurecount > self.num_browsers * 2 + 10:
                    self.logger.critical("BROWSER %i: Command execution failure pushes failure count above the allowable limit. Setting failure_flag." % browser.crawl_id)
                    self.failure_flag = True
                    return
                browser.restart_required = True
            else:
                with self.threadlock:
                    self.failurecount = 0

            if browser.restart_required:
                break

        if self.closing:
            return

        if browser.restart_required or reset:
            success = browser.restart_browser_manager(clear_profile = reset)
            if not success:
                self.logger.critical("BROWSER %i: Exceeded the maximum allowable consecutive browser launch failures. Setting failure_flag." % browser.crawl_id)
                self.failure_flag = True
                return
            browser.restart_required = False

    def execute_command_sequence(self, command_sequence, index=None):
        self._distribute_command(command_sequence, index)

    def close(self, post_process=True):
        """
        Execute shutdown procedure for TaskManager
        <post_process> flag to launch post_processing pipeline
        """
        if self.closing:
            self.logger.error("TaskManager already closed")
            return
        self._shutdown_manager()
        if post_process:
            post_processing.run(self.manager_params) # launch post-crawl processing