from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table, Text, text

metadata = MetaData()

# Note: All DATETIME columns from schema.sql are defined as Text here.
# Rationale: The extension sends timestamp strings (not Python datetime objects),
# and test_values.py uses random_word(12) for all timestamp fields. Using Text
# ensures cross-dialect compatibility (SQLite stores datetimes as text anyway,
# and PostgreSQL would reject non-datetime strings in a DATETIME column).
# Columns with server_default still use text("CURRENT_TIMESTAMP") which works
# on both SQLite and PostgreSQL regardless of column type.

# Note: Foreign keys from schema.sql are NOT included in the SQLAlchemy schema.
# Rationale: SQLite does not enforce FKs by default (requires PRAGMA foreign_keys=ON),
# and the current codebase never enables this pragma. PostgreSQL enforces FKs by
# default, and test data (test_values.py) generates random IDs that violate FK
# constraints. Removing FKs from the SQLAlchemy schema avoids PostgreSQL insert
# failures. The FKs remain documented in schema.sql as a reference.

# Note: Columns that can hold values > 2^31-1 use BigInteger instead of Integer.
# Rationale: test_values.py generates values up to 2^63-1 for fields like visit_id,
# request_id, window_id, tab_id, frame_id, event_ordinal, etc. SQLAlchemy Integer
# maps to a 4-byte integer on PostgreSQL (max 2^31-1), which overflows. BigInteger
# maps to an 8-byte integer (BIGINT) on PostgreSQL. On SQLite, both INTEGER and
# BIGINT have INTEGER affinity and support 8-byte values natively.

# Note: Every table carries an instance_id column. This mirrors the Arrow/parquet
# provider (parquet_schema.py), which stamps each record with a per-provider-instance
# shard key (random.getrandbits(32)) "for partitioning". When many volunteer nodes
# write to ONE shared database, their visit_id/browser_id values are per-node
# sequential and would collide. Stamping a per-instance instance_id and making it
# part of the effective primary key disambiguates clients and removes cross-client
# lock contention. instance_id is uint32 in parquet; we use BigInteger here because
# SQLAlchemy Integer maps to a signed 4-byte INT on PostgreSQL (max 2^31-1), which
# overflows for values in [2^31, 2^32). instance_id is NOT present in schema.sql
# (the single-node SQLite path); test_schema_equivalence excludes it accordingly.

task = Table(
    "task",
    metadata,
    # task_id is client-supplied (random 32-bit, see storage_controller.py), never
    # DB-autoincremented in practice. Making the key composite with instance_id
    # disambiguates clients on a shared DB. autoincrement=False because a composite
    # PK cannot be autoincremented and the value is always supplied explicitly.
    Column("instance_id", BigInteger, primary_key=True, nullable=False),
    Column("task_id", Integer, primary_key=True, autoincrement=False),
    Column("start_time", Text, server_default=text("CURRENT_TIMESTAMP")),
    Column("manager_params", Text, nullable=False),
    Column("openwpm_version", Text, nullable=False),
    Column("browser_version", Text, nullable=False),
)

crawl = Table(
    "crawl",
    metadata,
    # browser_id is per-node sequential -> collides across clients. Composite PK
    # with instance_id disambiguates.
    Column("instance_id", BigInteger, primary_key=True, nullable=False),
    Column("browser_id", Integer, primary_key=True, autoincrement=False),
    Column("task_id", Integer, nullable=False),
    Column("browser_params", Text, nullable=False),
    Column("start_time", Text, server_default=text("CURRENT_TIMESTAMP")),
)

site_visits = Table(
    "site_visits",
    metadata,
    # visit_id is per-node sequential -> collides across clients. Composite PK
    # with instance_id disambiguates.
    Column("instance_id", BigInteger, primary_key=True, nullable=False),
    Column("visit_id", BigInteger, primary_key=True, autoincrement=False),
    Column("browser_id", Integer, nullable=False),
    Column("site_url", String(500), nullable=False),
    Column("site_rank", Integer),
)

