/* TODO: link with requests */
CREATE TABLE IF NOT EXISTS http_responses(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crawl_id INTEGER NOT NULL,
  visit_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  method TEXT NOT NULL,
  referrer TEXT NOT NULL,
  response_status INTEGER NOT NULL,
  response_status_text TEXT NOT NULL,
  is_cached BOOLEAN NOT NULL,
  headers TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  location TEXT NOT NULL,
  time_stamp TEXT NOT NULL,
  content_hash TEXT
);
