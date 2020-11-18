from openwpm import CommandSequence, TaskManager
from openwpm.utilities import db_utils

from . import utilities
from .openwpmtest import OpenWPMTest

expected_js_cookie = (
    1,  # visit_id
    u"added-or-changed",  # record_type
    u"explicit",  # change_cause
    0,  # is_http_only
    1,  # is_host_only
    0,  # is_session
    u"%s" % utilities.BASE_TEST_URL_DOMAIN,  # host
    0,  # is_secure
    u"test_cookie",  # name
    u"/",  # path
    u"Test-0123456789",  # value
    u"no_restriction",  # same_site
)


class TestStorageVectors(OpenWPMTest):
    """Runs some basic tests to check that the saving of
    storage vectors (i.e. profile cookies) works.

    NOTE: These tests are very basic and should be expanded
    on to check for completeness and correctness.
    """

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)

    def test_js_profile_cookies(self):
        """ Check that profile cookies set by JS are saved """
        # Run the test crawl
        manager_params, browser_params = self.get_config()
        browser_params[0]["cookie_instrument"] = True
        manager = TaskManager.TaskManager(manager_params, browser_params)
        url = utilities.BASE_TEST_URL + "/js_cookie.html"
        cs = CommandSequence.CommandSequence(url)
        cs.get(sleep=3, timeout=120)
        manager.execute_command_sequence(cs)
        manager.close()
        # Check that the JS cookie we stored is recorded
        qry_res = db_utils.query_db(
            manager_params["db"],
            (
                "SELECT visit_id, record_type, change_cause, is_http_only, "
                "is_host_only, is_session, host, is_secure, name, path, "
                "value, same_site FROM javascript_cookies"
            ),
            as_tuple=True,
        )
        assert len(qry_res) == 1  # we store only one cookie
        cookies = qry_res[0]  # take the first cookie
        # compare URL, domain, name, value, origin, path
        assert cookies == expected_js_cookie
