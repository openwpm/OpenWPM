import pytest
import utilities
from openwpmtest import OpenWPMTest
from ..automation import TaskManager
from ..automation import CommandSequence
from ..automation.utilities import db_utils


class TestDisableWebdriverSelfId(OpenWPMTest):
    """Verify webdriver self-identification removed from DOM.

    Selenium webdriver self-identifies in two locations in the DOM, see:
    * https://github.com/SeleniumHQ/selenium/blob/b82512999938d41f6765ce8017284dcabe437d4c/javascript/firefox-driver/extension/content/server.js#L49
    * https://github.com/SeleniumHQ/selenium/blob/b82512999938d41f6765ce8017284dcabe437d4c/javascript/firefox-driver/extension/content/dommessenger.js#L98
    """

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)

    def test_self_id_present(self):
        manager_params, browser_params = self.get_config()
        browser_params[0]['disable_webdriver_self_id'] = False
        manager = TaskManager.TaskManager(manager_params, browser_params)
        test_url = utilities.BASE_TEST_URL + '/simple_a.html'

        def check_webdriver_id_not_exists(**kwargs):
            """ Check if webdriver self-identification attributes in the DOM"""
            driver = kwargs['driver']
            # Check if document element has `webdriver` attribute
            assert driver.execute_script(
                    'return null === document.documentElement.getAttribute("webdriver")')
            # Check if navigator has webdriver property
            assert driver.execute_script('return undefined === navigator.webdriver')
            assert driver.execute_script('return false === ("webdriver" in navigator)')

        cs = CommandSequence.CommandSequence(test_url, blocking=True)
        cs.get(sleep=5, timeout=60)
        cs.run_custom_function(check_webdriver_id_not_exists)
        with pytest.raises(AssertionError):
            manager.execute_command_sequence(cs)
            manager.close()

    def test_disable_self_id(self):
        manager_params, browser_params = self.get_config()
        browser_params[0]['disable_webdriver_self_id'] = True
        manager = TaskManager.TaskManager(manager_params, browser_params)
        test_url = utilities.BASE_TEST_URL + '/simple_a.html'

        def check_webdriver_id_not_exists(**kwargs):
            """ Check if webdriver self-identification attributes in the DOM"""
            driver = kwargs['driver']
            # Check if document element has `webdriver` attribute
            assert driver.execute_script(
                    'return null === document.documentElement.getAttribute("webdriver")')
            # Check if navigator has webdriver property
            assert driver.execute_script('return undefined === navigator.webdriver')
            assert driver.execute_script('return false === ("webdriver" in navigator)')

        cs = CommandSequence.CommandSequence(test_url, blocking=True)
        cs.get(sleep=5, timeout=60)
        cs.run_custom_function(check_webdriver_id_not_exists)
        manager.execute_command_sequence(cs)
        manager.close()
        assert not db_utils.any_command_failed(manager_params['db'])

    def test_define_property(self):
        manager_params, browser_params = self.get_config()
        browser_params[0]['disable_webdriver_self_id'] = True
        manager = TaskManager.TaskManager(manager_params, browser_params)
        test_url = utilities.BASE_TEST_URL + '/simple_a.html'

        def check_define_property_works(**kwargs):
            """ verify that define property works as expected """
            driver = kwargs['driver']
            # Set the `webdriver` attribute (our instrumentation should only
            # remove the first instance, set by Selenium).
            assert driver.execute_script("return undefined === navigator.webdriver")
            driver.execute_script("""
                Object.defineProperty(navigator,'webdriver',{
                    configurable: true,
                    value:true
                });""")
            assert driver.execute_script("return navigator.webdriver")
            driver.execute_script("""
                Object.defineProperty(navigator,'webdriver',{
                    configurable: true,
                    value:'blah'
                });""")
            assert driver.execute_script("return 'blah' === navigator.webdriver")
            driver.execute_script("""
                Object.defineProperty(navigator,'webdriver',{
                    configurable: true,
                    value:'test'
                });""")
            assert driver.execute_script("return 'test' === navigator.webdriver")

            # Setting on a custom object
            assert driver.execute_script("""
                var someObject = {
                    prop1:"testing"
                };
                Object.defineProperty(someObject,'testProp',{
                    configurable: true,
                    enumerable: false,
                    get: function() {
                        return this.prop1;
                    },
                    set: function(newValue) {
                        this.prop1 = newValue;
                    }
                });
                return 'testing' === someObject.testProp;""")
            # local variables not available to next `execute_script`. Need to recreate
            assert not driver.execute_script("""
                var someObject = {
                    prop1:"testing"
                };
                Object.defineProperty(someObject,'testProp',{
                    configurable: true,
                    enumerable: false,
                    get: function() {
                        return this.prop1;
                    },
                    set: function(newValue) {
                        this.prop1 = newValue;
                    }
                });
                return 'testProp' in Object.keys(someObject);""")

            # Setting on a DOM object
            driver.execute_script("""
                Object.defineProperty(window,'betterName',{
                    get: function() {
                        return this.name;
                    },
                    set: function(newValue) {
                        this.name = newValue;
                    }
                });""")
            assert driver.execute_script("return '' === window.betterName;")
            driver.execute_script("window.betterName = 'blah';")
            assert driver.execute_script("return 'blah' === window.betterName;")
            assert driver.execute_script("return 'blah' === window.name;")

        cs = CommandSequence.CommandSequence(test_url, blocking=True)
        cs.get(sleep=5, timeout=60)
        cs.run_custom_function(check_define_property_works)
        manager.execute_command_sequence(cs)
        manager.close()
        assert not db_utils.any_command_failed(manager_params['db'])
