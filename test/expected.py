""" Contains lists of expected data and or rows for tests """
from __future__ import absolute_import
from .utilities import BASE_TEST_URL, BASE_TEST_URL_DOMAIN, BASE_TEST_URL_NOPATH

# XXX DO NOT PLACE NEW PROPERTIES HERE. Move anything you need to edit out
# XXX of this file and into the respective test file. See Issue #73.


# HTTP request call stack instrumentation
# Expected stack frames
HTTP_STACKTRACE_TEST_URL = BASE_TEST_URL + "/http_stacktrace.html"
stack_trace_inject_image =\
    "inject_image@" + HTTP_STACKTRACE_TEST_URL + ":18:7;null\n"\
    "inject_all@" + HTTP_STACKTRACE_TEST_URL + ":22:7;null\n"\
    "onload@" + HTTP_STACKTRACE_TEST_URL + ":1:1;null"

RAWGIT_HTTP_STACKTRACE_TEST_URL = "https://rawgit.com/gunesacar/b927d3fe69f3e7bf456da5192f74beea/raw/8d3e490b5988c633101ec45ef1443e61b1fd495e/inject_pixel.js"  # noqa
stack_trace_inject_pixel =\
    "inject_pixel@" + RAWGIT_HTTP_STACKTRACE_TEST_URL + ":4:3;null\n"\
    "null@" + RAWGIT_HTTP_STACKTRACE_TEST_URL + ":6:1;null"

stack_trace_inject_js =\
    "inject_js@" + HTTP_STACKTRACE_TEST_URL + ":13:7;null\n"\
    "inject_all@" + HTTP_STACKTRACE_TEST_URL + ":21:7;null\n"\
    "onload@" + HTTP_STACKTRACE_TEST_URL + ":1:1;null"

http_stacktraces = set((stack_trace_inject_image, stack_trace_inject_pixel, stack_trace_inject_js))
# parsed HTTP call stack dict
call_stack_inject_image =\
    [{"func_name": "inject_image",
     "filename": HTTP_STACKTRACE_TEST_URL,
     "line_no": "18",
     "col_no": "7",
     "async_cause": "null"
     },
    {"func_name": "inject_all",
     "filename": HTTP_STACKTRACE_TEST_URL,
     "line_no": "22",
     "col_no": "7",
     "async_cause": "null"
     },
    {"func_name": "onload",
     "filename": HTTP_STACKTRACE_TEST_URL,
     "line_no": "1",
     "col_no": "1",
     "async_cause": "null"
     }]

JS_COOKIE_TEST_URL = u'%s/js_cookie.html' % BASE_TEST_URL

js_cookie = (JS_COOKIE_TEST_URL,
             u'%s' % BASE_TEST_URL_DOMAIN,
             u'test_cookie',
             u'Test-0123456789',
             u'%s' % BASE_TEST_URL_DOMAIN,
             u'/')

lso_content = [u'%s/lso/setlso.html?lso_test_key=test_key&lso_test_value=REPLACEME' % BASE_TEST_URL,  # noqa
               u'localtest.me',
               u'FlashCookie.sol',
               u'localtest.me/FlashCookie.sol',
               u'test_key',
               u'REPLACEME']

SET_PROP_TEST_PAGE = u'%s/set_property/set_property.js' % BASE_TEST_URL
set_property = [(SET_PROP_TEST_PAGE,
                 u'5', u'3',
                 u'set_window_name@%s:5:3\n'
                 '@%s:8:1\n' % (SET_PROP_TEST_PAGE, SET_PROP_TEST_PAGE),
                 u'window.HTMLFormElement.action',
                 u'set', u'TEST-ACTION', None, None)]

page_links = {
    (u'http://localtest.me:8000/test_pages/simple_a.html', u'http://localtest.me:8000/test_pages/simple_c.html'),
    (u'http://localtest.me:8000/test_pages/simple_a.html', u'http://localtest.me:8000/test_pages/simple_d.html'),
    (u'http://localtest.me:8000/test_pages/simple_a.html', u'http://example.com/test.html?localtest.me'),
}
