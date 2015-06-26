from BrowserManager import Browser
from DataAggregator import DataAggregator
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

SLEEP_CONS = 0.01  # command sleep constant (in seconds)
BROWSER_MEMORY_LIMIT = 1500 # in MB

def load_default_params(num_instances=1):
    """
    Loads num_instances copies of the default
    browser parameters from the included default settings json
    """
    fp = open(os.path.join(os.path.dirname(__file__), 'default_settings.json'))
    preferences = json.load(fp)
    fp.close()

    browser_params = [copy.deepcopy(preferences) for i in xrange(0, num_instances)]
    return browser_params

class TaskManager:
    """
    User-facing API for running browser automation
    The TaskManager runs two sub-processes - WebManger for browser actions/instrumentation and DataAggregator for DB I/O
    General paradigm is for the TaskManager to send commands and wait for response and/or restart workers if necessary
    Compared to light wrapper around WebDriver, provides robustness and timeout functionality

    <db_path> is the absolute path of the crawl DB (which may not yet exist)
    <browser_params> is a list of (or single) dictionaries that specify preferences for browsers to instantiate
    <num_browsers> is the number of browsers to instantiate
    <log_file> is the full path/name of the logfile. defaults to the user's home directory
    <process_watchdog> will monitor firefox and Xvfb processes, killing any not indexed in TaskManager's browser list.
        NOTE: Only run this in isolated environments. It kills processes by name, indiscriminately.
    <task_description> is an optional description string for a particular crawl (primarily for logging)
    """

    def __init__(self, db_path, browser_params, num_browsers, log_file = '~/openwpm.log', process_watchdog=False, task_description=None):
        # Flow control
        self.closing = False
        self.failure_flag = False
        self.threadlock = threading.Lock()
        self.failurecount = 0

        # sets up the information needed to write to the database
        self.desc = task_description
        self.db_path = db_path

        self.log_file = log_file
        self.process_watchdog = process_watchdog

        # sets up the crawl data database
        self.db = sqlite3.connect(db_path)
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
            self.db.executescript(f.read())
        
        # prepares browser settings
        self.num_browsers = num_browsers
        # special case: for singleton dictionary, we perform deep copies so that number of dicts is <num_browsers>
        if type(browser_params) is not list:
            browser_params = [copy.deepcopy(browser_params) for i in xrange(0, num_browsers)]

        if len(browser_params) != num_browsers:
            raise Exception("Number of browser parameter dictionaries is not the same as <num_browsers>")

        # sets up logging server + connect a client
        self.logging_status_queue = None
        self.loggingserver = self._launch_loggingserver()
        self.logger_address = self.logging_status_queue.get()  # socket location: (address, port)
        self.logger = MPLogger.loggingclient(*self.logger_address)
        
        # sets up the DataAggregator + associated queues
        self.aggregator_status_queue = None  # queue used for sending graceful KILL command to DataAggregator
        self.data_aggregator = self._launch_data_aggregator()
        self.aggregator_address = self.aggregator_status_queue.get()  # socket location: (address, port)

        # open client socket
        self.sock = clientsocket()
        self.sock.connect(self.aggregator_address[0], self.aggregator_address[1])

        # update task table
        cur = self.db.cursor()
        cur.execute("INSERT INTO task (description) VALUES (?)", (self.desc,))
        self.db.commit()
        self.task_id = cur.lastrowid
        
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
            browser_params[i]['aggregator_address'] = self.aggregator_address
            browser_params[i]['logger_address'] = self.logger_address
            browsers.append(Browser(browser_params[i]))

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
            if not browser.browser_settings['extensions']:
                extensions = 'None'
            else:
                extensions = ','.join(browser.browser_settings['extensions'])
            screen_res = str(browser.browser_settings['screen_res'])
            ua_string = str(browser.browser_settings['ua_string'])
            self.sock.send(("UPDATE crawl SET extensions = ?, screen_res = ?, ua_string = ? \
                             WHERE crawl_id = ?", (extensions, screen_res, ua_string, browser.crawl_id)))

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
                        browser.reset()
                except psutil.NoSuchProcess as e:
                    pass
            
            # Check for browsers or displays that were not closed correctly
            if self.process_watchdog:
                browser_pids = set()
                display_pids = set()
                check_time = time.time()
                for browser in self.browsers:
                    if browser.browser_pid is not None:
                        browser_pids.add(browser.browser_pid)
                    if browser.display_pid is not None:
                        display_pids.add(browser.display_pid)
                for process in psutil.get_process_list():
                    if (process.create_time() < check_time and
                            ((process.name() == 'firefox' and process.pid not in browser_pids) or
                            (process.name() == 'Xvfb' and process.pid not in display_pids))):
                        self.logger.debug("Process: %s (pid: %i) with start time %s found running but not in browser process list. Killing."
                                % (process.name(), process.pid, process.create_time()))
                        process.kill()

    def _launch_data_aggregator(self):
        """ sets up the DataAggregator (Must be launched prior to BrowserManager) """
        self.aggregator_status_queue = Queue()
        aggregator = Process(target=DataAggregator.DataAggregator,
                             args=(self.db_path, self.aggregator_status_queue, self.logger_address))
        aggregator.daemon = True
        aggregator.start()
        return aggregator

    def _kill_data_aggregator(self):
        """ terminates a DataAggregator with a graceful KILL COMMAND """
        self.logger.debug("Telling the DataAggregator to shut down...")
        self.aggregator_status_queue.put("DIE")
        start_time = time.time()
        self.data_aggregator.join(300)
        self.logger.debug("DataAggregator took " + str(time.time() - start_time) + " seconds to close")
    
    def _launch_loggingserver(self):
        """ sets up logging server """
        self.logging_status_queue = Queue()
        loggingserver = Process(target=MPLogger.loggingserver,
                             args=(self.log_file, self.logging_status_queue, ))
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
        self._kill_data_aggregator()
        self._kill_loggingserver()

    def _gracefully_fail(self, msg, command):
        """
        Execute shutdown commands before throwing error
        <msg>: an Exception will be raised with this message
        """
        self._shutdown_manager(failure=True)
        raise CommandExecutionError(msg, command)

    # CRAWLER COMMAND CODE

    def _distribute_command(self, command, index=None, timeout=None, reset=False):
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
                        browser.current_timeout = timeout
                        self._start_thread(browser, command, reset)
                        command_executed = True
                        break
                if command_executed:
                    break
                time.sleep(SLEEP_CONS)

        elif 0 <= index < len(self.browsers):
            #send the command to this specific browser
            while True:
                if self.browsers[index].ready():
                    self.browsers[index].current_timeout = timeout
                    self._start_thread(self.browsers[index], command, reset)
                    break
                time.sleep(SLEEP_CONS)
        elif index == '*':
            #send the command to all browsers
            command_executed = [False] * len(self.browsers)
            while False in command_executed:
                for i in xrange(len(self.browsers)):
                    if self.browsers[i].ready() and not command_executed[i]:
                        self.browsers[i].current_timeout = timeout
                        self._start_thread(self.browsers[i], command, reset)
                        command_executed[i] = True
                time.sleep(SLEEP_CONS)
        elif index == '**':
            #send the command to all browsers and sync it
            condition = threading.Condition()  # Used to block threads until ready
            command_executed = [False] * len(self.browsers)
            while False in command_executed:
                for i in xrange(len(self.browsers)):
                    if self.browsers[i].ready() and not command_executed[i]:
                        self.browsers[i].current_timeout = timeout
                        self._start_thread(self.browsers[i], command, reset, condition)
                        command_executed[i] = True
                time.sleep(SLEEP_CONS)
            with condition:
                condition.notifyAll()  # All browsers loaded, tell them to start
        else:
            self.logger.info("Command index type is not supported or out of range")

    def _start_thread(self, browser, command, reset, condition=None):
        """  starts the command execution thread """
        
        # Check status flags before starting thread
        if self.closing:
            self.logger.error("Attempted to execute command on a closed TaskManager")
            return
        if self.failure_flag:
            self.logger.debug("TaskManager failure threshold exceeded, raising CommandExecutionError")
            self._gracefully_fail("TaskManager failure threshold exceeded", command)

        # Start command execution thread
        args = (browser, command, reset, condition)
        thread = threading.Thread(target=self._issue_command, args=args)
        browser.command_thread = thread
        thread.daemon = True
        thread.start()

    def _issue_command(self, browser, command, reset, condition=None):
        """
        sends command tuple to the BrowserManager
        """
        browser.is_fresh = False  # since we are issuing a command, the BrowserManager is no longer a fresh instance
        
        # if this is a synced call, block on condition
        if condition is not None:
            with condition:
                condition.wait()

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
        
        if self.closing:
            return
        
        if command_succeeded != 1:
            with self.threadlock:
                self.failurecount += 1
            if self.failurecount > self.num_browsers * 2:
                self.logger.critical("BROWSER %i: Command execution failure pushes failure count above the allowable limit. Setting failure_flag." % browser.crawl_id)
                self.failure_flag = True
                return
            success = browser.restart_browser_manager()
            if not success:
                self.logger.critical("BROWSER %i: Exceeded the maximum allowable consecutive browser launch failures. Setting failure_flag." % browser.crawl_id)
                self.failure_flag = True
                return
        else:
            with self.threadlock:
                self.failurecount = 0
            if reset:
                browser.reset()
    
    # DEFINITIONS OF HIGH LEVEL COMMANDS

    def get(self, url, index=None, timeout=60, reset=False):
        """ goes to a url """
        self._distribute_command(('GET', url), index, timeout, reset)
        
    def browse(self, url, num_links = 2, index=None, timeout=60, reset=False):
        """ browse a website and visit <num_links> links on the page """
        self._distribute_command(('BROWSE', url, num_links), index, timeout, reset)

    def dump_storage_vectors(self, url, start_time, index=None, timeout=60):
        """ dumps the local storage vectors (flash, localStorage, cookies) to db """
        self._distribute_command(('DUMP_STORAGE_VECTORS', url, start_time), index, timeout)

    def dump_profile(self, dump_folder, close_webdriver=False, index=None, timeout=120):
        """ dumps from the profile path to a given file (absolute path) """
        self._distribute_command(('DUMP_PROF', dump_folder, close_webdriver), index, timeout)

    def extract_links(self, index=None, timeout=30):
        self._distribute_command(('EXTRACT_LINKS',), index, timeout)

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
            post_processing.run(self.db_path) # launch post-crawl processing

