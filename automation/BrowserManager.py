from Commands import command_executor
from DeployBrowsers import deploy_browser
from Proxy import deploy_mitm_proxy

import time

# Sets up a WebDriver instance that adheres to a given set of user paramters
# Continually listens to the TaskManager for commands and passes them to command module to execute
# Sends OK signal if command succeeds or else sends a FAILED signal to indicate that workers should be restarted
# TODO: this approach may be too coarse

# <command_queue> is the queue through which the browser sends command tuples
# <status_queue> is a queue through which the BrowserManager either signals command failure or success
# <db_socket_address> is the socket address through which to send data to the DataAggregator to manipulate and write
# <browser_params> are browser parameter settings (e.g. whether we're using a proxy, headless, etc.)

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
            status_queue.put("OK")
        except Exception as ex:
            print "CRASH IN DRIVER ORACLE:" + str(ex) + " RESTARTING BROWSER MANAGER"
            status_queue.put("FAILED")
            break
