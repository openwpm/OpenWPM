
import gzip
import json
import logging
import os
import random
import sys
import time
import traceback
from glob import glob
from hashlib import md5

from PIL import Image
from selenium.common.exceptions import (MoveTargetOutOfBoundsException,
                                        TimeoutException, WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..SocketInterface import clientsocket
from .utils.lso import get_flash_cookies
from .utils.webdriver_utils import (execute_in_all_frames,
                                    execute_script_with_retry, get_intra_links,
                                    is_displayed, scroll_down,
                                    wait_until_loaded)

# Constants for bot mitigation
NUM_MOUSE_MOVES = 10  # Times to randomly move the mouse
RANDOM_SLEEP_LOW = 1  # low (in sec) for random sleep between page loads
RANDOM_SLEEP_HIGH = 7  # high (in sec) for random sleep between page loads
logger = logging.getLogger('openwpm')


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
                x = int(round(window_size['height'] / 2))
                y = int(round(window_size['width'] / 2))
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
    except (TimeoutException, WebDriverException):
        pass

    close_other_windows(webdriver)

    if browser_params['bot_mitigation']:
        bot_mitigation(webdriver)


def browse_website(url, num_links, sleep, visit_id, webdriver,
                   browser_params, manager_params, extension_socket):
    """Calls get_website before visiting <num_links> present on the page.

    Note: the site_url in the site_visits table for the links visited will
    be the site_url of the original page and NOT the url of the links visited.
    """
    # First get the site
    get_website(url, sleep, visit_id, webdriver,
                browser_params, extension_socket)

    # Then visit a few subpages
    for _ in range(num_links):
        links = [x for x in get_intra_links(webdriver, url)
                 if is_displayed(x) is True]
        if not links:
            break
        r = int(random.random() * len(links))
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
        data = cookie._asdict()
        data["crawl_id"] = browser_params["crawl_id"]
        data["visit_id"] = visit_id
        sock.send(("flash_cookies", data))

    # Close connection to db
    sock.close()


def save_screenshot(visit_id, crawl_id, driver, manager_params, suffix=''):
    """ Save a screenshot of the current viewport"""
    if suffix != '':
        suffix = '-' + suffix

    urlhash = md5(driver.current_url.encode('utf-8')).hexdigest()
    outname = os.path.join(manager_params['screenshot_path'],
                           '%i-%s%s.png' %
                           (visit_id, urlhash, suffix))
    driver.save_screenshot(outname)


def _stitch_screenshot_parts(visit_id, crawl_id, manager_params):
    # Read image parts and compute dimensions of output image
    total_height = -1
    max_scroll = -1
    max_width = -1
    images = dict()
    parts = list()
    for f in glob(os.path.join(manager_params['screenshot_path'],
                               'parts',
                               '%i*-part-*.png' % visit_id)):

        # Load image from disk and parse params out of filename
        img_obj = Image.open(f)
        width, height = img_obj.size
        parts.append((f, width, height))
        outname, _, index, curr_scroll = os.path.basename(f).rsplit('-', 3)
        curr_scroll = int(curr_scroll.split('.')[0])
        index = int(index)

        # Update output image size
        if curr_scroll > max_scroll:
            max_scroll = curr_scroll
            total_height = max_scroll + height

        if width > max_width:
            max_width = width

        # Save image parameters
        img = {}
        img['object'] = img_obj
        img['scroll'] = curr_scroll
        images[index] = img

    # Output filename same for all parts, so we can just use last filename
    outname = outname + '.png'
    outname = os.path.join(manager_params['screenshot_path'], outname)
    output = Image.new('RGB', (max_width, total_height))

    # Compute dimensions for output image
    for i in range(max(images.keys()) + 1):
        img = images[i]
        output.paste(im=img['object'], box=(0, img['scroll']))
        img['object'].close()
    try:
        output.save(outname)
    except SystemError:
        logger.error(
            "BROWSER %i: SystemError while trying to save screenshot %s. \n"
            "Slices of image %s \n Final size %s, %s." %
            (crawl_id, outname, '\n'.join([str(x) for x in parts]),
             max_width, total_height)
        )
        pass


def screenshot_full_page(visit_id, crawl_id, driver, manager_params,
                         suffix=''):

    outdir = os.path.join(manager_params['screenshot_path'], 'parts')
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
    if suffix != '':
        suffix = '-' + suffix
    urlhash = md5(driver.current_url.encode('utf-8')).hexdigest()
    outname = os.path.join(outdir, '%i-%s%s-part-%%i-%%i.png' %
                           (visit_id, urlhash, suffix))

    try:
        part = 0
        max_height = execute_script_with_retry(
            driver, 'return document.body.scrollHeight;')
        inner_height = execute_script_with_retry(
            driver, 'return window.innerHeight;')
        curr_scrollY = execute_script_with_retry(
            driver, 'return window.scrollY;')
        prev_scrollY = -1
        driver.save_screenshot(outname % (part, curr_scrollY))
        while (curr_scrollY + inner_height) < max_height and \
                curr_scrollY != prev_scrollY:

            # Scroll down to bottom of previous viewport
            try:
                driver.execute_script('window.scrollBy(0, window.innerHeight)')
            except WebDriverException:
                logger.info(
                    "BROWSER %i: WebDriverException while scrolling, "
                    "screenshot may be misaligned!" % crawl_id)
                pass

            # Update control variables
            part += 1
            prev_scrollY = curr_scrollY
            curr_scrollY = execute_script_with_retry(
                driver, 'return window.scrollY;')

            # Save screenshot
            driver.save_screenshot(outname % (part, curr_scrollY))
    except WebDriverException:
        excp = traceback.format_exception(*sys.exc_info())
        logger.error(
            "BROWSER %i: Exception while taking full page screenshot \n %s" %
            (crawl_id, ''.join(excp)))
        return

    _stitch_screenshot_parts(visit_id, crawl_id, manager_params)


def dump_page_source(visit_id, driver, manager_params, suffix=''):
    if suffix != '':
        suffix = '-' + suffix

    outname = md5(driver.current_url.encode('utf-8')).hexdigest()
    outfile = os.path.join(manager_params['source_dump_path'],
                           '%i-%s%s.html' % (visit_id, outname, suffix))

    with open(outfile, 'wb') as f:
        f.write(driver.page_source.encode('utf8'))
        f.write(b'\n')


def recursive_dump_page_source(visit_id, driver, manager_params, suffix=''):
    """Dump a compressed html tree for the current page visit"""
    if suffix != '':
        suffix = '-' + suffix

    outname = md5(driver.current_url.encode('utf-8')).hexdigest()
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
        source = driver.page_source
        if type(source) != str:
            source = str(source, 'utf-8')
        page_source['source'] = source
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
        f.write(json.dumps(page_source).encode('utf-8'))
