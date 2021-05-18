#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import json
import os
from hashlib import sha256
from pathlib import Path
from time import sleep
from typing import List, Optional, Set, Tuple
from urllib.parse import urlparse

import pytest

from openwpm import command_sequence, task_manager
from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.leveldb import LevelDbProvider
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.utilities import db_utils

from . import utilities
from .openwpmtest import OpenWPMTest

# Data for test_page_visit
# format: (
# request_url,
# top_level_url,
# triggering_origin,
# loading_origin,
# loading_href,
# is_XHR, is_tp_content, is_tp_window,
#   resource_type
HTTP_REQUESTS = {
    (
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        "undefined",
        "undefined",
        "undefined",
        0,
        None,
        None,
        "main_frame",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_favicon.ico",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image_2.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_script_2.js",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "script",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_script.js",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "script",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "sub_frame",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_style.css",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "stylesheet",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/404.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame1.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame2.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req1.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req2.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req3.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image_2.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
}

# format: (request_url, referrer, location)
# TODO: webext instrumentation doesn't support referrer yet
HTTP_RESPONSES = {
    (
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        # u'',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_favicon.ico",
        # u'',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_style.css",
        # u'http://localhost:8000/test_pages/http_test_page.html',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_script.js",
        # u'http://localhost:8000/test_pages/http_test_page.html',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image.png",
        # u'http://localhost:8000/test_pages/http_test_page.html',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        # u'http://localhost:8000/test_pages/http_test_page.html',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image_2.png",
        # u'http://localhost:8000/test_pages/http_test_page_2.html',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_script_2.js",
        # u'http://localhost:8000/test_pages/http_test_page_2.html',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/404.png",
        # u'http://localhost:8000/test_pages/http_test_page_2.html',
        "",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image_2.png",
        # u'http://localhost:8000/test_pages/http_test_page.html',
        "",
    ),
}

# format: (source_url, destination_url, location header)
HTTP_REDIRECTS = {
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req1.png",
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req2.png",
        "req2.png?dst=req3.png&dst=/test_pages/shared/test_image_2.png",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req2.png",
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req3.png",
        "req3.png?dst=/test_pages/shared/test_image_2.png",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req3.png",
        f"{utilities.BASE_TEST_URL}/shared/test_image_2.png",
        "/test_pages/shared/test_image_2.png",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame1.png",
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame2.png",
        "frame2.png?dst=/404.png",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame2.png",
        f"{utilities.BASE_TEST_URL_NOPATH}/404.png",
        "/404.png",
    ),
}

# Data for test_cache_hits_recorded
HTTP_CACHED_REQUESTS = {
    (
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        "undefined",
        "undefined",
        "undefined",
        0,
        None,
        None,
        "main_frame",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_script_2.js",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "script",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_script.js",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "script",
    ),
    (
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "sub_frame",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/404.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame1.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame2.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req1.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req2.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req3.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image_2.png",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        0,
        None,
        None,
        "image",
    ),
}

# format: (request_url, referrer, is_cached)
# TODO: referrer isn't recorded by webext instrumentation yet.
HTTP_CACHED_RESPONSES = {
    (
        f"{utilities.BASE_TEST_URL}/http_test_page.html",
        # u'',
        1,
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_script.js",
        # u'http://localhost:8000/test_pages/http_test_page.html',
        1,
    ),
    (
        f"{utilities.BASE_TEST_URL}/http_test_page_2.html",
        # u'http://localhost:8000/test_pages/http_test_page.html',
        1,
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_script_2.js",
        # u'http://localhost:8000/test_pages/http_test_page_2.html',
        1,
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/404.png",
        # u'http://localhost:8000/test_pages/http_test_page_2.html',
        1,
    ),
    (f"{utilities.BASE_TEST_URL}/shared/test_image_2.png", 1),
}

