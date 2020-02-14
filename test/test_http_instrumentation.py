#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import json
import os
from hashlib import sha256
from time import sleep
from urllib.parse import urlparse

import pytest

from ..automation import CommandSequence, TaskManager
from ..automation.utilities import db_utils
from . import utilities
from .openwpmtest import OpenWPMTest

# Data for test_page_visit
# format: (
# request_url,
# top_level_url,
# triggering_origin,
# loading_origin,
# loading_href,
# is_XHR, is_frame_load, is_full_page, is_tp_content, is_tp_window,
#   resource_type
HTTP_REQUESTS = {
    (
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'undefined',
        u'undefined',
        u'undefined',
        0, 0, 1, None, None, u'main_frame',
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_favicon.ico',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image',
    ),
    # (
    #     u'http://localtest.me:8000/test_pages/shared/test_favicon.ico',
    #     u'undefined',
    #     u'http://localtest.me:8000',
    #     u'http://localtest.me:8000',
    #     u'http://localtest.me:8000/test_pages/http_test_page.html',
    #     0, 0, 1, None, None, u'image',
    #  ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image_2.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'image',
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_script_2.js',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'script',
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_script.js',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'script',
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image',
    ),
    (
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 1, 0, None, None, u'sub_frame',
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_style.css',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'stylesheet',
    ),
    (
        u'http://localtest.me:8000/404.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/frame1.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/frame2.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/req1.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/req2.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/req3.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image_2.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image'
    ),
}

# format: (request_url, referrer, location)
# TODO: webext instrumentation doesn't support referrer yet
HTTP_RESPONSES = {
    (
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        # u'',
        u''),
    (
        u'http://localtest.me:8000/test_pages/shared/test_favicon.ico',
        # u'',
        u''),
    (
        u'http://localtest.me:8000/test_pages/shared/test_style.css',
        # u'http://localtest.me:8000/test_pages/http_test_page.html',
        u''),
    (
        u'http://localtest.me:8000/test_pages/shared/test_script.js',
        # u'http://localtest.me:8000/test_pages/http_test_page.html',
        u''),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image.png',
        # u'http://localtest.me:8000/test_pages/http_test_page.html',
        u''),
    (
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        # u'http://localtest.me:8000/test_pages/http_test_page.html',
        u''),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image_2.png',
        # u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        u''),
    (
        u'http://localtest.me:8000/test_pages/shared/test_script_2.js',
        # u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        u''),
    (
        u'http://localtest.me:8000/404.png',
        # u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        u''),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image_2.png',
        # u'http://localtest.me:8000/test_pages/http_test_page.html',
        u''),
}

# format: (source_url, destination_url)
HTTP_REDIRECTS = {
    (u'http://localtest.me:8000/MAGIC_REDIRECT/req1.png',
     u'http://localtest.me:8000/MAGIC_REDIRECT/req2.png'),
    (u'http://localtest.me:8000/MAGIC_REDIRECT/req2.png',
     u'http://localtest.me:8000/MAGIC_REDIRECT/req3.png'),
    (u'http://localtest.me:8000/MAGIC_REDIRECT/req3.png',
     u'http://localtest.me:8000/test_pages/shared/test_image_2.png'),
    (u'http://localtest.me:8000/MAGIC_REDIRECT/frame1.png',
     u'http://localtest.me:8000/MAGIC_REDIRECT/frame2.png'),
    (u'http://localtest.me:8000/MAGIC_REDIRECT/frame2.png',
     u'http://localtest.me:8000/404.png')
}

# Data for test_cache_hits_recorded
HTTP_CACHED_REQUESTS = {
    (
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'undefined',
        u'undefined',
        u'undefined',
        0, 0, 1, None, None, u'main_frame'
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_script_2.js',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'script'
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_script.js',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'script',
    ),
    (
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 1, 0, None, None, u'sub_frame'
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_style.css',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'stylesheet'
    ),
    (
        u'http://localtest.me:8000/404.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/frame1.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/frame2.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        0, 0, 0, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/req1.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/req2.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/MAGIC_REDIRECT/req3.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image'
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image_2.png',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        0, 0, 1, None, None, u'image'
    ),
}

