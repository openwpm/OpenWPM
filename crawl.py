from automation import TaskManager, CommandSequence
from selenium.webdriver.common.keys import Keys

import time

def fill_input_elements(email, password, **kwargs):
    """use webdriver to fill input elements"""
    driver = kwargs['webdriver']
    email_input = driver.find_element_by_id('theEmail')
    email_input.send_keys(email)

    pass_input = driver.find_element_by_id('thePassword')
    pass_input.send_keys(password)
    pass_input.send_keys(Keys.TAB)

manager_params, browser_params = TaskManager.load_default_params(1)

browser_params[0]['headless'] = False
browser_params[0]['proxy'] = False

manager_params['data_directory'] = '~/Desktop/'
manager_params['log_directory'] = '~/Desktop/'

manager = TaskManager.TaskManager(manager_params, browser_params)

site = 'localtest.me:8000/test_custom_function.html'
command_sequence = CommandSequence.CommandSequence(site)
command_sequence.get(sleep=0, timeout=60)
command_sequence.run_custom_function(fill_input_elements, ('example@example.com', 'hunter2'))
manager.execute_command_sequence(command_sequence, index='**') # ** = synchronized browsers
time.sleep(10)

manager.close()
