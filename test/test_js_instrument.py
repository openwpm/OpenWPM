from pathlib import Path
from typing import List, Optional, Set, Tuple

from openwpm.config import BrowserParams, ManagerParams
from openwpm.utilities import db_utils

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

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        top_url = f"{self.server.base}/js_instrument/{self.TEST_PAGE}"
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=top_url,
            top_url=top_url,
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

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        top_url = f"{self.server.base}/js_instrument/{self.TEST_PAGE}"
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=top_url,
            top_url=top_url,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )


class TestJSInstrumentByPython(OpenWPMJSTest):  # noqa
    # This test tests python side configuration. But we can only test
    # built in browser APIs, so we're not using html specced objects.
    TEST_PAGE = "instrument_pyside.html"

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
        top_url = f"{self.server.base}/js_instrument/{self.TEST_PAGE}"
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=top_url,
            top_url=top_url,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )


class TestJSInstrumentNoObjectGlobalLeak(OpenWPMJSTest):
    """The legacy instrument must not assign its getPropertyDescriptor /
    getPropertyNames helpers as own properties of the page-world ``Object``
    global (#1187).

    The instrument is injected as a page-world ``<script>``, so anything it
    assigns onto ``Object`` stays visible to page scripts after the instrument
    runs. A one-liner like ``typeof Object.getPropertyDescriptor === "function"``
    then detects OpenWPM even with empty settings -- a config-independent
    fingerprinting tell named in Krumnow, Jonker & Karsch (arXiv:2205.08890).
    The fix keeps both helpers as closure-locals inside the injected instrument.

    The test page reads whether either name is an own property of the page-world
    ``Object`` and encodes the booleans into the arguments of an instrumented
    ``fetch`` call. Native ``Object`` carries neither helper, so a clean
    instrument logs ``gpd-false`` / ``gpn-false``; the leaking instrument would
    log ``gpd-true`` / ``gpn-true``.
    """

    TEST_PAGE = "instrument_no_object_global_leak.html"

    METHOD_CALLS = {
        (
            "window.fetch",
            "call",
            '["https://gpd-false.example.com/gpn-false"]',
        ),
    }
    GETS_AND_SETS: Set[Tuple[str, str, str]] = set()

    def get_config(
        self, data_dir: Optional[Path]
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = super().get_config(data_dir)
        browser_params[0].prefs = {
            "network.dns.localDomains": ("gpd-false.example.com,gpd-true.example.com")
        }
        browser_params[0].js_instrument_settings = [
            {
                "window": [
                    "fetch",
                ]
            },
        ]
        return manager_params, browser_params

    def test_instrument_object(self):
        """The page-world Object exposes neither helper as an own property."""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        top_url = f"{self.server.base}/js_instrument/{self.TEST_PAGE}"
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=top_url,
            top_url=top_url,
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

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        top_url = f"{self.server.base}/js_instrument/{self.TEST_PAGE}"

        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=top_url,
            top_url=top_url,
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

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/instrument_object.html")
        base = self.server.base
        top_url = f"{base}/js_instrument/instrument_object.html"
        frame1_url = f"{base}/js_instrument/framed1.html"
        frame2_url = f"{base}/js_instrument/framed2.html"
        self._check_calls(
            db=db,
            symbol_prefix="window.test.",
            doc_url=top_url,
            top_url=top_url,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )
        self._check_calls(
            db=db,
            symbol_prefix="window.frame1Test.",
            doc_url=frame1_url,
            top_url=top_url,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )
        self._check_calls(
            db=db,
            symbol_prefix="window.frame2Test.",
            doc_url=frame2_url,
            top_url=top_url,
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
            assert row["document_url"] == top_url
            assert row["top_level_url"] == top_url
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
            assert row["document_url"] == top_url
            assert row["top_level_url"] == top_url
            prop_access.add((row["symbol"], row["operation"], row["value"]))
        assert prop_access == self.RECURSIVE_PROP_SET

        # Check calls of object with sets prevented
        observed_gets_and_sets = set()
        observed_calls = set()
        for row in rows:
            if not row["symbol"].startswith("window.test3"):
                continue
            assert row["document_url"] == top_url
            assert row["top_level_url"] == top_url
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

    def test_instrument_object(self):
        """Ensure instrumentObject logs all property gets, sets, and calls"""
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)
        top_url = f"{self.server.base}/js_instrument/{self.TEST_PAGE}"
        self._check_calls(
            db=db,
            symbol_prefix="",
            doc_url=top_url,
            top_url=top_url,
            expected_method_calls=self.METHOD_CALLS,
            expected_gets_and_sets=self.GETS_AND_SETS,
        )


class TestJSInstrumentFailurePropagates(OpenWPMJSTest):
    """An instrument target that cannot be resolved/instrumented is fatal.

    Incomplete instrumentation means the browser would record an invalid
    measurement, so the desired behavior is that such a browser *never*
    produces a successful visit: every GetCommand fails with a
    ``JS instrumentation failed`` error, no ``javascript`` data is recorded,
    and the visit is marked incomplete. This is intentionally the opposite of
    silently skipping the failing target and continuing to collect partial
    data.

    ``instrument_pyside.html`` is reused on purpose: with a *valid* config it
    exercises instrumented APIs (cookies, ``fetch``) that populate the
    ``javascript`` table (see ``TestJSInstrumentByPython``). Asserting that the
    table stays empty here therefore proves the browser never started
    measuring, rather than merely that one command returned an error.
    """

    TEST_PAGE = "instrument_pyside.html"

    def get_config(
        self, data_dir: Optional[Path]
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = super().get_config(data_dir)
        # ``window.NonExistent`` is undefined, so resolving
        # ``window.NonExistent.deeplyMissing`` throws while setting up the
        # instrumentation. This stands in for a real-world misconfiguration
        # such as instrumenting a Worker-only global on the window scope.
        #
        # Two distinct failing targets are configured so the test also
        # verifies that *every* failure is reported, not just the first or
        # last one: ``instrumentJS`` runs all requests to completion and
        # aggregates their messages into a single error.
        browser_params[0].js_instrument_settings = [
            {"window.NonExistent.deeplyMissing": ["foo"]},
            {"window.AlsoMissing.deeplyMissing": ["bar"]},
        ]
        return manager_params, browser_params

    def test_failure_prevents_measurement(self):
        db = self.visit("/js_instrument/%s" % self.TEST_PAGE)

        # The GetCommand must surface the instrumentation failure.
        get_rows = db_utils.query_db(
            db,
            "SELECT command_status, error FROM crawl_history "
            "WHERE command = 'GetCommand'",
        )
        assert get_rows, "expected a GetCommand row in crawl_history"
        statuses = [row["command_status"] for row in get_rows]
        errors = [row["error"] or "" for row in get_rows]
        assert any(
            "JS instrumentation failed" in e for e in errors
        ), f"expected instrumentation error message, got errors={errors}"
        assert any(
            "window.NonExistent.deeplyMissing" in e for e in errors
        ), f"expected failing item name in error, got errors={errors}"
        # Both failing targets must appear in the same aggregated error: the
        # instrument loop runs to completion and reports every failure, so a
        # regression to first- or last-only reporting would drop one of these.
        assert any(
            "window.NonExistent.deeplyMissing" in e
            and "window.AlsoMissing.deeplyMissing" in e
            for e in errors
        ), f"expected both failing item names in a single error, got errors={errors}"

        # The browser must never become healthy: no GetCommand may succeed.
        # If it ever returned "ok" the browser would have started measuring
        # despite the incomplete instrumentation.
        assert "ok" not in statuses, (
            "no GetCommand should succeed when instrumentation fails, "
            f"got statuses={statuses}"
        )

        # No measurement data may be collected. ``instrument_pyside.html``
        # would populate this table under a valid config; an empty table
        # confirms the browser never started collecting.
        js_rows = db_utils.get_javascript_entries(db)
        assert not js_rows, (
            "expected no javascript rows when instrumentation fails, "
            f"got {len(js_rows)} rows"
        )

        # The visit must be recorded as incomplete (finalized success=False).
        incomplete = db_utils.query_db(db, "SELECT visit_id FROM incomplete_visits")
        assert incomplete, "expected the failed visit to be marked incomplete"