# format: (request_url, referrer, is_cached)
# TODO: referrer isn't recorded by webext instrumentation yet.
HTTP_CACHED_RESPONSES = {
    (
        u'http://localtest.me:8000/test_pages/http_test_page.html',
        # u'',
        1),
    (
        u'http://localtest.me:8000/test_pages/shared/test_style.css',
        # u'http://localtest.me:8000/test_pages/http_test_page.html',
        1),
    (
        u'http://localtest.me:8000/test_pages/shared/test_script.js',
        # u'http://localtest.me:8000/test_pages/http_test_page.html',
        1),
    (
        u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        # u'http://localtest.me:8000/test_pages/http_test_page.html',
        1),
    (
        u'http://localtest.me:8000/test_pages/shared/test_script_2.js',
        # u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        1),
    (
        u'http://localtest.me:8000/404.png',
        # u'http://localtest.me:8000/test_pages/http_test_page_2.html',
        1),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image_2.png',
        1),
}

# format: (source_url, destination_url)
HTTP_CACHED_REDIRECTS = {
    (u'http://localtest.me:8000/MAGIC_REDIRECT/frame1.png',
     u'http://localtest.me:8000/MAGIC_REDIRECT/frame2.png'),
    (u'http://localtest.me:8000/MAGIC_REDIRECT/frame2.png',
     u'http://localtest.me:8000/404.png'),
    (u'http://localtest.me:8000/MAGIC_REDIRECT/req1.png',
     u'http://localtest.me:8000/MAGIC_REDIRECT/req2.png'),
    (u'http://localtest.me:8000/MAGIC_REDIRECT/req2.png',
     u'http://localtest.me:8000/MAGIC_REDIRECT/req3.png'),
    (u'http://localtest.me:8000/MAGIC_REDIRECT/req3.png',
     u'http://localtest.me:8000/test_pages/shared/test_image_2.png'),
}

# Test URL attribution for worker script requests
HTTP_WORKER_SCRIPT_REQUESTS = {
    (
        u'http://localtest.me:8000/test_pages/http_worker_page.html',
        u'http://localtest.me:8000/test_pages/http_worker_page.html',
        u'undefined',
        u'undefined',
        u'undefined',
        0, 0, 1, None, None, u'main_frame',
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_favicon.ico',
        u'http://localtest.me:8000/test_pages/http_worker_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_worker_page.html',
        0, 0, 1, None, None, u'image',
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/worker.js',
        u'http://localtest.me:8000/test_pages/http_worker_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_worker_page.html',
        0, 0, 1, None, None, u'script'
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image.png',
        u'http://localtest.me:8000/test_pages/http_worker_page.html',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/http_worker_page.html',
        1, 0, 1, None, None, u'xmlhttprequest'
    ),
    (
        u'http://localtest.me:8000/test_pages/shared/test_image.png',
        u'http://localtest.me:8000/test_pages/shared/worker.js',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000',
        u'http://localtest.me:8000/test_pages/shared/worker.js',
        1, 0, 1, None, None, u'xmlhttprequest'
    ),
}

