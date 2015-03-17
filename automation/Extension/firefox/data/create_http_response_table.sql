CREATE TABLE http_responses(
	id INTEGER PRIMARY KEY ASC,
	url TEXT,
	method TEXT,
	referrer TEXT,
	response_status INTEGER,
	response_status_text TEXT,
	page_id INTEGER,
	is_cached INTEGER,
	http_request_id INTEGER
);