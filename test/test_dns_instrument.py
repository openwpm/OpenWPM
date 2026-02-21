from sqlite3 import Row
from typing import cast
from urllib.parse import urlparse

from openwpm.utilities import db_utils

from .conftest import FullConfig, TaskManagerCreator
from .utilities import ServerUrls


def test_name_resolution(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.dns_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))
    manager.get(f"http://test.localhost:{server.port}")
    manager.close()

    results = cast("list[Row]", db_utils.query_db(db, "SELECT * FROM dns_responses"))
    result = results[0]
    assert isinstance(result, Row)
    assert result["used_address"] == "127.0.0.1"
    assert result["addresses"] == "127.0.0.1,::1"
    assert result["hostname"] == "test.localhost"
    assert result["canonical_name"] == "test.localhost"
    assert result["redirect_url"] is not None
    assert f"test.localhost:{server.port}" in result["redirect_url"]

    # Each redirect hop should record the URL it was associated with
    redirect_urls = [r["redirect_url"] for r in results]
    assert all(url is not None for url in redirect_urls)


def test_dns_captured_on_connection_abort(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """Regression test: DNS data must be captured even when the connection
    aborts before completion. This verifies that the extension uses
    onHeadersReceived (not onCompleted) to record DNS responses."""
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.dns_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))
    manager.get(f"http://localhost:{server.port}/CONNECTION_ABORT/")
    manager.close()

    results = db_utils.query_db(db, "SELECT * FROM dns_responses")
    assert len(results) > 0, "No DNS responses captured for aborted connection"
    result = results[0]
    assert isinstance(result, Row)
    assert result["used_address"] is not None
    assert result["addresses"] is not None
    assert result["hostname"] == "localhost"


def test_dns_failure_captured(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
) -> None:
    """DNS failures (NXDOMAIN) should be captured via onErrorOccurred
    with error details and null addresses."""
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.dns_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))
    # example.invalid is guaranteed NXDOMAIN per RFC 2606
    manager.get("http://example.invalid/")
    manager.close()

    results = cast("list[Row]", db_utils.query_db(db, "SELECT * FROM dns_responses"))
    assert len(results) > 0, "No DNS responses captured for failed resolution"
    # Find the row for example.invalid
    dns_failure = [r for r in results if "example.invalid" in (r["hostname"] or "")]
    assert len(dns_failure) > 0, "No DNS failure row for example.invalid"
    result = dns_failure[0]
    assert isinstance(result, Row)
    assert result["addresses"] is None
    assert result["used_address"] is None
    assert result["error"] is not None


def test_redirect_chain_dns(
    default_params: FullConfig,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """A 2-hop redirect chain (hop1 -> hop2 -> simple_b.html) should produce
    exactly three dns_responses rows that, ordered by time_stamp, reconstruct
    the original chain — one row per redirect step, all sharing the same
    browser_id and request_id (Firefox preserves request_id across redirects).
    """
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.dns_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))

    chain_url = (
        f"http://test.localhost:{server.port}"
        f"/MAGIC_REDIRECT/hop1"
        f"?dst=/MAGIC_REDIRECT/hop2"
        f"&dst=/test_pages/simple_b.html"
    )
    manager.get(chain_url)
    manager.close()

    expected_paths = [
        "/MAGIC_REDIRECT/hop1",
        "/MAGIC_REDIRECT/hop2",
        "/test_pages/simple_b.html",
    ]
    rows = cast(
        "list[Row]",
        db_utils.query_db(
            db,
            "SELECT * FROM dns_responses WHERE hostname = 'test.localhost' "
            "ORDER BY time_stamp",
        ),
    )
    chain_rows = [r for r in rows if urlparse(r["redirect_url"]).path in expected_paths]

    paths = [urlparse(r["redirect_url"]).path for r in chain_rows]
    assert paths == expected_paths, (
        f"Reconstructed chain does not match expected sequence.\n"
        f"  expected: {expected_paths}\n"
        f"  got:      {paths}"
    )

    # The whole chain ran in one browser, on one request_id (Firefox keeps
    # request_id stable across redirects).
    browser_ids = {r["browser_id"] for r in chain_rows}
    request_ids = {r["request_id"] for r in chain_rows}
    assert len(browser_ids) == 1, f"Chain split across browsers: {browser_ids}"
    assert (
        len(request_ids) == 1
    ), f"Expected single request_id across redirect chain, got: {request_ids}"

    for r in chain_rows:
        assert isinstance(r, Row)
