from __future__ import absolute_import
from automation import TaskManager, CommandSequence

# The list of sites that we wish to crawl
NUM_BROWSERS = 1
sites = ['http://www.example.com',
         'http://www.princeton.edu',
         'http://citp.princeton.edu/']

manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

browser_params[0]['http_instrument'] = True
browser_params[0]['ublock-origin'] = True
browser_params[0]['headless'] = False

manager_params['data_directory'] = '~/Desktop/'
manager_params['log_directory'] = '~/Desktop/'

manager = TaskManager.TaskManager(manager_params, browser_params)

for site in sites:
    command_sequence = CommandSequence.CommandSequence(site)
    command_sequence.get(sleep=120, timeout=60)
    manager.execute_command_sequence(command_sequence)

manager.close()
