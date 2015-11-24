import browser_commands
import profile_commands


def execute_command(command, webdriver, proxy_queue, browser_settings, browser_params, manager_params, extension_socket):
    """
    executes BrowserManager commands by passing command tuples into necessary helper function
    commands are of form (COMMAND, ARG0, ARG1, ...)
    the only imports in this file should be imports to helper libraries
    """
    if command[0] == 'GET':
        browser_commands.get_website(command[1], command[2], webdriver,
                                     proxy_queue, browser_params, extension_socket)
        
    if command[0] == 'BROWSE':
        browser_commands.browse_website(command[1], command[2], command[3], webdriver,
                                        proxy_queue, browser_params, manager_params,
                                        extension_socket)
   
    if command[0] == 'DUMP_STORAGE_VECTORS':
        browser_commands.dump_storage_vectors(command[1], command[2], command[3], webdriver,
                                              browser_params, manager_params)

    if command[0] == 'DUMP_PROF':
        profile_commands.dump_profile(browser_params['profile_path'], manager_params,
                                      browser_params, command[1], command[2], webdriver,
                                      browser_settings, compress=command[3],
                                      save_flash=browser_params['disable_flash'] is False)

    if command[0] == 'EXTRACT_LINKS':
        browser_commands.extract_links(webdriver, browser_params, manager_params)