# format: (source_url, destination_url)
HTTP_CACHED_REDIRECTS = {
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame1.png",
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame2.png",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/frame2.png",
        f"{utilities.BASE_TEST_URL_NOPATH}/404.png",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req1.png",
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req2.png",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req2.png",
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req3.png",
    ),
    (
        f"{utilities.BASE_TEST_URL_NOPATH}/MAGIC_REDIRECT/req3.png",
        f"{utilities.BASE_TEST_URL}/shared/test_image_2.png",
    ),
}

# Test URL attribution for worker script requests
HTTP_WORKER_SCRIPT_REQUESTS = {
    (
        f"{utilities.BASE_TEST_URL}/http_worker_page.html",
        f"{utilities.BASE_TEST_URL}/http_worker_page.html",
        "undefined",
        "undefined",
        "undefined",
        0,
        None,
        None,
        "main_frame",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_favicon.ico",
        f"{utilities.BASE_TEST_URL}/http_worker_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_worker_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/worker.js",
        f"{utilities.BASE_TEST_URL}/http_worker_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_worker_page.html",
        0,
        None,
        None,
        "script",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image.png",
        f"{utilities.BASE_TEST_URL}/http_worker_page.html",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/http_worker_page.html",
        1,
        None,
        None,
        "xmlhttprequest",
    ),
    (
        f"{utilities.BASE_TEST_URL}/shared/test_image.png",
        f"{utilities.BASE_TEST_URL}/shared/worker.js",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL_NOPATH}",
        f"{utilities.BASE_TEST_URL}/shared/worker.js",
        1,
        None,
        None,
        "xmlhttprequest",
    ),
}

# Test URL-attribution for Service Worker requests.
HTTP_SERVICE_WORKER_REQUESTS = {
    (
        "http://localhost:8000/test_pages/http_service_worker_page.html",
        "http://localhost:8000/test_pages/http_service_worker_page.html",
        "undefined",
        "undefined",
        "undefined",
        0,
        None,
        None,
        "main_frame",
    ),
    (
        "http://localhost:8000/test_pages/shared/test_favicon.ico",
        "http://localhost:8000/test_pages/http_service_worker_page.html",
        "http://localhost:8000",
        "http://localhost:8000",
        "http://localhost:8000/test_pages/http_service_worker_page.html",
        0,
        None,
        None,
        "image",
    ),
    (
        "http://localhost:8000/test_pages/shared/service_worker.js",
        "http://localhost:8000/test_pages/http_service_worker_page.html",
        "http://localhost:8000",
        "http://localhost:8000",
        "http://localhost:8000/test_pages/http_service_worker_page.html",
        0,
        None,
        None,
        "script",
    ),
    (
        "http://localhost:8000/test_pages/shared/test_image.png",
        "http://localhost:8000/test_pages/http_service_worker_page.html",
        "http://localhost:8000",
        "http://localhost:8000",
        "http://localhost:8000/test_pages/http_service_worker_page.html",
        1,
        None,
        None,
        "xmlhttprequest",
    ),
    (
        "http://localhost:8000/test_pages/shared/test_image_2.png",
        "http://localhost:8000/test_pages/shared/service_worker.js",
        "http://localhost:8000",
        "http://localhost:8000",
        "http://localhost:8000/test_pages/shared/service_worker.js",
        1,
        None,
        None,
        "xmlhttprequest",
    ),
}

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class TestHTTPInstrument(OpenWPMTest):
    def get_config(
        self, data_dir: Optional[Path]
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0].http_instrument = True
        return manager_params, browser_params

    def test_worker_script_requests(self):
        """Check correct URL attribution for requests made by worker script"""
        test_url = utilities.BASE_TEST_URL + "/http_worker_page.html"
        db = self.visit(test_url)

        request_id_to_url = dict()

        # HTTP Requests
        rows = db_utils.query_db(db, "SELECT * FROM http_requests")
        observed_records = set()
        for row in rows:
            observed_records.add(
                (
                    row["url"].split("?")[0],
                    row["top_level_url"],
                    row["triggering_origin"],
                    row["loading_origin"],
                    row["loading_href"],
                    row["is_XHR"],
                    row["is_third_party_channel"],
                    row["is_third_party_to_top_window"],
                    row["resource_type"],
                )
            )
            request_id_to_url[row["request_id"]] = row["url"]

        assert HTTP_WORKER_SCRIPT_REQUESTS == observed_records

    def test_service_worker_requests(self):
        """Check correct URL attribution for requests made by service worker"""
        test_url = utilities.BASE_TEST_URL + "/http_service_worker_page.html"
        db = self.visit(test_url)

        request_id_to_url = dict()

        # HTTP Requests
        rows = db_utils.query_db(db, "SELECT * FROM http_requests")
        observed_records = set()
        for row in rows:
            observed_records.add(
                (
                    row["url"].split("?")[0],
                    row["top_level_url"],
                    row["triggering_origin"],
                    row["loading_origin"],
                    row["loading_href"],
                    row["is_XHR"],
                    row["is_third_party_channel"],
                    row["is_third_party_to_top_window"],
                    row["resource_type"],
                )
            )
            request_id_to_url[row["request_id"]] = row["url"]

        assert HTTP_SERVICE_WORKER_REQUESTS == observed_records


