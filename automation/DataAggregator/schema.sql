/* This file is sourced during the initialization
 * of the crawler. Make sure everything is CREATE
 * IF NOT EXISTS, otherwise there will be errors
 */

CREATE TABLE IF NOT EXISTS task (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    manager_params TEXT NOT NULL,
    openwpm_version TEXT NOT NULL,
    browser_version TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS crawl (
    crawl_id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    browser_params TEXT NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES task(task_id));

/*
# site_visits
 */
CREATE TABLE IF NOT EXISTS site_visits (
    visit_id INTEGER PRIMARY KEY,
    crawl_id INTEGER NOT NULL,
    site_url VARCHAR(500) NOT NULL,
    site_rank INTEGER,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

/*
# flash_cookies
 */
CREATE TABLE IF NOT EXISTS flash_cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    domain VARCHAR(500),
    filename VARCHAR(500),
    local_path VARCHAR(1000),
    key TEXT,
    content TEXT,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id),
    FOREIGN KEY(visit_id) REFERENCES site_visits(id));

/*
# crawl_history
 */
CREATE TABLE IF NOT EXISTS crawl_history (
    crawl_id INTEGER,
    visit_id INTEGER,
    command TEXT,
    arguments TEXT,
    retry_number INTEGER,
    command_status TEXT,
    error TEXT,
    traceback TEXT,
    dtg DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

/*
# http_requests
 */
CREATE TABLE IF NOT EXISTS http_requests(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  incognito INTEGER,
  crawl_id INTEGER NOT NULL,
  visit_id INTEGER NOT NULL,
  extension_session_uuid TEXT,
  event_ordinal INTEGER,
  window_id INTEGER,
  tab_id INTEGER,
  frame_id INTEGER,
  url TEXT NOT NULL,
  top_level_url TEXT,
  parent_frame_id INTEGER,
  frame_ancestors TEXT,
  method TEXT NOT NULL,
  referrer TEXT NOT NULL,
  headers TEXT NOT NULL,
  request_id TEXT NOT NULL,
  is_XHR INTEGER,
  is_frame_load INTEGER,
  is_full_page INTEGER,
  is_third_party_channel INTEGER,
  is_third_party_to_top_window INTEGER,
  triggering_origin TEXT,
  loading_origin TEXT,
  loading_href TEXT,
  req_call_stack TEXT,
  resource_type TEXT NOT NULL,
  post_body TEXT,
  post_body_raw TEXT,
  time_stamp DATETIME NOT NULL
);

/*
# http_responses
 */
CREATE TABLE IF NOT EXISTS http_responses(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  incognito INTEGER,
  crawl_id INTEGER NOT NULL,
  visit_id INTEGER NOT NULL,
  extension_session_uuid TEXT,
  event_ordinal INTEGER,
  window_id INTEGER,
  tab_id INTEGER,
  frame_id INTEGER,
  url TEXT NOT NULL,
  method TEXT NOT NULL,
  response_status INTEGER,
  response_status_text TEXT NOT NULL,
  is_cached INTEGER NOT NULL,
  headers TEXT NOT NULL,
  request_id TEXT NOT NULL,
  location TEXT NOT NULL,
  time_stamp DATETIME NOT NULL,
  content_hash TEXT
);

/*
# http_redirects
 */
CREATE TABLE IF NOT EXISTS http_redirects(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  incognito INTEGER,
  crawl_id INTEGER NOT NULL,
  visit_id INTEGER NOT NULL,
  old_request_url TEXT,
  old_request_id TEXT,
  new_request_url TEXT,
  new_request_id TEXT,
  extension_session_uuid TEXT,
  event_ordinal INTEGER,
  window_id INTEGER,
  tab_id INTEGER,
  frame_id INTEGER,
  response_status INTEGER NOT NULL,
  response_status_text TEXT NOT NULL,
  time_stamp DATETIME NOT NULL
);

/*
# javascript
 */
CREATE TABLE IF NOT EXISTS javascript(
  id INTEGER PRIMARY KEY,
  incognito INTEGER,
  crawl_id INTEGER NOT NULL,
  visit_id INTEGER NOT NULL,
  extension_session_uuid TEXT,
  event_ordinal INTEGER,
  page_scoped_event_ordinal INTEGER,
  window_id INTEGER,
  tab_id INTEGER,
  frame_id INTEGER,
  script_url TEXT,
  script_line TEXT,
  script_col TEXT,
  func_name TEXT,
  script_loc_eval TEXT,
  document_url TEXT,
  top_level_url TEXT,
  call_stack TEXT,
  symbol TEXT,
  operation TEXT,
  value TEXT,
  arguments TEXT,
  time_stamp DATETIME NOT NULL
);

/*
# javascript_cookies
 */
CREATE TABLE IF NOT EXISTS javascript_cookies(
    id INTEGER PRIMARY KEY ASC,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    extension_session_uuid TEXT,
    event_ordinal INTEGER,
    record_type TEXT,
    change_cause TEXT,
    expiry DATETIME,
    is_http_only INTEGER,
    is_host_only INTEGER,
    is_session INTEGER,
    host TEXT,
    is_secure INTEGER,
    name TEXT,
    path TEXT,
    value TEXT,
    same_site TEXT,
    first_party_domain TEXT,
    store_id STRING,
    time_stamp DATETIME
);

/*
# Navigations
 */
CREATE TABLE IF NOT EXISTS navigations(
  id INTEGER,
  incognito INTEGER,
  crawl_id INTEGER NOT NULL,
  visit_id INTEGER NOT NULL,
  extension_session_uuid TEXT,
  process_id INTEGER,
  window_id INTEGER,
  tab_id INTEGER,
  tab_opener_tab_id INTEGER,
  frame_id INTEGER,
  parent_frame_id INTEGER,
  window_width INTEGER,
  window_height INTEGER,
  window_type TEXT,
  tab_width INTEGER,
  tab_height INTEGER,
  tab_cookie_store_id TEXT,
  uuid TEXT,
  url TEXT,
  transition_qualifiers TEXT,
  transition_type TEXT,
  before_navigate_event_ordinal INTEGER,
  before_navigate_time_stamp DATETIME,
  committed_event_ordinal INTEGER,
  committed_time_stamp DATETIME
);

/*
# Callstacks
 */
CREATE TABLE IF NOT EXISTS callstacks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL,
  crawl_id INTEGER NOT NULL,
  visit_id INTEGER NOT NULL,
  call_stack TEXT
)