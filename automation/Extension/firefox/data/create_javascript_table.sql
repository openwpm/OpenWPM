CREATE TABLE IF NOT EXISTS javascript(
	id INTEGER ASC,
	crawl_id INTEGER,
        top_url TEXT,
        url TEXT,
	symbol TEXT,
	operation TEXT,
	value TEXT,
        PRIMARY KEY (id, crawl_id)
);
