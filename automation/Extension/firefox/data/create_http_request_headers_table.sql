CREATE TABLE http_request_headers(
	id INTEGER PRIMARY KEY ASC,
	http_request_id INTEGER,
	name TEXT,
	value TEXT
);