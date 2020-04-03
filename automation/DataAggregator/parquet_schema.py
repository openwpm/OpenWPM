import pyarrow as pa

PQ_SCHEMAS = dict()

# site_visits
fields = [
    pa.field('visit_id', pa.int64(), nullable=False),
    pa.field('crawl_id', pa.uint32(), nullable=False),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('site_url', pa.string(), nullable=False),
    pa.field('site_rank', pa.uint32())
]
PQ_SCHEMAS['site_visits'] = pa.schema(fields)

# flash_cookies
fields = [
    pa.field('crawl_id', pa.uint32(), nullable=False),
    pa.field('visit_id', pa.int64(), nullable=False),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('domain', pa.string()),
    pa.field('filename', pa.string()),
    pa.field('local_path', pa.string()),
    pa.field('key', pa.string()),
    pa.field('content', pa.string())
]
PQ_SCHEMAS['flash_cookies'] = pa.schema(fields)

# crawl_history
fields = [
    pa.field('crawl_id', pa.uint32(), nullable=False),
    pa.field('visit_id', pa.int64(), nullable=False),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('command', pa.string()),
    pa.field('arguments', pa.string()),
    pa.field('retry_number', pa.int8()),
    pa.field('command_status', pa.string()),
    pa.field('error', pa.string()),
    pa.field('traceback', pa.string())
]
PQ_SCHEMAS['crawl_history'] = pa.schema(fields)

# http_requests
fields = [
    pa.field('incognito', pa.int32()),
    pa.field('crawl_id', pa.uint32()),
    pa.field('visit_id', pa.int64()),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('extension_session_uuid', pa.string()),
    pa.field('event_ordinal', pa.int64()),
    pa.field('window_id', pa.int64()),
    pa.field('tab_id', pa.int64()),
    pa.field('frame_id', pa.int64()),
    pa.field('url', pa.string(), nullable=False),
    pa.field('top_level_url', pa.string()),
    pa.field('parent_frame_id', pa.int64()),
    pa.field('frame_ancestors', pa.string()),
    pa.field('method', pa.string(), nullable=False),
    pa.field('referrer', pa.string(), nullable=False),
    pa.field('headers', pa.string(), nullable=False),
    pa.field('request_id', pa.string(), nullable=False),
    pa.field('is_XHR', pa.bool_()),
    pa.field('is_frame_load', pa.bool_()),
    pa.field('is_full_page', pa.bool_()),
    pa.field('is_third_party_channel', pa.bool_()),
    pa.field('is_third_party_to_top_window', pa.bool_()),
    pa.field('triggering_origin', pa.string()),
    pa.field('loading_origin', pa.string()),
    pa.field('loading_href', pa.string()),
    pa.field('req_call_stack', pa.string()),
    pa.field('resource_type', pa.string(), nullable=False),
    pa.field('post_body', pa.string()),
    pa.field('post_body_raw', pa.string()),
    pa.field('time_stamp', pa.string(), nullable=False),
]
PQ_SCHEMAS['http_requests'] = pa.schema(fields)

# http_responses
fields = [
    pa.field('incognito', pa.int32()),
    pa.field('crawl_id', pa.uint32()),
    pa.field('visit_id', pa.int64()),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('extension_session_uuid', pa.string()),
    pa.field('event_ordinal', pa.int64()),
    pa.field('window_id', pa.int64()),
    pa.field('tab_id', pa.int64()),
    pa.field('frame_id', pa.int64()),
    pa.field('url', pa.string(), nullable=False),
    pa.field('method', pa.string(), nullable=False),
    pa.field('response_status', pa.int64()),
    pa.field('response_status_text', pa.string(), nullable=False),
    pa.field('is_cached', pa.bool_(), nullable=False),
    pa.field('headers', pa.string(), nullable=False),
    pa.field('request_id', pa.string(), nullable=False),
    pa.field('location', pa.string(), nullable=False),
    pa.field('time_stamp', pa.string(), nullable=False),
    pa.field('content_hash', pa.string())
]
PQ_SCHEMAS['http_responses'] = pa.schema(fields)

