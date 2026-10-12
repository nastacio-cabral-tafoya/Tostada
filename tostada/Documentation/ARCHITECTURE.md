# Tostada Web Server and Framework

A documentation of the custom Python HTTP server and application framework, based on the supplied `webserver_ipv4.py`, `webserver_ipv4_ssl.py`, and `my_http_handler.py` source files.

> **Scope:** This README describes architecture visible in those files. It does not assume that every deployment configuration, action, template, SQL script, or application module is included here. Confirm configuration values and the complete project tree before deploying.

## 1. Overview

The project combines two closely related layers:

- **HTTP server layer** — owns IPv4 TCP sockets, optional TLS, connection acceptance, request framing, bounded worker-thread concurrency, and connection cleanup.
- **HTTP framework layer** — parses requests, maps HTTP methods and URL paths to Python action files, renders templates containing embedded Python, serves public files, manages response headers/cookies and in-memory sessions, and routes errors to configured resources.
- **Application layer** — supplies action scripts, templates, public assets, configuration, SQL initialization scripts, and any application-specific database logic.
- **Persistence and configuration layer** — supports SQLite or MySQL through a thread-local connection facade; JSON files define server and framework settings.

The framework is file-oriented: a request normally maps to a Python action file under a method-specific directory. If no action file is found, the handler attempts to serve a corresponding public file. Templates can include executable Python blocks.

## 2. Architecture

```text
Browser / HTTP client
        |
        | IPv4 TCP
        v
+----------------------------+
| Socket listener            |
| webserver_ipv4.py          |
| or webserver_ipv4_ssl.py   |
+----------------------------+
        |
        | accept(), socket timeout,
        | semaphore-limited worker
        v
+----------------------------+
| Request receiver           |
| _recv_http_request()       |
| headers + body framing     |
+----------------------------+
        |
        v
+----------------------------+
| HTTPHandler instance       |
| respond_to_request()       |
|   parse_request()          |
|   handle_request()         |
+----------------------------+
        |
        +--> Method dispatch
        |       |
        |       v
        |   execute_action()
        |       |
        |       +--> method-specific Python action
        |       +--> configured error action
        |       +--> public-file fallback
        |
        +--> execute_template()
        |       +--> embedded Python
        |       +--> generated output
        |
        +--> session and cookie helpers
        |
        v
+----------------------------+
| HTTP response serialization|
| status + headers + cookies |
| body bytes                 |
+----------------------------+
        |
        v
sendall() -> close connection

Shared services:
- JSON configuration
- thread-local SQLite/MySQL connections
- database logger and text logger
- encryption/decryption helpers for configured secret material
```

## 3. Source files and responsibilities

### `webserver_ipv4.py`

The non-TLS server entry point. It loads configuration and secret material, loads `my_http_handler.py`, creates a thread-local database connection facade, initializes the handler, and starts the listener on the configured non-SSL port. It can be configured to redirect HTTP requests to HTTPS.

### `webserver_ipv4_ssl.py`

The TLS server entry point. It creates an IPv4 TCP socket, builds an `ssl.SSLContext` using `ssl.PROTOCOL_TLS_SERVER`, loads the configured certificate and private key, wraps the socket for server-side TLS, and passes it to the shared listener. It rejects startup when HTTPS is disabled in configuration.

### `my_http_handler.py`

Implements `HTTPHandler`, the request/response and application-dispatch framework. Responsibilities include:

