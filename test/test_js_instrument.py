
import re

from ..automation.utilities import db_utils
from . import utilities as util
from .openwpmtest import OpenWPMTest

GETS_AND_SETS = {
    ("prop1", "get", "prop1"),
    ("prop1", "set", "blah1"),
    ("prop1", "get", "blah1"),
    ("prop2", "get", "prop2"),
    ("prop2", "set", "blah2"),
    ("prop2", "get", "blah2"),
    ("objProp", "get", "{\"hello\":\"world\"}"),
    ("objProp", "set", "{\"key\":\"value\"}"),
    ("objProp", "get", "{\"key\":\"value\"}"),
    ("prop3", "get", "default-value"),
    ("prop3", "set", "blah3"),
    ("prop3", "get", "blah3"),
    ('method1', 'set', 'FUNCTION'),
    ('method1', 'set', 'now static'),
    ('method1', 'get', 'now static'),
    ('prop1', 'set', 'FUNCTION'),
    ('nestedObj', 'get',
     '{"prop1":"default1","prop2":"default2","method1":"FUNCTION"}')
}

METHOD_CALLS = {
    ('prop1', 'call', '["now accepting arguments"]'),
    ('method1', 'call', '["hello","{\\\"world\\\":true}"]'),
    ('method1', 'call', '["new argument"]')
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
    ('window.test2.nestedObj.method1', 'call', '["arg-before"]'),
    ('window.test2.nestedObj.method1', 'call', '["arg-after"]'),
    ('window.test2.nestedObj.doubleNested.method1', 'call', '["blah"]')
}

RECURSIVE_PROP_SET = {
    ('window.test2.l1.l2.l3.l4.l5.prop', 'get', 'level5prop'),
    ('window.test2.l1.l2.l3.l4.l5.l6', 'get', '{"prop":"level6prop"}')
}

SET_PREVENT_CALLS = {
    (u'window.test3.method1', u'call', None),
    ('window.test3.obj1.method2', 'call', None)
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

TOP_URL = u"%s/js_instrument/instrument_object.html" % util.BASE_TEST_URL
FRAME1_URL = u"%s/js_instrument/framed1.html" % util.BASE_TEST_URL
FRAME2_URL = u"%s/js_instrument/framed2.html" % util.BASE_TEST_URL


class TestJSInstrument(OpenWPMTest):

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0]['js_instrument'] = True
        manager_params['testing'] = True
        return manager_params, browser_params

    def _check_calls(self, rows, symbol_prefix, doc_url, top_url):
        """Helper to check method calls and accesses in each frame"""
        observed_gets_and_sets = set()
        observed_calls = set()
        for row in rows:
            if not row['symbol'].startswith(symbol_prefix):
                continue
            symbol = re.sub(symbol_prefix, '', row['symbol'])
            assert row['document_url'] == doc_url
            assert row['top_level_url'] == top_url
            if row['operation'] == 'get' or row['operation'] == 'set':
                observed_gets_and_sets.add(
                    (symbol, row['operation'], row['value'])
                )
            else:
                observed_calls.add(
                    (symbol, row['operation'], row['arguments'])
                )
        assert observed_calls == METHOD_CALLS
        assert observed_gets_and_sets == GETS_AND_SETS

    def test_instrument_object(self):
        """ Ensure instrumentObject logs all property gets, sets, and calls """
        db = self.visit('/js_instrument/instrument_object.html')
        rows = db_utils.get_javascript_entries(db, all_columns=True)

        # Check calls of non-recursive instrumentation
        self._check_calls(rows, 'window.test.', TOP_URL, TOP_URL)
        self._check_calls(rows, 'window.frame1Test.', FRAME1_URL, TOP_URL)
        self._check_calls(rows, 'window.frame2Test.', FRAME2_URL, TOP_URL)

        # Check calls of recursive instrumentation
        observed_gets_and_sets = set()
        observed_calls = set()
        for row in rows:
            if not row['symbol'].startswith('window.test2.nestedObj'):
                continue
            assert row['document_url'] == TOP_URL
            assert row['top_level_url'] == TOP_URL
            if row['operation'] == 'get' or row['operation'] == 'set':
                observed_gets_and_sets.add(
                    (row['symbol'], row['operation'], row['value'])
                )
            else:
                observed_calls.add(
                    (row['symbol'], row['operation'], row['arguments'])
                )
        assert observed_calls == RECURSIVE_METHOD_CALLS
        assert observed_gets_and_sets == RECURSIVE_GETS_AND_SETS

        # Check that calls not present after default recursion limit (5)
        # We should only see the window.test2.l1.l2.l3.l4.l5.prop access
        # and not window.test2.l1.l2.l3.l4.l5.l6.prop access.
        prop_access = set()
        for row in rows:
            if not row['symbol'].startswith('window.test2.l1'):
                continue
            assert row['document_url'] == TOP_URL
            assert row['top_level_url'] == TOP_URL
            prop_access.add(
                (row['symbol'], row['operation'], row['value'])
            )
        assert prop_access == RECURSIVE_PROP_SET

        # Check calls of object with sets prevented
        observed_gets_and_sets = set()
        observed_calls = set()
        for row in rows:
            if not row['symbol'].startswith('window.test3'):
                continue
            assert row['document_url'] == TOP_URL
            assert row['top_level_url'] == TOP_URL
            if row['operation'] == 'call':
                observed_calls.add(
                    (row['symbol'], row['operation'], row['arguments'])
                )
            else:
                observed_gets_and_sets.add(
                    (row['symbol'], row['operation'], row['value'])
                )
        assert observed_calls == SET_PREVENT_CALLS
        assert observed_gets_and_sets == SET_PREVENT_GETS_AND_SETS
