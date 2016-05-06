CREATE TABLE IF NOT EXISTS pages(
    id INTEGER PRIMARY KEY ASC,
    crawl_id INTEGER,
    visit_id INTEGER,
    location TEXT,
    parent_id INTEGER
);
