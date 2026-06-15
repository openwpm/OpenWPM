#!/usr/bin/python
# -*- coding: utf-8 -*-

import base64
import json
import os
from hashlib import sha256
from pathlib import Path
from sqlite3 import Row
from time import sleep
from typing import List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import pytest

from openwpm import command_sequence, task_manager
from openwpm.command_sequence import CommandSequence
from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.leveldb import LevelDbProvider
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.utilities import db_utils

from .conftest import FullConfig, HttpParams, TaskManagerCreator
from .openwpmtest import OpenWPMTest
from .utilities import ServerUrls


# Data for test_page_visit
# format: (
# request_url,
# top_level_url,
# triggering_origin,
# loading_origin,
# loading_href,
# is_XHR, is_tp_content, is_tp_window,
#   resource_type
def _http_requests(server: ServerUrls) -> set[tuple[Union[str, None, int], ...]]:
    return {
        (
            f"{server.base}/http_test_page.html",
            f"{server.base}/http_test_page.html",
            "undefined",
            "undefined",
            "undefined",
            0,
            None,
            None,
            "main_frame",
        ),
        (
            f"{server.base}/shared/test_favicon.ico",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base}/shared/test_image_2.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page_2.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base}/shared/test_script_2.js",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page_2.html",
            0,
            None,
            None,
            "script",
        ),
        (
            f"{server.base}/shared/test_script.js",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "script",
        ),
        (
            f"{server.base}/shared/test_image.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base}/http_test_page_2.html",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "sub_frame",
        ),
        (
            f"{server.base}/shared/test_style.css",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "stylesheet",
        ),
        (
            f"{server.base_nopath}/404.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page_2.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/frame1.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page_2.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/frame2.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page_2.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req1.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req2.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req3.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base}/shared/test_image_2.png",
            f"{server.base}/http_test_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_test_page.html",
            0,
            None,
            None,
            "image",
        ),
    }


# format: (request_url, referrer, location)
# TODO: webext instrumentation doesn't support referrer yet
def _http_responses(server: ServerUrls) -> set[tuple[str, str]]:
    return {
        (
            f"{server.base}/http_test_page.html",
            # u'',
            "",
        ),
        (
            f"{server.base}/shared/test_favicon.ico",
            # u'',
            "",
        ),
        (
            f"{server.base}/shared/test_style.css",
            # u'http://localhost:8000/test_pages/http_test_page.html',
            "",
        ),
        (
            f"{server.base}/shared/test_script.js",
            # u'http://localhost:8000/test_pages/http_test_page.html',
            "",
        ),
        (
            f"{server.base}/shared/test_image.png",
            # u'http://localhost:8000/test_pages/http_test_page.html',
            "",
        ),
        (
            f"{server.base}/http_test_page_2.html",
            # u'http://localhost:8000/test_pages/http_test_page.html',
            "",
        ),
        (
            f"{server.base}/shared/test_image_2.png",
            # u'http://localhost:8000/test_pages/http_test_page_2.html',
            "",
        ),
        (
            f"{server.base}/shared/test_script_2.js",
            # u'http://localhost:8000/test_pages/http_test_page_2.html',
            "",
        ),
        (
            f"{server.base_nopath}/404.png",
            # u'http://localhost:8000/test_pages/http_test_page_2.html',
            "",
        ),
        (
            f"{server.base}/shared/test_image_2.png",
            # u'http://localhost:8000/test_pages/http_test_page.html',
            "",
        ),
    }


# format: (source_url, destination_url, location header)
def _http_redirects(server: ServerUrls) -> set[tuple[str, str, str | None]]:
    return {
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req1.png",
            f"{server.base_nopath}/MAGIC_REDIRECT/req2.png",
            "req2.png?dst=req3.png&dst=/test_pages/shared/test_image_2.png",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req2.png",
            f"{server.base_nopath}/MAGIC_REDIRECT/req3.png",
            "req3.png?dst=/test_pages/shared/test_image_2.png",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req3.png",
            f"{server.base}/shared/test_image_2.png",
            "/test_pages/shared/test_image_2.png",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/frame1.png",
            f"{server.base_nopath}/MAGIC_REDIRECT/frame2.png",
            "frame2.png?dst=/404.png",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/frame2.png",
            f"{server.base_nopath}/404.png",
            "/404.png",
        ),
    }