class TestPOSTInstrument(OpenWPMTest):
    """Make sure we can capture all the POST request data.

    The encoding types tested are explained here:
    https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Using_XMLHttpRequest#Using_nothing_but_XMLHttpRequest
    """

    post_data = (
        '{"email":["test@example.com"],'
        '"username":["name surname+你好"],'
        '"test":["ПриватБанк – банк для тих, хто йде вперед"]}'
    )
    post_data_json = json.loads(post_data)
    post_data_multiline = (
        r'{"email":["test@example.com"],"username":'
        r'["name surname+你好"],'
        r'"test":["ПриватБанк – банк для тих, хто йде вперед"],'
        r'"multiline_text":["line1\r\n\r\nline2 line2_word2"]}'
    )
    post_data_multiline_json = json.loads(post_data_multiline)
    post_data_multiline_raw = (
        "email=test@example.com\r\n"
        "username=name surname+你好\r\n"
        "test=ПриватБанк – банк для тих, хто йде вперед\r\n"
        "multiline_text=line1\r\n\r\n"
        "line2 line2_word2\r\n"
    )

    def get_config(
        self, data_dir: Optional[Path] = None
    ) -> Tuple[ManagerParams, List[BrowserParams]]:
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0].http_instrument = True
        return manager_params, browser_params

    def get_post_requests_from_db(self, db):
        """Query the crawl database and return the POST requests."""
        return db_utils.query_db(
            db,
            "SELECT * FROM http_requests\
                                       WHERE method = 'POST'",
        )

    def get_post_request_body_from_db(self, db, raw=False):
        """Return the body of the first POST request in crawl db."""
        posts = self.get_post_requests_from_db(db)
        if raw:
            return base64.b64decode(json.loads(posts[0]["post_body_raw"])[0][1])
        else:
            return posts[0]["post_body"]

    def test_record_post_data_x_www_form_urlencoded(self):
        encoding_type = "application/x-www-form-urlencoded"
        db = self.visit("/post_request.html?encoding_type=" + encoding_type)
        post_body = self.get_post_request_body_from_db(db)
        assert json.loads(post_body) == self.post_data_multiline_json

    def test_record_post_data_text_plain(self):
        encoding_type = "text/plain"
        db = self.visit("/post_request.html?encoding_type=" + encoding_type)
        post_body = self.get_post_request_body_from_db(db, True)
        if not isinstance(self.post_data_multiline_raw, str):
            expected = self.post_data_multiline_raw.decode("utf-8")
        else:
            expected = self.post_data_multiline_raw
        assert post_body.decode("utf8") == expected

    def test_record_post_data_multipart_formdata(self):
        encoding_type = "multipart/form-data"
        db = self.visit("/post_request.html?encoding_type=" + encoding_type)
        post_body = self.get_post_request_body_from_db(db)
        assert json.loads(post_body) == self.post_data_multiline_json
        post_row = self.get_post_requests_from_db(db)[0]
        headers = post_row["headers"]
        # make sure the "request headers from upload stream" are stored in db
        assert "Content-Type" in headers
        assert encoding_type in headers
        assert "Content-Length" in post_row["headers"]

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
        assert post_body.decode("utf8") == "test@example.com + name surname"

    def test_record_post_data_ajax_no_key_value_base64_encoded(self):
        """Test Base64 encoded AJAX payloads (no key=value form)."""
        post_format = "noKeyValueBase64"
        db = self.visit("/post_request_ajax.html?format=" + post_format)
        post_body = self.get_post_request_body_from_db(db, True)
        assert post_body.decode("utf8") == (
            "dGVzdEBleGFtcGxlLmNvbSArIG5hbWUgc3VybmFtZQ=="
        )

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

    @pytest.mark.skip(
        reason="Firefox is currently not able to return the "
        "file content for an upload, only the filename"
    )
    def test_record_file_upload(self, task_manager_creator):
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

        manager_params, browser_params = self.get_config()
        manager, db_path = task_manager_creator((manager_params, browser_params))
        test_url = utilities.BASE_TEST_URL + "/post_file_upload.html"
        cs = command_sequence.CommandSequence(test_url)
        cs.get(sleep=0, timeout=60)
        cs.append_command(FilenamesIntoFormCommand(img_file_path, css_file_path))
        manager.execute_command_sequence(cs)
        manager.close()

        post_body = self.get_post_request_body_from_db(db_path)
        # Binary strings get put into the database as-if they were latin-1.
        with open(img_file_path, "rb") as f:
            img_file_content = f.read().strip().decode("latin-1")
        with open(css_file_path, "rt") as f:
            css_file_content = f.read().strip()
        # POST data is stored as JSON in the DB
        post_body_decoded = json.loads(post_body)
        expected_body = {
            "username": "name surname+",
            "upload-css": css_file_content,
            "upload-img": img_file_content,
        }
        assert expected_body == post_body_decoded