# http_redirects
fields = [
    pa.field('incognito', pa.int32()),
    pa.field('crawl_id', pa.uint32()),
    pa.field('visit_id', pa.int64()),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('old_request_url', pa.string()),
    pa.field('old_request_id', pa.string()),
    pa.field('new_request_url', pa.string()),
    pa.field('new_request_id', pa.string()),
    pa.field('extension_session_uuid', pa.string()),
    pa.field('event_ordinal', pa.int64()),
    pa.field('window_id', pa.int64()),
    pa.field('tab_id', pa.int64()),
    pa.field('frame_id', pa.int64()),
    pa.field('response_status', pa.int64()),
    pa.field('response_status_text', pa.string(), nullable=False),
    pa.field('time_stamp', pa.string(), nullable=False)
]
PQ_SCHEMAS['http_redirects'] = pa.schema(fields)

# javascript
fields = [
    pa.field('incognito', pa.int32()),
    pa.field('crawl_id', pa.uint32()),
    pa.field('visit_id', pa.int64()),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('extension_session_uuid', pa.string()),
    pa.field('event_ordinal', pa.int64()),
    pa.field('page_scoped_event_ordinal', pa.int64()),
    pa.field('window_id', pa.int64()),
    pa.field('tab_id', pa.int64()),
    pa.field('frame_id', pa.int64()),
    pa.field('script_url', pa.string()),
    pa.field('script_line', pa.string()),
    pa.field('script_col', pa.string()),
    pa.field('func_name', pa.string()),
    pa.field('script_loc_eval', pa.string()),
    pa.field('document_url', pa.string()),
    pa.field('top_level_url', pa.string()),
    pa.field('call_stack', pa.string()),
    pa.field('symbol', pa.string()),
    pa.field('operation', pa.string()),
    pa.field('value', pa.string()),
    pa.field('arguments', pa.string()),
    pa.field('time_stamp', pa.string(), nullable=False)
]
PQ_SCHEMAS['javascript'] = pa.schema(fields)

# javascript_cookies
fields = [
    pa.field('crawl_id', pa.uint32()),
    pa.field('visit_id', pa.int64()),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('extension_session_uuid', pa.string()),
    pa.field('event_ordinal', pa.int64()),
    pa.field('record_type', pa.string()),
    pa.field('change_cause', pa.string()),
    pa.field('expiry', pa.string()),
    pa.field('is_http_only', pa.bool_()),
    pa.field('is_host_only', pa.bool_()),
    pa.field('is_session', pa.bool_()),
    pa.field('host', pa.string()),
    pa.field('is_secure', pa.bool_()),
    pa.field('name', pa.string()),
    pa.field('path', pa.string()),
    pa.field('value', pa.string()),
    pa.field('same_site', pa.string()),
    pa.field('first_party_domain', pa.string()),
    pa.field('store_id', pa.string()),
    pa.field('time_stamp', pa.string())
]
PQ_SCHEMAS['javascript_cookies'] = pa.schema(fields)

# navigations
fields = [
    pa.field('incognito', pa.int32()),
    pa.field('crawl_id', pa.uint32()),
    pa.field('visit_id', pa.int64()),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('extension_session_uuid', pa.string()),
    pa.field('process_id', pa.int64()),
    pa.field('window_id', pa.int64()),
    pa.field('tab_id', pa.int64()),
    pa.field('tab_opener_tab_id', pa.int64()),
    pa.field('frame_id', pa.int64()),
    pa.field('parent_frame_id', pa.int64()),
    pa.field('window_width', pa.int64()),
    pa.field('window_height', pa.int64()),
    pa.field('window_type', pa.string()),
    pa.field('tab_width', pa.int64()),
    pa.field('tab_height', pa.int64()),
    pa.field('tab_cookie_store_id', pa.string()),
    pa.field('uuid', pa.string()),
    pa.field('url', pa.string()),
    pa.field('transition_qualifiers', pa.string()),
    pa.field('transition_type', pa.string()),
    pa.field('before_navigate_event_ordinal', pa.int64()),
    pa.field('before_navigate_time_stamp', pa.string()),
    pa.field('committed_event_ordinal', pa.int64()),
    pa.field('time_stamp', pa.string())
]
PQ_SCHEMAS['navigations'] = pa.schema(fields)

fields = [
    pa.field('visit_id', pa.int64(), nullable=False),
    pa.field('request_id', pa.int64(), nullable=False),
    pa.field('crawl_id', pa.uint32(), nullable=False),
    pa.field('instance_id', pa.uint32(), nullable=False),
    pa.field('call_stack', pa.string())
]
PQ_SCHEMAS['callstacks'] = pa.schema(fields)
