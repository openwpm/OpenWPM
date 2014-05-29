# A set of extensions to the functions normally provided by the selenium
# webdriver. These are primarily for parsing and searching.
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import NoSuchElementException

import XPathUtil

##### Search/Block Functions
# locator_type: a text representation of the standard
# webdriver.find_element_by_* functions. You can either
# import selenium.webdriver.common.by.By and use By.LINK_TEXT, etc.
# or just remember the string representations. For example:
# By.LINK_TEXT is 'link text'
# By.CSS_SELECTOR is 'css selector'
# By.NAME is 'name' ... and so on
# locator: string that you are looking for
def wait_and_find(driver, locator_type, locator, timeout=3, check_iframes=True):
    if is_found(driver, locator_type, locator, timeout):
        return driver.find_element(locator_type, locator)
    else:
        if check_iframes: #this may return the browser with an iframe active
            driver.switch_to_default_content()
            iframes = driver.find_elements_by_tag_name('iframe')

            for iframe in iframes:
                driver.switch_to_default_content()
                driver.switch_to_frame(iframe)
                if is_found(driver, locator_type, locator, timeout=0):
                    return driver.find_element(locator_type, locator)

            #If we get here, search also fails in iframes
            driver.switch_to_default_content()
        raise NoSuchElementException, "Element not found during wait_and_find"

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

#Selenium requires an element to be visible and enabled to be
#clickable. We extend that to require it to have a tag capable
#of containing a link. NOTE: doesn't work 100%
def is_clickable(driver, full_xpath, xpath, timeout = 1):
    try:
        w = WebDriverWait(driver, timeout)
        w.until(EC.element_to_be_clickable(('xpath',xpath)))
        return XPathUtil.is_clickable(full_xpath)
    except TimeoutException, ElementNotVisibleException:
        return False

#TODO Update this. No direct access to DB right now
'''
#get and set xpaths into xpath database
def get_xpath(driver, url, name):
cur = self.db.cursor()
cur.execute("SELECT xpath FROM xpath WHERE url = ? AND name = ?",(url, name))
response = cur.fetchone()
if response == None:
return None
else:
return response[0]

def set_xpath(driver, url, name, xpath, absolute_xpath = None):
cur = self.db.cursor()
if self.mp_lock is not None:
self.mp_lock.acquire()
cur.execute("UPDATE xpath SET xpath = ?, absolute_xpath = ? \
WHERE url = ? AND name = ?", (xpath, absolute_xpath, url, name))
if cur.rowcount == 0: #occurs when record does not already exist
cur.execute("INSERT INTO xpath (name, url, xpath, absolute_xpath) VALUES (?,?,?,?)",
(name, url, xpath, absolute_xpath))
self.db.commit()
if self.mp_lock is not None:
self.mp_lock.release()
return cur.lastrowid
'''

#Scroll to the bottom of a page
def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    return

#Click an xpath using javascript -- not working correctly
#gets around visibility requirements of selenium.
#def click_xpath(driver, xpath):
# driver.execute_script('$(document.evaluate('+xpath+', document, null, 9, null).singleNodeValue).click();')