- HTTP request-line, query-string, header, cookie, and body parsing.
- Dispatch for `GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `CONNECT`, `OPTIONS`, `TRACE`, and `PATCH`.
- Action-file lookup and execution.
- Static/public file delivery and content-type selection.
- Template processing with embedded Python.
- Response generation, redirects, error routing, and cookies.
- In-memory session state and authentication-related session helpers.
- A helper for opening application SQLite databases.

## 4. Startup and configuration

Both server entry points derive a working directory from their own source path and change into it. They load:

- `Server_Config/server_config.json` — listener, TLS, thread, socket, database, and secret-file settings.
- `Server_Config/http_config.json` — framework behavior such as root paths, action/template/public-file directories, default route, HTTP version, content types, status codes, and error locations.

The server configuration also identifies key files and a protected pepper value. The entry points read configured key files and decrypt the pepper using Fernet.

The source currently reads `my_http_handler.py` using `exec()` twice. This is redundant and should be reviewed; the framework class is defined in the executing server process rather than imported as a conventional Python module.

### Configuration areas to review

Actual key names and values are defined in the JSON configuration files. Important settings referenced by the source include:

- `server-host`
- `non-ssl-port` and `ssl-port`
- `queue-limit`
- `max-threads`
- `socket-buffer-size`
- `enable-https`, including force-SSL settings
- `cert-location` and `key-location`
- `database`, with SQLite or MySQL settings
- `pepperkey`, `saltskey`, `userskey`, and `pepper`

The framework configuration includes `root-path`, `paths`, `default-location`, `version`, `content-types`, `status-codes`, `status-locations`, `session-cookie-name`, and `session-timeout`.

Do not commit production secrets, private keys, credentials, or real user data to source control.

## 5. Request lifecycle

1. **Accept connection.** The listener acquires a semaphore slot before accepting a connection. The accepted socket receives a 10-second timeout and is assigned to a daemon worker thread.
2. **Read one request.** `_recv_http_request()` reads until the header terminator and then reads the body using `Content-Length` or chunked transfer encoding. It rejects oversized headers (over 1 MiB), invalid/conflicting content lengths, simultaneous `Transfer-Encoding` and `Content-Length`, unsupported transfer encodings, and incomplete bodies.
3. **Create request handler.** Each worker creates its own `HTTPHandler`, because request/response state is mutable.
4. **Parse request.** `respond_to_request()` initializes per-request state, and `parse_request()` extracts the method, protocol, path, query string, headers, cookies, and body.
5. **Apply HTTPS redirect policy.** When enabled for the non-TLS listener, the handler rewrites the request to the configured redirect action. The `true-path` setting controls whether the original path is passed along.
6. **Dispatch method.** `handle_request()` calls the matching method handler. `/` maps to `default-location` for GET/HEAD.
7. **Execute application behavior.** `execute_action()` decodes query/form-style parameters and looks for a Python action in the directory associated with the HTTP method. The action executes in the handler's Python context and can use handler helpers and process globals.
8. **Fallback or error.** If the action file is missing, the handler attempts to return a public file. If action execution fails, it invokes the configured 500 error resource. Missing files are routed through the configured 404 resource.
9. **Serialize response.** The framework assembles an HTTP status line, headers, each `Set-Cookie` header, a blank line, and the response body.
10. **Send and clean up.** The worker sends the response with `sendall()`, closes the client socket and its thread-local database connection, then releases the semaphore slot.

The implementation intentionally handles one HTTP request per TCP connection and closes the connection afterward; it is not a keep-alive request loop.

## 6. Routing and action files

The URL path and HTTP method determine the action path. The exact directory layout is controlled by `http_config.json` under `paths.actions`, including `actions-root` and method-specific directories.

Conceptually, a request such as `GET /reports` looks for a Python action in the configured GET action directory for that path. The root URL `/` is mapped to `default-location`. Other methods use their own action directories.

Action scripts are executed with Python `exec()`. The framework parses query/form-style values into a `parameters` dictionary and preserves bare arguments without `=` as `None` for compatibility. Application action scripts should follow the conventions used by the existing application files; those conventions are not fully specified by the three server/framework files alone.

### Important execution model

`exec()` executes code with the privileges of the server process. Consequently, action files and template code are trusted server-side code, not sandboxed plugins. Never build action paths directly from untrusted input without robust path validation, and do not allow untrusted users to upload executable actions or templates.

## 7. Templates

`execute_template()` loads a template from the configured templates directory and recognizes embedded Python blocks delimited by `<%` and `%>`. It executes each captured block, collects generated output through `template_print()`, and substitutes that output into the template. The framework includes indentation handling for standalone blocks and supports inline blocks.

Relevant helpers:

- `template_print(text, end='\n')` — appends generated template output.
- `get_exec_stdout()` — retrieves the current generated output.
- `reset_exec_stdout()` — clears the output buffer.
- `print(text, end='\n')` — appends to the response body.

Templates are executable Python and should be treated as trusted code. HTML escaping is an application responsibility unless the application applies it explicitly.

## 8. Public files and responses

If an action file cannot be opened, `get_file_bytes()` attempts to read a file from the configured public-files directory. The extension is mapped to a MIME type using `content-types`; textual and selected application types receive a UTF-8 charset parameter.

The response builder supports text or byte bodies, writes HTTP/1.x CRLF separators, includes response headers and individual `Set-Cookie` headers, and prevents a second response from replacing one already constructed. `HEAD` runs the GET-style action path and then strips the response body.

The framework provides `redirect()` for a `302 Found` response and `set_error()` for configured error actions. Error handling includes a guard to avoid recursively invoking a failing error resource.

## 9. Sessions and authentication state

`HTTPHandler.active_sessions` is a process-local dictionary shared by handler instances. An `RLock` protects session helper methods. Session IDs are generated with `secrets.token_urlsafe(64)`. Session records contain a creation/refresh timestamp, configured timeout, and a `parameters` dictionary initially containing `authenticated: False`.

Available helpers include:

- `set_session()`
- `validate_session(session_id)`
- `destroy_session(session_id)`
- `get_session_parameter(session_id, key)`
- `set_session_parameter(session_id, key, value)`
- `session_authenticated(session_id)`
- `authenticate_session(session_id, username)`
- `deauthenticate_session(session_id)`

The session cookie includes `Max-Age`, `SameSite=Strict`, and a hard-coded `Domain` value in the current source. Verify and change that domain for the deployment. The cookie construction shown does not itself add `Secure` or `HttpOnly`; these attributes should be considered before exposing authenticated sessions to production traffic.

Because sessions are stored in process memory, they are lost when the server restarts and are not shared between multiple server processes or machines. The session timeout is refreshed when a valid existing session is accepted by `set_session()`.

## 10. Database layer and logging

### Thread-local database facade

The server defines `ThreadLocalDatabaseConnection`, exposed globally as `db_connection` so action scripts can use a familiar connection interface. The facade lazily opens one connection per worker thread and delegates connection methods through `__getattr__`.

- **SQLite:** uses the configured database file, a 30-second connection timeout, WAL journal mode, and a 30-second busy timeout.
- **MySQL:** imports `mysql.connector` and connects using the configured host, port, database, username, and password.
- **Cleanup:** the worker calls `db_connection.close()` in its `finally` block, closing the current thread's connection.

The framework also has `create_sqlite_connection()` for opening a separate SQLite database under the configured private-files database directory.

### Logging

- `logger()` writes structured log entries to a database table named `log`. It supports SQLite and MySQL and reads the corresponding initialization SQL from `Server_Config/SQL_Scripts/`.
- `_logger_()` appends text entries to `log.txt`, falling back to creating the file if append fails.

Database logging depends on the configured database and SQL initialization scripts. Review log contents and access controls because exception traces and request-related data can contain sensitive information.

## 11. Security model and operational considerations

The following points are directly relevant to the implementation and should be checked before production use:

1. **Executable actions and templates:** `exec()` means the server trusts every action and template file. Keep write access restricted and review deployment workflows.
2. **Path traversal:** action and public-file paths are formed using configured roots plus request-derived paths. Ensure canonical path validation prevents paths from escaping their intended directories.
3. **TLS:** verify certificate/key permissions, renewal, supported TLS settings, and whether HTTP is redirected to HTTPS as intended.
4. **Session cookie flags:** configure the correct cookie domain and add `Secure` and `HttpOnly` for production HTTPS sessions where appropriate. Review session ID rotation after login and CSRF protections for state-changing requests.
5. **Session storage:** the in-memory session dictionary is per process; it does not provide persistence or multi-worker-process sharing.
6. **Request limits:** the receiver limits header size, but review body-size limits and read deadlines. The socket timeout is set at connection level; validate behavior for slow or very large uploads.
7. **HTTP parsing:** the receiver normalizes chunked bodies and checks some framing conflicts. Test malformed request lines, duplicate headers, chunk trailers, oversized bodies, and unusual transfer encodings.
8. **Error handling:** broad exception handlers can make failures hard to diagnose. Ensure internal stack traces are not returned to clients and that logs are protected.
9. **Response headers:** ensure application-provided header values cannot inject CR/LF characters. Set appropriate content-security and other browser security headers at the framework or deployment layer.
10. **Secrets:** keep key files, the decrypted pepper, database credentials, certificates, and private keys outside public asset directories and source control.
11. **Database access:** use parameterized SQL in action code, least-privilege database credentials, and explicit transaction handling.
12. **Startup path handling:** review the directory calculation and configuration-relative paths when moving the service between operating systems or deployment layouts.

This list is an architectural review checklist, not a claim that every listed control is absent elsewhere in the application.

## 12. Concurrency model

The listener uses a `Semaphore(max-threads)` to cap active worker threads. Each connection is handled by a daemon `Thread`. Mutable request/response state is isolated in a new `HTTPHandler` per request. Database connections are thread-local, while session data is shared across handler instances and protected by a reentrant lock.

This is a thread-per-connection design with a configured concurrency ceiling. Capacity depends on the configured thread limit, request duration, database behavior, and host resources. Since worker threads are daemon threads, graceful draining of in-flight requests at process shutdown is not implemented in the shown code.

## 13. Dependencies

Visible standard-library dependencies include:

- `socket`, `ssl` — TCP and TLS
- `threading` — worker threads, semaphore, thread-local state, and session lock
- `json`, `os`, `time`, `datetime`, `secrets`, `traceback`, `subprocess`, `sqlite3`, `atexit`

External dependencies visible in the source:

- `cryptography` — Fernet encryption/decryption
- `mysql-connector-python` — required when MySQL is selected

Install and pin dependencies according to the deployment's chosen Python version and dependency-management policy. The supplied files do not specify a supported Python version or pinned package versions.

## 14. Suggested project layout

The exact deployed layout is defined by configuration. The following is illustrative, not a claim that every directory was included in the supplied files:

```text
project-root/
├── webserver_ipv4.py
├── webserver_ipv4_ssl.py
├── my_http_handler.py
├── Server_Config/
│   ├── server_config.json
│   ├── http_config.json
│   └── SQL_Scripts/
│       ├── sqlite/
│       └── mysql/
├── actions/                 # configured method-specific action roots
├── templates/               # configured executable templates
├── public/                  # configured public assets
├── private/                 # private files/databases; never web-accessible
└── log.txt
```

## 15. Development and testing checklist

- [ ] Validate both configuration JSON files before startup.
- [ ] Confirm configured directories and SQL initialization scripts exist.
- [ ] Test plain HTTP, TLS, and HTTP-to-HTTPS redirect behavior.
- [ ] Test each supported HTTP method and the configured default route.
- [ ] Test query strings, form bodies, cookies, and chunked requests.
- [ ] Test action success, missing action/static file fallback, 404, 405, and 500 behavior.
- [ ] Test template execution, output encoding, and HTML escaping.
- [ ] Test session creation, expiration, authentication, logout, and cookie attributes.
- [ ] Test simultaneous SQLite writes and MySQL connection behavior if enabled.
- [ ] Test path traversal and malformed HTTP requests.
- [ ] Confirm logs do not expose secrets or sensitive user data.
- [ ] Verify TLS certificate renewal and backup/restore procedures.

## 16. Current architectural boundaries

Based on the supplied source files, the implementation is a compact custom HTTP server and server-side Python framework, rather than a framework built on WSGI/ASGI. It provides its own socket lifecycle, HTTP request framing, method dispatch, action execution, template engine, session helpers, and response serialization.

Some application details live outside these three files: actual route/action scripts, template contents, exact configuration values, authentication workflows, schema design, authorization policy, and deployment/service-manager configuration. Document those separately as the project evolves.
