import pytest # NOQA
import hashlib
import os

import utilities
import expected
from openwpmtest import OpenWPMTest
from ..automation import TaskManager
from ..automation.utilities.platform_utils import parse_http_stack_trace_str


class TestHTTPInstrument(OpenWPMTest):
    NUM_BROWSERS = 1

    def get_config(self, data_dir):
        manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        browser_params[0]['headless'] = True
        browser_params[0]['http_instrument'] = True
        browser_params[0]['save_javascript'] = True
        manager_params['db'] = os.path.join(manager_params['data_directory'],
                                            manager_params['database_name'])
        return manager_params, browser_params

    def test_page_visit(self, tmpdir):
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        db = self.visit(test_url, str(tmpdir))

        # HTTP Requests
        rows = utilities.query_db(db, (
            "SELECT url, top_level_url, is_XHR, is_frame_load, is_full_page, "
            "is_third_party_channel, is_third_party_window, triggering_origin "
            "loading_origin, loading_href, content_policy_type FROM http_requests"))
        observed_records = set()
        for row in rows:
            observed_records.add(row)
        assert expected.http_requests == observed_records

        # HTTP Responses
        rows = utilities.query_db(db,
            "SELECT url, referrer, location FROM http_responses")
        observed_records = set()
        for row in rows:
            observed_records.add(row)
        assert expected.http_responses == observed_records

    def test_cache_hits_recorded(self, tmpdir):
        """Verify all http responses are recorded, including cached responses

        Note that we expect to see all of the same requests and responses
        during the second vist (even if cached) except for images. Cached
        images do not trigger Observer Notification events.
        See Bug 634073: https://bugzilla.mozilla.org/show_bug.cgi?id=634073
        """
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(test_url, sleep=3)
        manager.get(test_url, sleep=3)
        manager.close()
        db = manager_params['db']

        # HTTP Requests
        rows = utilities.query_db(db, (
            "SELECT url, top_level_url, is_XHR, is_frame_load, is_full_page, "
            "is_third_party_channel, is_third_party_window, triggering_origin "
            "loading_origin, loading_href, content_policy_type "
            "FROM http_requests WHERE visit_id = 2"))
        observed_records = set()
        for row in rows:
            observed_records.add(row)
        assert expected.http_cached_requests == observed_records

        # HTTP Responses
        rows = utilities.query_db(db, (
            "SELECT url, referrer, is_cached FROM http_responses "
            "WHERE visit_id = 2"))
        observed_records = set()
        for row in rows:
            observed_records.add(row)
        assert expected.http_cached_responses == observed_records

    def test_http_stacktrace(self, tmpdir):
        test_url = utilities.BASE_TEST_URL + '/http_stacktrace.html'
        db = self.visit(test_url, str(tmpdir), sleep_after=3)
        rows = utilities.query_db(db, (
            "SELECT url, req_call_stack FROM http_requests"))
        observed_records = set()
        for row in rows:
            url, stacktrace = row
            if (url.endswith("inject_pixel.js") or
                url.endswith("test_image.png") or
                url.endswith("Blank.gif")):
                observed_records.add(stacktrace)
        assert observed_records == expected.http_stacktraces

    def test_parse_http_stack_trace_str(self, tmpdir):
        stacktrace = expected.stack_trace_inject_image
        stack_frames = parse_http_stack_trace_str(stacktrace)
        assert stack_frames == expected.call_stack_inject_image

    def test_http_stacktrace_nonjs_loads(self, tmpdir):
        # stacktrace should be empty for requests NOT triggered by scripts
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        db = self.visit(test_url, str(tmpdir), sleep_after=3)
        rows = utilities.query_db(db, (
            "SELECT url, req_call_stack FROM http_requests"))
        for row in rows:
            _, stacktrace = row
            assert stacktrace == ""

    def test_javascript_saving(self, tmpdir):
        """ check that javascript content is saved and hashed correctly """
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        db = self.visit(test_url, str(tmpdir), sleep_after=3) # NOQA
        expected_hashes = {'973e28500d500eab2c27b3bc55c8b621',
                           'a6475af1ad58b55cf781ca5e1218c7b1'}
        for chash, content in utilities.get_javascript_content(str(tmpdir)):
            pyhash = hashlib.md5(content).hexdigest()
            assert pyhash == chash # Verify expected key (md5 of content)
            assert chash in expected_hashes
            expected_hashes.remove(chash)
        assert len(expected_hashes) == 0 # All expected hashes have been seen
