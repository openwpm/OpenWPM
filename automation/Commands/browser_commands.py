from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from urlparse import urlparse
import random
import time
import logging

from ..SocketInterface import clientsocket
from utils.lso import get_flash_cookies
from utils.firefox_profile import get_cookies  # todo: add back get_localStorage,

# Library for core WebDriver-based browser commands

NUM_MOUSE_MOVES = 10  # number of times to randomly move the mouse as part of bot mitigation
RANDOM_SLEEP_LOW = 1  # low end (in seconds) for random sleep times between page loads (bot mitigation)
RANDOM_SLEEP_HIGH = 7  # high end (in seconds) for random sleep times between page loads (bot mitigation)


def bot_mitigation(webdriver):
    """ performs three optional commands for bot-detection mitigation when getting a site """

    # bot mitigation 1: move the randomly around a number of times
    window_size = webdriver.get_window_size()
    num_moves = 0
    num_fails = 0
    while num_moves < NUM_MOUSE_MOVES + 1 and num_fails < NUM_MOUSE_MOVES:
        try:
            if num_moves == 0: #move to the center of the screen
                x = int(round(window_size['height']/2))
                y = int(round(window_size['width']/2))
            else: #move a random amount in some direction
                move_max = random.randint(0,500)
                x = random.randint(-move_max, move_max)
                y = random.randint(-move_max, move_max)
            action = ActionChains(webdriver)
            action.move_by_offset(x, y)
            action.perform()
            num_moves += 1
        except MoveTargetOutOfBoundsException:
            num_fails += 1
            #print "[WARNING] - Mouse movement out of bounds, trying a different offset..."
            pass

    # bot mitigation 2: scroll to the bottom of the page
    # webdriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    atBottom = False
    while random.random()>.05 and not atBottom :
        k = str(10 + int(200*random.random()))
        webdriver.execute_script("window.scrollBy(0,"+k+")")
        atBottom = webdriver.execute_script("return (((window.scrollY + window.innerHeight ) +100 > document.body.clientHeight ))")
        time.sleep(.5+ 1.0 * random.random())	

    # bot mitigation 3: randomly wait so that page visits appear at irregular intervals
    time.sleep(random.randrange(RANDOM_SLEEP_LOW, RANDOM_SLEEP_HIGH))


def tab_restart_browser(webdriver):
    """
    kills the current tab and creates a new one to stop traffic
    note: this code if firefox-specific for now
    """
    if webdriver.current_url.lower() == 'about:blank':
        return

    switch_to_new_tab = ActionChains(webdriver)
    switch_to_new_tab.key_down(Keys.CONTROL).send_keys('t').key_up(Keys.CONTROL)
    switch_to_new_tab.key_down(Keys.CONTROL).send_keys(Keys.PAGE_UP).key_up(Keys.CONTROL)
    switch_to_new_tab.key_down(Keys.CONTROL).send_keys('w').key_up(Keys.CONTROL)
    switch_to_new_tab.perform()
    time.sleep(5)


def get_website(url, webdriver, proxy_queue, browser_params):
    """
    goes to <url> using the given <webdriver> instance
    <proxy_queue> is queue for sending the proxy the current first party site
    """

    tab_restart_browser(webdriver)
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
                webdriver.quit()
        webdriver.switch_to_window(main_handle)

    if browser_params['bot_mitigation']:
        bot_mitigation(webdriver)

def extract_links(webdriver, browser_params):
    link_elements = webdriver.find_elements_by_tag_name('a')
    link_urls = set(element.get_attribute("href") for element in link_elements)

    sock = clientsocket()
    sock.connect(*browser_params['aggregator_address'])
    create_table_query = ("""
    CREATE TABLE IF NOT EXISTS links_found (
      found_on TEXT,
      location TEXT
    )
    """, ())
    sock.send(create_table_query)

    if len(link_urls) > 0:
        current_url = webdriver.current_url
        insert_query_string = """
        INSERT INTO links_found (found_on, location)
        VALUES (?, ?)
        """
        for link in link_urls:
            sock.send((insert_query_string, (current_url, link)))

    sock.close()
    
