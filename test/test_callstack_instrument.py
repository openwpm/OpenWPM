import socket
from collections.abc import Iterator
from pathlib import Path

import pytest

from openwpm.utilities import db_utils

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls

# Mirrors MAX_FRAMES in OpenWPMStackDumpChild.sys.mjs.
MAX_FRAMES = 64


def _crawl_callstacks(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    *page_urls: str,
    sleep: int = 10,
) -> dict[str, list[str]]:
    """Visit page_urls in one browser and return every captured call stack
    keyed by request URL."""
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.http_instrument = True
        browser_param.callstack_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))
    for page_url in page_urls:
        manager.get(page_url, index=0, sleep=sleep)
    manager.close()
    return _callstacks_by_url(db)


def _callstacks_by_url(db: Path) -> dict[str, list[str]]:
    orphans = db_utils.query_db(
        db,
        "SELECT c.request_id, c.call_stack FROM callstacks c"
        "   LEFT JOIN http_requests hr"
        "   ON c.request_id=hr.request_id"
        "      AND c.visit_id= hr.visit_id"
        "      AND c.browser_id = hr.browser_id"
        "   WHERE hr.request_id IS NULL;",
    )
    assert [tuple(row) for row in orphans] == []
    rows = db_utils.query_db(
        db,
        "SELECT hr.url, c.call_stack"
        "   FROM callstacks c"
        "   JOIN http_requests hr"
        "   ON c.request_id=hr.request_id"
        "      AND c.visit_id= hr.visit_id"
        "      AND c.browser_id = hr.browser_id;",
    )
    stacks: dict[str, list[str]] = {}
    for row in rows:
        assert not isinstance(row, tuple)
        print(row["url"], repr(row["call_stack"]))
        stacks.setdefault(row["url"], []).append(row["call_stack"])
    for url, url_stacks in stacks.items():
        for stack in url_stacks:
            # Firefox's own code (e.g. the favicon loader) must not be attributed.
            assert "resource://" not in stack and "chrome://" not in stack, url
    return stacks


