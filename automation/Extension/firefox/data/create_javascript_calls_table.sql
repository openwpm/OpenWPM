CREATE TABLE IF NOT EXISTS javascript_calls(
	id INTEGER PRIMARY KEY ASC,
        crawl_id INTEGER,
	top_url TEXT,
        javascript_id INTEGER,
	parameter_index INTEGER,
	value TEXT
);
