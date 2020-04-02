
from ..Errors import CommandExecutionError
from . import browser_commands, profile_commands
from .Commands import (Browse_Command, Dump_Flash_Cookies_Command,
                       Dump_Page_Source_Command, Dump_Prof_Command,
                       Get_Command, Recursive_Dump_Page_Source_Command,
                       Run_Custom_Function_Command, Save_Screenshot_Command,
                       Screenshot_Full_Page_Command)


def execute_command(command, webdriver, browser_settings, browser_params,
                    manager_params, extension_socket):
    """Executes BrowserManager commands
    commands are of form (COMMAND, ARG0, ARG1, ...)
    """
    if type(command) is Get_Command:
        browser_commands.get_website(
            url=command.url, sleep=command.sleep, visit_id=command.visit_id,
            webdriver=webdriver, browser_params=browser_params,
            extension_socket=extension_socket)

    elif type(command) is Browse_Command:
        browser_commands.browse_website(
            url=command.url, num_links=command.num_links, sleep=command.sleep,
            visit_id=command.visit_id, webdriver=webdriver,
            browser_params=browser_params, manager_params=manager_params,
            extension_socket=extension_socket)

    elif type(command) is Dump_Flash_Cookies_Command:
        browser_commands.dump_flash_cookies(
            start_time=command.start_time, visit_id=command.visit_id,
            webdriver=webdriver, browser_params=browser_params,
            manager_params=manager_params)

    elif type(command) is Dump_Prof_Command:
        profile_commands.dump_profile(
            browser_profile_folder=browser_params['profile_path'],
            manager_params=manager_params,
            browser_params=browser_params,
            tar_location=command.dump_folder,
            close_webdriver=command.close_webdriver,
            webdriver=webdriver, browser_settings=browser_settings,
            compress=command.compress,
            save_flash=browser_params['disable_flash'] is False)

    elif type(command) is Dump_Page_Source_Command:
        browser_commands.dump_page_source(
            visit_id=command.visit_id, driver=webdriver,
            manager_params=manager_params, suffix=command.suffix)

    elif type(command) is Recursive_Dump_Page_Source_Command:
        browser_commands.recursive_dump_page_source(
            visit_id=command.visit_id, driver=webdriver,
            manager_params=manager_params, suffix=command.suffix)

    elif type(command) is Save_Screenshot_Command:
        browser_commands.save_screenshot(
            visit_id=command.visit_id, crawl_id=command.crawl_id,
            driver=webdriver, manager_params=manager_params,
            suffix=command.suffix)

    elif type(command) is Screenshot_Full_Page_Command:
        browser_commands.screenshot_full_page(
            visit_id=command.visit_id, crawl_id=command.crawl_id,
            driver=webdriver, manager_params=manager_params,
            suffix=command.suffix)

    elif type(command) is Run_Custom_Function_Command:
        arg_dict = {"command": command,
                    "driver": webdriver,
                    "browser_settings": browser_settings,
                    "browser_params": browser_params,
                    "manager_params": manager_params,
                    "extension_socket": extension_socket}
        command.function_handle(*command.func_args, **arg_dict)

    else:
        raise CommandExecutionError("Invalid Command", command)