def test_http_stacktrace(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """<script>, fetch and XHR issued from an onload handler.

    All three open their channel on the JS stack, so the stack is read from
    Components.stack at http-on-opening-request.
    """
    page_url = server.base + "/http_stacktrace.html"
    stacks = _crawl_callstacks(default_params, task_manager_creator, page_url)

    assert stacks[server.base + "/shared/inject_pixel.js"] == [
        f"inject_js@{page_url}:15:28;null\n"
        f"inject_all@{page_url}:32:7;null\n"
        f"onload@{page_url}:1:1;null"
    ]
    assert stacks[server.base + "/shared/test_script.js"] == [
        f"inject_fetch@{page_url}:22:12;null\n"
        f"inject_all@{page_url}:33:7;null\n"
        f"onload@{page_url}:1:1;null"
    ]
    assert stacks[server.base + "/shared/test_image_2.png"] == [
        f"inject_xhr@{page_url}:29:11;null\n"
        f"inject_all@{page_url}:34:7;null\n"
        f"onload@{page_url}:1:1;null"
    ]


def test_http_stacktrace_off_stack(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """Requests whose channel is not opened on the initiating JS stack.

    A worker's fetch opens its channel on the content process main thread with
    no JS on the stack, and a WebSocket's HTTP channel lives only in the parent
    process. Both are only attributable through the
    network-monitor-alternate-stack notification.
    """
    page_url = server.base + "/http_stacktrace_async.html"
    worker_url = server.base + "/shared/stacktrace_worker.js"
    stacks = _crawl_callstacks(default_params, task_manager_creator, page_url)

    assert stacks[server.base + "/shared/test_script_2.js?from_worker"] == [
        f"worker_fetch@{worker_url}:2:8;null\nnull@{worker_url}:4:1;null"
    ]
    assert stacks[f"ws://{server.domain}:{server.port}/stacktrace_ws"] == [
        f"open_websocket@{page_url}:11:5;null\n"
        f"run_all@{page_url}:24:5;null\n"
        f"onload@{page_url}:1:1;null"
    ]
    assert stacks[worker_url] == [
        f"start_worker@{page_url}:8:5;null\n"
        f"run_all@{page_url}:23:5;null\n"
        f"onload@{page_url}:1:1;null"
    ]
    # Opened on the JS stack, but Firefox only records async parent frames for
    # debuggees, so the stack starts at the timer callback / await resumption.
    assert stacks[server.base + "/shared/test_script.js?after_timeout"] == [
        f"timeout_cb@{page_url}:15:12;null"
    ]
    assert stacks[server.base + "/shared/test_script.js?after_await"] == [
        f"fetch_after_await@{page_url}:20:10;null"
    ]
    assert server.base + "/shared/test_favicon.ico" not in stacks


def test_http_stacktrace_same_process_iframe(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """A same-origin iframe shares the content process with its parent; its
    request must still produce exactly one row."""
    page_url = server.base + "/http_stacktrace_iframe.html"
    child_url = server.base + "/shared/stacktrace_iframe_child.html"
    stacks = _crawl_callstacks(default_params, task_manager_creator, page_url)

    assert stacks[server.base + "/shared/inject_pixel.js?from_iframe"] == [
        f"inject_from_iframe@{child_url}:8:19;null\nonload@{child_url}:1:1;null"
    ]


def test_http_stacktrace_hostile_page(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """Page-controlled function names cannot inject frames or break storage,
    and depth is capped."""
    page_url = server.base + "/http_stacktrace_hostile.html"
    next_url = server.base + "/http_stacktrace.html"
    stacks = _crawl_callstacks(default_params, task_manager_creator, page_url, next_url)

    (forged,) = stacks[server.base + "/shared/test_script.js?forged"]
    assert forged.splitlines() == [
        f"x\\u000aforged\\u0040https://forged.example/f.js:1:1;null@{page_url}:8:12;null",
        f"run_all@{page_url}:24:12;null",
        f"onload@{page_url}:1:1;null",
    ]

    (deep,) = stacks[server.base + "/shared/test_script.js?deep"]
    frames = deep.splitlines()
    assert len(frames) == MAX_FRAMES
    assert frames[0] == f"recurse@{page_url}:18:12;null"

    (surrogate,) = stacks[server.base + "/shared/test_script.js?surrogate"]
    assert surrogate.splitlines() == [
        f"lone\\ud800name@{page_url}:13:12;null",
        f"run_all@{page_url}:26:15;null",
        f"onload@{page_url}:1:1;null",
    ]
    # An unencodable string must not drop the extension's storage connection,
    # which would lose every later record.
    assert server.base + "/shared/inject_pixel.js" in stacks


def _websocket_stacks(server: ServerUrls, n: int) -> dict[str, list[str]]:
    origin = f"127.0.0.{n}:{server.port}"
    child_url = f"http://{origin}/test_pages/shared/stacktrace_ws_child.html?n={n}"
    worker_url = f"http://{origin}/test_pages/shared/stacktrace_ws_worker.js?n={n}"
    return {
        f"ws://{origin}/stacktrace_ws_{n}": [
            f"open_ws_{n}@{child_url}:9:7;null\n"
            f"run_all@{child_url}:13:17;null\n"
            f"onload@{child_url}:1:1;null"
        ],
        f"ws://{origin}/stacktrace_ws_worker_{n}": [
            f"worker_ws_{n}@{worker_url}:5:5;null\nnull@{worker_url}:8:13;null"
        ],
    }


def test_http_stacktrace_websockets_cross_site_iframes(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """WebSockets opened concurrently from several content processes are each
    attributed to their own stack."""
    stacks = _crawl_callstacks(
        default_params,
        task_manager_creator,
        server.base + "/http_stacktrace_websockets.html",
    )
    for n in range(2, 8):
        for url, expected in _websocket_stacks(server, n).items():
            assert stacks.get(url) == expected, url


def test_http_stacktrace_websockets_sequential_visits(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """A WebSocket is not attributed to a stack captured in an earlier visit."""
    ns = range(2, 6)
    stacks = _crawl_callstacks(
        default_params,
        task_manager_creator,
        *(
            f"http://127.0.0.{n}:{server.port}/test_pages/shared/"
            f"stacktrace_ws_child.html?n={n}"
            for n in ns
        ),
    )
    for n in ns:
        for url, expected in _websocket_stacks(server, n).items():
            assert stacks.get(url) == expected, url


@pytest.fixture
def stalled_host() -> Iterator[str]:
    """A listener that completes the TCP handshake and never answers."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.9", 0))
        listener.listen()
        host, port = listener.getsockname()
        yield f"{host}:{port}"


def test_http_stacktrace_websocket_queued_behind_stalled_connection(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
    stalled_host: str,
) -> None:
    """Firefox connects one WebSocket per host at a time, so stall_2's request
    only opens once stall_1 times out. Its stack, sent at `new WebSocket()`,
    must still be attributed."""
    open_timeout_s = 8
    for browser_param in default_params[1]:
        browser_param.prefs["network.websocket.timeout.open"] = open_timeout_s
    page_url = (
        f"{server.base}/http_stacktrace_websockets_stalled.html?stalled={stalled_host}"
    )
    stacks = _crawl_callstacks(
        default_params, task_manager_creator, page_url, sleep=open_timeout_s + 10
    )

    for name, line in [("stall_1", 11), ("stall_2", 12)]:
        assert stacks.get(f"ws://{stalled_host}/{name}") == [
            f"open_stalled@{page_url}:8:5;null\n"
            f"run_all@{page_url}:{line}:17;null\n"
            f"onload@{page_url}:1:1;null"
        ], name
    assert stacks.get(f"ws://{server.domain}:{server.port}/control_ws") == [
        f"run_all@{page_url}:13:5;null\n" f"onload@{page_url}:1:1;null"
    ]
