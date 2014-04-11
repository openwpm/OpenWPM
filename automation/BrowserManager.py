from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
                fourthparty, browser_debugging, profile, timeout):
        # manager parameters
        self.profile_path = profile
        self.crawl_id = crawl_id
        self.timeout = timeout
        self.db_socket_address = db_socket_address
        
        # constructs dictionary of browser parameters
        self.browser_params = {
            'browser': browser,
            'headless': headless,
            'proxy': proxy,
            'fourthparty': fourthparty,
            'debugging': browser_debugging,
            'crawl_id': crawl_id
        }
        
        # Queues and process IDs for BrowserManager
        self.command_thread = None # thread to run commands issues from TaskManager
        self.command_queue = None  # queue for passing command tuples to BrowserManager
        self.status_queue = None  # queue for receiving command execution status from BrowserManager
        self.browser_pid = None  # pid for browser instance controlled by BrowserManager
        self.display_pid = None  # the pid of the display for the headless browser (if it exists)
        self.is_fresh = None  # boolean that says if the BrowserManager new (used to optimize restarts)
        
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
        os.kill(self.browser_manager.pid, signal.SIGKILL)
        if self.display_pid is not None:
            os.kill(self.display_pid, signal.SIGKILL)
        os.kill(self.browser_pid, signal.SIGKILL)

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
            (self.command_queue, self.status_queue) = (Queue(), Queue())

            # builds and launches the browser_manager
            browser_manager = Process(target=BrowserManager,
                                      args=(self.command_queue, self.status_queue,
                                            self.db_socket_address, self.browser_params, ))
            browser_manager.start()

            # waits for BrowserManager to send success tuple i.e. (profile_path, browser pid, display pid)
            for i in xrange(0, int(spawn_timeout) * 1000):
                 # no status for now -> sleep to avoid pegging CPU on blocking get
                if self.status_queue.empty():
                    time.sleep(0.001)
                    continue

                (self.profile_path, self.browser_pid, self.display_pid) = self.status_queue.get()
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

    # resets the worker processes with profile to a clean state
    def reset(self):
        if not self.is_fresh:  # optimization in case resetting after a relaunch
            self.restart_workers(reset=True)

    # kill and restart the two worker processes
    # <reset> marks whether we want to wipe the old profile
    def restart_browser_manager(self, reset=False):
        self.kill_browser_manager()

        # in case of reset, hard-deletes old profile
        if reset and self.profile_path is not None:
            subprocess.call(["rm", "-r", self.profile_path])
            self.profile_path = None

        self.browser_manager = self.launch_browser_manager()

def BrowserManager(command_queue, status_queue, db_socket_address, browser_params):
    # sets up the proxy (for now, mitmproxy) if necessary
    proxy_site_queue = None  # used to pass the current site down to the proxy
    if browser_params['proxy']:
        (local_port, proxy_site_queue) = deploy_mitm_proxy.init_proxy(db_socket_address, browser_params['crawl_id'])
        browser_params['proxy'] = local_port

    # Gets the WebDriver, profile folder (i.e. where history/cookies are stored) and display pid (None if not headless)
    (driver, prof_folder, display_pid) = deploy_browser.deploy_browser(browser_params)

    # passes the profile folder, WebDriver pid and display pid back to the TaskManager
    # now, the TaskManager knows that the browser is successfully set up
    status_queue.put((prof_folder, int(driver.binary.process.pid), display_pid))

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
            command_executor.execute_command(command, driver, prof_folder, proxy_site_queue)

            # This is a fix for when selenium claims it is done loading but actually isn't
            # TODO: make this not dependent on selenium - get the right timeout?
            element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            element.send_keys("Keys.ESCAPE") #Make sure it is really done loading

            status_queue.put("OK")
        except Exception as ex:
            print "CRASH IN DRIVER ORACLE:" + str(ex) + " RESTARTING BROWSER MANAGER"
            status_queue.put("FAILED")
            break
