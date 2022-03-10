"""Runs some basic tests to check that the saving of
storage vectors (i.e. profile cookies) works.

NOTE: These tests are very basic and should be expanded
on to check for completeness and correctness.
"""

from openwpm import command_sequence
from openwpm.utilities import db_utils

from . import utilities

expected_js_cookie = (
    "added-or-changed",  # record_type
    "explicit",  # change_cause
    0,  # is_http_only
    1,  # is_host_only
    0,  # is_session
    "%s" % utilities.BASE_TEST_URL_DOMAIN,  # host
    0,  # is_secure
    "test_cookie",  # name
    "/",  # path
    "Test-0123456789",  # value
    "no_restriction",  # same_site
)


def test_js_profile_cookies(default_params, task_manager_creator):
    """Check that profile cookies set by JS are saved"""
    # Run the test crawl
    manager_params, browser_params = default_params
    for browser_param in browser_params:
        browser_param.cookie_instrument = True
    manager, db = task_manager_creator((manager_params, browser_params))
    url = utilities.BASE_TEST_URL + "/js_cookie.html"
    cs = command_sequence.CommandSequence(url)
    cs.get(sleep=3, timeout=120)
    manager.execute_command_sequence(cs)
    manager.close()
    # Check that the JS cookie we stored is recorded
    qry_res = db_utils.query_db(
        db,
        (
            "SELECT record_type, change_cause, is_http_only, "
            "is_host_only, is_session, host, is_secure, name, path, "
            "value, same_site FROM javascript_cookies"
        ),
        as_tuple=True,
    )
    assert len(qry_res) == 1  # we store only one cookie
    cookies = qry_res[0]  # take the first cookie
    # compare URL, domain, name, value, origin, path
    assert cookies == expected_js_cookie
