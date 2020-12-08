import logging
import os

from openwpm.command_sequence import CommandSequence
from openwpm.storage.cloud_storage.gcp_storage import (
    GcsStructuredProvider,
    GcsUnstructuredProvider,
)
from openwpm.storage.sql_provider import SqlLiteStorageProvider
from openwpm.task_manager import TaskManager, load_default_params

# The list of sites that we wish to crawl
NUM_BROWSERS = 1
sites = [
    "http://www.example.com",
    "http://www.princeton.edu",
    "http://citp.princeton.edu/",
]

# Loads the default manager params
# and NUM_BROWSERS copies of the default browser params
manager_params, browser_params = load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    browser_params[i]["http_instrument"] = True
    # Record cookie changes
    browser_params[i]["cookie_instrument"] = True
    # Record Navigations
    browser_params[i]["navigation_instrument"] = True
    # Record JS Web API calls
    browser_params[i]["js_instrument"] = True
    # Record the callstack of all WebRequests made
    browser_params[i]["callstack_instrument"] = True
    # Record DNS resolution
    browser_params[i]["dns_instrument"] = True


# Launch only browser 0 headless
# browser_params[0]["display_mode"] = "headless"

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params["data_directory"] = "./datadir/"
manager_params["log_directory"] = "./datadir/"

logging_params = {"log_level_console": logging.DEBUG}

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
        site,
        site_rank=index,
        reset=True,
        callback=callback,
    )

    # Start by visiting the page
    command_sequence.get(sleep=3, timeout=60)

    # Run commands across the three browsers (simple parallelization)
    manager.execute_command_sequence(command_sequence)

# Shuts down the browsers and waits for the data to finish logging
manager.close()
