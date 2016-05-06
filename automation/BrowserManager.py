from Commands import command_executor
from DeployBrowsers import deploy_browser
from Commands import profile_commands
from Proxy import deploy_mitm_proxy
from SocketInterface import clientsocket
from MPLogger import loggingclient
from Errors import ProfileLoadError, BrowserConfigError, BrowserCrashError

from multiprocessing import Process, Queue
from Queue import Empty as EmptyQueue
from tblib import pickling_support
pickling_support.install()
from six import reraise
import traceback
import tempfile
import cPickle
import shutil
import signal
import time
import sys
import os

class Browser:
    """
     The Browser class is responsbile for holding all of the
     configuration and status information on BrowserManager process
     it corresponds to. It also includes a set of methods for managing
     the BrowserManager process and its child processes/threads.
     <manager_params> are the TaskManager configuration settings.
     <browser_params> are per-browser parameter settings (e.g. whether
                      this browser is using a proxy, headless, etc.)
     """
    def __init__(self, manager_params, browser_params):
        # Constants
        self._SPAWN_TIMEOUT = 120 #seconds
        self._UNSUCCESSFUL_SPAWN_LIMIT = 4

        # manager parameters
        self.current_profile_path = None
        self.db_socket_address = manager_params['aggregator_address']
        self.logger_address = manager_params['logger_address']
        self.crawl_id = browser_params['crawl_id']
        self.curr_visit_id = None
        self.browser_params = browser_params
        self.manager_params = manager_params

        # Queues and process IDs for BrowserManager
        self.command_thread = None  # thread to run commands issues from TaskManager
        self.command_queue = None  # queue for passing command tuples to BrowserManager
        self.status_queue = None  # queue for receiving command execution status from BrowserManager
        self.browser_pid = None  # pid for browser instance controlled by BrowserManager
        self.display_pid = None  # the pid of the display for the headless browser (if it exists)
        self.display_port = None  # the port of the display for the headless browser (if it exists)

        self.is_fresh = True  # boolean that says if the BrowserManager new (used to optimize restarts)
        self.restart_required = False # boolean indicating if the browser should be restarted

        self.current_timeout = None # timeout of the current command
        self.browser_settings = None  # dict of additional browser profile settings (e.g. screen_res)
        self.browser_manager = None # process that controls browser
        self.logger = loggingclient(*self.logger_address) # connection to loggingserver

    def ready(self):
        """ return if the browser is ready to accept a command """
        return self.command_thread is None or not self.command_thread.is_alive()

    def set_visit_id(self, visit_id):
        self.curr_visit_id = visit_id

    def launch_browser_manager(self):
        """
        sets up the BrowserManager and gets the process id, browser pid and, if applicable, screen pid
        loads associated user profile if necessary
        """
        # if this is restarting from a crash, update the tar location
        # to be a tar of the crashed browser's history
        if self.current_profile_path is not None:
            # tar contents of crashed profile to a temp dir
            tempdir = tempfile.mkdtemp() + "/"
            profile_commands.dump_profile(self.current_profile_path,
                                          self.manager_params,
                                          self.browser_params,
                                          tempdir,
                                          close_webdriver=False,
                                          browser_settings=self.browser_settings)
            self.browser_params['profile_tar'] = tempdir  # make sure browser loads crashed profile
            self.browser_params['random_attributes'] = False  # don't re-randomize attributes
            crash_recovery = True
        else:
            tempdir = None
            crash_recovery = False
        self.is_fresh = not crash_recovery

        # Try to spawn the browser within the timelimit
        unsuccessful_spawns = 0
        success = False

        def check_queue(launch_status):
            result = self.status_queue.get(True, self._SPAWN_TIMEOUT)
            if result[0] == 'STATUS':
                launch_status[result[1]] = True
                return result[2]
            elif result[0] == 'CRITICAL':
                reraise(*cPickle.loads(result[1]))
            elif result[0] == 'FAILED':
                raise BrowserCrashError('Browser spawn returned failure status')

        while not success and unsuccessful_spawns < self._UNSUCCESSFUL_SPAWN_LIMIT:
            self.logger.debug("BROWSER %i: Spawn attempt %i " % (self.crawl_id, unsuccessful_spawns))
            # Resets the command/status queues
            (self.command_queue, self.status_queue) = (Queue(), Queue())

            # builds and launches the browser_manager
            args = (self.command_queue, self.status_queue, self.browser_params, self.manager_params, crash_recovery)
            self.browser_manager = Process(target=BrowserManager, args=args)
            self.browser_manager.daemon = True
            self.browser_manager.start()

            # Read success status of browser manager
            launch_status = dict()
            try:
                check_queue(launch_status) # proxy enabled (if necessary)
                spawned_profile_path = check_queue(launch_status) # selenium profile created
                check_queue(launch_status) # profile tar loaded (if necessary)
                (self.display_pid, self.display_port) = check_queue(launch_status) # Display launched
                check_queue(launch_status) # browser launch attempted
                (self.browser_pid, self.browser_settings) = check_queue(launch_status) # Browser launched
                if check_queue(launch_status) != 'READY':
                    self.logger.error("BROWSER %i: Mismatch of status queue return values, trying again..." % self.crawl_id)
                    unsuccessful_spawns += 1
                    continue
                success = True
            except (EmptyQueue, BrowserCrashError):
                unsuccessful_spawns += 1
                error_string = ''
                status_strings = ['Proxy Ready','Profile Created','Profile Tar','Display','Launch Attempted', 'Browser Launched', 'Browser Ready']
                for string in status_strings:
                    error_string += " | %s: %s " % (string, launch_status.get(string, False))
                self.logger.error("BROWSER %i: Spawn unsuccessful %s" % (self.crawl_id, error_string))
                self.kill_browser_manager()
                if launch_status.has_key('Profile Created'):
                    shutil.rmtree(spawned_profile_path, ignore_errors=True)

        # If the browser spawned successfully, we should update the
        # current profile path class variable and clean up the tempdir
        # and previous profile path.
        if success:
            self.logger.debug("BROWSER %i: Browser spawn sucessful!" % self.crawl_id)
            previous_profile_path = self.current_profile_path
            self.current_profile_path = spawned_profile_path
            if previous_profile_path is not None:
                shutil.rmtree(previous_profile_path, ignore_errors=True)
            if tempdir is not None:
                shutil.rmtree(tempdir, ignore_errors=True)

        return success

    def restart_browser_manager(self, clear_profile=False):
        """
        kill and restart the two worker processes
        <clear_profile> marks whether we want to wipe the old profile
        """
        if self.is_fresh: # Return success if browser is fresh
            return True

        self.kill_browser_manager()

        # if crawl should be stateless we can clear profile
        if clear_profile and self.current_profile_path is not None:
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

    def shutdown_browser(self, during_init):
        """ Runs the closing tasks for this Browser/BrowserManager """
        # Join command thread
        if self.command_thread is not None:
            self.logger.debug("BROWSER %i: Joining command thread" % self.crawl_id)
            start_time = time.time()
            if self.current_timeout is not None:
                self.command_thread.join(self.current_timeout + 10)
            else:
                self.command_thread.join(60)
            self.logger.debug("BROWSER %i: %f seconds to join command thread" % (self.crawl_id, time.time() - start_time))

        # Kill BrowserManager process and children
        self.logger.debug("BROWSER %i: Killing browser manager..." % self.crawl_id)
        self.kill_browser_manager()

        # Archive browser profile (if requested)
        self.logger.debug("BROWSER %i: during_init=%s | profile_archive_dir=%s" % (self.crawl_id, str(during_init), self.browser_params['profile_archive_dir']))
        if not during_init and self.browser_params['profile_archive_dir'] is not None:
            self.logger.debug("BROWSER %i: Archiving browser profile directory to %s" % (self.crawl_id, self.browser_params['profile_archive_dir']))
            profile_commands.dump_profile(self.current_profile_path,
                                          self.manager_params,
                                          self.browser_params,
                                          self.browser_params['profile_archive_dir'],
                                          close_webdriver=False,
                                          browser_settings=self.browser_settings,
                                          compress=True,
                                          save_flash=self.browser_params['disable_flash'] is False)

        # Clean up temporary files
        if self.current_profile_path is not None:
            shutil.rmtree(self.current_profile_path, ignore_errors = True)

