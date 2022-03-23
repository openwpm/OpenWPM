from pathlib import Path
from typing import List, Optional, Set, Tuple

from openwpm.config import BrowserParams, ManagerParams
from openwpm.utilities import db_utils

from . import utilities as util
from .openwpm_jstest import OpenWPMJSTest


class TestJSInstrumentNonExistingWindowProperty(OpenWPMJSTest):
    # Since the window property remains non-existing, attempts to
    # access the window property's attributes first fails when evaluating
    # the non-existing window property, thus preventing us from receiving
    # events about the attributes that were attempted to be accessed
    # This is why we don't see any gets to window.nonExisting.nonExistingProp1
    # etc below

    GETS_AND_SETS = {
        ("window.nonExisting", "get", "undefined"),
        ("window.nonExisting", "get", "undefined"),
        ("window.nonExisting", "get", "undefined"),
        ("window.nonExisting", "get", "undefined"),
        ("window.nonExisting", "get", "undefined"),
        ("window.nonExisting", "get", "undefined"),
    }

    METHOD_CALLS: Set[Tuple[str, str, str]] = set()

    TEST_PAGE = "instrument_non_existing_window_property.html"
    TOP_URL = "%s/js_instrument/%s" % (util.BASE_TEST_URL, TEST_PAGE)

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=self.TOP_URL,
            top_url=self.TOP_URL,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )


class TestJSInstrumentExistingWindowProperty(OpenWPMJSTest):

    GETS_AND_SETS = {
        ("window.partiallyExisting", "get", '{"existingProp":"foo"}'),
        ("window.partiallyExisting", "get", '{"existingProp":"foo"}'),
        ("window.partiallyExisting", "get", '{"existingProp":"foo"}'),
        ("window.partiallyExisting", "get", '{"existingProp":"foo"}'),
        ("window.partiallyExisting.existingProp", "get", "foo"),
        ("window.partiallyExisting", "get", '{"existingProp":"foo"}'),
        ("window.partiallyExisting.existingProp", "set", "blah1"),
        ("window.partiallyExisting", "get", '{"existingProp":"blah1"}'),
        ("window.partiallyExisting.existingProp", "get", "blah1"),
        ("window.partiallyExisting", "get", '{"existingProp":"blah1"}'),
        ("window.partiallyExisting.nonExistingProp1", "get", "undefined"),
        ("window.partiallyExisting", "get", '{"existingProp":"blah1"}'),
        ("window.partiallyExisting.nonExistingProp1", "set", "blah1"),
        ("window.partiallyExisting", "get", '{"existingProp":"blah1"}'),
        ("window.partiallyExisting.nonExistingProp1", "get", "blah1"),
        ("window.partiallyExisting", "get", '{"existingProp":"blah1"}'),  # Note 1
        ("window.partiallyExisting.nonExistingMethod1", "get", "undefined"),  # Note 2
    }

    # Note 1: nonExistingProp1 is not enumerable even after being set
    # Note 2: nonExistingMethod1 shows up as a get rather than call

    METHOD_CALLS: Set[Tuple[str, str, str]] = set()  # Note 2

    TEST_PAGE = "instrument_existing_window_property.html"
    TOP_URL = "%s/js_instrument/%s" % (util.BASE_TEST_URL, TEST_PAGE)

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=self.TOP_URL,
            top_url=self.TOP_URL,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )


class TestJSInstrumentByPython(OpenWPMJSTest):  # noqa
    # This test tests python side configuration. But we can only test
    # built in browser APIs, so we're not using html specced objects.
    TEST_PAGE = "instrument_pyside.html"
    TOP_URL = "%s/js_instrument/%s" % (util.BASE_TEST_URL, TEST_PAGE)

    GETS_AND_SETS = {
        ("window.navigator.webdriver", "get", "true"),
        ("window.document.cookie", "set", "a=COOKIE"),
        ("window.document.cookie", "get", "a=COOKIE"),
    }
    METHOD_CALLS = {
        # In the JS we use both fetch and window.fetch
        ("window.fetch", "call", '["https://example.com"]'),
        ("window.fetch", "call", '["https://example.org"]'),
    }

    def get_config(
        self, data_dir: Optional[Path]
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = super().get_config(data_dir)
        browser_params[0].prefs = {
            "network.dns.localDomains": "example.com,example.org"
        }
        browser_params[0].js_instrument_settings = [
            # Note that the string "window.document.cookie" does not work.
            {
                "window.document": [
                    "cookie",
                ]
            },
            {
                "window.navigator": [
                    "webdriver",
                ]
            },
            {
                "window": [
                    "fetch",
                ]
            },
        ]
        return manager_params, browser_params

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=self.TOP_URL,
            top_url=self.TOP_URL,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )


