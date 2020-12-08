import logging
import os
from pathlib import Path

from openwpm.command_sequence import CommandSequence
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.cloud_storage.gcp_storage import (
    GcsStructuredProvider,
    GcsUnstructuredProvider,
)
from openwpm.storage.sql_provider import SqlLiteStorageProvider
from openwpm.task_manager import TaskManager

# The list of sites that we wish to crawl
NUM_BROWSERS = 1
sites = [
    "http://www.example.com",
    "http://www.princeton.edu",
    "http://citp.princeton.edu/",
]

# Loads the default ManagerParams
# and NUM_BROWSERS copies of the default BrowserParams

manager_params = ManagerParams(
    num_browsers=NUM_BROWSERS
)  # num_browsers is necessary to let TaskManager know how many browsers to spawn

browser_params = [BrowserParams(display_mode="headless") for _ in range(NUM_BROWSERS)]

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
manager_params.data_directory = Path("./datadir/")
manager_params.log_directory = Path("./datadir/")

logging_params = {"log_level_console": logging.DEBUG}
# memory_watchdog and process_watchdog are useful for large scale cloud crawls.
# Please refer to docs/Configuration.md#platform-configuration-options for more information
# manager_params.memory_watchdog = True
# manager_params.process_watchdog = True

# Instantiates the measurement platform
project = "senglehardt-openwpm-test-1"
bucket_name = "openwpm-test-bucket"
# Commands time out by default after 60 seconds
manager = TaskManager(
    manager_params,
    browser_params,
    GcsStructuredProvider(
        project=project,
        bucket_name=bucket_name,
        base_path="demo/visits",
        token="/home/stefan/.config/gcloud/legacy_credentials/szabka@mozilla.com/adc.json",
    ),
    None,
)

# Visits the sites
for index, site in enumerate(sites):

    def callback(success: bool, val: str = site) -> None:
        print("CommandSequence {} done".format(val))

    # Parallelize sites over all number of browsers set above.
    command_sequence = CommandSequence(
        site, site_rank=index, reset=True, callback=callback,
    )

    # Start by visiting the page
    command_sequence.get(sleep=3, timeout=60)

    # Run commands across the three browsers (simple parallelization)
    manager.execute_command_sequence(command_sequence)

# Shuts down the browsers and waits for the data to finish logging
manager.close()
