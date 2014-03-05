import BrowserManager
from Commands import profile_commands
from DataAggregator import DataAggregator

from multiprocessing import Process, Queue
import os
import signal
import sqlite3
import subprocess
import tempfile
import time

# User-facing API for running browser automation
# The TaskManager runs two sub-processes - WebManger for browser actions/instrumentation and DataAggregator for DB I/O
# General paradigm is for the TaskManager to send commands and wait for response and/or restart workers if necessary
# Compared to light wrapper around WebDriver, provides robustness and timeout functionality

# <db_location> is the absolute path of the folder in which we want to build our crawl data DB
# <db_name> is the name of the database (including .sqlite suffix)
# <browsers> is the type of browser we want to instantiate (currently accepts 'firefox' / 'chrome')
# <timeout> is the default amount of time we want to allow a command to execute (can override on individual commands)
# <headless> is a boolean that indicates whether we want to run a headless browser (TODO: make this work for Chrome)
# <proxy> is a boolean that indicates whether we want to use a proxy (for now mitmproxy)
# <fourthparty> is a boolean that indicates whether we want to add support for FourthParty
# <browser_debugging> is a boolean that indicates whether we want to run the browser in debugging mode
# <profile_path> is an absolute path of the folder containing a browser profile that we wish to load
# <description> is an optional description string for a particular crawl
# <mp_lock> is a multi-processing lock used for DB I/O


