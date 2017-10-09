CREATE TABLE IF NOT EXISTS http_redirects(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crawl_id INTEGER NOT NULL,
  visit_id INTEGER NOT NULL,
  old_channel_id TEXT,
  new_channel_id TEXT,
  is_temporary BOOLEAN NOT NULL,
  is_permanent BOOLEAN NOT NULL,
  is_internal BOOLEAN NOT NULL,
  is_sts_upgrade BOOLEAN NOT NULL,
  time_stamp TEXT NOT NULL
);
