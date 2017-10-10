from __future__ import absolute_import
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from hashlib import md5
import random
import json
import time
import gzip
import os

from ..SocketInterface import clientsocket
from ..MPLogger import loggingclient
from .utils.lso import get_flash_cookies
from .utils.firefox_profile import get_cookies
from .utils.webdriver_extensions import (scroll_down, wait_until_loaded,
                                         get_intra_links,
                                         execute_in_all_frames)
from six.moves import range

# Constants for bot mitigation
NUM_MOUSE_MOVES = 10  # Times to randomly move the mouse
RANDOM_SLEEP_LOW = 1  # low (in sec) for random sleep between page loads
RANDOM_SLEEP_HIGH = 7  # high (in sec) for random sleep between page loads


def bot_mitigation(webdriver):
    """ performs three optional commands for bot-detection
    mitigation when getting a site """

    # bot mitigation 1: move the randomly around a number of times
    window_size = webdriver.get_window_size()
    num_moves = 0
    num_fails = 0
    while num_moves < NUM_MOUSE_MOVES + 1 and num_fails < NUM_MOUSE_MOVES:
        try:
            if num_moves == 0:  # move to the center of the screen
                x = int(round(window_size['height']/2))
                y = int(round(window_size['width']/2))
            else:  # move a random amount in some direction
                move_max = random.randint(0, 500)
                x = random.randint(-move_max, move_max)
                y = random.randint(-move_max, move_max)
            action = ActionChains(webdriver)
            action.move_by_offset(x, y)
            action.perform()
            num_moves += 1
        except MoveTargetOutOfBoundsException:
            num_fails += 1
            pass

    # bot mitigation 2: scroll in random intervals down page
    scroll_down(webdriver)

    # bot mitigation 3: randomly wait so page visits happen with irregularity
    time.sleep(random.randrange(RANDOM_SLEEP_LOW, RANDOM_SLEEP_HIGH))


def close_other_windows(webdriver):
    """
    close all open pop-up windows and tabs other than the current one
    """
    main_handle = webdriver.current_window_handle
    windows = webdriver.window_handles
    if len(windows) > 1:
        for window in windows:
            if window != main_handle:
                webdriver.switch_to_window(window)
                webdriver.close()
        webdriver.switch_to_window(main_handle)


def tab_restart_browser(webdriver):
    """
    kills the current tab and creates a new one to stop traffic
    """
    # note: this technically uses windows, not tabs, due to problems with
    # chrome-targeted keyboard commands in Selenium 3 (intermittent
    # nonsense WebDriverExceptions are thrown). windows can be reliably
    # created, although we do have to detour into JS to do it.
    close_other_windows(webdriver)

    if webdriver.current_url.lower() == 'about:blank':
        return

    # Create a new window.  Note that it is not practical to use
    # noopener here, as we would then be forced to specify a bunch of
    # other "features" that we don't know whether they are on or off.
    # Closing the old window will kill the opener anyway.
    webdriver.execute_script("window.open('')")

    # This closes the _old_ window, and does _not_ switch to the new one.
    webdriver.close()

    # The only remaining window handle will be for the new window;
    # switch to it.
    assert len(webdriver.window_handles) == 1
    webdriver.switch_to_window(webdriver.window_handles[0])


def get_website(url, sleep, visit_id, webdriver,
                browser_params, extension_socket):
    """
    goes to <url> using the given <webdriver> instance
    """

    tab_restart_browser(webdriver)

    if extension_socket is not None:
        extension_socket.send(visit_id)

    # Execute a get through selenium
    try:
        webdriver.get(url)
    except TimeoutException:
        pass

    # Sleep after get returns
    time.sleep(sleep)

    # Close modal dialog if exists
    try:
        WebDriverWait(webdriver, .5).until(EC.alert_is_present())
        alert = webdriver.switch_to_alert()
        alert.dismiss()
        time.sleep(1)
    except TimeoutException:
        pass

    close_other_windows(webdriver)

    if browser_params['bot_mitigation']:
        bot_mitigation(webdriver)


def extract_links(webdriver, browser_params, manager_params):
    link_elements = webdriver.find_elements_by_tag_name('a')
    link_urls = set(element.get_attribute("href") for element in link_elements)

    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])
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