class TaskManager:

    def __init__(self, db_location, db_name, browser='firefox', timeout=30, headless=False, proxy=False,
                 fourthparty=False, browser_debugging=False, profile=None, description=None, mp_lock=None):
         # sets up the information needed to write to the database
        self.profile_path = profile
        self.desc = description
        self.mp_lock = mp_lock
        self.db_loc = db_location if db_location.endswith("/") else db_location + "/"
        self.db_name = db_name

        # sets up the crawl data database and extracts crawl id
        if self.mp_lock is not None:
            self.mp_lock.acquire()
        self.db = sqlite3.connect(db_location + db_name)
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
            self.db.executescript(f.read())
        self.crawl_id = self.get_id()
        if self.mp_lock is not None:
            self.mp_lock.release()

        # constructs dictionary of browser parameters
        self.browser_params = {
            'browser': browser,
            'headless': headless,
            'proxy': proxy,
            'fourthparty': fourthparty,
            'debugging': browser_debugging,
            'crawl_id': self.crawl_id
        }
       
        # sets up the BrowserManager/DataAggregator + associate queues as well as process ids
        self.browser_pid = None  # pid for browser instance controlled by BrowserManager
        self.display_pid = None  # the pid of the display for the headless browser (if it exists)
        self.is_fresh = None  # boolean that says if the BrowserManager new (used to optimize restarts)
        self.timeout = timeout
        self.browser_command_queue = None  # queue for passing command tuples to BrowserManager
        self.browser_status_queue = None  # queue for receiving command execution status from BrowserManager
        self.aggregator_query_queue = None  # queue for sending data/queries to DataAggregator
        self.aggregator_status_queue = None  # queue used for sending graceful KILL command to DataAggregator
        self.browser_manager = self.launch_browser_manager()
        self.data_aggregator = self.launch_data_aggregator()

    # CRAWLER SETUP / KILL CODE

    # assigns id to the crawler based on the output database
    def get_id(self):
        if self.mp_lock is not None:
            self.mp_lock.acquire()
        cur = self.db.cursor()
        cur.execute("INSERT INTO crawl (db_location, description, profile) VALUES (?,?,?)",
                    (self.db_loc, self.desc, self.profile_path))
        self.db.commit()
        if self.mp_lock is not None:
            self.mp_lock.release()
        return cur.lastrowid

    # sets up the BrowserManager and gets the process id, browser pid and, if applicable, screen pid
    # loads associated user profile if necessary
    # <spawn_timeout> is the timeout for creating BrowserManager
    def launch_browser_manager(self, spawn_timeout=300):
        # save the old profile to be copied if it exists (also used for initialization)
        old_profile = self.profile_path
        td = tempfile.mkdtemp() + "/"
        if old_profile is not None:
            profile_commands.dump_profile(old_profile, td)

        # keep trying to spawn a BrowserManager until we have a successful launch within the timeout limit
        browser_manager = None
        successful_spawn = False
        while not successful_spawn:
            # Resets the command/status queues
            (self.browser_command_queue, self.browser_status_queue, self.aggregator_query_queue) \
                = (Queue(), Queue(), Queue())

            # builds and launches the browser_manager
            browser_manager = Process(target=BrowserManager.BrowserManager,
                                      args=(self.browser_command_queue, self.browser_status_queue,
                                            self.aggregator_query_queue, self.browser_params, ))
            browser_manager.start()

            # waits for BrowserManager to send success tuple i.e. (profile_path, browser pid, display pid)
            for i in xrange(0, int(spawn_timeout) * 1000):
                 # no status for now -> sleep to avoid pegging CPU on blocking get
                if self.browser_status_queue.empty():
                    time.sleep(0.001)
                    continue

                (self.profile_path, self.browser_pid, self.display_pid) = self.browser_status_queue.get()
                if old_profile is not None:  # i.e. we are loading an old profile
                    profile_commands.load_profile(self.profile_path, td)
                successful_spawn = True
                break

            # kill the BrowserManager if it failed to start up the browser
            if not successful_spawn:
                os.kill(browser_manager.pid, signal.SIGKILL)

        # cleans up old profile and temporary profile if they exist
        subprocess.call(["rm", "-r", td])
        if old_profile is not None:
            subprocess.call(["rm", "-r", old_profile])

        self.is_fresh = old_profile is None  # browser is fresh iff it starts from a blank profile
        return browser_manager

    # sets up the DataAggregator (should only be called once corresponding BrowserManager is live)
    def launch_data_aggregator(self):
        self.aggregator_status_queue = Queue()
        aggregator = Process(target=DataAggregator.DataAggregator,
                             args=(self.crawl_id, self.db_loc + self.db_name,
                                   self.aggregator_query_queue, self.aggregator_status_queue, ))
        aggregator.start()
        return aggregator

    # terminates a BrowserManager, its browser instance and, if necessary, its virtual display
    def kill_browser_manager(self):
        os.kill(self.browser_manager.pid, signal.SIGKILL)
        if self.display_pid is not None:
            os.kill(self.display_pid, signal.SIGKILL)
        os.kill(self.browser_pid, signal.SIGKILL)

    # terminates a DataAggregator with a graceful KILL COMMAND
    def kill_data_aggregator(self):
        self.aggregator_status_queue.put("DIE")
        self.data_aggregator.join()

    # kill and restart the two worker processes
    # <reset> marks whether we want to wipe the old profile
    def restart_workers(self, reset=False):
        self.kill_browser_manager()
        self.kill_data_aggregator()

        # in case of reset, hard-deletes old profile
        if reset and self.profile_path is not None:
            subprocess.call(["rm", "-r", self.profile_path])
            self.profile_path = None

        self.browser_manager = self.launch_browser_manager()
        self.data_aggregator = self.launch_data_aggregator()

    # closes the TaskManager for good and frees up memory
    def close(self):
        self.kill_browser_manager()
        if self.profile_path is not None:
            subprocess.call(["rm", "-r", self.profile_path])
        self.kill_data_aggregator()

    # CRAWLER COMMAND CODE   

    # sends command tuple to the BrowserManager
    # <timeout> gives the option to override default timeout
    def issue_command(self, command, timeout=None):
        self.is_fresh = False  # since we are issuing a command, the BrowserManager is no longer a fresh instance
        timeout = self.timeout if timeout is None else timeout  # allows user to overwrite timeout

        # passes off command and waits for a success (or failure signal)
        self.browser_command_queue.put(command)
        command_succeeded = False

        # repeatedly waits for a reply from the BrowserManager; if fails/times-out => restart
        for i in xrange(0, int(timeout) * 1000):
            if self.browser_status_queue.empty():  # nothing to do -> sleep so as to not peg CPU
                time.sleep(0.001)
                continue

            # received reply from BrowserManager, either success signal or failure notice
            status = self.browser_status_queue.get()
            if status == "OK":
                command_succeeded = True
            break

        if not command_succeeded:  # reboots since BrowserManager is down
            self.restart_workers()

    # DEFINITIONS OF HIGH LEVEL COMMANDS

    # goes to a url
    def get(self, url, overwrite_timeout=None):
        self.issue_command(('GET', url), overwrite_timeout)

    # dumps from the profile path to a given file (absolute path)
    def dump_profile(self, dump_folder, overwrite_timeout=None):
        self.issue_command(('DUMP_PROF', dump_folder), overwrite_timeout)
    
    # loads profile from the load folder 
    # if prof is None, picks newest folder, otherwise chooses prof tar file
    def load_profile(self, load_folder, prof=None, overwrite_timeout=None):
        self.issue_command(('LOAD_PROF', load_folder, prof), overwrite_timeout)

    # resets the worker processes with profile to a clean state
    def reset(self):
        if not self.is_fresh:  # optimization in case resetting after a relaunch
            self.restart_workers(reset=True)