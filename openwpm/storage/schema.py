from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)

metadata_obj = MetaData()

Table(
    "task",
    metadata_obj,
    Column("task_id", Integer, primary_key=True),
    Column("start_time", DateTime, server_default=Text("CURRENT_TIMESTAMP")),
    Column("manager_params", String, nullable=False),
    Column("openwpm_version", String, nullable=False),
    Column("browser_version", String, nullable=False),
)

Table(
    "crawl",
    metadata_obj,
    Column("browser_id", Integer, primary_key=True),
    Column("task_id", Integer, ForeignKey("task.task_id"), nullable=False),
    Column("browser_params", String, nullable=False),
    Column("start_time", DateTime, server_default=Text("CURRENT_TIMESTAMP")),
)

Table(
    "site_visits",
    metadata_obj,
    Column("visit_id", Integer, primary_key=True),
    Column("browser_id", Integer, ForeignKey("crawl.browser_id"), nullable=False),
    Column("site_url", String, nullable=False),
    Column("site_rank", Integer),
)

Table(
    "crawl_history",
    metadata_obj,
    Column("visit_id", Integer, ForeignKey("site_visits.visit_id"), nullable=False),
    Column("browser_id", Integer, ForeignKey("crawl.browser_id"), nullable=False),
    Column("command", String, nullable=False),
    Column("arguments", String),
    Column("retry_number", Integer),
    Column("command_status", String),
    Column("error", String),
    Column("traceback", String),
    Column("duration", Integer),
)
Table(
    "http_requests",
    metadata_obj,
    Column("visit_id", Integer, ForeignKey("site_visits.visit_id"), nullable=False),
    Column("browser_id", Integer, ForeignKey("crawl.browser_id"), nullable=False),
    Column("incognito", Integer),
    Column("extension_session_uuid", String),
    Column("event_ordinal", Integer),
    Column("window_id", Integer),
    Column("tab_id", Integer),
    Column("frame_id", Integer),
    Column("url", String, nullable=False),
    Column("parent_frame_id", Integer),
    Column("frame_ancestors", String),
    Column("method", String, nullable=False),
    Column("referrer", String, nullable=False),
    Column("headers", String, nullable=False),
    Column("request_id", Integer, nullable=False),
    Column("is_XHR", Boolean),
    Column("is_third_party_channel", Boolean),
    Column("is_third_party_to_top_window", Boolean),
    Column("triggering_origin", String),
    Column("tab_id", Integer),
    Column("frame_id", Integer),
)
Table()