def BrowserManager(command_queue, status_queue, browser_params, manager_params, crash_recovery):
    """
    The BrowserManager function runs in each new browser process.
    It is responsible for listening to command instructions from
    the Task Manager and passing them to the command module to execute
    and interface with Selenium. Command execution status is sent back
    to the TaskManager.
    """
    try:
        logger = loggingclient(*manager_params['logger_address'])

        # Start the proxy
        proxy_site_queue = None  # used to pass the current site down to the proxy
        if browser_params['proxy']:
            (local_port, proxy_site_queue) = deploy_mitm_proxy.init_proxy(browser_params,
                                                                          manager_params,
                                                                          status_queue)
            browser_params['proxy'] = local_port
        status_queue.put(('STATUS','Proxy Ready','READY'))

        # Start the virtualdisplay (if necessary), webdriver, and browser
        (driver, prof_folder, browser_settings) = deploy_browser.deploy_browser(status_queue, browser_params, manager_params, crash_recovery)

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
        status_queue.put(('STATUS','Browser Ready','READY'))
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
            command_executor.execute_command(command,
                                             driver,
                                             proxy_site_queue,
                                             browser_settings,
                                             browser_params,
                                             manager_params,
                                             extension_socket)
            status_queue.put("OK")

    except (ProfileLoadError, BrowserConfigError) as e:
        logger.info("BROWSER %i: %s thrown, informing parent and raising" %
                (browser_params['crawl_id'], e.__class__.__name__))
        err_info = sys.exc_info()
        status_queue.put(('CRITICAL',cPickle.dumps(err_info)))
        return
    except Exception as e:
        excp = traceback.format_exception(*sys.exc_info())
        logger.info("BROWSER %i: Crash in driver, restarting browser manager \n %s" % (browser_params['crawl_id'], ''.join(excp)))
        status_queue.put(('FAILED',None))
        return
