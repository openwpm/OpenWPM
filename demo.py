from openwpm.command_sequence import CommandSequence
from openwpm.config import BrowserParams, ManagerParams
from openwpm.task_manager import TaskManager

# The list of sites that we wish to crawl
NUM_BROWSERS = 2
sites = [
    "http://www.example.com",
    "http://www.princeton.edu",
    "http://citp.princeton.edu/",
]

# TODO Write documentation/tutorial on how to import custom browser and manager params

# Loads the default manager params
# and NUM_BROWSERS copies of the default browser params
manager_params = ManagerParams()

browser_params = []
for _ in range(NUM_BROWSERS):
    browser_params.append(BrowserParams(display_mode="headless"))

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    browser_params[i].http_instrument = True
    # Record cookie changes
    browser_params[i].cookie_instrument = True
    # Record Navigations
    browser_params[i].navigation_instrument = True
    # Record JS Web API calls
    browser_params[i].js_instrument = True
    # Record the callstack of all WebRequests made
    browser_params[i].callstack_instrument = True
    # Record DNS resolution
    browser_params[i].dns_instrument = True

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params.data_directory = "~/Desktop/"
manager_params.log_directory = "~/Desktop/"

# memory_watchdog and process_watchdog are useful for large scale cloud crawls.
# Please refer to docs/Configuration.md#platform-configuration-options for more information
# manager_params.memory_watchdog = True
# manager_params.process_watchdog = True

# This assignment is necessary to let TaskManager know how many browsers to spawn
manager_params.num_browsers = NUM_BROWSERS

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager(manager_params, browser_params)

# Visits the sites
for site in sites:

    # Parallelize sites over all number of browsers set above.
    command_sequence = CommandSequence(
        site,
        reset=True,
        callback=lambda success, val=site: print("CommandSequence {} done".format(val)),
    )

    # Start by visiting the page
    command_sequence.get(sleep=3, timeout=60)

    # Run commands across the three browsers (simple parallelization)
    manager.execute_command_sequence(command_sequence)

# Shuts down the browsers and waits for the data to finish logging
manager.close()
