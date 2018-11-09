from __future__ import absolute_import

from six.moves import range

from automation import CommandSequence, TaskManager

import time

from get_sites import update_last_scanned, get_urls_to_inspect


# The list of sites that we wish to crawl
#days_ago_3 = int(time.time()) - 86400*3
#update_last_scanned(days_ago_3)
NUM_BROWSERS = 3
sites = get_urls_to_inspect()
print(sites)
#sites = ['http://www.example.com',
#         'http://www.princeton.edu',
#         'http://citp.princeton.edu/']

# Loads the manager preference and 3 copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    browser_params[i]['http_instrument'] = True
    # Enable flash for all three browsers
    browser_params[i]['disable_flash'] = False
browser_params[0]['headless'] = True  # Launch only browser 0 headless

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '~/Desktop/'
manager_params['log_directory'] = '~/Desktop/'

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

#TODO: Some check that inspection was successful
if True:
    cur_time = int(time.time())
    update_last_scanned(cur_time)