def browse_website(url, num_links, sleep, visit_id, webdriver,
                   browser_params, manager_params, extension_socket):
    """Calls get_website before visiting <num_links> present on the page.

    Note: the site_url in the site_visits table for the links visited will
    be the site_url of the original page and NOT the url of the links visited.
    """
    # First get the site
    get_website(url, sleep, visit_id, webdriver,
                browser_params, extension_socket)

    # Connect to logger
    logger = loggingclient(*manager_params['logger_address'])

    # Then visit a few subpages
    for i in range(num_links):
        links = [x for x in get_intra_links(webdriver, url)
                 if x.is_displayed() is True]
        if not links:
            break
        r = int(random.random()*len(links))
        logger.info("BROWSER %i: visiting internal link %s" % (
            browser_params['crawl_id'], links[r].get_attribute("href")))

        try:
            links[r].click()
            wait_until_loaded(webdriver, 300)
            time.sleep(max(1, sleep))
            if browser_params['bot_mitigation']:
                bot_mitigation(webdriver)
            webdriver.back()
            wait_until_loaded(webdriver, 300)
        except Exception:
            pass


def dump_flash_cookies(start_time, visit_id, webdriver, browser_params,
                       manager_params):
    """ Save newly changed Flash LSOs to database

    We determine which LSOs to save by the `start_time` timestamp.
    This timestamp should be taken prior to calling the `get` for
    which creates these changes.
    """
    # Set up a connection to DataAggregator
    tab_restart_browser(webdriver)  # kills window to avoid stray requests
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])

    # Flash cookies
    flash_cookies = get_flash_cookies(start_time)
    for cookie in flash_cookies:
        query = ("INSERT INTO flash_cookies (crawl_id, visit_id, domain, "
                 "filename, local_path, key, content) VALUES (?,?,?,?,?,?,?)",
                 (browser_params['crawl_id'], visit_id, cookie.domain,
                  cookie.filename, cookie.local_path, cookie.key,
                  cookie.content))
        sock.send(query)

    # Close connection to db
    sock.close()


def dump_profile_cookies(start_time, visit_id, webdriver,
                         browser_params, manager_params):
    """ Save changes to Firefox's cookies.sqlite to database

    We determine which cookies to save by the `start_time` timestamp.
    This timestamp should be taken prior to calling the `get` for
    which creates these changes.

    Note that the extension's cookieInstrument is preferred to this approach,
    as this is likely to miss changes still present in the sqlite `wal` files.
    This will likely be removed in a future version.
    """
    # Set up a connection to DataAggregator
    tab_restart_browser(webdriver)  # kills window to avoid stray requests
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])

    # Cookies
    rows = get_cookies(browser_params['profile_path'], start_time)
    if rows is not None:
        for row in rows:
            query = ("INSERT INTO profile_cookies (crawl_id, visit_id, "
                     "baseDomain, name, value, host, path, expiry, accessed, "
                     "creationTime, isSecure, isHttpOnly) VALUES "
                     "(?,?,?,?,?,?,?,?,?,?,?,?)", (browser_params['crawl_id'],
                                                   visit_id) + row)
            sock.send(query)

    # Close connection to db
    sock.close()


def save_screenshot(screenshot_name, webdriver,
                    browser_params, manager_params):
    webdriver.save_screenshot(
        os.path.join(
            manager_params['screenshot_path'],
            screenshot_name + '.png'
        ))


def dump_page_source(visit_id, driver, manager_params, suffix=''):
    if suffix != '':
        suffix = '-' + suffix

    outname = md5(driver.current_url).hexdigest()
    outfile = os.path.join(manager_params['source_dump_path'],
                           '%i-%s%s.html' % (visit_id, outname, suffix))

    with open(outfile, 'wb') as f:
        f.write(driver.page_source.encode('utf8'))
        f.write(b'\n')


def recursive_dump_page_source(visit_id, driver, manager_params, suffix=''):
    """Dump a compressed html tree for the current page visit"""
    if suffix != '':
        suffix = '-' + suffix

    outname = md5(driver.current_url).hexdigest()
    outfile = os.path.join(manager_params['source_dump_path'],
                           '%i-%s%s.json.gz' % (visit_id, outname, suffix))

    def collect_source(driver, frame_stack, rv={}):
        is_top_frame = len(frame_stack) == 1

        # Gather frame information
        doc_url = driver.execute_script("return window.document.URL;")
        if is_top_frame:
            page_source = rv
        else:
            page_source = dict()
        page_source['doc_url'] = doc_url
        page_source['source'] = driver.page_source.encode('UTF-8')
        page_source['iframes'] = dict()

        # Store frame info in correct area of return value
        if is_top_frame:
            return
        out_dict = rv['iframes']
        for frame in frame_stack[1:-1]:
            out_dict = out_dict[frame.id]['iframes']
        out_dict[frame_stack[-1].id] = page_source

    page_source = dict()
    execute_in_all_frames(driver, collect_source, {'rv': page_source})

    with gzip.GzipFile(outfile, 'wb') as f:
        f.write(json.dumps(page_source))
