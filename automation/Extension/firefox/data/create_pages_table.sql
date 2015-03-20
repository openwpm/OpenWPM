CREATE TABLE IF NOT EXISTS pages(
	id INTEGER PRIMARY KEY ASC,
	crawl_id INTEGER,
        top_url TEXT,
        location TEXT,
	parent_id INTEGER
);
