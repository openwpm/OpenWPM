from __future__ import absolute_import

from sys import platform

from six.moves import range

from automation import CommandSequence, TaskManager

import os
from test.utilities import local_s3_bucket, download_s3_directory

# The list of sites that we wish to crawl
NUM_BROWSERS = 3
sites = ['http://www.example.com',
         'http://www.princeton.edu',
         'http://citp.princeton.edu/']

# Loads the manager preference and 3 copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    browser_params[i]['http_instrument'] = True
    # Enable flash for all three browsers
    browser_params[i]['disable_flash'] = False
if platform != 'darwin':
    browser_params[0]['headless'] = True  # Launch only browser 0 headless

# Update TaskManager configuration (use this for crawl-wide settings)
# Requires that `SERVICES=s3 localstack start` has been started
manager_params['output_format'] = 's3'
manager_params['s3_bucket'] = local_s3_bucket()
manager_params['s3_directory'] = 'demo-local-s3'

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(manager_params, browser_params)

# Visits the sites with all browsers simultaneously
for site in sites:
    command_sequence = CommandSequence.CommandSequence(site)

    # Start by visiting the page
    command_sequence.get(sleep=0, timeout=60)

    # dump_profile_cookies/dump_flash_cookies closes the current tab.
    command_sequence.dump_profile_cookies(120)

    # index='**' synchronizes visits between the three browsers
    manager.execute_command_sequence(command_sequence, index='**')

# Shuts down the browsers and waits for the data to finish logging
manager.close()

# Copy the resulting S3 contents to ./local-s3-data
print("Copying the resulting S3 contents...")
root_dir = os.path.dirname(__file__)
destination = os.path.join(root_dir, 'local-s3-data')
download_s3_directory(
    manager_params['s3_directory'],
    destination,
    manager_params['s3_bucket'])
print("Copied the resulting S3 contents to ./local-s3-data")
