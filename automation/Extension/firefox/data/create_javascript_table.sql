CREATE TABLE IF NOT EXISTS javascript(
	id INTEGER PRIMARY KEY,
	crawl_id INTEGER,
        top_url TEXT,
        url TEXT,
	symbol TEXT,
	operation TEXT,
	value TEXT,
	parameter_index INTEGER,
	parameter_value TEXT
);
