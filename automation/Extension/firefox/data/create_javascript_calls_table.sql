CREATE TABLE IF NOT EXISTS javascript_calls(
    id INTEGER PRIMARY KEY ASC,
    crawl_id INTEGER,
    visit_id INTEGER,
    javascript_id INTEGER,
    parameter_index INTEGER,
    value TEXT
);
