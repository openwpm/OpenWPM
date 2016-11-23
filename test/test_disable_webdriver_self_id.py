import pytest # NOQA
import os
import utilities
from openwpmtest import OpenWPMTest
from ..automation import TaskManager
from ..automation import CommandSequence

class TestDisableWebdriverSelfId(OpenWPMTest):
    """Verify webdriver self-identification removed from DOM.

    Selenium webdriver self-identifies in two locations in the DOM, see:
    * https://github.com/SeleniumHQ/selenium/blob/b82512999938d41f6765ce8017284dcabe437d4c/javascript/firefox-driver/extension/content/server.js#L49
    * https://github.com/SeleniumHQ/selenium/blob/b82512999938d41f6765ce8017284dcabe437d4c/javascript/firefox-driver/extension/content/dommessenger.js#L98
    """
    NUM_BROWSERS = 1

    def get_config(self, data_dir):
        manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        browser_params[0]['headless'] = True
        manager_params['db'] = os.path.join(manager_params['data_directory'],
                                            manager_params['database_name'])
        return manager_params, browser_params

    def test_self_id_present(self, tmpdir):
        def check_webdriver_id_exists(**kwargs):
            """ Check if webdriver self-identification attributes in the DOM"""
            driver = kwargs['driver']

            # Check if document element has `webdriver` attribute
            assert 'true' == driver.execute_script(
                    'return document.documentElement.getAttribute("webdriver")')
            # Check if navigator has webdriver property
            assert driver.execute_script('return navigator.webdriver')
            assert driver.execute_script('return !!("webdriver" in navigator)')

        manager_params, browser_params = self.get_config(str(tmpdir))
        browser_params[0]['disable_webdriver_self_id'] = False
        manager = TaskManager.TaskManager(manager_params, browser_params)
        test_url = utilities.BASE_TEST_URL + '/simple_a.html'
        cs = CommandSequence.CommandSequence(test_url, blocking=True)
        cs.get(sleep=5, timeout=60)
        cs.run_custom_function(check_webdriver_id_exists)
        manager.execute_command_sequence(cs)
        manager.close(post_process=False)

    def test_disable_self_id(self, tmpdir):
        def check_webdriver_id_not_exists(**kwargs):
            """ Check if webdriver self-identification attributes in the DOM"""
            driver = kwargs['driver']

            # Check if document element has `webdriver` attribute
            assert 'true' != driver.execute_script(
                    'return document.documentElement.getAttribute("webdriver")')
            # Check if navigator has webdriver property
            assert not driver.execute_script('return navigator.webdriver')
            assert not driver.execute_script('return !!("webdriver" in navigator)')
        manager_params, browser_params = self.get_config(str(tmpdir))
        browser_params[0]['disable_webdriver_self_id'] = True
        manager = TaskManager.TaskManager(manager_params, browser_params)
        test_url = utilities.BASE_TEST_URL + '/simple_a.html'
        cs = CommandSequence.CommandSequence(test_url, blocking=True)
        cs.get(sleep=5, timeout=60)
        cs.run_custom_function(check_webdriver_id_not_exists)
        manager.execute_command_sequence(cs)
        manager.close(post_process=False)
