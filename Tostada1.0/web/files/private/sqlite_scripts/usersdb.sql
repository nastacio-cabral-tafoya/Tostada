CREATE TABLE IF NOT EXISTS users (
	id INTEGER PRIMARY KEY,
	username TEXT NOT NULL UNIQUE,
	password TEXT NOT NULL,
	link TEXT,
	createdate TEXT NOT NULL,
	deletedate TEXT,
	firstname TEXT NOT NULL,
	lastname TEXT NOT NULL,
	dob TEXT NOT NULL,
	email TEXT NOT NULL,
	verified TEXT NOT NULL,
	twofactor TEXT NOT NULL,
	lastaccess TEXT NOT NULL,
	lastsuccessfulllogin TEXT
);

CREATE TABLE IF NOT EXISTS secureanswers (
	id INTEGER PRIMARY KEY,
	username TEXT NOT NULL UNIQUE,
	securequestion1 TEXT,
	secureanswer1 TEXT,
	securequestion2 TEXT,
	secureanswer2 TEXT,
	securequestion3 TEXT,
	secureanswer3 TEXT,
	lastaccess TEXT
);

CREATE TABLE IF NOT EXISTS securequestions (
	id INTEGER PRIMARY KEY,
	securequestion TEXT NOT NULL UNIQUE
);