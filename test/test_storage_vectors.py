
import pytest

from ..automation import CommandSequence, TaskManager
from ..automation.utilities import db_utils
from . import utilities
from .openwpmtest import OpenWPMTest

expected_lso_content_a = [
    1,  # visit id
    u'localtest.me',
    u'FlashCookie.sol',
    u'localtest.me/FlashCookie.sol',
    u'test_key',
    u'REPLACEME']

expected_lso_content_b = [
    2,  # visit id
    u'localtest.me',
    u'FlashCookie.sol',
    u'localtest.me/FlashCookie.sol',
    u'test_key',
    u'REPLACEME']

expected_js_cookie = (
    1,                                       # visit_id
    u'added-or-changed',                     # record_type
    u'explicit',                             # change_cause
    0,                                       # is_http_only
    1,                                       # is_host_only
    0,                                       # is_session
    u'%s' % utilities.BASE_TEST_URL_DOMAIN,  # host
    0,                                       # is_secure
    u'test_cookie',                          # name
    u'/',                                    # path
    u'Test-0123456789',                      # value
    u'no_restriction'                        # same_site
)


class TestStorageVectors(OpenWPMTest):
    """ Runs some basic tests to check that the saving of
    storage vectors (i.e. Flash LSOs, profile cookies) works.

    NOTE: These tests are very basic and should be expanded
    on to check for completeness and correctness.
    """

    def get_config(self, data_dir=""):
        return self.get_test_config(data_dir)

    @pytest.mark.xfail(reason='Flash cookies no longer supported')
    def test_flash_cookies(self):
        """ Check that some Flash LSOs are saved and
        are properly keyed in db."""
        # Run the test crawl
        manager_params, browser_params = self.get_config()
        browser_params[0]['disable_flash'] = False
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Get a site we know sets Flash cookies and visit it twice
        lso_value_a = utilities.rand_str(8)
        expected_lso_content_a[5] = lso_value_a  # expected to be present
        qry_str = '?lso_test_key=%s&lso_test_value=%s' % ("test_key",
                                                          lso_value_a)
        test_url_a = utilities.BASE_TEST_URL + '/lso/setlso.html' + qry_str
        cs = CommandSequence.CommandSequence(test_url_a)
        cs.get(sleep=3, timeout=120)
        cs.dump_flash_cookies()
        manager.execute_command_sequence(cs)

        lso_value_b = utilities.rand_str(8)
        expected_lso_content_b[5] = lso_value_b  # expected to be present
        qry_str = '?lso_test_key=%s&lso_test_value=%s' % ("test_key",
                                                          lso_value_b)
        test_url_b = utilities.BASE_TEST_URL + '/lso/setlso.html' + qry_str
        cs = CommandSequence.CommandSequence(test_url_b)
        cs.get(sleep=3, timeout=120)
        cs.dump_flash_cookies()
        manager.execute_command_sequence(cs)

        manager.close()

        #  Check that some flash cookies are recorded
        qry_res = db_utils.query_db(manager_params['db'],
                                    "SELECT * FROM flash_cookies",
                                    as_tuple=True)
        lso_count = len(qry_res)
        assert lso_count == 2
        lso_content_a = list(qry_res[0][2:])  # Remove first two items
        lso_content_b = list(qry_res[1][2:])  # Remove first two items
        # remove randomly generated LSO directory name
        # e.g. TY2FOJUG/localtest.me/Flash.sol -> localtest.me/Flash.sol
        lso_content_a[3] = lso_content_a[3].split("/", 1)[-1]  # rm LSO dirname
        lso_content_b[3] = lso_content_b[3].split("/", 1)[-1]  # rm LSO dirname
        assert lso_content_a == expected_lso_content_a
        assert lso_content_b == expected_lso_content_b

    def test_js_profile_cookies(self):
        """ Check that profile cookies set by JS are saved """
        # Run the test crawl
        manager_params, browser_params = self.get_config()
        browser_params[0]['cookie_instrument'] = True
        manager = TaskManager.TaskManager(manager_params, browser_params)
        url = utilities.BASE_TEST_URL + "/js_cookie.html"
        cs = CommandSequence.CommandSequence(url)
        cs.get(sleep=3, timeout=120)
        manager.execute_command_sequence(cs)
        manager.close()
        # Check that the JS cookie we stored is recorded
        qry_res = db_utils.query_db(
            manager_params['db'], (
                "SELECT visit_id, record_type, change_cause, is_http_only, "
                "is_host_only, is_session, host, is_secure, name, path, "
                "value, same_site FROM javascript_cookies"),
            as_tuple=True
        )
        assert len(qry_res) == 1  # we store only one cookie
        cookies = qry_res[0]  # take the first cookie
        # compare URL, domain, name, value, origin, path
        assert cookies == expected_js_cookie
