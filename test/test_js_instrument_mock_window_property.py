from ..automation.utilities import db_utils
from . import utilities as util
from .openwpm_jstest import OpenWPMJSTest

GETS_AND_SETS = {
    ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
    ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
    ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
    ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
    ("window.MockClass.nonExistingProp1", "get", "undefined"),
    ("window.alreadyInstantiatedMockClassInstance.nonExistingProp1",
     "get", "undefined"),
    ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
    ("window.MockClass.nonExistingProp1", "set", "blah1"),
    ("window.alreadyInstantiatedMockClassInstance.nonExistingProp1",
     "set", "blah1"),
    ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
    ("window.MockClass.nonExistingProp1", "get", "blah1"),
    ("window.alreadyInstantiatedMockClassInstance.nonExistingProp1",
     "get", "blah1"),
    ("window.alreadyInstantiatedMockClassInstance", "get", "{}"),
    ("window.MockClass.nonExistingMethod1", "get", "undefined"),  # Note 1
    ("window.alreadyInstantiatedMockClassInstance.nonExistingMethod1",
     "get", "undefined"),  # Note 1
    ("window.newMockClassInstance", "get", "{}"),
    ("window.newMockClassInstance", "get", "{}"),
    ("window.newMockClassInstance", "get", "{}"),
    ("window.MockClass.nonExistingProp1", "get", "blah1"),  # Note 2
    ("window.newMockClassInstance", "get", "{}"),
    ("window.MockClass.nonExistingProp1", "set", "blah1"),
    ("window.newMockClassInstance", "get", "{}"),
    ("window.MockClass.nonExistingProp1", "get", "blah1"),
    ("window.newMockClassInstance", "get", "{}"),
    ("window.MockClass.nonExistingMethod1", "get", "undefined"),  # Note 1
}

# Note 1: nonExistingMethod1 shows up as a get rather than call
# Note 2: This may be a bug - the new instance
#         should not have a value here yet

METHOD_CALLS = {
    ("window.MockClass", "call", None),
}

TEST_PAGE = "instrument_mock_window_property.html"
TOP_URL = (
    u"%s/js_instrument/%s" % (util.BASE_TEST_URL, TEST_PAGE)
)


class TestJSInstrumentMockWindowProperty(OpenWPMJSTest):

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