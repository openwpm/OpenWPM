from openwpm.utilities import db_utils

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls

# HTTP request call stack instrumentation
#
# http_stacktrace.html's onload handler runs inject_all(), which fires three
# requests via three different initiation mechanisms. The instrument captures
# the full initiator stack for each, via two distinct code paths:
#
#   * SYNCHRONOUS, script-initiated (inject_js): appending a <script> issues its
#     src request synchronously from JS, so the content process captures the
#     stack from Components.stack at http-on-opening-request.
#
#   * ASYNCHRONOUS, fetch/XHR-initiated (inject_fetch / inject_xhr): these open
#     their channel off the JS stack, so Components.stack is empty. Firefox
#     instead delivers the initiator stack via the network-monitor-alternate-stack
#     notification (gated on the top BrowsingContext's watchedByDevTools flag,
#     which the parent actor enables), which the parent actor deserializes into
#     the same name@file:line:col;asyncCause format. This closes #1177.
#
# The line/column offsets below correspond to the call sites in
# http_stacktrace.html. All three assertions are non-vacuous: each asserts a
# specific captured frame chain and fails if capture for that path breaks.


def test_http_stacktrace(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        # Record HTTP Requests and Responses
        browser_param.http_instrument = True
        # Record JS Web API calls
        browser_param.js_instrument = True
        # Record the callstack of all WebRequests made
        browser_param.callstack_instrument = True

    page_url = server.base + "/http_stacktrace.html"

    # SYNC, <script>-initiated -> shared/inject_pixel.js
    stack_trace_inject_js = (
        f"inject_js@{page_url}:15:28;null\n"
        f"inject_all@{page_url}:32:7;null\n"
        f"onload@{page_url}:1:1;null"
    )
    inject_pixel_url = server.base + "/shared/inject_pixel.js"

    # ASYNC, fetch-initiated -> shared/test_script.js (alternate-stack path)
    stack_trace_inject_fetch = (
        f"inject_fetch@{page_url}:22:12;null\n"
        f"inject_all@{page_url}:33:7;null\n"
        f"onload@{page_url}:1:1;null"
    )
    inject_fetch_url = server.base + "/shared/test_script.js"

    # ASYNC, XHR-initiated -> shared/test_image_2.png (alternate-stack path)
    stack_trace_inject_xhr = (
        f"inject_xhr@{page_url}:29:11;null\n"
        f"inject_all@{page_url}:34:7;null\n"
        f"onload@{page_url}:1:1;null"
    )
    inject_xhr_url = server.base + "/shared/test_image_2.png"

    manager, db = task_manager_creator((manager_params, browser_params))
    manager.get(page_url, sleep=10)
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
    stacks_by_url: dict[str, set[str]] = {}
    for row in rows:
        assert not isinstance(row, tuple)
        print(row["call_stack"])
        url, call_stack = row["url"], row["call_stack"]
        stacks_by_url.setdefault(url, set()).add(call_stack)

    # Sync, script-initiated request stack (content-process Components.stack path).
    assert stack_trace_inject_js in stacks_by_url.get(inject_pixel_url, set())
    # Async fetch-initiated request stack (network-monitor-alternate-stack path).
    assert stack_trace_inject_fetch in stacks_by_url.get(inject_fetch_url, set())
    # Async XHR-initiated request stack (network-monitor-alternate-stack path).
    assert stack_trace_inject_xhr in stacks_by_url.get(inject_xhr_url, set())
