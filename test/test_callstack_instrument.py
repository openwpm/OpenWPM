import pytest

from openwpm.utilities import db_utils

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls

RAWGIT_HTTP_STACKTRACE_TEST_URL = "https://gist.githack.com/gunesacar/b927d3fe69f3e7bf456da5192f74beea/raw/8d3e490b5988c633101ec45ef1443e61b1fd495e/inject_pixel.js"  # noqa


def _http_stacktraces(base_url: str) -> set[str]:
    """Build expected stack traces (needs dynamic base_url)."""
    url = base_url + "/http_stacktrace.html"
    inject_image = (
        f"inject_image@{url}:18:7;null\n"
        f"inject_all@{url}:22:7;null\n"
        f"onload@{url}:1:1;null"
    )
    inject_pixel = (
        f"inject_pixel@{RAWGIT_HTTP_STACKTRACE_TEST_URL}:4:3;null\n"
        f"null@{RAWGIT_HTTP_STACKTRACE_TEST_URL}:6:1;null"
    )
    inject_js = (
        f"inject_js@{url}:13:28;null\n"
        f"inject_all@{url}:21:7;null\n"
        f"onload@{url}:1:1;null"
    )
    return {inject_image, inject_pixel, inject_js}


@pytest.mark.skip("We don't have the resources to fix this")
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
    test_url = server.base + "/http_stacktrace.html"
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
    observed_records: set[str] = set()
    for row in rows:
        assert not isinstance(row, tuple)
        print(row["call_stack"])
        url, call_stack = row["url"], row["call_stack"]
        test_urls = (
            "inject_pixel.js",
            "test_image.png",
            "Blank.gif",
        )
        if url.endswith(test_urls):
            observed_records.add(call_stack)
    assert _http_stacktraces(server.base) == observed_records
