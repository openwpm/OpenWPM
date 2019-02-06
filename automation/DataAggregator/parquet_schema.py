import pyarrow as pa

PQ_SCHEMAS = dict()

# site_visits
fields = [
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("site_url", pa.string(), nullable=False),
]
PQ_SCHEMAS["site_visits"] = pa.schema(fields)

# flash_cookies
fields = [
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("domain", pa.string()),
    pa.field("filename", pa.string()),
    pa.field("local_path", pa.string()),
    pa.field("key", pa.string()),
    pa.field("content", pa.string()),
]
PQ_SCHEMAS["flash_cookies"] = pa.schema(fields)

# profile_cookies
fields = [
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("baseDomain", pa.string()),
    pa.field("name", pa.string()),
    pa.field("value", pa.string()),
    pa.field("host", pa.string()),
    pa.field("path", pa.string()),
    pa.field("expiry", pa.int32()),
    pa.field("lastAccessed", pa.int32()),
    pa.field("creationTime", pa.int32()),
    pa.field("isSecure", pa.bool_()),
    pa.field("isHttpOnly", pa.bool_()),
]
PQ_SCHEMAS["profile_cookies"] = pa.schema(fields)

# crawl_history
fields = [
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("command", pa.string()),
    pa.field("arguments", pa.string()),
    pa.field("bool_success", pa.int8()),
]
PQ_SCHEMAS["crawl_history"] = pa.schema(fields)

# http_requests
fields = [
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("url", pa.string(), nullable=False),
    pa.field("top_level_url", pa.string()),
    pa.field("method", pa.string(), nullable=False),
    pa.field("referrer", pa.string(), nullable=False),
    pa.field("headers", pa.string(), nullable=False),
    pa.field("channel_id", pa.string(), nullable=False),
    pa.field("is_XHR", pa.bool_()),
    pa.field("is_frame_load", pa.bool_()),
    pa.field("is_full_page", pa.bool_()),
    pa.field("is_third_party_channel", pa.bool_()),
    pa.field("is_third_party_to_top_window", pa.bool_()),
    pa.field("triggering_origin", pa.string()),
    pa.field("loading_origin", pa.string()),
    pa.field("loading_href", pa.string()),
    pa.field("req_call_stack", pa.string()),
    pa.field("content_policy_type", pa.int16(), nullable=False),
    pa.field("post_body", pa.string()),
    pa.field("time_stamp", pa.string(), nullable=False),
]
PQ_SCHEMAS["http_requests"] = pa.schema(fields)

# http_responses
fields = [
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("url", pa.string(), nullable=False),
    pa.field("method", pa.string(), nullable=False),
    pa.field("referrer", pa.string(), nullable=False),
    pa.field("response_status", pa.string(), nullable=False),
    pa.field("response_status_text", pa.string(), nullable=False),
    pa.field("is_cached", pa.bool_(), nullable=False),
    pa.field("headers", pa.string(), nullable=False),
    pa.field("channel_id", pa.string(), nullable=False),
    pa.field("location", pa.string(), nullable=False),
    pa.field("time_stamp", pa.string(), nullable=False),
    pa.field("content_hash", pa.string()),
]
PQ_SCHEMAS["http_responses"] = pa.schema(fields)

# http_redirects
fields = [
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("old_channel_id", pa.string()),
    pa.field("new_channel_id", pa.string()),
    pa.field("is_temporary", pa.bool_(), nullable=False),
    pa.field("is_permanent", pa.bool_(), nullable=False),
    pa.field("is_internal", pa.bool_(), nullable=False),
    pa.field("is_sts_upgrade", pa.bool_(), nullable=False),
    pa.field("time_stamp", pa.string(), nullable=False),
]
PQ_SCHEMAS["http_redirects"] = pa.schema(fields)

# javascript
fields = [
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("script_url", pa.string()),
    pa.field("script_line", pa.string()),
    pa.field("script_col", pa.string()),
    pa.field("func_name", pa.string()),
    pa.field("script_loc_eval", pa.string()),
    pa.field("document_url", pa.string()),
    pa.field("top_level_url", pa.string()),
    pa.field("call_stack", pa.string()),
    pa.field("symbol", pa.string()),
    pa.field("operation", pa.string()),
    pa.field("value", pa.string()),
    pa.field("arguments", pa.string()),
    pa.field("time_stamp", pa.string(), nullable=False),
]
PQ_SCHEMAS["javascript"] = pa.schema(fields)

# javascript_cookies
fields = [
    pa.field("crawl_id", pa.int32(), nullable=False),
    pa.field("visit_id", pa.int64(), nullable=False),
    pa.field("instance_id", pa.int32(), nullable=False),
    pa.field("change", pa.string()),
    pa.field("creationTime", pa.string()),
    pa.field("expiry", pa.string()),
    pa.field("is_http_only", pa.bool_()),
    pa.field("is_session", pa.bool_()),
    pa.field("last_accessed", pa.string()),
    pa.field("raw_host", pa.string()),
    pa.field("expires", pa.int64()),
    pa.field("host", pa.string()),
    pa.field("is_domain", pa.bool_()),
    pa.field("is_secure", pa.bool_()),
    pa.field("name", pa.string()),
    pa.field("path", pa.string()),
    pa.field("policy", pa.int32()),
    pa.field("status", pa.int32()),
    pa.field("value", pa.string()),
]
PQ_SCHEMAS["javascript_cookies"] = pa.schema(fields)
