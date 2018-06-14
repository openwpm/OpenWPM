CREATE TABLE IF NOT EXISTS javascript(
    id INTEGER PRIMARY KEY,
    crawl_id INTEGER,
    visit_id INTEGER,
    script_url TEXT,
    document_url TEXT,
    top_document_url TEXT,
    referrer_url TEXT,
    script_line TEXT,
    script_col TEXT,
    func_name TEXT,
    script_loc_eval TEXT,
    call_stack TEXT,
    symbol TEXT,
    operation TEXT,
    value TEXT,
    arguments TEXT,
    time_stamp TEXT NOT NULL
);
