CREATE TABLE IF NOT EXISTS content_policy(
    id INTEGER PRIMARY KEY ASC,
    crawl_id INTEGER,
    content_type INTEGER,
    content_location TEXT,
    request_origin TEXT,
    mime_type_guess TEXT,
    page_id INTEGER,
    visit_id INTEGER
);
