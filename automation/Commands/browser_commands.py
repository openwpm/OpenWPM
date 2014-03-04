from selenium.common.exceptions import TimeoutException

# Library for core WebDriver-based browser commands

# goes to <url> using the given <webdriver> instance
# <proxy_queue> is queue for sending the proxy the current first party site
def get_website(url, webdriver, proxy_queue):
    if proxy_queue is not None:
        proxy_queue.put(url)
    try:
        webdriver.get(url)
    except TimeoutException:
        pass