@pytest.mark.parametrize("delayed", [True, False])
def test_page_visit(task_manager_creator, http_params, delayed):
    test_url = utilities.BASE_TEST_URL + "/http_test_page.html"
    manager_params, browser_params = http_params()
    if delayed:
        for browser_param in browser_params:
            browser_param.custom_params[
                "pre_instrumentation_code"
            ] = """
                const startTime = Date.now();
                while (Date.now() - startTime < 5000) { // Delaying for 5s
                    console.log("delaying startup");
                };
            """

    tm, db = task_manager_creator((manager_params, browser_params))
    with tm as tm:
        tm.get(test_url)

    request_id_to_url = dict()

    # HTTP Requests
    rows = db_utils.query_db(db, "SELECT * FROM http_requests")
    observed_records = set()
    for row in rows:
        observed_records.add(
            (
                row["url"].split("?")[0],
                row["top_level_url"],
                row["triggering_origin"],
                row["loading_origin"],
                row["loading_href"],
                row["is_XHR"],
                row["is_third_party_channel"],
                row["is_third_party_to_top_window"],
                row["resource_type"],
            )
        )

        request_id_to_url[row["request_id"]] = row["url"]
    assert HTTP_REQUESTS == observed_records

    # HTTP Responses
    rows = db_utils.query_db(db, "SELECT * FROM http_responses")
    observed_records: Set[Tuple[str, str]] = set()
    for row in rows:
        observed_records.add(
            (
                row["url"].split("?")[0],
                # TODO: webext-instrumentation doesn't support referrer
                # yet | row['referrer'],
                row["location"],
            )
        )
        assert row["request_id"] in request_id_to_url
        assert request_id_to_url[row["request_id"]] == row["url"]
    assert HTTP_RESPONSES == observed_records

    # HTTP Redirects
    rows = db_utils.query_db(db, "SELECT * FROM http_redirects")
    observed_records = set()
    for row in rows:
        # TODO: webext instrumentation doesn't support new_request_id yet
        # src = request_id_to_url[row['old_request_id']].split('?')[0]
        # dst = request_id_to_url[row['new_request_id']].split('?')[0]
        src = row["old_request_url"].split("?")[0]
        dst = row["new_request_url"].split("?")[0]
        headers = json.loads(row["headers"])
        location = None
        for header, value in headers:
            if header.lower() == "location":
                location = value
                break
        observed_records.add((src, dst, location))
    assert HTTP_REDIRECTS == observed_records


