CREATE TABLE content_policy(
	id INTEGER PRIMARY KEY ASC,
	content_type INTEGER,
	content_location TEXT,
	request_origin TEXT,
	mime_type_guess TEXT,
	page_id INTEGER
);