from Commands import command_executor
from DeployBrowsers import deploy_browser
from Commands import profile_commands
from Proxy import deploy_mitm_proxy

from multiprocessing import Process, Queue
import subprocess
import tempfile
import signal
import time
import os

# Sets up a WebDriver instance that adheres to a given set of user paramters
# Continually listens to the TaskManager for commands and passes them to command module to execute
# Sends OK signal if command succeeds or else sends a FAILED signal to indicate that workers should be restarted
# TODO: this approach may be too coarse

# <command_queue> is the queue through which the browser sends command tuples
# <status_queue> is a queue through which the BrowserManager either signals command failure or success
# <db_socket_address> is the socket address through which to send data to the DataAggregator to manipulate and write
# <browser_params> are browser parameter settings (e.g. whether we're using a proxy, headless, etc.)

class Browser:
    def __init__(self, crawl_id, db_socket_address, browser, headless, proxy, 
                fourthparty, donottrack, tp_cookies, disable_flash, browser_debugging,
                profile_tar, timeout, random_attributes):
        # manager parameters
        self.current_profile_path = None
        self.crawl_id = crawl_id
        self.timeout = timeout
        self.db_socket_address = db_socket_address
        
        # constructs dictionary of browser parameters
        self.browser_params = {
            'browser': browser,
            'headless': headless,
            'proxy': proxy,
            'fourthparty': fourthparty,
            'donottrack': donottrack,
            'tp_cookies': tp_cookies,
            'disable_flash': disable_flash,
            'debugging': browser_debugging,
            'crawl_id': crawl_id,
            'profile_tar': profile_tar,
            'random_attributes': random_attributes,
            'timeout': timeout
        }
        
        # Queues and process IDs for BrowserManager
        self.command_thread = None # thread to run commands issues from TaskManager
        self.command_queue = None  # queue for passing command tuples to BrowserManager
        self.status_queue = None  # queue for receiving command execution status from BrowserManager
        self.browser_pid = None  # pid for browser instance controlled by BrowserManager
        self.display_pid = None  # the pid of the display for the headless browser (if it exists)
        
        self.is_fresh = None  # boolean that says if the BrowserManager new (used to optimize restarts)
        self.browser_settings = None # dict of additional browser profile settings (e.g. screen_res)
        
        # start the browser process
        self.browser_manager = self.launch_browser_manager()

    # CRAWLER SETUP / KILL CODE

    # return if the browser is ready to accept a command
    def ready(self):
        if self.command_thread == None or not self.command_thread.is_alive():
            return True
        else:
            return False

    # terminates a BrowserManager, its browser instance and, if necessary, its virtual display
    def kill_browser_manager(self):
        try:
            os.kill(self.browser_manager.pid, signal.SIGKILL)
        except OSError:
            print "Browser manager process already dead"
        if self.display_pid is not None:
            try:
                os.kill(self.display_pid, signal.SIGKILL)
            except OSError:
                print "Display process already dead"
        try:
            os.kill(self.browser_pid, signal.SIGKILL)
        except OSError:
            print "Browser process already dead"

    # sets up the BrowserManager and gets the process id, browser pid and, if applicable, screen pid
    # loads associated user profile if necessary
    # <spawn_timeout> is the timeout for creating BrowserManager
    def launch_browser_manager(self, spawn_timeout=300):
        # if this is restarting from a crash, update the tar location
        # to be a tar of the crashed browser's history
        if self.current_profile_path is not None:
            crashed_profile_path = self.current_profile_path
            # tar contents of crashed profile to a temp dir
            tempdir = tempfile.mkdtemp() + "/"
            profile_commands.dump_profile(crashed_profile_path, tempdir, self.browser_settings, full_profile=True)
            self.browser_params['profile_tar'] = tempdir # make sure browser loads crashed profile
            self.browser_params['random_attributes'] = False # don't re-randomize attributes
        else:
            tempdir = None
            crashed_profile_path = None
        
        # keep trying to spawn a BrowserManager until we have a successful launch within the timeout limit
        browser_manager = None
        successful_spawn = False
        while not successful_spawn:
            # Resets the command/status queues
            (self.command_queue, self.status_queue) = (Queue(), Queue())

            # builds and launches the browser_manager
            args = (self.command_queue, self.status_queue, self.db_socket_address, self.browser_params)
            browser_manager = Process(target=BrowserManager, args=args)
            browser_manager.start()

            # waits for BrowserManager to send success tuple i.e. (current_profile_path, browser pid, display pid)
            for i in xrange(0, int(spawn_timeout) * 1000):
                 # no status for now -> sleep to avoid pegging CPU on blocking get
                if self.status_queue.empty():
                    time.sleep(0.001)
                    continue

                (self.current_profile_path, self.browser_pid, self.display_pid, self.browser_settings) = self.status_queue.get()
                successful_spawn = True
                break

            # kill the BrowserManager if it failed to start up the browser
            if not successful_spawn:
                os.kill(browser_manager.pid, signal.SIGKILL)

        # if recovering from a crash, new browser has a new profile dir
        # so the crashed dir and temporary tar dump can be cleaned up
        if tempdir is not None:
            subprocess.call(["rm", "-r", tempdir])
        if crashed_profile_path is not None:
            subprocess.call(["rm", "-r", crashed_profile_path])

        self.is_fresh = crashed_profile_path is None  # browser is fresh iff it starts from a blank profile
        return browser_manager

    # resets the worker processes with profile to a clean state
    def reset(self):
        if not self.is_fresh:  # optimization in case resetting after a relaunch
            self.restart_browser_manager(reset=True)

    # kill and restart the two worker processes
    # <reset> marks whether we want to wipe the old profile
    def restart_browser_manager(self, reset=False):
        self.kill_browser_manager()

        # in case of reset, hard-deletes old profile
        if reset and self.current_profile_path is not None:
            subprocess.call(["rm", "-r", self.current_profile_path])
            self.current_profile_path = None

        self.browser_manager = self.launch_browser_manager()

def BrowserManager(command_queue, status_queue, db_socket_address, browser_params):
    # sets up the proxy (for now, mitmproxy) if necessary
    proxy_site_queue = None  # used to pass the current site down to the proxy
    if browser_params['proxy']:
        (local_port, proxy_site_queue) = deploy_mitm_proxy.init_proxy(db_socket_address, browser_params['crawl_id'])
        browser_params['proxy'] = local_port

    # Gets the WebDriver, profile folder (i.e. where history/cookies are stored) and display pid (None if not headless)
    (driver, prof_folder, display_pid, browser_settings) = deploy_browser.deploy_browser(browser_params)

    # passes the profile folder, WebDriver pid and display pid back to the TaskManager
    # now, the TaskManager knows that the browser is successfully set up
    status_queue.put((prof_folder, int(driver.binary.process.pid), display_pid, browser_settings))

    # starts accepting arguments until told to die
    while True:
        # no command for now -> sleep to avoid pegging CPU on blocking get
        if command_queue.empty():
            time.sleep(0.001)
            continue

        # reads in the command tuple of form (command, arg0, arg1, arg2, ..., argN) where N is variable
        command = command_queue.get()
        print "EXECUTING COMMAND: " + str(command)

        # attempts to perform an action and return an OK signal
        # if command fails for whatever reason, tell the TaskMaster to kill and restart its worker processes
        try:
            command_executor.execute_command(command, driver, prof_folder, browser_settings, proxy_site_queue)
            status_queue.put("OK")
        except Exception as ex:
            print "CRASH IN DRIVER ORACLE:" + str(ex) + " RESTARTING BROWSER MANAGER"
            status_queue.put("FAILED")
            break