# Test URL-attribution for Service Worker requests.
# localhost URLs are used instead of localtest.me because service workers
# are only loaded from secure contexts.
HTTP_SERVICE_WORKER_REQUESTS = {
    (
        u'http://localhost:8000/test_pages/http_service_worker_page.html',
        u'http://localhost:8000/test_pages/http_service_worker_page.html',
        u'undefined',
        u'undefined',
        u'undefined',
        0, 0, 1, None, None, u'main_frame',
    ),
    (
        u'http://localhost:8000/test_pages/shared/test_favicon.ico',
        u'http://localhost:8000/test_pages/http_service_worker_page.html',
        u'http://localhost:8000',
        u'http://localhost:8000',
        u'http://localhost:8000/test_pages/http_service_worker_page.html',
        0, 0, 1, None, None, u'image',
    ),
    (
        u'http://localhost:8000/test_pages/shared/service_worker.js',
        u'http://localhost:8000/test_pages/http_service_worker_page.html',
        u'http://localhost:8000',
        u'http://localhost:8000',
        u'http://localhost:8000/test_pages/http_service_worker_page.html',
        0, 0, 1, None, None, u'script'
    ),
    (
        u'http://localhost:8000/test_pages/shared/test_image.png',
        u'http://localhost:8000/test_pages/http_service_worker_page.html',
        u'http://localhost:8000',
        u'http://localhost:8000',
        u'http://localhost:8000/test_pages/http_service_worker_page.html',
        1, 0, 1, None, None, u'xmlhttprequest'
    ),
    (
        u'http://localhost:8000/test_pages/shared/test_image_2.png',
        u'http://localhost:8000/test_pages/shared/service_worker.js',
        u'http://localhost:8000',
        u'http://localhost:8000',
        u'http://localhost:8000/test_pages/shared/service_worker.js',
        1, 0, 1, None, None, u'xmlhttprequest'
    ),
}

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class TestHTTPInstrument(OpenWPMTest):

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0]['http_instrument'] = True
        return manager_params, browser_params

    def test_page_visit(self):
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        db = self.visit(test_url)

        request_id_to_url = dict()

        # HTTP Requests
        rows = db_utils.query_db(db, "SELECT * FROM http_requests")
        observed_records = set()
        for row in rows:
            observed_records.add((
                row['url'].split('?')[0],
                row['top_level_url'],
                row['triggering_origin'], row['loading_origin'],
                row['loading_href'], row['is_XHR'],
                row['is_frame_load'], row['is_full_page'],
                row['is_third_party_channel'],
                row['is_third_party_to_top_window'],
                row['resource_type'])
            )
            request_id_to_url[row['request_id']] = row['url']
        assert HTTP_REQUESTS == observed_records

        # HTTP Responses
        rows = db_utils.query_db(db, "SELECT * FROM http_responses")
        observed_records = set()
        for row in rows:
            observed_records.add((
                row['url'].split('?')[0],
                # TODO: webext-instrumentation doesn't support referrer
                # yet | row['referrer'],
                row['location']))
            assert row['request_id'] in request_id_to_url
            assert request_id_to_url[row['request_id']] == row['url']
        assert HTTP_RESPONSES == observed_records

        # HTTP Redirects
        rows = db_utils.query_db(db, "SELECT * FROM http_redirects")
        observed_records = set()
        for row in rows:
            # TODO: webext instrumentation doesn't support new_request_id yet
            # src = request_id_to_url[row['old_request_id']].split('?')[0]
            # dst = request_id_to_url[row['new_request_id']].split('?')[0]
            src = row['old_request_url'].split('?')[0]
            dst = row['new_request_url'].split('?')[0]
            observed_records.add((src, dst))
        assert HTTP_REDIRECTS == observed_records

    def test_cache_hits_recorded(self):
        """Verify all http responses are recorded, including cached responses

        Note that we expect to see all of the same requests and responses
        during the second vist (even if cached) except for images. Cached
        images do not trigger Observer Notification events.
        See Bug 634073: https://bugzilla.mozilla.org/show_bug.cgi?id=634073

        The test page includes an image which does several permanent redirects
        before returning a 404. We expect to see new requests and responses
        for this image when the page is reloaded. Additionally, the redirects
        should be cached.
        """
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(test_url, sleep=5)
        manager.get(test_url, sleep=5)
        manager.close()
        db = manager_params['db']

        request_id_to_url = dict()

        # HTTP Requests
        rows = db_utils.query_db(
            db, "SELECT * FROM http_requests WHERE visit_id = 2")
        observed_records = set()
        for row in rows:
            # HACK: favicon caching is unpredictable, don't bother checking it
            if row['url'].split('?')[0].endswith('favicon.ico'):
                continue
            observed_records.add((
                row['url'].split('?')[0],
                row['top_level_url'],
                row['triggering_origin'], row['loading_origin'],
                row['loading_href'], row['is_XHR'],
                row['is_frame_load'], row['is_full_page'],
                row['is_third_party_channel'],
                row['is_third_party_to_top_window'],
                row['resource_type'])
            )
            request_id_to_url[row['request_id']] = row['url']
        assert HTTP_CACHED_REQUESTS == observed_records

        # HTTP Responses
        rows = db_utils.query_db(
            db, "SELECT * FROM http_responses WHERE visit_id = 2")
        observed_records = set()
        for row in rows:
            # HACK: favicon caching is unpredictable, don't bother checking it
            if row['url'].split('?')[0].endswith('favicon.ico'):
                continue
            observed_records.add((
                row['url'].split('?')[0],
                # TODO: referrer isn't available yet in the
                # webext instrumentation | row['referrer'],
                row['is_cached']))
            assert row['request_id'] in request_id_to_url
            assert request_id_to_url[row['request_id']] == row['url']
        assert HTTP_CACHED_RESPONSES == observed_records

        # HTTP Redirects
        rows = db_utils.query_db(
            db, "SELECT * FROM http_redirects WHERE visit_id = 2")
        observed_records = set()
        for row in rows:
            # TODO: new_request_id isn't supported yet
            # src = request_id_to_url[row['old_request_id']].split('?')[0]
            # dst = request_id_to_url[row['new_request_id']].split('?')[0]
            src = row['old_request_url'].split('?')[0]
            dst = row['new_request_url'].split('?')[0]
            observed_records.add((src, dst))
        assert HTTP_CACHED_REDIRECTS == observed_records

    def test_javascript_saving(self, tmpdir):
        """ check that javascript content is saved and hashed correctly """
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        manager_params, browser_params = self.get_test_config(str(tmpdir))
        browser_params[0]['http_instrument'] = True
        browser_params[0]['save_content'] = "script"
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(url=test_url, sleep=1)
        manager.close()
        expected_hashes = {
            '0110c0521088c74f179615cd7c404816816126fa657550032f75ede67a66c7cc',
            'b34744034cd61e139f85f6c4c92464927bed8343a7ac08acf9fb3c6796f80f08'}
        for chash, content in db_utils.get_content(str(tmpdir)):
            chash = chash.decode('ascii').lower()
            pyhash = sha256(content).hexdigest().lower()
            assert pyhash == chash  # Verify expected key (sha256 of content)
            assert chash in expected_hashes
            expected_hashes.remove(chash)
        assert len(expected_hashes) == 0  # All expected hashes have been seen

    def test_document_saving(self, tmpdir):
        """ check that document content is saved and hashed correctly """
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        expected_hashes = {
            '2390eceab422db15bc45940b7e042e83e6cbd5f279f57e714bc4ad6cded7f966',
            '25343f42d9ffa5c082745f775b172db87d6e14dfbc3160b48669e06d727bfc8d'}
        manager_params, browser_params = self.get_test_config(str(tmpdir))
        browser_params[0]['http_instrument'] = True
        browser_params[0]['save_content'] = "main_frame,sub_frame"
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(url=test_url, sleep=1)
        manager.close()
        for chash, content in db_utils.get_content(str(tmpdir)):
            chash = chash.decode('ascii').lower()
            pyhash = sha256(content).hexdigest().lower()
            assert pyhash == chash  # Verify expected key (sha256 of content)
            assert chash in expected_hashes
            expected_hashes.remove(chash)
        assert len(expected_hashes) == 0  # All expected hashes have been seen

    def test_content_saving(self, tmpdir):
        """ check that content is saved and hashed correctly """
        test_url = utilities.BASE_TEST_URL + '/http_test_page.html'
        manager_params, browser_params = self.get_test_config(str(tmpdir))
        browser_params[0]['http_instrument'] = True
        browser_params[0]['save_content'] = True
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(url=test_url, sleep=1)
        manager.close()
        db = manager_params['db']
        rows = db_utils.query_db(db, "SELECT * FROM http_responses;")
        disk_content = dict()
        for row in rows:
            if 'MAGIC_REDIRECT' in row['url'] or '404' in row['url']:
                continue
            path = urlparse(row['url']).path
            with open(os.path.join(BASE_PATH, path[1:]), 'rb') as f:
                content = f.read()
            chash = sha256(content).hexdigest()
            assert chash == row['content_hash']
            disk_content[chash] = content

        ldb_content = dict()
        for chash, content in db_utils.get_content(str(tmpdir)):
            chash = chash.decode('ascii')
            ldb_content[chash] = content

        for k, v in disk_content.items():
            assert v == ldb_content[k]

    def test_worker_script_requests(self):
        """Check correct URL attribution for requests made by worker script"""
        test_url = utilities.BASE_TEST_URL + '/http_worker_page.html'
        db = self.visit(test_url)

        request_id_to_url = dict()

        # HTTP Requests
        rows = db_utils.query_db(db, "SELECT * FROM http_requests")
        observed_records = set()
        for row in rows:
            observed_records.add((
                row['url'].split('?')[0],
                row['top_level_url'],
                row['triggering_origin'], row['loading_origin'],
                row['loading_href'], row['is_XHR'],
                row['is_frame_load'], row['is_full_page'],
                row['is_third_party_channel'],
                row['is_third_party_to_top_window'],
                row['resource_type'])
            )
            request_id_to_url[row['request_id']] = row['url']

        assert HTTP_WORKER_SCRIPT_REQUESTS == observed_records

    def test_service_worker_requests(self):
        """Check correct URL attribution for requests made by service worker"""
        test_url = 'http://localhost:8000/test_pages' + \
            '/http_service_worker_page.html'
        db = self.visit(test_url)

        request_id_to_url = dict()

        # HTTP Requests
        rows = db_utils.query_db(db, "SELECT * FROM http_requests")
        observed_records = set()
        for row in rows:
            observed_records.add((
                row['url'].split('?')[0],
                row['top_level_url'],
                row['triggering_origin'], row['loading_origin'],
                row['loading_href'], row['is_XHR'],
                row['is_frame_load'], row['is_full_page'],
                row['is_third_party_channel'],
                row['is_third_party_to_top_window'],
                row['resource_type'])
            )
            request_id_to_url[row['request_id']] = row['url']

        assert HTTP_SERVICE_WORKER_REQUESTS == observed_records


