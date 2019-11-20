
from . import browser_commands, profile_commands


def execute_command(command, webdriver, browser_settings, browser_params,
                    manager_params, extension_socket):
    """Executes BrowserManager commands
    commands are of form (COMMAND, ARG0, ARG1, ...)
    """
    if command[0] == 'GET':
        browser_commands.get_website(
            url=command[1], sleep=command[2], visit_id=command[3],
            webdriver=webdriver, browser_params=browser_params,
            extension_socket=extension_socket)

    if command[0] == 'BROWSE':
        browser_commands.browse_website(
            url=command[1], num_links=command[2], sleep=command[3],
            visit_id=command[4], webdriver=webdriver,
            browser_params=browser_params, manager_params=manager_params,
            extension_socket=extension_socket)

    if command[0] == 'DUMP_FLASH_COOKIES':
        browser_commands.dump_flash_cookies(
            start_time=command[1], visit_id=command[2],
            webdriver=webdriver, browser_params=browser_params,
            manager_params=manager_params)

    if command[0] == 'DUMP_PROF':
        profile_commands.dump_profile(
            browser_profile_folder=browser_params['profile_path'],
            manager_params=manager_params,
            browser_params=browser_params,
            tar_location=command[1], close_webdriver=command[2],
            webdriver=webdriver, browser_settings=browser_settings,
            compress=command[3],
            save_flash=browser_params['disable_flash'] is False)

    if command[0] == 'DUMP_PAGE_SOURCE':
        browser_commands.dump_page_source(
            visit_id=command[2], driver=webdriver,
            manager_params=manager_params, suffix=command[1])

    if command[0] == 'RECURSIVE_DUMP_PAGE_SOURCE':
        browser_commands.recursive_dump_page_source(
            visit_id=command[2], driver=webdriver,
            manager_params=manager_params, suffix=command[1])

    if command[0] == 'SAVE_SCREENSHOT':
        browser_commands.save_screenshot(
            visit_id=command[2], crawl_id=browser_params['crawl_id'],
            driver=webdriver, manager_params=manager_params, suffix=command[1])

    if command[0] == 'SCREENSHOT_FULL_PAGE':
        browser_commands.screenshot_full_page(
            visit_id=command[2], crawl_id=browser_params['crawl_id'],
            driver=webdriver, manager_params=manager_params, suffix=command[1])

    if command[0] == 'RUN_CUSTOM_FUNCTION':
        arg_dict = {"command": command,
                    "driver": webdriver,
                    "browser_settings": browser_settings,
                    "browser_params": browser_params,
                    "manager_params": manager_params,
                    "extension_socket": extension_socket}
        command[1](*command[2], **arg_dict)
