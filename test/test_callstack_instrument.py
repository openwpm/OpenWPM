from openwpm.utilities import db_utils

from . import utilities

# HTTP request call stack instrumentation
# Expected stack frames
HTTP_STACKTRACE_TEST_URL = utilities.BASE_TEST_URL + "/http_stacktrace.html"
STACK_TRACE_INJECT_IMAGE = (
    "inject_image@" + HTTP_STACKTRACE_TEST_URL + ":18:7;null\n"
    "inject_all@" + HTTP_STACKTRACE_TEST_URL + ":22:7;null\n"
    "onload@" + HTTP_STACKTRACE_TEST_URL + ":1:1;null"
)

RAWGIT_HTTP_STACKTRACE_TEST_URL = "https://gist.githack.com/gunesacar/b927d3fe69f3e7bf456da5192f74beea/raw/8d3e490b5988c633101ec45ef1443e61b1fd495e/inject_pixel.js"  # noqa
# https://gist.github.com/gunesacar/b927d3fe69f3e7bf456da5192f74beea
STACK_TRACE_INJECT_PIXEL = (
    "inject_pixel@" + RAWGIT_HTTP_STACKTRACE_TEST_URL + ":4:3;null\n"
    "null@" + RAWGIT_HTTP_STACKTRACE_TEST_URL + ":6:1;null"
)

STACK_TRACE_INJECT_JS = (
    "inject_js@" + HTTP_STACKTRACE_TEST_URL + ":13:28;null\n"
    "inject_all@" + HTTP_STACKTRACE_TEST_URL + ":21:7;null\n"
    "onload@" + HTTP_STACKTRACE_TEST_URL + ":1:1;null"
)

HTTP_STACKTRACES = {
    STACK_TRACE_INJECT_IMAGE,
    STACK_TRACE_INJECT_PIXEL,
    STACK_TRACE_INJECT_JS,
}


def test_http_stacktrace(default_params, task_manager_creator):
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        # Record HTTP Requests and Responses
        browser_param.http_instrument = True
        # Record JS Web API calls
        browser_param.js_instrument = True
        # Record the callstack of all WebRequests made
        browser_param.callstack_instrument = True
    test_url = utilities.BASE_TEST_URL + "/http_stacktrace.html"
    manager, db = task_manager_creator((manager_params, browser_params))
    manager.get(test_url, sleep=10)
    manager.close()
    rows = db_utils.query_db(
        db,
        (
            "SELECT hr.url, c.call_stack"
            "   FROM callstacks c"
            "   JOIN http_requests hr"
            "   ON c.request_id=hr.request_id"
            "      AND c.visit_id= hr.visit_id"
            "      AND c.browser_id = hr.browser_id;"
        ),
    )
    print("Printing callstacks contents")
    observed_records = set()
    for row in rows:
        print(row["call_stack"])
        url, call_stack = row
        test_urls = (
            "inject_pixel.js",
            "test_image.png",
            "Blank.gif",
        )
        if url.endswith(test_urls):
            observed_records.add(call_stack)
    assert HTTP_STACKTRACES == observed_records
