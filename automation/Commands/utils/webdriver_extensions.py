# A set of extensions to the functions normally provided by the selenium
# webdriver. These are primarily for parsing and searching.

from __future__ import absolute_import

import random
import time
from six.moves.urllib.parse import urljoin

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import NoSuchElementException

from . import XPathUtil
from ...utilities import domain_utils as du


# Basic functions
def scroll_down(driver):
    at_bottom = False
    while random.random() > .20 and not at_bottom:
        driver.execute_script("window.scrollBy(0,%d)"
                              % (10 + int(200*random.random())))
        at_bottom = driver.execute_script(
            "return (((window.scrollY + window.innerHeight ) + 100 "
            "> document.body.clientHeight ))")
        time.sleep(0.5 + random.random())


def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    return


def is_loaded(webdriver):
    return (webdriver.execute_script(
        "return document.readyState") == "complete")


def wait_until_loaded(webdriver, timeout, period=0.25):
    mustend = time.time() + timeout
    while time.time() < mustend:
        if is_loaded(webdriver):
            return True
        time.sleep(period)
    return False


def get_intra_links(webdriver, url):
    ps1 = du.get_ps_plus_1(url)
    return [
        x for x in webdriver.find_elements_by_tag_name("a")
        if (x.get_attribute("href") and
            du.get_ps_plus_1(urljoin(url, x.get_attribute("href"))) == ps1)
    ]


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