class TestPOSTInstrument(OpenWPMTest):
    """Make sure we can capture all the POST request data.

    The encoding types tested are explained here:
    https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Using_XMLHttpRequest#Using_nothing_but_XMLHttpRequest
    """
    post_data = ('{"email":["test@example.com"],'
                 '"username":["name surname+你好"],'
                 '"test":["ПриватБанк – банк для тих, хто йде вперед"]}')
    post_data_json = json.loads(post_data)
    post_data_multiline = r'{"email":["test@example.com"],"username":'\
        r'["name surname+你好"],'\
        r'"test":["ПриватБанк – банк для тих, хто йде вперед"],'\
        r'"multiline_text":["line1\r\n\r\nline2 line2_word2"]}'
    post_data_multiline_json = json.loads(post_data_multiline)
    post_data_multiline_raw = 'email=test@example.com\r\n'\
        'username=name surname+你好\r\n'\
        'test=ПриватБанк – банк для тих, хто йде вперед\r\n'\
        'multiline_text=line1\r\n\r\n'\
        'line2 line2_word2\r\n'

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0]['http_instrument'] = True
        return manager_params, browser_params

    def get_post_requests_from_db(self, db):
        """Query the crawl database and return the POST requests."""
        return db_utils.query_db(db, "SELECT * FROM http_requests\
                                       WHERE method = 'POST'")

    def get_post_request_body_from_db(self, db, raw=False):
        """Return the body of the first POST request in crawl db."""
        posts = self.get_post_requests_from_db(db)
        if raw:
            return base64.b64decode(
                json.loads(posts[0]['post_body_raw'])[0][1])
        else:
            return posts[0]['post_body']

    def test_record_post_data_x_www_form_urlencoded(self):
        encoding_type = "application/x-www-form-urlencoded"
        db = self.visit("/post_request.html?encoding_type=" + encoding_type)
        post_body = self.get_post_request_body_from_db(db)
        assert json.loads(post_body) == self.post_data_multiline_json

    def test_record_post_data_text_plain(self):
        encoding_type = "text/plain"
        db = self.visit('/post_request.html?encoding_type=' + encoding_type)
        post_body = self.get_post_request_body_from_db(db, True)
        if not isinstance(self.post_data_multiline_raw, str):
            expected = self.post_data_multiline_raw.decode('utf-8')
        else:
            expected = self.post_data_multiline_raw
        assert post_body.decode('utf8') == expected

    def test_record_post_data_multipart_formdata(self):
        encoding_type = "multipart/form-data"
        db = self.visit('/post_request.html?encoding_type=' + encoding_type)
        post_body = self.get_post_request_body_from_db(db)
        assert json.loads(post_body) == self.post_data_multiline_json
        post_row = self.get_post_requests_from_db(db)[0]
        headers = post_row['headers']
        # make sure the "request headers from upload stream" are stored in db
        assert "Content-Type" in headers
        assert encoding_type in headers
        assert "Content-Length" in post_row['headers']

    def test_record_post_data_ajax(self, tmpdir):
        post_format = "object"
        db = self.visit("/post_request_ajax.html?format=" + post_format)
        post_body = self.get_post_request_body_from_db(db)
        assert json.loads(post_body) == self.post_data_json

    def test_record_post_data_ajax_no_key_value(self):
        """Test AJAX payloads that are not in the key=value form."""
        post_format = "noKeyValue"
        db = self.visit("/post_request_ajax.html?format=" + post_format)
        post_body = self.get_post_request_body_from_db(db, True)
        assert post_body.decode('utf8') == "test@example.com + name surname"

    def test_record_post_data_ajax_no_key_value_base64_encoded(self):
        """Test Base64 encoded AJAX payloads (no key=value form)."""
        post_format = "noKeyValueBase64"
        db = self.visit("/post_request_ajax.html?format=" + post_format)
        post_body = self.get_post_request_body_from_db(db, True)
        assert post_body.decode('utf8') == (
            "dGVzdEBleGFtcGxlLmNvbSArIG5hbWUgc3VybmFtZQ==")

    def test_record_post_formdata(self):
        post_format = "formData"
        db = self.visit("/post_request_ajax.html?format=" + post_format)
        post_body = self.get_post_request_body_from_db(db)
        assert json.loads(post_body) == self.post_data_json

    def test_record_binary_post_data(self):
        post_format = "binary"
        db = self.visit("/post_request_ajax.html?format=" + post_format)
        post_body = self.get_post_request_body_from_db(db, True)
        # Binary strings get put into the database as-if they were latin-1.
        assert bytes(bytearray(range(100))) == post_body

    @pytest.mark.skip(reason="Firefox is currently not able to return the "
                      "file content for an upload, only the filename")
    def test_record_file_upload(self):
        """Test that we correctly capture the uploaded file contents.

        We upload a CSS file and a PNG file to test both text based and
        binary files.

        File uploads are not expected in the crawl data, but we make sure we
        correctly parse the POST data in this very common scenario.

        Firefox is currently not able to return the FormData with the file
        contents, currently only the filenames are returned. This is due to
        a limitation in the current API implementation:

        https://searchfox.org/mozilla-central/rev/b3b401254229f0a26f7ee625ef5f09c6c31e3949/toolkit/components/extensions/webrequest/WebRequestUpload.jsm#339

        Therefore, the test is currently skipped.
        """
        img_file_path = os.path.abspath("test_pages/shared/test_image.png")
        css_file_path = os.path.abspath("test_pages/shared/test_style.css")

        def type_filenames_into_form(**kwargs):
            """Simulate typing into the file upload input fields."""
            driver = kwargs['driver']
            img_file_upload_element = driver.find_element_by_id("upload-img")
            css_file_upload_element = driver.find_element_by_id("upload-css")
            img_file_upload_element.send_keys(img_file_path)
            css_file_upload_element.send_keys(css_file_path)
            sleep(5)  # wait for the form submission (3 sec after onload)

        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)
        test_url = utilities.BASE_TEST_URL + "/post_file_upload.html"
        cs = CommandSequence.CommandSequence(test_url)
        cs.get(sleep=0, timeout=60)
        cs.run_custom_function(type_filenames_into_form, ())
        manager.execute_command_sequence(cs)
        manager.close()

        post_body = self.get_post_request_body_from_db(manager_params['db'])
        # Binary strings get put into the database as-if they were latin-1.
        with open(img_file_path, 'rb') as f:
            img_file_content = f.read().strip().decode('latin-1')
        with open(css_file_path, 'rt') as f:
            css_file_content = f.read().strip()
        # POST data is stored as JSON in the DB
        post_body_decoded = json.loads(post_body)
        expected_body = {u"username": u"name surname+",
                         u"upload-css": css_file_content,
                         u"upload-img": img_file_content}
        assert expected_body == post_body_decoded
