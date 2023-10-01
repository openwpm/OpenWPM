""" This file aims to demonstrate how to write custom commands in OpenWPM

Steps to have a custom command run as part of a CommandSequence

1. Create a class that derives from BaseCommand
2. Implement the execute method
3. Append it to the CommandSequence
4. Execute the CommandSequence

"""
import logging
import time

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket


class LinkCountingCommand(BaseCommand):
    """This command logs how many links it found on any given page"""

    def __init__(self) -> None:
        self.logger = logging.getLogger("openwpm")

    # While this is not strictly necessary, we use the repr of a command for logging
    # So not having a proper repr will make your logs a lot less useful
    def __repr__(self) -> str:
        return "LinkCountingCommand"

    # Have a look at openwpm.commands.types.BaseCommand.execute to see
    # an explanation of each parameter
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        current_url = webdriver.current_url
        link_count = len(webdriver.find_elements(By.TAG_NAME, "a"))
        self.logger.info("There are %d links on %s", link_count, current_url)


##ayesha

class BrowsingCommand(BaseCommand):
    """This browses a given page"""

    def __init__(self) -> None:
        self.logger = logging.getLogger("openwpm")


    def __repr__(self) -> str:
        return "LinkCountingCommand"

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        current_url = webdriver.current_url
        link_count = len(webdriver.find_elements(By.TAG_NAME, "a"))
        self.logger.info("There are %d links on %s", link_count, current_url)

        # Browse 2-3 links (modify as needed)
        links_to_browse = webdriver.find_elements(By.TAG_NAME, "a")[:3]  # Select the first 3 links
        for link in links_to_browse:
            try:
                link.click()  # Click the link to navigate to it
                time.sleep(1)
                # You can add further interactions with the link's page here if needed
                webdriver.back()  # Go back to the original page
            except Exception as e:
                self.logger.error(f"Error browsing link: {e}")



class AdScrapingCommand(BaseCommand):
    def __init__(self) -> None:
        self.logger = logging.getLogger("openwpm")

    def __repr__(self) -> str:
        return "AdScrapingCommand"

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        try:
            # Identify and scrape ad elements (modify as needed)
            ad_elements = webdriver.find_elements(By.CLASS_NAME, "ad-class")  # Replace with the appropriate selector
            ad_content = []
            for ad_element in ad_elements:
                ad_content.append(ad_element.text)
            
            # Process and store ad content as needed
            # You can save it to a file, database, or perform further analysis
            with open("ad_content.txt", "a") as ad_file:
                for ad_text in ad_content:
                    ad_file.write(ad_text + "\n")

        except Exception as e:
            self.logger.error(f"Error scraping ad content: {e}")