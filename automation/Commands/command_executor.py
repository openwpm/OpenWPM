
from ..Errors import CommandExecutionError
from . import browser_commands, profile_commands
from .Types import (BrowseCommand, DumpPageSourceCommand, DumpProfCommand,
                    FinalizeCommand, GetCommand,
                    RecursiveDumpPageSourceCommand, RunCustomFunctionCommand,
                    SaveScreenshotCommand, ScreenshotFullPageCommand)


def execute_command(command, webdriver, browser_settings, browser_params,
                    manager_params, extension_socket):
    """Executes BrowserManager commands
    commands are of form (COMMAND, ARG0, ARG1, ...)
    """
    if type(command) is GetCommand:
        browser_commands.get_website(
            url=command.url, sleep=command.sleep, visit_id=command.visit_id,
            webdriver=webdriver, browser_params=browser_params,
            extension_socket=extension_socket)

    elif type(command) is BrowseCommand:
        browser_commands.browse_website(
            url=command.url, num_links=command.num_links, sleep=command.sleep,
            visit_id=command.visit_id, webdriver=webdriver,
            browser_params=browser_params, manager_params=manager_params,
            extension_socket=extension_socket)

    elif type(command) is DumpProfCommand:
        profile_commands.dump_profile(
            browser_profile_folder=browser_params['profile_path'],
            manager_params=manager_params,
            browser_params=browser_params,
            tar_location=command.dump_folder,
            close_webdriver=command.close_webdriver,
            webdriver=webdriver, browser_settings=browser_settings,
            compress=command.compress)

    elif type(command) is DumpPageSourceCommand:
        browser_commands.dump_page_source(
            visit_id=command.visit_id, driver=webdriver,
            manager_params=manager_params, suffix=command.suffix)

    elif type(command) is RecursiveDumpPageSourceCommand:
        browser_commands.recursive_dump_page_source(
            visit_id=command.visit_id, driver=webdriver,
            manager_params=manager_params, suffix=command.suffix)

    elif type(command) is SaveScreenshotCommand:
        browser_commands.save_screenshot(
            visit_id=command.visit_id, crawl_id=command.crawl_id,
            driver=webdriver, manager_params=manager_params,
            suffix=command.suffix)

    elif type(command) is ScreenshotFullPageCommand:
        browser_commands.screenshot_full_page(
            visit_id=command.visit_id, crawl_id=command.crawl_id,
            driver=webdriver, manager_params=manager_params,
            suffix=command.suffix)

    elif type(command) is RunCustomFunctionCommand:
        arg_dict = {"command": command,
                    "driver": webdriver,
                    "browser_settings": browser_settings,
                    "browser_params": browser_params,
                    "manager_params": manager_params,
                    "extension_socket": extension_socket}
        command.function_handle(*command.func_args, **arg_dict)

    elif type(command) is FinalizeCommand:
        browser_commands.finalize(command.visit_id, extension_socket)

    else:
        raise CommandExecutionError("Invalid Command", command)
