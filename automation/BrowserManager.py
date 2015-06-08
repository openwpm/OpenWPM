from Commands import command_executor
from DeployBrowsers import deploy_browser
from Commands import profile_commands
from Proxy import deploy_mitm_proxy
from SocketInterface import clientsocket
from MPLogger import loggingclient

from multiprocessing import Process, Queue
from Queue import Empty as EmptyQueue
import tempfile
import logging
import shutil
import signal
import time
import os


class Browser:
    """
     Sets up a WebDriver instance that adheres to a given set of user paramters
     Continually listens to the TaskManager for commands and passes them to command module to execute
     Sends OK signal if command succeeds or else sends a FAILED signal to indicate that workers should be restarted

     <command_queue> is the queue through which the browser sends command tuples
     <status_queue> is a queue through which the BrowserManager either signals command failure or success
     <db_socket_address> is the socket address through which to send data to the DataAggregator to manipulate and write
     <browser_params> are browser parameter settings (e.g. whether we're using a proxy, headless, etc.)

     """
    def __init__(self, browser_params):
        # manager parameters
        self.current_profile_path = None
        self.db_socket_address = browser_params['aggregator_address']
        self.logger_address = browser_params['logger_address']
        self.crawl_id = browser_params['crawl_id']
        self.browser_params = browser_params
        
        # Queues and process IDs for BrowserManager
        self.command_thread = None  # thread to run commands issues from TaskManager
        self.command_queue = None  # queue for passing command tuples to BrowserManager
        self.status_queue = None  # queue for receiving command execution status from BrowserManager
        self.browser_pid = None  # pid for browser instance controlled by BrowserManager
        self.display_pid = None  # the pid of the display for the headless browser (if it exists)
        self.display_port = None  # the port of the display for the headless browser (if it exists)
        
        self.is_fresh = None  # boolean that says if the BrowserManager new (used to optimize restarts)
        self.current_timeout = None # timeout of the current command
        self.browser_settings = None  # dict of additional browser profile settings (e.g. screen_res)
        self.browser_manager = None # process that controls browser
        self.logger = loggingclient(*self.logger_address) # connection to loggingserver

    def ready(self):
        """ return if the browser is ready to accept a command """
        return self.command_thread is None or not self.command_thread.is_alive()

    def launch_browser_manager(self, spawn_timeout=120):
        """
        sets up the BrowserManager and gets the process id, browser pid and, if applicable, screen pid
        loads associated user profile if necessary
        <spawn_timeout> is the timeout for creating BrowserManager
        """
        # if this is restarting from a crash, update the tar location
        # to be a tar of the crashed browser's history
        if self.current_profile_path is not None:
            crashed_profile_path = self.current_profile_path
            # tar contents of crashed profile to a temp dir
            tempdir = tempfile.mkdtemp() + "/"
            profile_commands.dump_profile(crashed_profile_path, tempdir, close_webdriver=False,
                                          browser_settings=self.browser_settings, full_profile=True)
            self.browser_params['profile_tar'] = tempdir  # make sure browser loads crashed profile
            self.browser_params['random_attributes'] = False  # don't re-randomize attributes
            crash_recovery = True
        else:
            tempdir = None
            crashed_profile_path = None
            crash_recovery = False
        
        # Try to spawn the browser within the timelimit
        unsuccessful_spawns = 0
        retry = False
        success = False
        while not success and unsuccessful_spawns < 4:
            self.logger.debug("BROWSER %i: Spawn attempt %i " % (self.crawl_id, unsuccessful_spawns))
            # Resets the command/status queues
            (self.command_queue, self.status_queue) = (Queue(), Queue())

            # builds and launches the browser_manager
            args = (self.command_queue, self.status_queue, self.browser_params, crash_recovery)
            self.browser_manager = Process(target=BrowserManager, args=args)
            self.browser_manager.daemon = True
            self.browser_manager.start()

            # Read success status of browser manager
            prof_done = disp_done = browser_done = ready_done = launch_attempted = False
            try:
                self.current_profile_path = self.status_queue.get(True, spawn_timeout)
                prof_done = True
                (self.display_pid, self.display_port) = self.status_queue.get(True, spawn_timeout)
                disp_done = True
                useless = self.status_queue.get(True, spawn_timeout)
                launch_attempted = True
                (self.browser_pid, self.browser_settings) = self.status_queue.get(True, spawn_timeout)
                browser_done = True
                if self.status_queue.get(True, spawn_timeout) != 'READY':
                    self.logger.error("BROWSER %i: Mismatch of status queue return values, trying again..." % self.crawl_id)
                    unsuccessful_spawns += 1
                    continue
                success = True
            except EmptyQueue:
                unsuccessful_spawns += 1
                self.logger.error("BROWSER %i: Spawn unsuccessful | Profile: %s | Display: %s | Launch attempted: %s | Browser: %s" %
                        (self.crawl_id, str(prof_done), str(disp_done), str(launch_attempted), str(browser_done)))
                self.kill_browser_manager()
                if self.current_profile_path is not None:
                    shutil.rmtree(self.current_profile_path, ignore_errors=True)

        # if recovering from a crash, new browser has a new profile dir
        # so the crashed dir and temporary tar dump can be cleaned up
        if success:
            self.logger.debug("BROWSER %i: Browser spawn sucessful!" % self.crawl_id)
            if tempdir is not None:
                shutil.rmtree(tempdir, ignore_errors=True)
            if crashed_profile_path is not None:
                shutil.rmtree(crashed_profile_path, ignore_errors=True)

            self.is_fresh = crashed_profile_path is None  # browser is fresh iff it starts from a blank profile
        
        return success

    def reset(self):
        """ resets the worker processes with profile to a clean state """
        if not self.is_fresh:  # optimization in case resetting after a relaunch
            self.restart_browser_manager(reset=True)

    def restart_browser_manager(self, reset=False):
        """
        kill and restart the two worker processes
        <reset> marks whether we want to wipe the old profile
        """
        self.kill_browser_manager()

        # in case of reset, hard-deletes old profile
        if reset and self.current_profile_path is not None:
            shutil.rmtree(self.current_profile_path, ignore_errors=True)
            self.current_profile_path = None
            self.browser_params['profile_tar'] = None

        return self.launch_browser_manager()

    # terminates a BrowserManager, its browser instance and, if necessary, its virtual display
    def kill_browser_manager(self):
        if self.browser_manager is not None and self.browser_manager.pid is not None:
            try:
                os.kill(self.browser_manager.pid, signal.SIGKILL)
            except OSError:
                self.logger.debug("BROWSER %i: Browser manager process does not exist" % self.crawl_id)
                pass
        if self.display_pid is not None:
            try:
                os.kill(self.display_pid, signal.SIGKILL)
            except OSError:
                self.logger.debug("BROWSER %i: Display process does not exit" % self.crawl_id)
                pass
            except TypeError:
                self.logger.error("BROWSER %i: PID may not be the correct type %s" % (self.crawl_id, str(self.display_pid)))
        if self.display_port is not None: # xvfb diplay lock
            try:
                os.remove("/tmp/.X"+str(self.display_port)+"-lock")
            except OSError:
                self.logger.debug("BROWSER %i: Screen lockfile already removed" % self.crawl_id)
                pass
        if self.browser_pid is not None:
            try:
                os.kill(self.browser_pid, signal.SIGKILL)
            except OSError:
                self.logger.debug("BROWSER %i: Browser process does not exist" % self.crawl_id)
                pass

