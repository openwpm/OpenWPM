# A set of extensions to the functions normally provided by the selenium
# webdriver. These are primarily for parsing and searching.


import random
import re
import time
from urllib import parse as urlparse

from selenium.common.exceptions import (ElementNotVisibleException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException, WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ...utilities import domain_utils as du
from . import XPathUtil

NETERROR_RE = re.compile(
    r"WebDriverException: Message: Reached error page: about:neterror\?(.*)\."
)


def parse_neterror(error_message):
    """Attempt to parse the about:neterror message.

    If any errors occur while parsing, we fall back to the unparsed message
    """
    try:
        qs = re.match(NETERROR_RE, error_message).group(1)
        params = urlparse.parse_qs(qs)
        return '&'.join(params['e'])
    except Exception:
        return error_message


def scroll_down(driver):
    at_bottom = False
    while random.random() > .20 and not at_bottom:
        driver.execute_script("window.scrollBy(0,%d)"
                              % (10 + int(200 * random.random())))
        at_bottom = driver.execute_script(
            "return (((window.scrollY + window.innerHeight ) + 100 "
            "> document.body.clientHeight ))")
        time.sleep(0.5 + random.random())


def scroll_to_bottom(driver):
    try:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
    except WebDriverException:
        pass


def is_loaded(webdriver):
    return (webdriver.execute_script(
        "return document.readyState") == "complete")


def wait_until_loaded(webdriver, timeout, period=0.25, min_time=0):
    start_time = time.time()
    mustend = time.time() + timeout
    while time.time() < mustend:
        if is_loaded(webdriver):
            if time.time() - start_time < min_time:
                time.sleep(min_time + start_time - time.time())
            return True
        time.sleep(period)
    return False


def get_intra_links(webdriver, url):
    ps1 = du.get_ps_plus_1(url)
    links = list()
    for elem in webdriver.find_elements_by_tag_name("a"):
        try:
            href = elem.get_attribute('href')
        except StaleElementReferenceException:
            continue
        if href is None:
            continue
        full_href = urlparse.urljoin(url, href)
        if not full_href.startswith('http'):
            continue
        if du.get_ps_plus_1(full_href) == ps1:
            links.append(elem)
    return links


def execute_script_with_retry(driver, script):
    """Execute script, retrying if a WebDriverException is thrown

    See:
    https://github.com/seleniumhq/selenium-google-code-issue-archive/issues/7931#issuecomment-192191013
    """
    try:
        return driver.execute_script(script)
    except WebDriverException:
        return driver.execute_script(script)


# ####### Search Helpers ########
def wait_and_find(driver, locator_type, locator,
                  timeout=3, check_iframes=True):
    """Search for element with `locator` and block if not found

    Parameters
    ----------
    driver : selenium.webdriver.firefox.webdriver.WebDriver
        An instance of the Firefox webdriver
    locator_type : string
        A text representation of the attribute to search by, e.g. searching
        by `id`, `class name`, and so on. For a list of supported types,
        `import selenium.webdriver.common.by.By` and use `By.LINK_TEXT`,
        `By.ID`, and so on.
    locator : string
        The search string used to identify the candidate element.
    timeout : int, optional
        Time in seconds to block before throwing `NoSuchElementException`. The
        default is 3 seconds.
    check_iframes : bool, optional
        Set to `True` to also check all iframes contained directly in the
        current frame.

    Returns
    -------
    selenium.webdriver.firefox.webelement.FirefoxWebElement
        Matching element (if any is found before `timeout`).

    Raises
    ------
    NoSuchElementException
        Raised if no element is located with `locator` before `timeout`.
    """
    if is_found(driver, locator_type, locator, timeout):
        return driver.find_element(locator_type, locator)
    else:
        if check_iframes:  # this may return the browser with an iframe active
            driver.switch_to_default_content()
            iframes = driver.find_elements_by_tag_name('iframe')

            for iframe in iframes:
                driver.switch_to_default_content()
                driver.switch_to_frame(iframe)
                if is_found(driver, locator_type, locator, timeout=0):
                    return driver.find_element(locator_type, locator)

            # If we get here, search also fails in iframes
            driver.switch_to_default_content()
        raise NoSuchElementException("Element not found during wait_and_find")


def is_found(driver, locator_type, locator, timeout=3):
    try:
        w = WebDriverWait(driver, timeout)
        w.until(lambda d: d.find_element(locator_type, locator))
        return True
    except TimeoutException:
        return False


def is_visible(driver, locator_type, locator, timeout=3):
    try:
        w = WebDriverWait(driver, timeout)
        w.until(EC.visibility_of_element_located((locator_type, locator)))
        return True
    except TimeoutException:
        return False


def title_is(driver, title, timeout=3):
    try:
        w = WebDriverWait(driver, timeout)
        w.until(EC.title_is(title))
        return True
    except TimeoutException:
        return False


def title_contains(driver, title, timeout=3):
    try:
        w = WebDriverWait(driver, timeout)
        w.until(EC.title_contains(title))
        return True
    except TimeoutException:
        return False


def is_clickable(driver, full_xpath, xpath, timeout=1):
    """Check if an element is visible and enabled.

    Selenium requires an element to be visible and enabled to be
    clickable. We extend that to require it to have a tag capable
    of containing a link. NOTE: doesn't work 100%
    """
    try:
        w = WebDriverWait(driver, timeout)
        w.until(EC.element_to_be_clickable(('xpath', xpath)))
        return XPathUtil.is_clickable(full_xpath)
    except (TimeoutException, ElementNotVisibleException):
        return False


def click_to_element(element, sleep_after=0.5):
    """Click to element and handle WebDriverException."""
    try:
        element.click()
        time.sleep(sleep_after)
    except WebDriverException:
        pass


def move_to_element(driver, element):
    try:
        ActionChains(driver).move_to_element(element).perform()
    except WebDriverException:
        pass


def scroll_to_element(driver, element):
    try:
        driver.execute_script("window.scrollTo(%s, %s);" % (
            element.location['x'], element.location['y']))
    except WebDriverException:
        pass


def move_to_and_click(driver, element, sleep_after=0.5):
    """Scroll to the element, hover over it, and click it"""
    scroll_to_element(driver, element)
    move_to_element(driver, element)
    click_to_element(element, sleep_after)
    return


def is_displayed(element):
    try:
        return element.is_displayed()
    except (StaleElementReferenceException, WebDriverException):
        return False


def is_active(input_element):
    """Check if we can interact with the given element."""
    try:
        return is_displayed(input_element) and input_element.is_enabled()
    except WebDriverException:
        return False


def get_button_text(element):
    """Get the text either via `value` attribute or using (inner) `text`.

    `value` attribute works for <input type="button"...> or
    <input type="submit".

    `text` works for <button>elements, e.g. <button>text</button>.
    """
    button_text = element.get_attribute("value") or element.text
    return button_text.lower()


def iter_frames(driver):
    """Return a generator for iframes."""
    driver.switch_to_default_content()
    iframes = driver.find_elements_by_tag_name('iframe')
    for iframe in iframes:
        driver.switch_to_default_content()
        yield iframe
    driver.switch_to_default_content()


def switch_to_parent_frame(driver, frame_stack):
    """Switch driver to parent frame

    Selenium doesn't provide a method to switch up to a parent frame.
    Any frame handles collected in a parent frame can't be used in the
    child frame, so the only way to switch to a parent frame is to
    switch back to the top-level frame and then switch back down to the
    parent through all iframes.

    Parameters
    ----------
    driver : selenium.webdriver
        A Selenium webdriver instance.
    frame_stack : list of selenium.webdriver.remote.webelement.WebElement
        list of parent frame handles (including current frame)
    """
    driver.switch_to_default_content()  # start at top frame
    # First item is 'default', last item is current frame
    for frame in frame_stack[1:-1]:
        driver.switch_to_frame(frame)


def execute_in_all_frames(driver, func, kwargs={}, frame_stack=['default'],
                          max_depth=5, logger=None, visit_id=-1):
    """Recursively apply `func` within each iframe

    When called at each level, `func` will be passed the webdriver instance
    as an argument as well as any named arguments given in `kwargs`. If you
    require a return value from `func` it should be stored in a mutable
    argument. Function returns and positional arguments are not supported.
    `func` should be defined with the following structure:

    >>> def print_and_gather_links(driver, frame_stack,
    >>>                            print_prefix='', links=[]):
    >>>     elems = driver.find_elements_by_tag_name('a')
    >>>     for elem in elems:
    >>>         link = elem.get_attribute('href')
    >>>         print print_prefix + link
    >>>         links.append(link)

    `execute_in_all_frames` should then be called as follows:

    >>> all_links = list()
    >>> execute_in_all_frames(driver, print_and_gather_links,
    >>>                       {'prefix': 'Link ', 'links': all_links})
    >>> print "All links on page (including all iframes):"
    >>> print all_links

    Parameters
    ----------
    driver : selenium.webdriver
        A Selenium webdriver instance.
    func : function
        A function handle to apply to the webdriver instance within each frame
    max_depth : int
        Maximum depth to recurse into
    frame_stack : list of selenium.webdriver.remote.webelement.WebElement
        list of parent frame handles (including current frame)
    logger : logger
        logging module's logger
    visit_id : int
        ID of the visit

    """
    # Ensure we start at the top level frame
    if len(frame_stack) == 1:
        driver.switch_to_default_content()

    # Bail if past depth cutoff
    if len(frame_stack) - 1 > max_depth:
        return

    # Execute function in this frame
    func(driver, frame_stack, **kwargs)

    # Grab all iframes in the current frame
    frames = driver.find_elements_by_tag_name('iframe')

    # Recurse through frames
    for frame in frames:
        frame_stack.append(frame)
        try:
            driver.switch_to_frame(frame)
        except StaleElementReferenceException:
            if logger is not None:
                logger.error("Error while switching to frame %s (visit: %d))" %
                             (str(frame), visit_id))
            continue
        else:
            if logger is not None:
                doc_url = driver.execute_script("return window.document.URL;")
                logger.info("Switched to frame: %s (visit: %d)" %
                            (doc_url, visit_id))
            # Search within child frame
            execute_in_all_frames(driver, func, kwargs, frame_stack, max_depth)
            switch_to_parent_frame(driver, frame_stack)
        finally:
            frame_stack.pop()
