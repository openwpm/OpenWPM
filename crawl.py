import argparse
import sqlite3
from pathlib import Path
from typing import Literal
from custom_command import BrowsingCommand, AdScrapingCommand
from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import subprocess
from cookie_extraction import read_websites_from_file
# parser = argparse.ArgumentParser()
# parser.add_argument("--headless", action="store_true", default=False),
# args = parser.parse_args()

# display_mode: Literal["native", "headless", "xvfb"] = "native"
# if args.headless:
#     display_mode = "headless"


# # Loads the default ManagerParams
# # and NUM_BROWSERS copies of the default BrowserParams
# NUM_BROWSERS = 1
# manager_params = ManagerParams(num_browsers=NUM_BROWSERS)
# browser_params = [BrowserParams(display_mode=display_mode) for _ in range(NUM_BROWSERS)]

# # Update browser configuration (use this for per-browser settings)
# for browser_param in browser_params:
#     # Record HTTP Requests and Responses
#     browser_param.http_instrument = True
#     # Record cookie changes
#     browser_param.cookie_instrument = False #saves to javascript_cookie table in sqlite, but dont need this for the actual scraping
#     # Record Navigations
#     browser_param.navigation_instrument = True
#     # Record JS Web API calls
#     browser_param.js_instrument = True
#     # Record the callstack of all WebRequests made
#     # browser_param.callstack_instrument = True
#     # Record DNS resolution
#     browser_param.dns_instrument = True


# # Update TaskManager configuration (use this for crawl-wide settings)
# manager_params.data_directory = Path("./datadir/")
# manager_params.log_path = Path("./datadir/openwpm.log")

# def connect_to_nordvpn(location):
#     try:
#         subprocess.run(['nordvpn', 'connect', location], check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"Error connecting to NordVPN: {e}")
#         # Handle the error as needed


# def disconnect_from_nordvpn():
#     try:
#         subprocess.run(['nordvpn', 'disconnect'], check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"Error disconnecting from NordVPN: {e}")
#         # Handle the error as needed
        

def return_cookies():

    # Connect to the SQLite database
    conn = sqlite3.connect("./datadir/crawl-data.sqlite")  # Replace with the actual path

    # Create a cursor object
    cursor = conn.cursor()

    # Execute an SQL query to retrieve cookies
    cursor.execute("SELECT * FROM javascript_cookies")

    # Fetch the query results
    cookie_data = cursor.fetchall()

    # Close the database connection
    conn.close()

    return cookie_data

cookie_data = return_cookies()
print("cookie data: ", cookie_data)
# vpn_locations = ['United_States', 'Canada', 'United_Kingdom', 'Germany']
# sites = read_websites_from_file("websites.txt")


# def set_cookies_callback(driver, data):
#     for cookie_row in cookie_data:
#         cookie_dict = {
#             'name': cookie_row[0],
#             'value': cookie_row[1],
#             'domain': cookie_row[2],
#             'path': cookie_row[3],
#             'secure': bool(cookie_row[4]),
#             'httpOnly': bool(cookie_row[5]),
#         }
#         driver.add_cookie(cookie_dict)



# # Update TaskManager configuration (use this for crawl-wide settings)
# manager_params.data_directory = Path("./datadir/")
# manager_params.log_path = Path("./datadir/openwpm.log")

# # Commands time out by default after 60 seconds
# with TaskManager(
#     manager_params,
#     browser_params,
#     SQLiteStorageProvider(Path("./datadir/crawl-data.sqlite")),
#     None,
# ) as manager:
#     # Visits the sites
#     for index, site in enumerate(sites):
#         def callback(success: bool, val: str = site) -> None:
#             print(
#                 f"CommandSequence for {val} ran {'successfully' if success else 'unsuccessfully'}"
#             )


#         # Parallelize sites over all number of browsers set above.
#         command_sequence = CommandSequence(
#             site,
#             site_rank=index,
#             callback=set_cookies_callback, #i think callback means its alr ran
#         )

#         # Start by visiting the page
#         # command_sequence.append_command(GetCommand(url=site, sleep=3), timeout=60)
#         command_sequence.append_command(AdScrapingCommand())
#         # Run commands across all browsers (simple parallelization)
#         manager.execute_command_sequence(command_sequence)