class TestJSInstrumentMockWindowProperty(OpenWPMJSTest):

    GETS_AND_SETS = {
        ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
        ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
        ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
        ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
        ("window.MockClass.nonExistingProp1", "get", "undefined"),
        (
            "window.alreadyInstantiatedMockClassInstance.nonExistingProp1",
            "get",
            "undefined",
        ),
        ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
        ("window.MockClass.nonExistingProp1", "set", "blah1"),
        (
            "window.alreadyInstantiatedMockClassInstance.nonExistingProp1",
            "set",
            "blah1",
        ),
        ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
        ("window.MockClass.nonExistingProp1", "get", "blah1"),
        (
            "window.alreadyInstantiatedMockClassInstance.nonExistingProp1",
            "get",
            "blah1",
        ),
        ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
        ("window.MockClass.nonExistingMethod1", "get", "undefined"),  # Note 1
        (
            "window.alreadyInstantiatedMockClassInstance.nonExistingMethod1",
            "get",
            "undefined",
        ),  # Note 1
        ("window.newMockClassInstance", "get", "{}"),
        ("window.newMockClassInstance", "get", "{}"),
        ("window.newMockClassInstance", "get", "{}"),
        ("window.MockClass.nonExistingProp1", "get", "blah1"),  # Note 2
        ("window.newMockClassInstance", "get", "{}"),
        ("window.MockClass.nonExistingProp1", "set", "blah1"),
        ("window.newMockClassInstance", "get", "{}"),
        ("window.MockClass.nonExistingProp1", "get", "blah1"),
        ("window.newMockClassInstance", "get", "{}"),
        ("window.MockClass.nonExistingMethod1", "get", "undefined"),  # Note 1
    }

    # Note 1: nonExistingMethod1 shows up as a get rather than call
    # Note 2: This may be a bug - the new instance
    #         should not have a value here yet

    METHOD_CALLS = {
        ("window.MockClass", "call", None),
    }

    TEST_PAGE = "instrument_mock_window_property.html"
    TOP_URL = "%s/js_instrument/%s" % (util.BASE_TEST_URL, TEST_PAGE)

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)

        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=self.TOP_URL,
            top_url=self.TOP_URL,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )


