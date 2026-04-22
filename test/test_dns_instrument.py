from sqlite3 import Row

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

    results = db_utils.query_db(db, "SELECT * FROM dns_responses")
    result = results[0]
    assert isinstance(result, Row)
    assert result["used_address"] == "127.0.0.1"
    assert result["addresses"] == "127.0.0.1,::1"
    assert result["hostname"] == "test.localhost"
    assert result["canonical_name"] == "test.localhost"
    assert result["redirect_url"] is not None
    assert "test.localhost:8000" in result["redirect_url"]

    # Each redirect hop should record the URL it was associated with
    redirect_urls = [r["redirect_url"] for r in results]
    assert all(url is not None for url in redirect_urls)


def test_dns_captured_on_connection_abort(default_params, task_manager_creator):
    """Regression test: DNS data must be captured even when the connection
    aborts before completion. This verifies that the extension uses
    onHeadersReceived (not onCompleted) to record DNS responses."""
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.dns_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))
    manager.get("http://localhost:8000/CONNECTION_ABORT/")
    manager.close()

    results = db_utils.query_db(db, "SELECT * FROM dns_responses")
    assert len(results) > 0, "No DNS responses captured for aborted connection"
    result = results[0]
    assert isinstance(result, Row)
    assert result["used_address"] is not None
    assert result["addresses"] is not None
    assert result["hostname"] == "localhost"


def test_dns_failure_captured(default_params, task_manager_creator):
    """DNS failures (NXDOMAIN) should be captured via onErrorOccurred
    with error details and null addresses."""
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.dns_instrument = True

    manager, db = task_manager_creator((manager_params, browser_params))
    # example.invalid is guaranteed NXDOMAIN per RFC 2606
    manager.get("http://example.invalid/")
    manager.close()

    results = db_utils.query_db(db, "SELECT * FROM dns_responses")
    assert len(results) > 0, "No DNS responses captured for failed resolution"
    # Find the row for example.invalid
    dns_failure = [r for r in results if "example.invalid" in (r["hostname"] or "")]
    assert len(dns_failure) > 0, "No DNS failure row for example.invalid"
    result = dns_failure[0]
    assert isinstance(result, Row)
    assert result["addresses"] is None
    assert result["used_address"] is None
    assert result["error"] is not None
