import browser_commands
import profile_commands

# executes BrowserManager commands by passing command tuples into necessary helper function
# commands are of form (COMMAND, ARG0, ARG1, ...)
# the only imports in this file should be imports to helper libraries
# the only function should be execute_command, which is just a series of branch statements for executing commands

def execute_command(command, webdriver, proxy_queue, browser_settings, browser_params):
    if command[0] == 'GET':
        browser_commands.get_website(command[1], webdriver, proxy_queue, browser_params)
    
    if command[0] == 'DUMP_STORAGE_VECTORS':
        browser_commands.dump_storage_vectors(command[1], command[2], browser_params)

    if command[0] == 'DUMP_PROF':
        profile_commands.dump_profile(browser_params['profile_path'],
                                      command[1], command[2], webdriver, browser_settings)
