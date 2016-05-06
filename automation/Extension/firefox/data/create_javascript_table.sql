CREATE TABLE IF NOT EXISTS javascript(
    id INTEGER PRIMARY KEY,
    crawl_id INTEGER,
    visit_id INTEGER,
    script_url TEXT,
    script_line TEXT,
    script_col TEXT,
    call_stack TEXT,
    symbol TEXT,
    operation TEXT,
    value TEXT,
    parameter_index INTEGER,
    parameter_value TEXT
);
