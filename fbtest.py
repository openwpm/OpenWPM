from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time


def fblogin(site, email, password):
    driver = webdriver.Firefox()
    #driver.implicitly_wait(0.5)
    wait = WebDriverWait(driver, 10)
    driver.get(site)
    signin = driver.find_element_by_id('header-signin')
    signin.click()
    fbbutton = driver.find_element_by_class_name('fb-button')
    fbbutton.click()
    
    driver.switch_to_window(driver.window_handles[-1])

    emailfield = wait.until(EC.presence_of_element_located((By.ID,'email')))
    emailfield.send_keys(email)
    passwordfield = driver.find_element_by_id('pass')
    passwordfield.send_keys(password)
    login = driver.find_element_by_name("login")
    login.click()
    time.sleep(1)
    driver.switch_to_window(driver.window_handles[-1])

    action = ActionChains(driver)
    signoutselect = driver.find_element_by_id('usernav-profile-link')
    action.move_to_element(signoutselect).perform()
    signout = wait.until(EC.element_to_be_clickable((By.ID,'usernav-signout')))
    signout.click()
    #driver.close()


if __name__ == '__main__':
    # Put email and password
    fblogin('http://www.buzzfeed.com', 'nayebir@gmail.com', 'yugiho')