def test_javascript_saving(http_params, xpi, server):
    """check that javascript content is saved and hashed correctly"""
    test_url = utilities.BASE_TEST_URL + "/http_test_page.html"
    manager_params, browser_params = http_params()

    for browser_param in browser_params:
        browser_param.http_instrument = True
        browser_param.save_content = "script"

    structured_storage = SQLiteStorageProvider(
        db_path=manager_params.data_directory / "crawl-data.sqlite"
    )
    ldb_path = Path(manager_params.data_directory) / "content.ldb"
    unstructured_storage = LevelDbProvider(db_path=ldb_path)
    manager = task_manager.TaskManager(
        manager_params, browser_params, structured_storage, unstructured_storage
    )
    manager.get(url=test_url, sleep=1)
    manager.close()
    expected_hashes = {
        "0110c0521088c74f179615cd7c404816816126fa657550032f75ede67a66c7cc",
        "b34744034cd61e139f85f6c4c92464927bed8343a7ac08acf9fb3c6796f80f08",
    }
    for chash, content in db_utils.get_content(ldb_path):
        chash = chash.decode("ascii").lower()
        pyhash = sha256(content).hexdigest().lower()
        assert pyhash == chash  # Verify expected key (sha256 of content)
        assert chash in expected_hashes
        expected_hashes.remove(chash)
    assert len(expected_hashes) == 0  # All expected hashes have been seen


def test_document_saving(http_params, xpi, server):
    """check that document content is saved and hashed correctly"""
    test_url = utilities.BASE_TEST_URL + "/http_test_page.html"
    expected_hashes = {
        "2390eceab422db15bc45940b7e042e83e6cbd5f279f57e714bc4ad6cded7f966",
        "25343f42d9ffa5c082745f775b172db87d6e14dfbc3160b48669e06d727bfc8d",
    }
    manager_params, browser_params = http_params()
    for browser_param in browser_params:
        browser_param.http_instrument = True
        browser_param.save_content = "main_frame,sub_frame"

    structured_storage = SQLiteStorageProvider(
        db_path=manager_params.data_directory / "crawl-data.sqlite"
    )
    ldb_path = Path(manager_params.data_directory) / "content.ldb"
    unstructured_storage = LevelDbProvider(db_path=ldb_path)
    manager = task_manager.TaskManager(
        manager_params, browser_params, structured_storage, unstructured_storage
    )

    manager.get(url=test_url, sleep=1)
    manager.close()
    for chash, content in db_utils.get_content(ldb_path):
        chash = chash.decode("ascii").lower()
        pyhash = sha256(content).hexdigest().lower()
        assert pyhash == chash  # Verify expected key (sha256 of content)
        assert chash in expected_hashes
        expected_hashes.remove(chash)
    assert len(expected_hashes) == 0  # All expected hashes have been seen


def test_content_saving(http_params, xpi, server):
    """check that content is saved and hashed correctly"""
    test_url = utilities.BASE_TEST_URL + "/http_test_page.html"
    manager_params, browser_params = http_params()
    for browser_param in browser_params:
        browser_param.http_instrument = True
        browser_param.save_content = True
    db = manager_params.data_directory / "crawl-data.sqlite"
    structured_storage = SQLiteStorageProvider(db_path=db)
    ldb_path = Path(manager_params.data_directory) / "content.ldb"
    unstructured_storage = LevelDbProvider(db_path=ldb_path)
    manager = task_manager.TaskManager(
        manager_params, browser_params, structured_storage, unstructured_storage
    )
    manager.get(url=test_url, sleep=1)
    manager.close()

    rows = db_utils.query_db(db, "SELECT * FROM http_responses;")
    disk_content = dict()
    for row in rows:
        if "MAGIC_REDIRECT" in row["url"] or "404" in row["url"]:
            continue
        path = urlparse(row["url"]).path
        with open(os.path.join(BASE_PATH, path[1:]), "rb") as f:
            content = f.read()
        chash = sha256(content).hexdigest()
        assert chash == row["content_hash"]
        disk_content[chash] = content

    ldb_content = dict()
    for chash, content in db_utils.get_content(ldb_path):
        chash = chash.decode("ascii")
        ldb_content[chash] = content

    for k, v in disk_content.items():
        assert v == ldb_content[k]


