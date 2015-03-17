CREATE TABLE cookies(
	id INTEGER PRIMARY KEY ASC,
	change TEXT,
	creationTime INTEGER,
	expiry INTEGER,
	is_http_only INTEGER,
	is_session INTEGER,
	last_accessed INTEGER,
	raw_host TEXT,
	expires INTEGER,
	host TEXT,
	is_domain INTEGER,
	is_secure INTEGER,
	name TEXT,
	path TEXT,
	policy INTEGER,
	status INTEGER,
	value TEXT
);