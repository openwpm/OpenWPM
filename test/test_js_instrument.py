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
    ("window.test.prop3", "get", "blah3"),
    ('window.test.method1', 'set', 'FUNCTION'),
    ('window.test.method1', 'set', 'now static'),
    ('window.test.method1', 'get', 'now static'),
    ('window.test.prop1', 'set', 'FUNCTION'),
    ('window.test.nestedObj', 'get',
     '{"prop1":"default1","prop2":"default2","method1":"FUNCTION"}')
}

METHOD_CALLS = {
    ("window.test.method1", "call", 0, "hello"),
    ("window.test.method1", "call", 1, "{\"world\":true}"),
    ("window.test.method1", "call", 0, "new argument"),
    ("window.test.prop1", "call", 0, "now accepting arugments")
}

RECURSIVE_GETS_AND_SETS = {
    ("window.test2.nestedObj.prop1", "get", "default1"),
    ("window.test2.nestedObj.prop1", "set", "updatedprop1"),
    ("window.test2.nestedObj.prop1", "get", "updatedprop1"),
    ("window.test2.nestedObj.prop2", "get", "default2"),
    ("window.test2.nestedObj.method1", "set", "FUNCTION"),
    ("window.test2.nestedObj.doubleNested.prop1", "get", "double default"),
    ("window.test2.nestedObj.doubleNested.prop1", "set", "doubleprop1"),
    ("window.test2.nestedObj.doubleNested.prop1", "get", "doubleprop1"),
    ("window.test2.nestedObj.doubleNested.method1", "set", "FUNCTION")
}

RECURSIVE_METHOD_CALLS = {
    ("window.test2.nestedObj.method1", "call", 0, "arg-before"),
    ("window.test2.nestedObj.method1", "call", 0, "arg-after"),
    ("window.test2.nestedObj.doubleNested.method1", "call", 0, "blah")
}

RECURSIVE_PROP_SET = {
    ('window.test2.l1.l2.l3.l4.l5.prop', 'get', 'level5prop'),
    ('window.test2.l1.l2.l3.l4.l5.l6', 'get', '{"prop":"level6prop"}')
}

SET_PREVENT_CALLS = {
    (u'window.test3.method1', u'call', None, None),
    ('window.test3.obj1.method2', 'call', None, None)
}

SET_PREVENT_GETS_AND_SETS = {
    (u'window.test3.prop1', u'set', u'newprop1'),
    ('window.test3.method1', 'set(prevented)', 'FUNCTION'),
    ('window.test3.obj1', 'set(prevented)', '{"new":"object"}'),
    (u'window.test3.obj1.prop2', u'set', u'newprop2'),
    ('window.test3.obj1.method2', 'set(prevented)', 'FUNCTION'),
    ('window.test3.obj1.obj2', 'set(prevented)', '{"new":"object2"}'),
    (u'window.test3.prop1', u'get', u'newprop1'),
    ('window.test3.obj1.obj2', 'get', '{"testobj":"nested"}'),
    ('window.test3.obj1.prop2', 'get', 'newprop2'),
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

        # Check calls of non-recursive instrumentation
        observed_gets_and_sets = set()
        observed_calls = set()
        for script_url, symbol, operation, value, pindex, pvalue in rows:
            if not symbol.startswith('window.test.'):
                continue
            if operation == 'get' or operation == 'set':
                observed_gets_and_sets.add((symbol, operation, value))
            else:
                observed_calls.add((symbol, operation, pindex, pvalue))
        assert observed_calls == METHOD_CALLS
        assert observed_gets_and_sets == GETS_AND_SETS

        # Check calls of recursive instrumentation
        observed_gets_and_sets = set()
        observed_calls = set()
        for script_url, symbol, operation, value, pindex, pvalue in rows:
            if not symbol.startswith('window.test2.nestedObj'):
                continue
            if operation == 'get' or operation == 'set':
                observed_gets_and_sets.add((symbol, operation, value))
            else:
                observed_calls.add((symbol, operation, pindex, pvalue))
        assert observed_calls == RECURSIVE_METHOD_CALLS
        assert observed_gets_and_sets == RECURSIVE_GETS_AND_SETS

        # Check that calls not present after default recursion limit (5)
        # We should only see the window.test2.l1.l2.l3.l4.l5.prop access
        # and not window.test2.l1.l2.l3.l4.l5.l6.prop access.
        prop_access = set()
        for script_url, symbol, operation, value, pindex, pvalue in rows:
            if not symbol.startswith('window.test2.l1'):
                continue
            prop_access.add((symbol, operation, value))
        assert prop_access == RECURSIVE_PROP_SET

        # Check calls of object with sets prevented
        observed_gets_and_sets = set()
        observed_calls = set()
        for script_url, symbol, operation, value, pindex, pvalue in rows:
            if not symbol.startswith('window.test3'):
                continue
            if operation == 'call':
                observed_calls.add((symbol, operation, pindex, pvalue))
            else:
                observed_gets_and_sets.add((symbol, operation, value))
        assert observed_calls == SET_PREVENT_CALLS
        assert observed_gets_and_sets == SET_PREVENT_GETS_AND_SETS
