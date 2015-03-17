CREATE TABLE http_response_headers(
	id INTEGER PRIMARY KEY ASC,
	http_response_id INTEGER,
	name TEXT,
	value TEXT
);