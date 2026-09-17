CREATE TABLE IF NOT EXISTS salts (
	id INTEGER PRIMARY KEY,
	saltstr TEXT NOT NULL UNIQUE,
	link TEXT,
	createdate TEXT NOT NULL,
	deletedate TEXT,
	lastaccess TEXT
);