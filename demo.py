import json
import time
from typing import Any, Dict

from selenium.webdriver import Firefox

from automation import CommandSequence, TaskManager
from automation.Commands.types import BaseCommand
from automation.SocketInterface import clientsocket


class AcceptGoogleCookies(BaseCommand):
    def execute(
        self,
        webdriver: Firefox,
        browser_settings: Dict[str, Any],
        browser_params: Dict[str, Any],
        manager_params: Dict[str, Any],
        extension_socket: clientsocket,
    ) -> None:
        iframe = webdriver.find_element_by_tag_name("iframe")
        webdriver.switch_to.frame(iframe)
        button = webdriver.find_element_by_id("introAgreeButton")
        button.click()
        webdriver.switch_to.default_content()


class ClickOnGoogleAd(BaseCommand):
    def execute(
        self,
        webdriver: Firefox,
        browser_settings: Dict[str, Any],
        browser_params: Dict[str, Any],
        manager_params: Dict[str, Any],
        extension_socket: clientsocket,
    ) -> None:
        ad = webdriver.find_element_by_class_name("pla-unit")
        link = ad.find_element_by_tag_name("a")
        ad.click()


class SleepCommand(BaseCommand):
    def __init__(self, sleep):
        self.sleep = sleep

    def execute(
        self,
        webdriver: Firefox,
        browser_settings: Dict[str, Any],
        browser_params: Dict[str, Any],
        manager_params: Dict[str, Any],
        extension_socket: clientsocket,
    ) -> None:
        time.sleep(self.sleep)


# The list of sites that we wish to crawl
NUM_BROWSERS = 4


def main():
    # Loads the default manager params
    # and NUM_BROWSERS copies of the default browser params
    manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

    # Update browser configuration (use this for per-browser settings)
    for i in range(NUM_BROWSERS):
        # Record HTTP Requests and Responses
        browser_params[i]["http_instrument"] = True
        # Record cookie changes
        browser_params[i]["cookie_instrument"] = True
        # Record Navigations
        browser_params[i]["navigation_instrument"] = True
        # Record JS Web API calls
        browser_params[i]["js_instrument"] = True
        # Record the callstack of all WebRequests made
        browser_params[i]["callstack_instrument"] = True
        # Record DNS resolution
        browser_params[i]["dns_instrument"] = True

        # Launch only browser 0 headless
        # browser_params[i]["display_mode"] = "headless"

    # Update TaskManager configuration (use this for crawl-wide settings)
    manager_params["data_directory"] = "datadir"
    manager_params["log_directory"] = "datadir"

    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(manager_params, browser_params)

    with open("seed.json", mode="r") as f:
        search_words = json.load(f)
    # Visits the sites
    for search_word in search_words:
        search_word = search_word.replace(" ", "+")
        query_url = f"https://www.google.de/search?q={search_word}"
        # Parallelize sites over all number of browsers set above.
        command_sequence = CommandSequence.CommandSequence(
            query_url,
            reset=True,
            callback=lambda success, val=search_word: print(
                "CommandSequence {} done".format(val)
            ),
        )

        # Start by visiting the page
        command_sequence.get(sleep=3)
        command_sequence.append_command(AcceptGoogleCookies())
        command_sequence.append_command(ClickOnGoogleAd())
        command_sequence.append_command(SleepCommand(15))
        # Run commands across the three browsers (simple parallelization)
        manager.execute_command_sequence(command_sequence)

    # Shuts down the browsers and waits for the data to finish logging
    manager.close()


if __name__ == "__main__":
    main()