# Data for test_cache_hits_recorded.
#
# On the second visit (site_rank == 1) the browser opens a fresh tab that
# shares the same Firefox profile and HTTP cache as the first visit. Most
# resources are re-requested and fire a webRequest event, but Firefox's
# cross-tab in-memory image cache can satisfy an <img> (or a stylesheet)
# directly from already-decoded bytes, before the request ever reaches the
# HTTP channel. When that happens no webRequest event fires and the row is
# simply absent. Firefox offers no documented, stable pref that forces a
# request for every memory-cache-served resource, so this is genuine,
# uncontrollable nondeterminism (see Bug 634073 and GitHub issue #1162).
#
# We therefore split the expectations into two parts:
#   * a deterministic floor that must hold on every run, asserted exactly, and
#   * an explicit tolerated range for the cache-dependent image/css resources.
#
# Separately, every recorded row must carry a visit_id that belongs to the
# visit it was generated by. The instrument stamps records from a mutable
# module-global visit_id and async handlers may await before persisting, so a
# record can be written under a stale visit_id after the active visit changed
# (GitHub issue #1162). The test pins each row's visit_id to the test's actual
# visits and requires the top-level document row to appear exactly once per
# visit, so a drifted or duplicated row is caught rather than masked.


# Request URLs that must always be recorded on the second visit, regardless of
# cache state. These are the documents, the scripts, the 404 image, and every
# hop of the two MAGIC_REDIRECT chains. Redirect hops and the 404 are never
# served from the image cache, so they re-fire deterministically.
def _mandatory_second_visit_request_urls(server: ServerUrls) -> set[str]:
    return {
        f"{server.base}/http_test_page.html",
        f"{server.base}/http_test_page_2.html",
        f"{server.base}/shared/test_script.js",
        f"{server.base}/shared/test_script_2.js",
        f"{server.base_nopath}/404.png",
        f"{server.base_nopath}/MAGIC_REDIRECT/frame1.png",
        f"{server.base_nopath}/MAGIC_REDIRECT/frame2.png",
        f"{server.base_nopath}/MAGIC_REDIRECT/req1.png",
        f"{server.base_nopath}/MAGIC_REDIRECT/req2.png",
        f"{server.base_nopath}/MAGIC_REDIRECT/req3.png",
    }


# Resources that may or may not fire a request on the second visit because
# Firefox's cross-tab in-memory image cache can serve them silently. The floor
# is zero for each, because the cache may swallow every reference and produce
# no event at all. The ceiling is the most requests the test pages can drive
# for that resource; a higher count would mean a request was recorded that the
# pages never make, which is a real regression.
#
# test_image.png is referenced once on page 1 and once on page 2 (max 2).
# test_image_2.png is referenced once on page 2 directly and once as the final
#   destination of page 1's req1->req2->req3 redirect chain (max 2).
# test_style.css is referenced once, in page 1's <head>, but Firefox may issue
#   a second request to revalidate it against the cache on the new tab (max 2).
def _cache_dependent_request_url_ranges(
    server: ServerUrls,
) -> dict[str, tuple[int, int]]:
    return {
        f"{server.base}/shared/test_image.png": (0, 2),
        f"{server.base}/shared/test_image_2.png": (0, 2),
        f"{server.base}/shared/test_style.css": (0, 2),
    }


# At least one response on the second visit must be served from cache. This
# proves the instrument can still observe and label cache hits, without pinning
# which resources or how many. The documents and scripts reliably revalidate
# out of the HTTP cache, so this floor is comfortably met in practice while
# remaining robust to the image-cache nondeterminism above.
MIN_CACHED_RESPONSES_SECOND_VISIT: int = 1


# The 404 image is never cacheable, so its response must always be recorded
# with is_cached == 0 on the second visit. This is a deterministic anchor.
def _uncacheable_response_url(server: ServerUrls) -> str:
    return f"{server.base_nopath}/404.png"


# The top-level document. Exactly one main_frame request for this URL must be
# recorded per visit; a second one is the extra-document-row signature of the
# visit_id drift bug (GitHub issue #1162).
def _document_url(server: ServerUrls) -> str:
    return f"{server.base}/http_test_page.html"