crawl_history = Table(
    "crawl_history",
    metadata,
    Column("instance_id", BigInteger, nullable=False),
    Column("browser_id", Integer),
    Column("visit_id", BigInteger),
    Column("command", Text),
    Column("arguments", Text),
    Column("retry_number", Integer),
    Column("command_status", Text),
    Column("error", Text),
    Column("traceback", Text),
    Column("duration", Integer),
    Column("dtg", Text, server_default=text("CURRENT_TIMESTAMP")),
)

http_requests = Table(
    "http_requests",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("instance_id", BigInteger, nullable=False),
    Column("incognito", Integer),
    Column("browser_id", Integer, nullable=False),
    Column("visit_id", BigInteger, nullable=False),
    Column("extension_session_uuid", Text),
    Column("event_ordinal", BigInteger),
    Column("window_id", BigInteger),
    Column("tab_id", BigInteger),
    Column("frame_id", BigInteger),
    Column("url", Text, nullable=False),
    Column("top_level_url", Text),
    Column("parent_frame_id", BigInteger),
    Column("frame_ancestors", Text),
    Column("method", Text, nullable=False),
    Column("referrer", Text, nullable=False),
    Column("headers", Text, nullable=False),
    Column("request_id", BigInteger, nullable=False),
    Column("is_XHR", Integer),
    Column("is_third_party_channel", Integer),
    Column("is_third_party_to_top_window", Integer),
    Column("triggering_origin", Text),
    Column("loading_origin", Text),
    Column("loading_href", Text),
    Column("req_call_stack", Text),
    Column("resource_type", Text, nullable=False),
    Column("post_body", Text),
    Column("post_body_raw", Text),
    Column("time_stamp", Text, nullable=False),
    sqlite_autoincrement=True,
)

http_responses = Table(
    "http_responses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("instance_id", BigInteger, nullable=False),
    Column("incognito", Integer),
    Column("browser_id", Integer, nullable=False),
    Column("visit_id", BigInteger, nullable=False),
    Column("extension_session_uuid", Text),
    Column("event_ordinal", BigInteger),
    Column("window_id", BigInteger),
    Column("tab_id", BigInteger),
    Column("frame_id", BigInteger),
    Column("url", Text, nullable=False),
    Column("method", Text, nullable=False),
    Column("response_status", Integer),
    Column("response_status_text", Text, nullable=False),
    Column("is_cached", Integer, nullable=False),
    Column("headers", Text, nullable=False),
    Column("request_id", BigInteger, nullable=False),
    Column("location", Text, nullable=False),
    Column("time_stamp", Text, nullable=False),
    Column("content_hash", Text),
    sqlite_autoincrement=True,
)

http_redirects = Table(
    "http_redirects",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("instance_id", BigInteger, nullable=False),
    Column("incognito", Integer),
    Column("browser_id", Integer, nullable=False),
    Column("visit_id", BigInteger, nullable=False),
    Column("old_request_url", Text),
    Column("old_request_id", Text),
    Column("new_request_url", Text),
    Column("new_request_id", Text),
    Column("extension_session_uuid", Text),
    Column("event_ordinal", BigInteger),
    Column("window_id", BigInteger),
    Column("tab_id", BigInteger),
    Column("frame_id", BigInteger),
    Column("response_status", Integer, nullable=False),
    Column("response_status_text", Text, nullable=False),
    Column("headers", Text, nullable=False),
    Column("time_stamp", Text, nullable=False),
    sqlite_autoincrement=True,
)

# javascript: Note that id is INTEGER PRIMARY KEY *without* AUTOINCREMENT.
# The id is provided by the extension, not auto-generated.
javascript = Table(
    "javascript",
    metadata,
    # id is client-supplied (extension-provided, autoincrement=False) and
    # per-node sequential -> collides across clients. Composite PK with
    # instance_id disambiguates.
    Column("instance_id", BigInteger, primary_key=True, nullable=False),
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("incognito", Integer),
    Column("browser_id", Integer, nullable=False),
    Column("visit_id", BigInteger, nullable=False),
    Column("extension_session_uuid", Text),
    Column("event_ordinal", BigInteger),
    Column("page_scoped_event_ordinal", BigInteger),
    Column("window_id", BigInteger),
    Column("tab_id", BigInteger),
    Column("frame_id", BigInteger),
    Column("script_url", Text),
    Column("script_line", Text),
    Column("script_col", Text),
    Column("func_name", Text),
    Column("script_loc_eval", Text),
    Column("document_url", Text),
    Column("top_level_url", Text),
    Column("call_stack", Text),
    Column("symbol", Text),
    Column("operation", Text),
    Column("value", Text),
    Column("arguments", Text),
    Column("time_stamp", Text, nullable=False),
)

