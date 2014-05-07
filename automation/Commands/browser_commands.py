from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import random
import time

# Library for core WebDriver-based browser commands

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

    # Add bot detection mitigation techniques
    # TODO: make this an option in the future?
    # move the mouse to random positions a number of times
    for i in range(0,10):
        x = random.randrange(0,500)
        y = random.randrange(0,500)
        action = ActionChains(webdriver)
        action.move_by_offset(x,y)
        action.perform

    # scroll to bottom of page
    webdriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # random wait time
    time.sleep(random.randrange(1,7))