# format: (source_url, destination_url)
def _http_cached_redirects(server: ServerUrls) -> set[tuple[str, str]]:
    return {
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/frame1.png",
            f"{server.base_nopath}/MAGIC_REDIRECT/frame2.png",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/frame2.png",
            f"{server.base_nopath}/404.png",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req1.png",
            f"{server.base_nopath}/MAGIC_REDIRECT/req2.png",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req2.png",
            f"{server.base_nopath}/MAGIC_REDIRECT/req3.png",
        ),
        (
            f"{server.base_nopath}/MAGIC_REDIRECT/req3.png",
            f"{server.base}/shared/test_image_2.png",
        ),
    }


# Test URL attribution for worker script requests
def _http_worker_script_requests(
    server: ServerUrls,
) -> set[tuple[Union[str, None, int], ...]]:
    return {
        (
            f"{server.base}/http_worker_page.html",
            f"{server.base}/http_worker_page.html",
            "undefined",
            "undefined",
            "undefined",
            0,
            None,
            None,
            "main_frame",
        ),
        (
            f"{server.base}/shared/test_favicon.ico",
            f"{server.base}/http_worker_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_worker_page.html",
            0,
            None,
            None,
            "image",
        ),
        (
            f"{server.base}/shared/worker.js",
            f"{server.base}/http_worker_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_worker_page.html",
            0,
            None,
            None,
            "script",
        ),
        (
            f"{server.base}/shared/test_image.png",
            f"{server.base}/http_worker_page.html",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/http_worker_page.html",
            1,
            None,
            None,
            "xmlhttprequest",
        ),
        (
            f"{server.base}/shared/test_image.png",
            f"{server.base}/shared/worker.js",
            f"{server.base_nopath}",
            f"{server.base_nopath}",
            f"{server.base}/shared/worker.js",
            1,
            None,
            None,
            "xmlhttprequest",
        ),
    }


def _http_service_worker_requests(
    server: ServerUrls,
) -> set[tuple[Union[str, None, int], ...]]:
    """Build expected service worker requests (needs dynamic BASE_TEST_URL)."""
    base = server.base
    origin = server.base_nopath
    page = f"{base}/http_service_worker_page.html"
    sw = f"{base}/shared/service_worker.js"
    return {
        (
            page,
            page,
            "undefined",
            "undefined",
            "undefined",
            0,
            None,
            None,
            "main_frame",
        ),
        (
            f"{base}/shared/test_favicon.ico",
            page,
            origin,
            origin,
            page,
            0,
            None,
            None,
            "image",
        ),
        (sw, page, origin, origin, page, 0, None, None, "script"),
        (
            f"{base}/shared/test_image.png",
            page,
            origin,
            origin,
            page,
            1,
            None,
            None,
            "xmlhttprequest",
        ),
        (
            f"{base}/shared/test_image_2.png",
            sw,
            origin,
            origin,
            sw,
            1,
            None,
            None,
            "xmlhttprequest",
        ),
    }


BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class TestHTTPInstrument(OpenWPMTest):
    def get_config(self, data_dir: Optional[Path]) -> FullConfig:
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0].http_instrument = True
        return manager_params, browser_params

    def test_worker_script_requests(self):
        """Check correct URL attribution for requests made by worker script"""
        test_url = self.server.base + "/http_worker_page.html"
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

        assert _http_worker_script_requests(self.server) == observed_records

    def test_service_worker_requests(self):
        """Check correct URL attribution for requests made by service worker"""
        test_url = self.server.base + "/http_service_worker_page.html"
        # sleep_after gives the webRequest pipeline (extension → socket → StorageController)
        # time to flush the SW's fetch before manager.close() shuts down the browser.
        # The SW uses event.waitUntil() so the fetch itself completes, but the async
        # instrumentation path still needs a moment. The storage controller drains all
        # pending tasks on shutdown, so any request captured before close() will land.
        db = self.visit(test_url, sleep_after=5)

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

        assert _http_service_worker_requests(self.server) == observed_records


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
        test_url = self.server.base + "/post_file_upload.html"
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
def test_page_visit(
    task_manager_creator: TaskManagerCreator,
    http_params: HttpParams,
    delayed: bool,
    server: ServerUrls,
) -> None:
    test_url = server.base + "/http_test_page.html"
    manager_params, browser_params = http_params()
    if delayed:
        for browser_param in browser_params:
            browser_param.custom_params["pre_instrumentation_code"] = """
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
    observed_requests = set()
    for row in rows:
        assert isinstance(row, Row)
        observed_requests.add(
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
    assert _http_requests(server) == observed_requests

    # HTTP Responses
    rows = db_utils.query_db(db, "SELECT * FROM http_responses")
    observed_responses: Set[Tuple[str, str]] = set()
    for row in rows:
        assert isinstance(row, Row)
        observed_responses.add(
            (
                row["url"].split("?")[0],
                # TODO: webext-instrumentation doesn't support referrer
                # yet | row['referrer'],
                row["location"],
            )
        )
        assert row["request_id"] in request_id_to_url
        assert request_id_to_url[row["request_id"]] == row["url"]
    assert _http_responses(server) == observed_responses

    # HTTP Redirects
    rows = db_utils.query_db(db, "SELECT * FROM http_redirects")
    observed_redirects: set[tuple[str, str, str | None]] = set()
    for row in rows:
        assert isinstance(row, Row)
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
        observed_redirects.add((src, dst, location))
    assert _http_redirects(server) == observed_redirects


def test_javascript_saving(
    http_params: HttpParams, xpi: None, server: ServerUrls
) -> None:
    """check that javascript content is saved and hashed correctly"""
    test_url = server.base + "/http_test_page.html"
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
    for chash_raw, content in db_utils.get_content(ldb_path):
        assert isinstance(chash_raw, bytes)
        assert isinstance(content, bytes)
        chash = chash_raw.decode("ascii").lower()
        pyhash = sha256(content).hexdigest().lower()
        assert pyhash == chash  # Verify expected key (sha256 of content)
        assert chash in expected_hashes
        expected_hashes.remove(chash)
    assert len(expected_hashes) == 0  # All expected hashes have been seen


def test_document_saving(
    http_params: HttpParams, xpi: None, server: ServerUrls
) -> None:
    """check that document content is saved and hashed correctly"""
    test_url = server.base + "/http_test_page.html"
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
    for chash_raw, content in db_utils.get_content(ldb_path):
        assert isinstance(chash_raw, bytes)
        assert isinstance(content, bytes)
        chash = chash_raw.decode("ascii").lower()
        pyhash = sha256(content).hexdigest().lower()
        assert pyhash == chash  # Verify expected key (sha256 of content)
        assert chash in expected_hashes
        expected_hashes.remove(chash)
    assert len(expected_hashes) == 0  # All expected hashes have been seen


def test_content_saving(http_params: HttpParams, xpi: None, server: ServerUrls) -> None:
    """check that content is saved and hashed correctly"""
    test_url = server.base + "/http_test_page.html"
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
    disk_content: dict[str, bytes] = dict()
    for row in rows:
        assert not isinstance(row, tuple)
        if "MAGIC_REDIRECT" in row["url"] or "404" in row["url"]:
            continue
        path = urlparse(row["url"]).path
        with open(os.path.join(BASE_PATH, path[1:]), "rb") as f:
            content = f.read()
        chash = sha256(content).hexdigest()
        assert chash == row["content_hash"]
        disk_content[chash] = content

    ldb_content: dict[str, bytes] = dict()
    for chash_raw, content_raw in db_utils.get_content(ldb_path):
        assert isinstance(chash_raw, bytes)
        assert isinstance(content_raw, bytes)
        ldb_content[chash_raw.decode("ascii")] = content_raw

    for k, v in disk_content.items():
        assert v == ldb_content[k]


def test_cache_hits_recorded(
    http_params: HttpParams,
    task_manager_creator: TaskManagerCreator,
    server: ServerUrls,
) -> None:
    """Verify the HTTP instrument records requests, responses and redirects on
    a revisit, including cache hits, with correct visit_id attribution.

    The test visits the same page twice with one browser. The second visit
    reuses the profile and HTTP cache from the first, so resources may be
    served from cache. Cached images do not always trigger a webRequest event
    (see Bug 634073: https://bugzilla.mozilla.org/show_bug.cgi?id=634073), and
    Firefox's cross-tab in-memory image cache can serve an image or stylesheet
    silently with no event at all. That makes the exact set of second-visit
    requests nondeterministic for those resources.

    The design is deliberately strict on what is determinable and tolerant on
    what is inherently flaky:

    * Strict (visit_id correctness, GitHub issue #1162): every recorded request
      and response row carries a visit_id that belongs to one of this test's two
      actual visits, and the top-level document row appears exactly once per
      visit. A record persisted under a stale visit_id, or a duplicated document
      row, is caught here rather than masked.
    * Tolerant (Firefox heuristic cache status): instead of pinning the exact
      set of second-visit requests, we assert a deterministic floor that must
      always hold and bound the genuinely cache-dependent resources to an
      explicit tolerated range. The redirect chain re-walks on every visit and
      is asserted exactly.
    """
    test_url = server.base + "/http_test_page.html"
    manager_params, browser_params = http_params()
    # ensuring that we only spawn one browser
    manager_params.num_browsers = 1
    manager, db = task_manager_creator((manager_params, [browser_params[0]]))
    for i in range(2):
        cs = CommandSequence(test_url, site_rank=i)
        cs.get(sleep=5)
        manager.execute_command_sequence(cs)

    manager.close()

    # The test's actual visits: exactly one per site_rank (0 = first visit,
    # 1 = second visit). visit_id_for_rank is the ground truth every recorded
    # row must agree with.
    visit_rows = db_utils.query_db(
        db,
        "SELECT visit_id, site_rank FROM site_visits ORDER BY site_rank",
    )
    visit_id_for_rank: dict[object, object] = {}
    for row in visit_rows:
        assert not isinstance(row, tuple)
        rank = row["site_rank"]
        assert (
            rank not in visit_id_for_rank
        ), f"duplicate site_visits row for rank {rank}"
        visit_id_for_rank[rank] = row["visit_id"]
    assert set(visit_id_for_rank) == {
        0,
        1,
    }, f"expected exactly two visits (ranks 0 and 1), got {set(visit_id_for_rank)}"
    expected_visit_ids = set(visit_id_for_rank.values())
    first_visit_id = visit_id_for_rank[0]
    second_visit_id = visit_id_for_rank[1]
    document_url = _document_url(server)

    def _is_favicon(url: object) -> bool:
        return isinstance(url, str) and url.split("?")[0].endswith("favicon.ico")

    # --- visit_id drift guards (across BOTH visits) -----------------------
    #
    # Every recorded http_requests / http_responses row must be attributed to
    # one of the test's actual visit_ids, and the top-level document row must
    # appear exactly once per visit. A drifted visit_id or an extra document row
    # is the observable signature of GitHub issue #1162; these checks fail loudly
    # rather than letting it slip through.
    for table in ("http_requests", "http_responses"):
        all_rows = db_utils.query_db(
            db,
            f"SELECT visit_id, url FROM {table}",
        )
        unexpected_visit_rows = []
        document_rows_per_visit: dict[object, int] = {}
        for row in all_rows:
            assert not isinstance(row, tuple)
            if _is_favicon(row["url"]):
                continue
            if row["visit_id"] not in expected_visit_ids:
                unexpected_visit_rows.append((row["url"], row["visit_id"]))
            if row["url"].split("?")[0] == document_url:
                document_rows_per_visit[row["visit_id"]] = (
                    document_rows_per_visit.get(row["visit_id"], 0) + 1
                )
        assert not unexpected_visit_rows, (
            f"{table} rows attributed to a visit_id outside the test's actual "
            f"visits {expected_visit_ids} (visit_id drift, issue #1162): "
            f"{unexpected_visit_rows}"
        )
        for visit_id in (first_visit_id, second_visit_id):
            count = document_rows_per_visit.get(visit_id, 0)
            assert count == 1, (
                f"{table}: expected exactly one document row ({document_url}) "
                f"for visit_id {visit_id}, found {count} (extra/missing document "
                f"row is the issue #1162 drift signature)"
            )

    request_id_to_url: dict[object, object] = dict()

    # --- second visit: requests (deterministic floor + tolerated range) ---
    rows = db_utils.query_db(
        db,
        """
        SELECT hr.*
        FROM http_requests as hr
        JOIN site_visits sv ON sv.visit_id = hr.visit_id and sv.browser_id = hr.browser_id
        WHERE sv.site_rank = 1""",
    )
    observed_request_url_counts: dict[str, int] = {}
    for row in rows:
        assert not isinstance(row, tuple)
        # HACK: favicon caching is unpredictable, don't bother checking it
        url = row["url"].split("?")[0]
        if url.endswith("favicon.ico"):
            continue
        observed_request_url_counts[url] = observed_request_url_counts.get(url, 0) + 1
        request_id_to_url[row["request_id"]] = row["url"]
    observed_request_urls = set(observed_request_url_counts)

    # Deterministic floor: every mandatory resource was requested at least once
    # on the second visit. None of these depend on cache state.
    mandatory = _mandatory_second_visit_request_urls(server)
    missing = mandatory - observed_request_urls
    assert not missing, f"mandatory second-visit requests were not recorded: {missing}"

    # Tolerated range: the cache-dependent image/css resources may be served
    # silently from Firefox's cross-tab image cache, so each may appear between
    # its minimum and maximum number of times.
    cache_dependent = _cache_dependent_request_url_ranges(server)
    for url, (min_count, max_count) in cache_dependent.items():
        count = observed_request_url_counts.get(url, 0)
        assert min_count <= count <= max_count, (
            f"cache-dependent request {url} was recorded {count} times, "
            f"outside the tolerated range [{min_count}, {max_count}]"
        )

    # No request URL outside the mandatory set and the tolerated range should
    # appear (apart from the favicon, already skipped). This catches stray or
    # mis-attributed requests.
    allowed_request_urls = mandatory | cache_dependent.keys()
    unexpected = observed_request_urls - allowed_request_urls
    assert (
        not unexpected
    ), f"unexpected second-visit requests were recorded: {unexpected}"

    # --- second visit: responses -----------------------------------------
    rows = db_utils.query_db(
        db,
        """
         SELECT hp.*
         FROM http_responses as hp
         JOIN site_visits sv ON sv.visit_id = hp.visit_id and sv.browser_id = hp.browser_id
         WHERE sv.site_rank = 1""",
    )
    cached_response_count = 0
    saw_uncacheable_response = False
    uncacheable_url = _uncacheable_response_url(server)
    for row in rows:
        assert not isinstance(row, tuple)
        # HACK: favicon caching is unpredictable, don't bother checking it
        url = row["url"].split("?")[0]
        if url.endswith("favicon.ico"):
            continue
        # Every response links back to a recorded request row by request_id,
        # with matching URL. This never depends on cache state.
        assert row["request_id"] in request_id_to_url
        assert request_id_to_url[row["request_id"]] == row["url"]
        if row["is_cached"]:
            cached_response_count += 1
        if url == uncacheable_url:
            saw_uncacheable_response = True
            # The 404 image is never cacheable, so it is always a fresh fetch.
            assert row["is_cached"] == 0, (
                f"{uncacheable_url} must never be served from cache, "
                f"got is_cached={row['is_cached']}"
            )

    # The instrument must still surface cache hits on a revisit.
    assert cached_response_count >= MIN_CACHED_RESPONSES_SECOND_VISIT, (
        f"expected at least {MIN_CACHED_RESPONSES_SECOND_VISIT} cached responses "
        f"on the second visit, got {cached_response_count}"
    )
    # The deterministic uncacheable anchor must be present.
    assert saw_uncacheable_response, (
        f"the uncacheable response {uncacheable_url} was not recorded on the "
        f"second visit"
    )

    # --- second visit: redirects (asserted exactly) ----------------------
    rows = db_utils.query_db(
        db,
        """
         SELECT hr.*
         FROM http_redirects as hr
         JOIN site_visits sv ON sv.visit_id = hr.visit_id and sv.browser_id = hr.browser_id
         WHERE sv.site_rank = 1""",
    )
    observed_redirects: set[tuple[str, str]] = set()
    for row in rows:
        assert not isinstance(row, tuple)
        # TODO: new_request_id isn't supported yet
        # src = request_id_to_url[row['old_request_id']].split('?')[0]
        # dst = request_id_to_url[row['new_request_id']].split('?')[0]
        src = row["old_request_url"].split("?")[0]
        dst = row["new_request_url"].split("?")[0]
        observed_redirects.add((src, dst))
    assert _http_cached_redirects(server) == observed_redirects


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
