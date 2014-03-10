from selenium.common.exceptions import TimeoutException
import time

# Library for core WebDriver-based browser commands

# goes to <url> using the given <webdriver> instance
# <proxy_queue> is queue for sending the proxy the current first party site
def get_website(url, webdriver, proxy_queue):
    try :
        # sends top-level domain to proxy
        # then, waits for it to finish marking traffic in queue before moving to new site
        if proxy_queue is not None:
            proxy_queue.put(url)
            while not proxy_queue.empty():
                time.sleep(0.001)

        webdriver.get(url)

    except TimeoutException:
        pass