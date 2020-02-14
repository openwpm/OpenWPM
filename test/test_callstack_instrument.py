from ..automation import TaskManager
from ..automation.utilities import db_utils
from ..automation.utilities.platform_utils import parse_http_stack_trace_str
from . import utilities
from .openwpmtest import OpenWPMTest

# HTTP request call stack instrumentation
# Expected stack frames
HTTP_STACKTRACE_TEST_URL = utilities.BASE_TEST_URL + "/http_stacktrace.html"
STACK_TRACE_INJECT_IMAGE =\
    "inject_image@" + HTTP_STACKTRACE_TEST_URL + ":18:7;null\n"\
    "inject_all@" + HTTP_STACKTRACE_TEST_URL + ":22:7;null\n"\
    "onload@" + HTTP_STACKTRACE_TEST_URL + ":1:1;null"

RAWGIT_HTTP_STACKTRACE_TEST_URL = "https://gist.githack.com/gunesacar/b927d3fe69f3e7bf456da5192f74beea/raw/8d3e490b5988c633101ec45ef1443e61b1fd495e/inject_pixel.js"  # noqa
# https://gist.github.com/gunesacar/b927d3fe69f3e7bf456da5192f74beea
STACK_TRACE_INJECT_PIXEL =\
    "inject_pixel@" + RAWGIT_HTTP_STACKTRACE_TEST_URL + ":4:3;null\n"\
    "null@" + RAWGIT_HTTP_STACKTRACE_TEST_URL + ":6:1;null"

STACK_TRACE_INJECT_JS =\
    "inject_js@" + HTTP_STACKTRACE_TEST_URL + ":13:28;null\n"\
    "inject_all@" + HTTP_STACKTRACE_TEST_URL + ":21:7;null\n"\
    "onload@" + HTTP_STACKTRACE_TEST_URL + ":1:1;null"

HTTP_STACKTRACES = set((STACK_TRACE_INJECT_IMAGE,
                        STACK_TRACE_INJECT_PIXEL,
                        STACK_TRACE_INJECT_JS))
# parsed HTTP call stack dict
CALL_STACK_INJECT_IMAGE =\
    [{"func_name": "inject_image",
      "filename": HTTP_STACKTRACE_TEST_URL,
      "line_no": "18",
      "col_no": "7",
      "async_cause": "null"},
     {"func_name": "inject_all",
      "filename": HTTP_STACKTRACE_TEST_URL,
      "line_no": "22",
      "col_no": "7",
      "async_cause": "null"},
     {"func_name": "onload",
      "filename": HTTP_STACKTRACE_TEST_URL,
      "line_no": "1",
      "col_no": "1",
      "async_cause": "null"}]


class TestCallstackInstrument(OpenWPMTest):
    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        # Record HTTP Requests and Responses
        browser_params[0]['http_instrument'] = True
        # Record JS Web API calls
        browser_params[0]['js_instrument'] = True
        # Record the callstack of all WebRequests made
        browser_params[0]['callstack_instrument'] = True
        return manager_params, browser_params

    def test_http_stacktrace(self):
        test_url = utilities.BASE_TEST_URL + '/http_stacktrace.html'
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(test_url, sleep=10)
        db = manager_params['db']
        manager.close()
        rows = db_utils.query_db(db, (
            "SELECT * FROM callstacks;"))
        print("Printing callstacks contents")
        for row in rows:
            print(row["call_stack"])
        rows = db_utils.query_db(db, (
            "SELECT hr.url, c.call_stack"
            "   FROM callstacks c"
            "   JOIN http_requests hr"
            "   ON c.request_id=hr.request_id"
            "      AND c.visit_id= hr.visit_id"
            "      AND c.crawl_id = hr.crawl_id;"))
        observed_records = set()
        for row in rows:
            url, stacktrace = row
            if (url.endswith("inject_pixel.js")
                    or url.endswith("test_image.png")  # noqa: W503
                    or url.endswith("Blank.gif")):  # noqa: W503
                observed_records.add(stacktrace)
        assert HTTP_STACKTRACES == observed_records

    def test_parse_http_stack_trace_str(self):
        stacktrace = STACK_TRACE_INJECT_IMAGE
        stack_frames = parse_http_stack_trace_str(stacktrace)
        assert stack_frames == CALL_STACK_INJECT_IMAGE

    # TODO: webext instrumentation doesn't support req_call_stack yet.
    # def test_http_stacktrace_nonjs_loads(self):
    #     # stacktrace should be empty for requests NOT triggered by scripts
    #     test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
    #     db = self.visit(test_url, sleep_after=3)
    #     rows = db_utils.query_db(db, (
    #         "SELECT url, req_call_stack FROM http_requests"))
    #     for row in rows:
    #         _, stacktrace = row
    #         assert stacktrace == ""
