""" Contains lists of expected data and or rows for tests """
from __future__ import absolute_import

from .utilities import BASE_TEST_URL, BASE_TEST_URL_DOMAIN

# XXX DO NOT PLACE NEW PROPERTIES HERE. Move anything you need to edit out
# XXX of this file and into the respective test file. See Issue #73.

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
