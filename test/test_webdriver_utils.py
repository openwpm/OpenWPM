import pytest

from openwpm.browser_manager import is_dns_error
from openwpm.commands.utils.webdriver_utils import parse_neterror
from openwpm.utilities import db_utils


def test_parse_neterror():
    text = (
        "selenium.common.exceptions.WebDriverException: "
        "Message: Reached error page: "
        "about:neterror?e=dnsNotFound&u=http%3A//medmood.it/&c=UTF-8&"
        "f=regular&d=We%20can%E2%80%99t%20"
        "connect%20to%20the%20server%20at%20medmood.it."
    )
    assert parse_neterror(text) == "dnsNotFound"


def test_parse_neterror_integration(default_params, task_manager_creator):
    manager, db = task_manager_creator(default_params)
    manager.get("http://website.invalid")
    manager.close()

    get_command = db_utils.query_db(
        db,
        "SELECT command_status, error FROM crawl_history WHERE command ='GetCommand'",
        as_tuple=True,
    )[0]

    assert get_command[0] == "neterror"
    assert get_command[1] == "dnsNotFound"


@pytest.mark.slow
def test_dns_error_does_not_count_against_failure_limit(
    default_params, task_manager_creator
):
    """AC-4: 100+ DNS errors must not trigger CommandExecutionError even with
    a low failure_limit.  Each navigation to a non-existent domain produces a
    dnsNotFound neterror that should be excluded from the failure counter."""
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager_params.failure_limit = 5
    manager, db = task_manager_creator((manager_params, browser_params[:1]))

    num_domains = 110
    for i in range(num_domains):
        manager.get(f"http://domain-{i}.invalid")

    manager.close()

    rows = db_utils.query_db(
        db,
        "SELECT command_status, error FROM crawl_history WHERE command='GetCommand'",
        as_tuple=True,
    )
    dns_rows = [(s, e) for s, e in rows if s == "neterror" and e == "dnsNotFound"]
    assert len(dns_rows) == num_domains


def testis_dns_error_predicate():
    """AC-5: Verify that is_dns_error is True only for dnsNotFound neterrors.

    Non-DNS neterror types (connectionRefused, netOffline, etc.) and other
    command statuses must NOT be treated as DNS errors, so they continue to
    increment failure_count as before.
    """
    # Only this exact combination qualifies
    assert is_dns_error("neterror", "dnsNotFound") is True

    # Other neterror types must NOT be exempt
    assert is_dns_error("neterror", "connectionRefused") is False
    assert is_dns_error("neterror", "netOffline") is False
    assert is_dns_error("neterror", "proxyConnectFailure") is False

    # Missing error_text must NOT be exempt
    assert is_dns_error("neterror", None) is False

    # Non-neterror statuses must NOT be exempt
    assert is_dns_error("ok", "dnsNotFound") is False
    assert is_dns_error("critical", "dnsNotFound") is False
    assert is_dns_error("error", "dnsNotFound") is False
    assert is_dns_error("timeout", "dnsNotFound") is False

    # parse_neterror returns the right code for a DNS failure message
    dns_msg = (
        "selenium.common.exceptions.WebDriverException: "
        "Message: Reached error page: "
        "about:neterror?e=dnsNotFound&u=http%3A//missing.example/&c=UTF-8&"
        "f=regular&d=We+can%27t+connect"
    )
    assert parse_neterror(dns_msg) == "dnsNotFound"
    assert is_dns_error("neterror", parse_neterror(dns_msg)) is True

    # A different neterror code does NOT trigger the exemption
    conn_msg = (
        "selenium.common.exceptions.WebDriverException: "
        "Message: Reached error page: "
        "about:neterror?e=connectionRefused&u=http%3A//localhost%3A1/&c=UTF-8&"
        "f=regular&d=refused."
    )
    assert parse_neterror(conn_msg) == "connectionRefused"
    assert is_dns_error("neterror", parse_neterror(conn_msg)) is False