class TestJSInstrument(OpenWPMJSTest):

    GETS_AND_SETS = {
        ("prop1", "get", "prop1"),
        ("prop1", "set", "blah1"),
        ("prop1", "get", "blah1"),
        ("prop2", "get", "prop2"),
        ("prop2", "set", "blah2"),
        ("prop2", "get", "blah2"),
        ("objProp", "get", '{"hello":"world"}'),
        ("objProp", "set", '{"key":"value"}'),
        ("objProp", "get", '{"key":"value"}'),
        ("prop3", "get", "default-value"),
        ("prop3", "set", "blah3"),
        ("prop3", "get", "blah3"),
        ("method1", "set", "FUNCTION"),
        ("method1", "set", "now static"),
        ("method1", "get", "now static"),
        ("prop1", "set", "FUNCTION"),
        (
            "nestedObj",
            "get",
            '{"prop1":"default1","prop2":"default2","method1":"FUNCTION"}',
        ),
    }

    METHOD_CALLS = {
        ("prop1", "call", '["now accepting arguments"]'),
        ("method1", "call", '["hello","{\\"world\\":true}"]'),
        ("method1", "call", '["new argument"]'),
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
        ("window.test2.nestedObj.doubleNested.method1", "set", "FUNCTION"),
    }

    RECURSIVE_METHOD_CALLS = {
        ("window.test2.nestedObj.method1", "call", '["arg-before"]'),
        ("window.test2.nestedObj.method1", "call", '["arg-after"]'),
        ("window.test2.nestedObj.doubleNested.method1", "call", '["blah"]'),
    }

    RECURSIVE_PROP_SET = {
        ("window.test2.l1.l2.l3.l4.l5.prop", "get", "level5prop"),
        ("window.test2.l1.l2.l3.l4.l5.l6", "get", '{"prop":"level6prop"}'),
    }

    SET_PREVENT_CALLS = {
        ("window.test3.method1", "call", None),
        ("window.test3.obj1.method2", "call", None),
    }

    SET_PREVENT_GETS_AND_SETS = {
        ("window.test3.prop1", "set", "newprop1"),
        ("window.test3.method1", "set(prevented)", "FUNCTION"),
        ("window.test3.obj1", "set(prevented)", '{"new":"object"}'),
        ("window.test3.obj1.prop2", "set", "newprop2"),
        ("window.test3.obj1.method2", "set(prevented)", "FUNCTION"),
        ("window.test3.obj1.obj2", "set(prevented)", '{"new":"object2"}'),
        ("window.test3.prop1", "get", "newprop1"),
        ("window.test3.obj1.obj2", "get", '{"testobj":"nested"}'),
        ("window.test3.obj1.prop2", "get", "newprop2"),
    }

    TOP_URL = "%s/js_instrument/instrument_object.html" % util.BASE_TEST_URL
    FRAME1_URL = "%s/js_instrument/framed1.html" % util.BASE_TEST_URL
    FRAME2_URL = "%s/js_instrument/framed2.html" % util.BASE_TEST_URL

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/instrument_object.html")
        self._check_calls(
            db=db,
            symbol_prefix="window.test.",
            doc_url=self.TOP_URL,
            top_url=self.TOP_URL,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )
        self._check_calls(
            db=db,
            symbol_prefix="window.frame1Test.",
            doc_url=self.FRAME1_URL,
            top_url=self.TOP_URL,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )
        self._check_calls(
            db=db,
            symbol_prefix="window.frame2Test.",
            doc_url=self.FRAME2_URL,
            top_url=self.TOP_URL,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )

        # Check calls of recursive instrumentation
        observed_gets_and_sets = set()
        observed_calls = set()
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        for row in rows:
            if not row["symbol"].startswith("window.test2.nestedObj"):
                continue
            assert row["document_url"] == self.TOP_URL
            assert row["top_level_url"] == self.TOP_URL
            if row["operation"] == "get" or row["operation"] == "set":
                observed_gets_and_sets.add(
                    (row["symbol"], row["operation"], row["value"])
                )
            else:
                observed_calls.add((row["symbol"], row["operation"], row["arguments"]))
        assert observed_calls == self.RECURSIVE_METHOD_CALLS
        assert observed_gets_and_sets == self.RECURSIVE_GETS_AND_SETS

        # Check that calls not present after default recursion limit (5)
        # We should only see the window.test2.l1.l2.l3.l4.l5.prop access
        # and not window.test2.l1.l2.l3.l4.l5.l6.prop access.
        prop_access = set()
        for row in rows:
            if not row["symbol"].startswith("window.test2.l1"):
                continue
            assert row["document_url"] == self.TOP_URL
            assert row["top_level_url"] == self.TOP_URL
            prop_access.add((row["symbol"], row["operation"], row["value"]))
        assert prop_access == self.RECURSIVE_PROP_SET

        # Check calls of object with sets prevented
        observed_gets_and_sets = set()
        observed_calls = set()
        for row in rows:
            if not row["symbol"].startswith("window.test3"):
                continue
            assert row["document_url"] == self.TOP_URL
            assert row["top_level_url"] == self.TOP_URL
            if row["operation"] == "call":
                observed_calls.add((row["symbol"], row["operation"], row["arguments"]))
            else:
                observed_gets_and_sets.add(
                    (row["symbol"], row["operation"], row["value"])
                )
        assert observed_calls == self.SET_PREVENT_CALLS
        assert observed_gets_and_sets == self.SET_PREVENT_GETS_AND_SETS


class TestJSInstrumentRecursiveProperties(OpenWPMJSTest):
    # Since the window property remains non-existing, attempts to
    # access the window property's attributes first fails when evaluating
    # the non-existing window property, thus preventing us from receiving
    # events about the attributes that were attempted to be accessed
    # This is why we don't see any gets to window.nonExisting.nonExistingProp1
    # etc below

    GETS_AND_SETS = {
        ("window.test.prop1", "get", "test_prop1"),
        # At the nested level we have both because the propertiesToInstrument
        # was not propogated down.
        ("window.test.test.prop1", "get", "test_test_prop1"),
        ("window.test.test.prop2", "get", "test_test_prop2"),
    }

    METHOD_CALLS: Set[Tuple[str, str, str]] = set()

    TEST_PAGE = "instrument_do_not_recurse_properties_to_instrument.html"
    TOP_URL = "%s/js_instrument/%s" % (util.BASE_TEST_URL, TEST_PAGE)

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=self.TOP_URL,
            top_url=self.TOP_URL,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )
