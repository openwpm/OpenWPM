from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import random
import time

from ..SocketInterface import clientsocket
from utils.lso import get_flash_cookies
from utils.firefox_profile import get_localStorage, get_cookies

# Library for core WebDriver-based browser commands

NUM_MOUSE_MOVES = 10  # number of times to randomly move the mouse as part of bot mitigation
RANDOM_SLEEP_LOW = 1  # low end (in seconds) for random sleep times between page loads (bot mitigation)
RANDOM_SLEEP_HIGH = 7  # high end (in seconds) for random sleep times between page loads (bot mitigation)

# goes to <url> using the given <webdriver> instance
# <proxy_queue> is queue for sending the proxy the current first party site
def get_website(url, webdriver, proxy_queue):
    main_handle = webdriver.current_window_handle
    # sends top-level domain to proxy
    # then, waits for it to finish marking traffic in queue before moving to new site
    if proxy_queue is not None:
        proxy_queue.put(url)
        while not proxy_queue.empty():
            time.sleep(0.001)
    
    # Execute a get through selenium
    try:
        webdriver.get(url)
    except TimeoutException:
        pass
    
    # Close modal dialog if exists
    try:
        WebDriverWait(webdriver, .5).until(EC.alert_is_present())
        alert = webdriver.switch_to_alert()
        alert.dismiss()
        time.sleep(1)
    except TimeoutException:
        pass

    # Close other windows (popups or "tabs")
    windows = webdriver.window_handles
    if len(windows) > 1:
        for window in windows:
            if window != main_handle:
                webdriver.switch_to_window(window)
                webdriver.close()
        webdriver.switch_to_window(main_handle)

    #TODO: bot mitigation should be optional
    #TODO: should do bounds checking
    # bot mitigation 1: move the randomly around a number of times
    num_moves = 0
    while num_moves < NUM_MOUSE_MOVES:
        try:
            x = random.randrange(0, 100)
            y = random.randrange(0, 100)
            action = ActionChains(webdriver)
            action.move_by_offset(x, y)
            action.perform()
            num_moves += 1
        except MoveTargetOutOfBoundsException:
            print "[ERROR] - mouse moves out of bounds"
            pass

    # bot mitigation 2: scroll to the bottom of the page
    webdriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # bot mitigation 3: randomly wait so that page visits appear at irregular intervals
    time.sleep(random.randrange(RANDOM_SLEEP_LOW, RANDOM_SLEEP_HIGH))
    
    # Create a new tab and kill this one to stop traffic
    # NOTE: This code is firefox specific
    # TODO: This should be optional
    time.sleep(1)
    switch_to_new_tab = ActionChains(webdriver)
    switch_to_new_tab.key_down(Keys.CONTROL + 't') # open new tab
    switch_to_new_tab.key_up(Keys.CONTROL + 't')
    switch_to_new_tab.key_down(Keys.CONTROL + Keys.PAGE_UP) # switch to prev tab
    switch_to_new_tab.key_up(Keys.CONTROL + Keys.PAGE_UP)
    switch_to_new_tab.key_down(Keys.CONTROL + 'w') # close tab
    switch_to_new_tab.key_up(Keys.CONTROL + 'w')
    switch_to_new_tab.perform()
    time.sleep(5)

def dump_storage_vectors(top_url, start_time, profile_dir, db_socket_address, crawl_id):
    ''' Grab the newly changed items in supported storage vectors '''
    # Set up a connection to DataAggregator
    sock = clientsocket()
    sock.connect(*db_socket_address)

    # Wait for SQLite Checkpointing - never happens when browser open

    # Flash cookies
    flash_cookies = get_flash_cookies(start_time)
    for cookie in flash_cookies:
        query = ("INSERT INTO flash_cookies (crawl_id, page_url, domain, filename, local_path, \
                  key, content) VALUES (?,?,?,?,?,?,?)", 
                  (crawl_id, top_url, cookie.domain, cookie.filename, cookie.local_path, 
                  cookie.key, cookie.content))
        sock.send(query)

    # Cookies
    rows = get_cookies(profile_dir, start_time)
    if rows is not None:
        for row in rows:
            query = ("INSERT INTO profile_cookies (crawl_id, page_url, baseDomain, name, value, \
                      host, path, expiry, accessed, creationTime, isSecure, isHttpOnly) \
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(crawl_id, top_url) + row)
            sock.send(query)
    
    # localStorage - TODO this doesn't have a modified time support
    '''
    rows = get_localStorage(profile_dir, start_time)
    if rows is not None:
        for row in rows:
            query = ("INSERT INTO localStorage (crawl_id, page_url, scope, KEY, value) \
                      VALUES (?,?,?,?)",(crawl_id, top_url) + row)
            sock.send(query)
    '''

    # Close connection to db
    sock.close()
