from automation import TaskManager
import time
import os

# The list of sites that we wish to crawl
NUM_BROWSERS = 3
sites = ['http://www.example.com',
         'http://www.princeton.edu',
         'https://citp.princeton.edu/']

# Saves a crawl output DB to the Desktop
db_loc  = os.path.expanduser('~/Desktop/openwpm_demo.sqlite')

# Loads 3 copies of the default browser preference dictionaries
browser_params = TaskManager.load_default_params(NUM_BROWSERS)

#Enable flash for all three browsers
for i in xrange(NUM_BROWSERS):
    browser_params[i]['disable_flash'] = False

#Launch the first browser headless
browser_params[0]['headless'] = True

# Instantiates the measurement platform
# Launches two (non-headless) Firefox instances and one headless instance
# logging data with MITMProxy
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(db_loc, browser_params, NUM_BROWSERS)

# Visits the sites with both browsers simultaneously, 5 seconds between visits
for site in sites:
    manager.get(site, index='**') # ** = synchronized browsers
    time.sleep(5)

# Shuts down the browsers and waits for the data to finish logging
manager.close()
