from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import random
import time

# Library for core WebDriver-based browser commands

NUM_MOUSE_MOVES = 10  # number of times to randomly move the mouse as part of bot mitigation
RANDOM_SLEEP_LOW = 1  # low end (in seconds) for random sleep times between page loads (bot mitigation)
RANDOM_SLEEP_HIGH = 7  # high end (in seconds) for random sleep times between page loads (bot mitigation)

# goes to <url> using the given <webdriver> instance
# <proxy_queue> is queue for sending the proxy the current first party site
def get_website(url, webdriver, proxy_queue):
    # sends top-level domain to proxy
    # then, waits for it to finish marking traffic in queue before moving to new site
    if proxy_queue is not None:
        proxy_queue.put(url)
        while not proxy_queue.empty():
            time.sleep(0.001)
    
    try:
        webdriver.get(url)
    except TimeoutException:
        pass

    # bot mitigation 1: move the randomly around a number of times
    for i in xrange(0, NUM_MOUSE_MOVES):
        x = random.randrange(0, 500)
        y = random.randrange(0, 500)
        action = ActionChains(webdriver)
        action.move_by_offset(x, y)
        action.perform()

    # bot mitigation 2: scroll to the bottom of the page
    webdriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # bot mitigation 3: randomly wait so that page visits appear at irregular intervals
    time.sleep(random.randrange(RANDOM_SLEEP_LOW, RANDOM_SLEEP_HIGH))
