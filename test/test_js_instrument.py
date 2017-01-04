from openwpmtest import OpenWPMTest
from ..automation.utilities import db_utils

GETS_AND_SETS = {
    ("window.test.prop1", "get", "prop1"),
    ("window.test.prop1", "set", "blah1"),
    ("window.test.prop1", "get", "blah1"),
    ("window.test.prop2", "get", "prop2"),
    ("window.test.prop2", "set", "blah2"),
    ("window.test.prop2", "get", "blah2"),
    ("window.test.objProp", "get", "{\"hello\":\"world\"}"),
    ("window.test.objProp", "set", "{\"key\":\"value\"}"),
    ("window.test.objProp", "get", "{\"key\":\"value\"}"),
    ("window.test.prop3", "get", "default-value"),
    ("window.test.prop3", "set", "blah3"),
    ("window.test.prop3", "get", "blah3")
}

METHOD_CALLS = {
    ("window.test.method1", "call", 0, "hello"),
    ("window.test.method1", "call", 1, "{\"world\":true}")
}


class TestJSInstrument(OpenWPMTest):

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0]['js_instrument'] = True
        manager_params['testing'] = True
        return manager_params, browser_params

    def test_instrument_object(self):
        """ Ensure instrumentObject logs all property gets, sets, and calls """
        db = self.visit('/instrument_object.html')
        rows = db_utils.get_javascript_entries(db)
        observed_gets_and_sets = set()
        observed_calls = set()
        for script_url, symbol, operation, value, pindex, pvalue in rows:
            if operation == 'get' or operation == 'set':
                observed_gets_and_sets.add((symbol, operation, value))
            else:
                observed_calls.add((symbol, operation, pindex, pvalue))
        assert observed_calls == METHOD_CALLS
        assert observed_gets_and_sets == GETS_AND_SETS