def browse_website(url, webdriver, proxy_queue, browser_params):
       tab_restart_browser(webdriver)
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
                   webdriver.quit()
            webdriver.switch_to_window(main_handle)
       
       
       if browser_params['bot_mitigation']:
             bot_mitigation(webdriver)
       for i in range(1,2):
             links = get_intra_links(webdriver, url)
             print "List size is %d" % len(links)
             if len(links) == 0:
                return
             r = int(random.random()*len(links)-1 )
             print "Visiting link to %s" % links[r].get_attribute("href")
             try:
               clicked_url = links[r].get_attribute("href")
               scroll_and_click(links[r])
               waituntil(webdriver, 300)
               if browser_params['bot_mitigation']:
                    bot_mitigation(webdriver)
               webdriver.back()
             except:
               logging.info("Failed to click on link: %s" % links[r].get_attribute("href"))
               time.sleep(2)
               
               
def scroll_down(webdriver, url):
	atBottom = False
	while random.random()>.05 and not atBottom :
		k = str(10 + int(200*random.random()))
		#send_command({'command':'Scroll','domain':url,'param':k})
		webdriver.execute_script("window.scrollBy(0,"+k+")")
		atBottom = webdriver.execute_script("return (((window.scrollY + window.innerHeight ) +100 > document.body.clientHeight ))")
		time.sleep(.5+ 1.0 * random.random())	



def scroll_and_click(link):
	link.location_once_scrolled_into_view
	link.click()


   
def get_intra_links(webdriver, url):
    domain = urlparse(url).hostname
    links = filter( lambda x: (x.get_attribute("href") and  x.get_attribute("href").find(domain)>0 and x.get_attribute("href").find("http") == 0)  ,webdriver.find_elements_by_tag_name("a")) 
    return links
    
def optOutYOC(webdriver):
    webdriver.get("http://www.youronlinechoices.com/fr/controler-ses-cookies/")
    opt_out_link = browser.find_element_by_id("allOptOutButton");
    opt_out_link.click();
    time.sleep(10)

def is_loaded(webdriver):
    return (webdriver.execute_script("return document.readyState") == "complete") 

def waituntil(webdriver, timeout, period=0.25):
    mustend = time.time() + timeout
    while time.time() < mustend:
      if is_loaded(webdriver): return True
      time.sleep(period)
    return False
	
def dump_storage_vectors(top_url, start_time, webdriver, browser_params):
    """ Grab the newly changed items in supported storage vectors """

    # Set up a connection to DataAggregator
    tab_restart_browser(webdriver)  # kills traffic so we can cleanly record data
    sock = clientsocket()
    sock.connect(*browser_params['aggregator_address'])

    # Wait for SQLite Checkpointing - never happens when browser open

    # Flash cookies
    flash_cookies = get_flash_cookies(start_time)
    for cookie in flash_cookies:
        query = ("INSERT INTO flash_cookies (crawl_id, page_url, domain, filename, local_path, \
                  key, content) VALUES (?,?,?,?,?,?,?)", (browser_params['crawl_id'], top_url, cookie.domain,
                                                          cookie.filename, cookie.local_path,
                                                          cookie.key, cookie.content))
        sock.send(query)

    # Cookies
    rows = get_cookies(browser_params['profile_path'], start_time)
    if rows is not None:
        for row in rows:
            query = ("INSERT INTO profile_cookies (crawl_id, page_url, baseDomain, name, value, \
                      host, path, expiry, accessed, creationTime, isSecure, isHttpOnly) \
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (browser_params['crawl_id'], top_url) + row)
            sock.send(query)
    
    # localStorage - TODO this doesn't have a modified time support
    #rows = get_localStorage(profile_dir, start_time)
    #if rows is not None:
    #    for row in rows:
    #        query = ("INSERT INTO localStorage (crawl_id, page_url, scope, KEY, value) \
    #                  VALUES (?,?,?,?)",(crawl_id, top_url) + row)
    #        sock.send(query)

    # Close connection to db
    sock.close()
