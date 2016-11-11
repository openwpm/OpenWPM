from automation import TaskManager, CommandSequence
import time

NUM_BROWSERS = 1
sites = ['http://twitter.com',
         'http://twitter.com']

manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

for i in xrange(NUM_BROWSERS):
    browser_params[i]['proxy'] = True
    browser_params[i]['extension']['enabled'] = True
    browser_params[i]['extension']['jsInstrument'] = True # Using this + proxy so we can compare

manager_params['data_directory'] = '~/Desktop/'
manager_params['log_directory'] = '~/Desktop/'

manager = TaskManager.TaskManager(manager_params, browser_params)

for site in sites:
    command_sequence = CommandSequence.CommandSequence(site)
    command_sequence.get(sleep=10, timeout=60)
    manager.execute_command_sequence(command_sequence)

manager.close()
