CREATE TABLE IF NOT EXISTS log (
	id INTEGER PRIMARY KEY,
	logdate TEXT NOT NULL,
	logfile TEXT NOT NULL,
	logfunc TEXT NOT NULL,
	loguser TEXT NOT NULL,
	logstr TEXT
);