def BrowserManager(command_queue, status_queue, browser_params, crash_recovery):
    logger = loggingclient(*browser_params['logger_address'])
    
    # Start the proxy
    proxy_site_queue = None  # used to pass the current site down to the proxy
    if browser_params['proxy']:
        (local_port, proxy_site_queue) = deploy_mitm_proxy.init_proxy(browser_params['aggregator_address'],
                                                                      browser_params['logger_address'],
                                                                      browser_params['crawl_id'])
        browser_params['proxy'] = local_port

    # Start the virtualdisplay (if necessary), webdriver, and browser
    (driver, prof_folder, browser_settings) = deploy_browser.deploy_browser(status_queue, browser_params, crash_recovery)

    # Read the extension port -- if extension is enabled
    # TODO: This needs to be cleaner
    if browser_params['browser'] == 'firefox' and browser_params['extension']['enabled']:
        logger.debug("BROWSER %i: Looking for extension port information in %s" % (browser_params['crawl_id'], prof_folder))
        while not os.path.isfile(prof_folder + 'extension_port.txt'):
            time.sleep(0.1)
        time.sleep(0.5)
        with open(prof_folder + 'extension_port.txt', 'r') as f:
            port = f.read().strip()
        extension_socket = clientsocket()
        extension_socket.connect('127.0.0.1',int(port))
    else:
        extension_socket = None

    # passes the profile folder, WebDriver pid and display pid back to the TaskManager
    # now, the TaskManager knows that the browser is successfully set up
    status_queue.put('READY')
    browser_params['profile_path'] = prof_folder

    # starts accepting arguments until told to die
    while True:
        # no command for now -> sleep to avoid pegging CPU on blocking get
        if command_queue.empty():
            time.sleep(0.001)
            continue

        # reads in the command tuple of form (command, arg0, arg1, arg2, ..., argN) where N is variable
        command = command_queue.get()
        logger.info("BROWSER %i: EXECUTING COMMAND: %s" % (browser_params['crawl_id'], str(command)))

        # attempts to perform an action and return an OK signal
        # if command fails for whatever reason, tell the TaskMaster to kill and restart its worker processes
        try:
            command_executor.execute_command(command, driver, proxy_site_queue, browser_settings, browser_params, extension_socket)
            status_queue.put("OK")
        except Exception as e:
            logger.info("BROWSER %i: Crash in driver, restarting browser manager \n %s \n %s" % (browser_params['crawl_id'], str(type(e)), str(e)))
            status_queue.put("FAILED")
            break