def test_cache_hits_recorded(http_params, task_manager_creator):
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
    test_url = utilities.BASE_TEST_URL + "/http_test_page.html"
    manager_params, browser_params = http_params()
    # ensuring that we only spawn one browser
    manager_params.num_browsers = 1
    manager, db = task_manager_creator((manager_params, [browser_params[0]]))
    for i in range(2):
        cs = CommandSequence(test_url, site_rank=i)
        cs.get(sleep=5)
        manager.execute_command_sequence(cs)

    manager.close()

    request_id_to_url = dict()

    # HTTP Requests
    rows = db_utils.query_db(
        db,
        """
        SELECT hr.*
        FROM http_requests as hr
        JOIN site_visits sv ON sv.visit_id = hr.visit_id and sv.browser_id = hr.browser_id
        WHERE sv.site_rank = 1""",
    )
    observed_records = set()
    for row in rows:
        # HACK: favicon caching is unpredictable, don't bother checking it
        if row["url"].split("?")[0].endswith("favicon.ico"):
            continue
        observed_records.add(
            (
                row["url"].split("?")[0],
                row["top_level_url"],
                row["triggering_origin"],
                row["loading_origin"],
                row["loading_href"],
                row["is_XHR"],
                row["is_third_party_channel"],
                row["is_third_party_to_top_window"],
                row["resource_type"],
            )
        )
        request_id_to_url[row["request_id"]] = row["url"]
    assert observed_records == HTTP_CACHED_REQUESTS

    # HTTP Responses
    rows = db_utils.query_db(
        db,
        """
         SELECT hp.*
         FROM http_responses as hp
         JOIN site_visits sv ON sv.visit_id = hp.visit_id and sv.browser_id = hp.browser_id
         WHERE sv.site_rank = 1""",
    )
    observed_records = set()
    for row in rows:
        # HACK: favicon caching is unpredictable, don't bother checking it
        if row["url"].split("?")[0].endswith("favicon.ico"):
            continue
        observed_records.add(
            (
                row["url"].split("?")[0],
                # TODO: referrer isn't available yet in the
                # webext instrumentation | row['referrer'],
                row["is_cached"],
            )
        )
        assert row["request_id"] in request_id_to_url
        assert request_id_to_url[row["request_id"]] == row["url"]
    assert HTTP_CACHED_RESPONSES == observed_records

    # HTTP Redirects
    rows = db_utils.query_db(
        db,
        """
         SELECT hr.*
         FROM http_redirects as hr
         JOIN site_visits sv ON sv.visit_id = hr.visit_id and sv.browser_id = hr.browser_id
         WHERE sv.site_rank = 1""",
    )
    observed_records = set()
    for row in rows:
        # TODO: new_request_id isn't supported yet
        # src = request_id_to_url[row['old_request_id']].split('?')[0]
        # dst = request_id_to_url[row['new_request_id']].split('?')[0]
        src = row["old_request_url"].split("?")[0]
        dst = row["new_request_url"].split("?")[0]
        observed_records.add((src, dst))
    assert HTTP_CACHED_REDIRECTS == observed_records


class FilenamesIntoFormCommand(BaseCommand):
    def __init__(self, img_file_path: str, css_file_path: str) -> None:
        self.img_file_path = img_file_path
        self.css_file_path = css_file_path

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        img_file_upload_element = webdriver.find_element_by_id("upload-img")
        css_file_upload_element = webdriver.find_element_by_id("upload-css")
        img_file_upload_element.send_keys(self.img_file_path)
        css_file_upload_element.send_keys(self.css_file_path)
        sleep(5)  # wait for the form submission (3 sec after onload)