# javascript_cookies: id is INTEGER PRIMARY KEY ASC (no AUTOINCREMENT).
# ASC merely specifies sort order (which is the default); it does NOT add
# AUTOINCREMENT semantics. Use autoincrement=False.
javascript_cookies = Table(
    "javascript_cookies",
    metadata,
    # id is client-supplied (autoincrement=False) -> collides across clients.
    # Composite PK with instance_id disambiguates.
    Column("instance_id", BigInteger, primary_key=True, nullable=False),
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("browser_id", Integer, nullable=False),
    Column("visit_id", BigInteger, nullable=False),
    Column("extension_session_uuid", Text),
    Column("event_ordinal", BigInteger),
    Column("record_type", Text),
    Column("change_cause", Text),
    Column("expiry", Text),
    Column("is_http_only", Integer),
    Column("is_host_only", Integer),
    Column("is_session", Integer),
    Column("host", Text),
    Column("is_secure", Integer),
    Column("name", Text),
    Column("path", Text),
    Column("value", Text),
    Column("same_site", Text),
    Column("first_party_domain", Text),
    Column(
        "store_id", Text
    ),  # schema.sql uses STRING, which is non-standard; Text is correct
    Column("time_stamp", Text),
)

# navigations: UNUSUAL -- id is just INTEGER (not a primary key at all).
# No autoincrement. Has committed_time_stamp as a separate DATETIME column.
navigations = Table(
    "navigations",
    metadata,
    Column("instance_id", BigInteger, nullable=False),
    Column("id", Integer),  # NOT a primary key
    Column("incognito", Integer),
    Column("browser_id", Integer, nullable=False),
    Column("visit_id", BigInteger, nullable=False),
    Column("extension_session_uuid", Text),
    Column("process_id", BigInteger),
    Column("window_id", BigInteger),
    Column("tab_id", BigInteger),
    Column("tab_opener_tab_id", BigInteger),
    Column("frame_id", BigInteger),
    Column("parent_frame_id", BigInteger),
    Column("window_width", BigInteger),
    Column("window_height", BigInteger),
    Column("window_type", Text),
    Column("tab_width", BigInteger),
    Column("tab_height", BigInteger),
    Column("tab_cookie_store_id", Text),
    Column("uuid", Text),
    Column("url", Text),
    Column("transition_qualifiers", Text),
    Column("transition_type", Text),
    Column("before_navigate_event_ordinal", BigInteger),
    Column("before_navigate_time_stamp", Text),
    Column("committed_event_ordinal", BigInteger),
    Column("committed_time_stamp", Text),
)

callstacks = Table(
    "callstacks",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("instance_id", BigInteger, nullable=False),
    Column("request_id", BigInteger, nullable=False),
    Column("browser_id", Integer, nullable=False),
    Column("visit_id", BigInteger, nullable=False),
    Column("call_stack", Text),
    sqlite_autoincrement=True,
)

incomplete_visits = Table(
    "incomplete_visits",
    metadata,
    Column("visit_id", BigInteger, nullable=False),
    Column("instance_id", BigInteger, nullable=False),
)

# dns_responses: Note the used_address column which IS in schema.sql
# but is NOT in test_values.py. It must be included here.
dns_responses = Table(
    "dns_responses",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("instance_id", BigInteger, nullable=False),
    Column("request_id", BigInteger, nullable=False),
    Column("browser_id", Integer, nullable=False),
    Column("visit_id", BigInteger, nullable=False),
    Column("hostname", Text),
    Column("redirect_url", Text),
    Column("addresses", Text),
    Column("used_address", Text),
    Column("canonical_name", Text),
    Column("is_TRR", Integer),
    Column("error", Text),
    Column("time_stamp", Text, nullable=False),
    sqlite_autoincrement=True,
)

# A dict mapping TableName -> Table for runtime lookup:
TABLE_MAP = {t.name: t for t in metadata.sorted_tables}
