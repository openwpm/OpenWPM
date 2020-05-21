from ..automation.utilities import db_utils
from . import utilities as util
from .openwpm_jstest import OpenWPMJSTest

GETS_AND_SETS = {
    ("window.partiallyExisting", "get", "{\"existingProp\":\"foo\"}"),
    ("window.partiallyExisting", "get", "{\"existingProp\":\"foo\"}"),
    ("window.partiallyExisting", "get", "{\"existingProp\":\"foo\"}"),
    ("window.partiallyExisting", "get", "{\"existingProp\":\"foo\"}"),
    ("window.partiallyExisting.existingProp", "get", "foo"),
    ("window.partiallyExisting", "get", "{\"existingProp\":\"foo\"}"),
    ("window.partiallyExisting.existingProp", "set", "blah1"),
    ("window.partiallyExisting", "get", "{\"existingProp\":\"blah1\"}"),
    ("window.partiallyExisting.existingProp", "get", "blah1"),
    ("window.partiallyExisting", "get", "{\"existingProp\":\"blah1\"}"),
    ("window.partiallyExisting.nonExistingProp1", "get", "undefined"),
    ("window.partiallyExisting", "get", "{\"existingProp\":\"blah1\"}"),
    ("window.partiallyExisting.nonExistingProp1", "set", "blah1"),
    ("window.partiallyExisting", "get", "{\"existingProp\":\"blah1\"}"),
    ("window.partiallyExisting.nonExistingProp1", "get", "blah1"),
    ("window.partiallyExisting", "get",
     "{\"existingProp\":\"blah1\"}"),  # Note 1
    ("window.partiallyExisting.nonExistingMethod1",
     "get", "undefined"),  # Note 2
}

# Note 1: nonExistingProp1 is not enumerable even after being set
# Note 2: nonExistingMethod1 shows up as a get rather than call

METHOD_CALLS = set()  # Note 2

TEST_PAGE = "instrument_existing_window_property.html"
TOP_URL = (
    u"%s/js_instrument/%s" % (util.BASE_TEST_URL, TEST_PAGE)
)


class TestJSInstrumentExistingWindowProperty(OpenWPMJSTest):

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
