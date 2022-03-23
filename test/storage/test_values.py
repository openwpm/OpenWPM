""" This file should contain one entry for every table
so that we can test storing and loading for every single entry
for every structured storage provider.

IF YOU CHANGE THIS FILE ALSO CHANGE schema.sql and parquet_schema.py
AND Schema-Documentation.md
"""

import random
import string
from typing import Any, Dict, Set, Tuple

from openwpm.storage.storage_providers import TableName
from openwpm.types import VisitId

dt_test_values = Tuple[Dict[TableName, Dict[str, Any]], Set[VisitId]]


def generate_test_values() -> dt_test_values:
    test_values: Dict[TableName, Dict[str, Any]] = dict()

    def random_word(length):
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(length))

    # task
    fields = {
        "task_id": random.randint(0, 2**63 - 1),
        "manager_params": random_word(12),
        "openwpm_version": random_word(12),
        "browser_version": random_word(12),
    }
    test_values[TableName("task")] = fields
    # crawl
    fields = {
        "browser_id": random.randint(0, 2**31 - 1),
        "task_id": random.randint(0, 2**63 - 1),
        "browser_params": random_word(12),
    }
    test_values[TableName("crawl")] = fields
    # site_visits
    fields = {
        "visit_id": random.randint(0, 2**63 - 1),
        "browser_id": random.randint(0, 2**31 - 1),
        "site_url": random_word(12),
        "site_rank": random.randint(0, 2**31 - 1),
    }
    test_values[TableName("site_visits")] = fields
    # crawl_history
    fields = {
        "browser_id": random.randint(0, 2**31 - 1),
        "visit_id": random.randint(0, 2**63 - 1),
        "command": random_word(12),
        "arguments": random_word(12),
        "retry_number": random.randint(0, 2**7 - 1),
        "command_status": random_word(12),
        "error": random_word(12),
        "traceback": random_word(12),
        "duration": random.randint(0, 2**63 - 1),
    }
    test_values[TableName("crawl_history")] = fields
    # http_requests
    fields = {
        "incognito": random.randint(0, 2**31 - 1),
        "browser_id": random.randint(0, 2**31 - 1),
        "visit_id": random.randint(0, 2**63 - 1),
        "extension_session_uuid": random_word(12),
        "event_ordinal": random.randint(0, 2**63 - 1),
        "window_id": random.randint(0, 2**63 - 1),
        "tab_id": random.randint(0, 2**63 - 1),
        "frame_id": random.randint(0, 2**63 - 1),
        "url": random_word(12),
        "top_level_url": random_word(12),
        "parent_frame_id": random.randint(0, 2**63 - 1),
        "frame_ancestors": random_word(12),
        "method": random_word(12),
        "referrer": random_word(12),
        "headers": random_word(12),
        "request_id": random.randint(0, 2**63 - 1),
        "is_XHR": random.choice([True, False]),
        "is_third_party_channel": random.choice([True, False]),
        "is_third_party_to_top_window": random.choice([True, False]),
        "triggering_origin": random_word(12),
        "loading_origin": random_word(12),
        "loading_href": random_word(12),
        "req_call_stack": random_word(12),
        "resource_type": random_word(12),
        "post_body": random_word(12),
        "post_body_raw": random_word(12),
        "time_stamp": random_word(12),
    }
    test_values[TableName("http_requests")] = fields
    # http_responses
    fields = {
        "incognito": random.randint(0, 2**31 - 1),
        "browser_id": random.randint(0, 2**31 - 1),
        "visit_id": random.randint(0, 2**63 - 1),
        "extension_session_uuid": random_word(12),
        "event_ordinal": random.randint(0, 2**63 - 1),
        "window_id": random.randint(0, 2**63 - 1),
        "tab_id": random.randint(0, 2**63 - 1),
        "frame_id": random.randint(0, 2**63 - 1),
        "url": random_word(12),
        "method": random_word(12),
        "response_status": random.randint(0, 2**63 - 1),
        "response_status_text": random_word(12),
        "is_cached": random.choice([True, False]),
        "headers": random_word(12),
        "request_id": random.randint(0, 2**63 - 1),
        "location": random_word(12),
        "time_stamp": random_word(12),
        "content_hash": random_word(12),
    }
    test_values[TableName("http_responses")] = fields
    # http_redirects
    fields = {
        "incognito": random.randint(0, 2**31 - 1),
        "browser_id": random.randint(0, 2**31 - 1),
        "visit_id": random.randint(0, 2**63 - 1),
        "old_request_url": random_word(12),
        "old_request_id": random_word(12),
        "new_request_url": random_word(12),
        "new_request_id": random_word(12),
        "extension_session_uuid": random_word(12),
        "event_ordinal": random.randint(0, 2**63 - 1),
        "window_id": random.randint(0, 2**63 - 1),
        "tab_id": random.randint(0, 2**63 - 1),
        "frame_id": random.randint(0, 2**63 - 1),
        "response_status": random.randint(0, 2**63 - 1),
        "response_status_text": random_word(12),
        "headers": random_word(12),
        "time_stamp": random_word(12),
    }
    test_values[TableName("http_redirects")] = fields
    # javascript
    fields = {
        "incognito": random.randint(0, 2**31 - 1),
        "browser_id": random.randint(0, 2**31 - 1),
        "visit_id": random.randint(0, 2**63 - 1),
        "extension_session_uuid": random_word(12),
        "event_ordinal": random.randint(0, 2**63 - 1),
        "page_scoped_event_ordinal": random.randint(0, 2**63 - 1),
        "window_id": random.randint(0, 2**63 - 1),
        "tab_id": random.randint(0, 2**63 - 1),
        "frame_id": random.randint(0, 2**63 - 1),
        "script_url": random_word(12),
        "script_line": random_word(12),
        "script_col": random_word(12),
        "func_name": random_word(12),
        "script_loc_eval": random_word(12),
        "document_url": random_word(12),
        "top_level_url": random_word(12),
        "call_stack": random_word(12),
        "symbol": random_word(12),
        "operation": random_word(12),
        "value": random_word(12),
        "arguments": random_word(12),
        "time_stamp": random_word(12),
    }
    test_values[TableName("javascript")] = fields
    # javascript_cookies
    fields = {
        "browser_id": random.randint(0, 2**31 - 1),
        "visit_id": random.randint(0, 2**63 - 1),
        "extension_session_uuid": random_word(12),
        "event_ordinal": random.randint(0, 2**63 - 1),
        "record_type": random_word(12),
        "change_cause": random_word(12),
        "expiry": random_word(12),
        "is_http_only": random.choice([True, False]),
        "is_host_only": random.choice([True, False]),
        "is_session": random.choice([True, False]),
        "host": random_word(12),
        "is_secure": random.choice([True, False]),
        "name": random_word(12),
        "path": random_word(12),
        "value": random_word(12),
        "same_site": random_word(12),
        "first_party_domain": random_word(12),
        "store_id": random_word(12),
        "time_stamp": random_word(12),
    }
    test_values[TableName("javascript_cookies")] = fields
    # navigations
    fields = {
        "incognito": random.randint(0, 2**31 - 1),
        "browser_id": random.randint(0, 2**31 - 1),
        "visit_id": random.randint(0, 2**63 - 1),
        "extension_session_uuid": random_word(12),
        "process_id": random.randint(0, 2**63 - 1),
        "window_id": random.randint(0, 2**63 - 1),
        "tab_id": random.randint(0, 2**63 - 1),
        "tab_opener_tab_id": random.randint(0, 2**63 - 1),
        "frame_id": random.randint(0, 2**63 - 1),
        "parent_frame_id": random.randint(0, 2**63 - 1),
        "window_width": random.randint(0, 2**63 - 1),
        "window_height": random.randint(0, 2**63 - 1),
        "window_type": random_word(12),
        "tab_width": random.randint(0, 2**63 - 1),
        "tab_height": random.randint(0, 2**63 - 1),
        "tab_cookie_store_id": random_word(12),
        "uuid": random_word(12),
        "url": random_word(12),
        "transition_qualifiers": random_word(12),
        "transition_type": random_word(12),
        "before_navigate_event_ordinal": random.randint(0, 2**63 - 1),
        "before_navigate_time_stamp": random_word(12),
        "committed_event_ordinal": random.randint(0, 2**63 - 1),
        "time_stamp": random_word(12),
    }
    test_values[TableName("navigations")] = fields
    # callstacks
    fields = {
        "visit_id": random.randint(0, 2**63 - 1),
        "request_id": random.randint(0, 2**63 - 1),
        "browser_id": random.randint(0, 2**31 - 1),
        "call_stack": random_word(12),
    }
    test_values[TableName("callstacks")] = fields
    # incomplete_visits
    fields = {
        "visit_id": random.randint(0, 2**63 - 1),
    }
    test_values[TableName("incomplete_visits")] = fields
    # dns_responses
    fields = {
        "request_id": random.randint(0, 2**63 - 1),
        "browser_id": random.randint(0, 2**31 - 1),
        "visit_id": random.randint(0, 2**63 - 1),
        "hostname": random_word(12),
        "addresses": random_word(12),
        "canonical_name": random_word(12),
        "is_TRR": random.choice([True, False]),
        "time_stamp": random_word(12),
    }
    test_values[TableName("dns_responses")] = fields
    visit_id_set = set(
        d["visit_id"] for d in filter(lambda d: "visit_id" in d, test_values.values())
    )
    return test_values, visit_id_set
