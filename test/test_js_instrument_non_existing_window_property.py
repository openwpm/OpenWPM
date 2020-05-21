
import re

from ..automation.utilities import db_utils
from . import utilities as util
from .openwpm_jstest import OpenWPMJSTest

# Since the window property remains non-existing, attempts to
# access the window property's attributes first fails when evaluating
# the non-existing window property, thus preventing us from receiving
# events about the attributes that were attempted to be accessed
# This is why we don't see any gets to window.nonExisting.nonExistingProp1
# etc below

GETS_AND_SETS = {
    ("window.nonExisting", "get", "undefined"),
    ("window.nonExisting", "get", "undefined"),
    ("window.nonExisting", "get", "undefined"),
    ("window.nonExisting", "get", "undefined"),
    ("window.nonExisting", "get", "undefined"),
    ("window.nonExisting", "get", "undefined"),
}

METHOD_CALLS = set()

TEST_PAGE = "instrument_non_existing_window_property.html"
TOP_URL = (
    u"%s/js_instrument/%s" % (util.BASE_TEST_URL, TEST_PAGE)
)

class TestJSInstrumentNonExistingWindowProperty(OpenWPMJSTest):


    def test_instrument_object(self):
        """ Ensure instrumentObject logs all property gets, sets, and calls """
        db = self.visit('/js_instrument/%s' % TEST_PAGE)
        rows = db_utils.get_javascript_entries(db, all_columns=True)
        self._check_calls(
            rows=rows,
            symbol_prefix='',
            doc_url=TOP_URL,
            top_url=TOP_URL,
            expected_method_calls=METHOD_CALLS,
            expected_gets_and_sets=GETS_AND_SETS,
        )
