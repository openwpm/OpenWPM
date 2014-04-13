from BrowserManager import Browser, BrowserManager
from DataAggregator import DataAggregator
from SocketInterface import clientsocket

from multiprocessing import Process, Queue
from collections import namedtuple
import threading
import os
import signal
import sqlite3
import subprocess
import time

# User-facing API for running browser automation
# The TaskManager runs two sub-processes - WebManger for browser actions/instrumentation and DataAggregator for DB I/O
# General paradigm is for the TaskManager to send commands and wait for response and/or restart workers if necessary
# Compared to light wrapper around WebDriver, provides robustness and timeout functionality
#TODO: improve db management in Task manager - the connection doesn't need to remain open
#TODO: sensibly handle crawl descriptions and saving configuration parameters
#TODO: clean up this documentation to match the refactor

# <db_location> is the absolute path of the folder in which we want to build our crawl data DB
# <db_name> is the name of the database (including .sqlite suffix)
# <browsers> is the type of browser we want to instantiate (currently accepts 'firefox' / 'chrome')
# <timeout> is the default amount of time we want to allow a command to execute (can override on individual commands)
# <num_instances> is the number of browser managers to launch if you wish to crawl in parallel
# <headless> is a boolean that indicates whether we want to run a headless browser (TODO: make this work for Chrome)
# <proxy> is a boolean that indicates whether we want to use a proxy (for now mitmproxy)
# <fourthparty> is a boolean that indicates whether we want to add support for FourthParty
# <browser_debugging> is a boolean that indicates whether we want to run the browser in debugging mode
# <profile_path> is an absolute path of the folder containing a browser profile that we wish to load
# <description> is an optional description string for a particular crawl
class TaskManager:
    def __init__(self, db_location, db_name, description = None, num_browsers = 2,
                browser='firefox', headless=False, proxy=False, fourthparty=False,
                browser_debugging=False, timeout=30, profile=None):
        # sets up the information needed to write to the database
        self.profile_path = 'FIX-ME' #TODO - make per-browser
        self.desc = description #TODO - update for multiprocessing
        self.db_loc = db_location if db_location.endswith("/") else db_location + "/"
        self.db_name = db_name

        # Store parameters for the database
        self.parameters = (browser, headless, proxy, fourthparty,
                            browser_debugging, profile, timeout)

        # sets up the crawl data database
        self.db = sqlite3.connect(db_location + db_name)
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
            self.db.executescript(f.read())
        
        # prepares browser settings
        self.num_browsers = num_browsers
        browser_params = self.build_browser_params(browser, headless, proxy, fourthparty, 
                                                   browser_debugging, profile, timeout)

        # sets up the DataAggregator + associated queues
        self.aggregator_status_queue = None  # queue used for sending graceful KILL command to DataAggregator
        self.data_aggregator = self.launch_data_aggregator()
        self.aggregator_address = self.aggregator_status_queue.get() #socket location: (address, port)

        # open client socket
        self.sock = clientsocket()
        self.sock.connect(self.aggregator_address[0], self.aggregator_address[1])

        # update task table
        self.task_id = None
        self.sock.send( ("INSERT INTO task (description) VALUES (?)", (self.desc,) ))
        # Get task ID (last item added to seq table)
        cur = self.db.cursor()
        cur.execute("SELECT seq from sqlite_sequence WHERE name='task'")
        data = cur.fetchall()
        try:
            self.task_id = data[0][0]
        except:
            self.task_id = 1
        
        # sets up the BrowserManager(s) + associated queues
        self.browsers = self.initialize_browsers(browser_params) #List of the Browser(s)



    # CRAWLER SETUP / KILL CODE

    # initialize the browsers, each with a unique set of parameters
    def initialize_browsers(self, browser_params):
        browsers = list()
        for i in range(self.num_browsers):
            crawl_id = self.get_id(browser_params[i])
            browsers.append(Browser(crawl_id, self.aggregator_address, *browser_params[i]))
        return browsers

    # builds the browser parameter vectors, scaling all parameters to the number of browsers
    def build_browser_params(self, *args):
        # scale parameter vectors
        params = list()
        for arg in args:
            if type(arg) == list:
                # list arguments must not exceed # of browsers and divide # of browsers evenly
                if len(arg) <= self.num_browsers and self.num_browsers % len(arg) == 0:
                    params.append(arg * (self.num_browsers / len(arg)))
                else:
                    raise Exception("Number of browsers requested is not the length of \
                                    the specified parameters (or a multiple).")
            else: #single length parameter
                params.append([arg] * self.num_browsers)
        # create a per-browser list
        params_list = list()
        for i in range(self.num_browsers):
            params_list.append([x[i] for x in params])
        return params_list

    # assigns id to the crawler based on the output database
    #TODO: the crawl database needs some serious TLC
    def get_id(self, browser_params):
        cur = self.db.cursor()

        #TO DO finish task and crawls table
        import ipdb; ipdb.set_trace()

        # update crawl table
        self.sock.send( ("INSERT INTO crawl (task_id, profile, \
                        browser, headless, proxy, fourthparty, debugging, timeout) VALUES (?,?,?,?,?,?,?,?)",
                                 (self.task_id, self.parameters[0], self.parameters[1], self.parameters[2],
                                 self.parameters[3], self.parameters[4], self.parameters[5],
                                 self.parameters[6]) ))
        #cur.execute("INSERT INTO crawl (db_location, description, profile) VALUES (?,?,?)",
        #            (self.db_loc, str(browser_params), self.profile_path))
        #self.db.commit()
        return cur.lastrowid
    
    # sets up the DataAggregator (Must be launched prior to BrowserManager) 
    def launch_data_aggregator(self):
        self.aggregator_status_queue = Queue()
        aggregator = Process(target=DataAggregator.DataAggregator,
                             args=(self.db_loc + self.db_name, 
                                 self.aggregator_status_queue, ))
        aggregator.start()
        return aggregator

    # terminates a DataAggregator with a graceful KILL COMMAND
    def kill_data_aggregator(self):
        self.aggregator_status_queue.put("DIE")
        self.data_aggregator.join()

    # closes the TaskManager for good and frees up memory
    def close(self):
        for browser in self.browsers:
            if browser.command_thread is not None:
                browser.command_thread.join()
            browser.kill_browser_manager()
            if browser.profile_path is not None:
                subprocess.call(["rm", "-r", browser.profile_path])
        self.kill_data_aggregator()
        self.db.close()

    # CRAWLER COMMAND CODE

    # parses command type and issues command(s) to the proper browser
    # <index> specifies the type of command this is
    #         = None  -> first come, first serve
    #         = #     -> index of browser to send command to
    #         = *     -> sends command to all browsers
    #         = **    -> sends command to all browsers (synchronized)
    def distribute_command(self, command, index=None, timeout=None):
        if index is None:
            #send to first browser available
            command_executed = False
            while True:
                for browser in self.browsers:
                    if browser.ready():
                        self.start_thread(browser, command, timeout)
                        command_executed = True
                        break
                if command_executed:
                    break
                time.sleep(0.01)
        elif index >= 0 and index < len(self.browsers):
            #send the command to this specific browser
            self.start_thread(self.browsers[index], command, timeout)
        elif index == '*':
            #send the command to all browsers
            command_executed = [False] * len(self.browsers)
            while False in command_executed:
                for i in range(len(self.browsers)):
                    if self.browsers[i].ready() and not command_executed[i]:
                        self.start_thread(self.browsers[i], command, timeout)
                        command_executed[i] = True
                time.sleep(0.01)
        elif index == '**':
            #send the command to all browsers and sync it
            condition = threading.Condition() #Used to block threads until ready
            command_executed = [False] * len(self.browsers)
            while False in command_executed:
                for i in range(len(self.browsers)):
                    if self.browsers[i].ready() and not command_executed[i]:
                        self.start_thread(self.browsers[i], command, timeout, condition)
                        command_executed[i] = True
                time.sleep(0.01)
            with condition:
                condition.notifyAll() #All browsers loaded, tell them to start
        else:
            #not a supported command
            print "Command index type is not supported or out of range"

    # starts the command execution thread
    def start_thread(self, browser, command, timeout, condition=None):
        args = (browser, command, timeout, condition)
        thread = threading.Thread(target=self.issue_command, args=args)
        browser.command_thread = thread
        thread.start()
    
    # sends command tuple to the BrowserManager
    # <timeout> gives the option to override default timeout
    def issue_command(self, browser, command, timeout=None, condition=None):
        browser.is_fresh = False  # since we are issuing a command, the BrowserManager is no longer a fresh instance
        timeout = browser.timeout if timeout is None else timeout  # allows user to overwrite timeout
        # if this is a synced call, block on condition
        if condition is not None:
            with condition:
                condition.wait()

        # passes off command and waits for a success (or failure signal)
        browser.command_queue.put(command)
        command_succeeded = False

        # repeatedly waits for a reply from the BrowserManager; if fails/times-out => restart
        for i in xrange(0, int(timeout) * 1000):
            if browser.status_queue.empty():  # nothing to do -> sleep so as to not peg CPU
                time.sleep(0.001)
                continue

            # received reply from BrowserManager, either success signal or failure notice
            status = browser.status_queue.get()
            if status == "OK":
                print str(browser.crawl_id) + " " + "got OK"
                command_succeeded = True
                self.sock.send( ("INSERT INTO CrawlHistory (crawl_id, command, arguments, bool_success) VALUES (?,?,?,?)",
                                 (browser.crawl_id, command[0], command[1], True) ))
            break
        if not command_succeeded:  # reboots since BrowserManager is down
            self.sock.send( ("INSERT INTO CrawlHistory (crawl_id, command, arguments, bool_success) VALUES (?,?,?,?)",
                                 (browser.crawl_id, command[0], command[1], False) ))
            browser.restart_browser_manager()

    # DEFINITIONS OF HIGH LEVEL COMMANDS

    # goes to a url
    def get(self, url, index=None, overwrite_timeout=None):
        self.distribute_command(('GET', url), index, overwrite_timeout)

    # dumps from the profile path to a given file (absolute path)
    def dump_profile(self, dump_folder, index=None, overwrite_timeout=None):
        self.distribute_command(('DUMP_PROF', dump_folder), index, overwrite_timeout)


