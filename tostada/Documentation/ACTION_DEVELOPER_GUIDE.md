# Tostada Python Action Developer Guide

## Purpose

A Python action is the server-side handler for a routed HTTP request. Tostada resolves an action by HTTP method and action name, reads the corresponding `.py` file, and executes that file in the request handler's execution context.

This guide documents the reusable capabilities provided by `HTTPHandler`, the request/response lifecycle, and the web-server layer. It is not an inventory of the current application's endpoints.

## 1. How a request reaches an action

At a high level:

1. The server accepts a TCP connection and receives one HTTP request.
2. A fresh `HTTPHandler` instance is created for that request.
3. `respond_to_request(...)` initializes request-specific state and parses the request.
4. `handle_request()` dispatches by HTTP method.
5. The handler resolves and executes the matching action script.
6. The action writes a response, sets headers/cookies, renders a template, or uses another available helper.
7. The handler serializes the response and the server sends it to the client.

The action file is selected using the configured action root, the method-specific directory, and the action name. Conceptually:

```text
<root-path>
  + <paths.actions.actions-root>
  + <paths.actions[method]>
  + <action-name>
  + ".py"
```

The public URL prefix and the filesystem location are configuration-driven; do not assume that the path on disk is identical to the URL path.

## 2. What is available inside an action

The handler calls `exec(action_script)` from `HTTPHandler.execute_action`. In the current implementation, action scripts use these names:

| Name | Meaning |
|---|---|
| `self` | The active `HTTPHandler` instance for this request. Use it to inspect request data and build the response. |
| `parameters` | A dictionary created from the argument string passed to the action. |
| `HTTPHandler` | The handler class. Its session storage is class-level and shared by handler instances in this process. |
| `json` | JSON library imported by the server's execution environment. |
| `timeout_to_seconds` | Server helper that converts an `HH:MM:SS` string to seconds. |
| `server_config` | Parsed server configuration dictionary. It contains server-level settings; do not return it wholesale to clients. |
| `db_connection` | Server-provided database connection proxy used by existing action code. |
| `sqlite3`, `Error` | SQLite interfaces imported by the server module. |
| `subprocess` | Python subprocess module imported by the server module. Use with care and never pass untrusted input into a shell command. |

Other module globals may exist because the action is executed in the server module's context. Treat the table above as a practical guide to the names used by the framework/application code, not a guarantee that every imported name is a stable public API.

## 3. Request data

The handler's `self.request` dictionary is populated by `parse_request()`.

| Key | Description |
|---|---|
| `type` | HTTP method, such as `GET`, `POST`, or `PATCH`. |
| `protocol` | Request protocol string, typically an HTTP/1.x version. |
| `path` | URL path without the query string; defaults to `/` when empty. |
| `path-parameters` | Raw query string from the URL, without the leading `?`. |
| `parameters` | Request body as text decoded by the handler's request parser. |
| `Cookie` | Parsed cookie-name/value dictionary when a Cookie header is present. |
| `request_headers` | Lowercase-keyed header dictionary stored as `self.request_headers`; repeated ordinary header fields are combined with `, `. |
| Header-specific keys | The parser also stores many headers under their original spelling and normalizes common headers such as `Content-Length`, `Content-Type`, `Host`, `Connection`, and `Cookie`. |

Examples:

```python
method = self.request["type"]
path = self.request["path"]
query_string = self.request["path-parameters"]
body_text = self.request["parameters"]
content_type = self.request_headers.get("content-type")
```

Use `.get(...)` for optional headers and cookies rather than assuming they exist.

### How `parameters` is built

`HTTPHandler.execute_action()` parses its `args` string with `urllib.parse.parse_qsl(..., keep_blank_values=True)` and builds a dictionary.

- GET and HEAD actions receive the URL query string.
- DELETE, CONNECT, OPTIONS, TRACE, and PATCH also receive the URL query string.
- POST and PUT actions receive the request body text as their `args` string.
- URL-encoded key/value pairs are URL-decoded.
- Repeated parameter names overwrite earlier values in the resulting dictionary.
- A bare field with no `=` is retained with the value `None`.
- Empty values such as `name=` are retained as an empty string.

For JSON payloads, the current handler does **not** automatically decode a raw JSON body into `parameters`. An action can parse JSON from the request body itself, or a client can submit a URL-encoded field whose value is a JSON string. Follow the convention established by the specific action being extended.

Example for a raw JSON body:

```python
payload = json.loads(self.request["parameters"])
```

Example for a URL-encoded field named `data` that contains JSON:

```python
payload = json.loads(parameters["data"])
```

Validate the parsed value's type and required fields before using it.

## 4. Writing a response

### `self.print(text, end='\n')`

Appends text to `self.response_body`. By default it appends a newline.

```python
self.set_response_header("Content-Type", "application/json; charset=utf-8")
self.print(json.dumps({"ok": True}), end="")
```

Prefer `json.dumps(...)` for JSON responses rather than manually concatenating JSON strings.

### `self.set_response_header(key, value)`

Adds or replaces a response header in `self.response_headers`.

```python
self.set_response_header("Content-Type", "application/json; charset=utf-8")
self.set_response_header("Cache-Control", "no-store")
```

The action dispatcher sets a default `Content-Type` of `text/html;charset=utf-8` before executing an action. Set the correct type explicitly when returning JSON, plain text, binary content, or another format.

### `self.set_response(body=None, status='200 OK')`

Finalizes the response bytes. If `body` is omitted, it uses `self.response_body`. The body may be `str` or `bytes`; other types raise `TypeError`.

```python
self.set_response(body="Created", status="201 Created")
```

The method will not replace a response if `self.response` has already been set. Most action scripts can simply use `self.print(...)` and allow `execute_action()` to finalize the response after the action finishes.

The handler creates a status line using `self.config["version"]`, emits response headers and each queued cookie as a separate `Set-Cookie` header, then adds the response body.

### `self.redirect(path)`

Sets a `Location` header and creates a `302 Found` response with an empty body.

```python
self.redirect("/login")
```

### `self.set_error(code, parameters, method)`

Dispatches to the configured error action for the supplied status code. It uses the configured status description and has a recursion guard so an error action does not repeatedly invoke itself when it cannot be loaded.

Use the configured error mechanism when it matches the desired behavior; for application-specific errors, consider returning an explicit status and response body.

## 5. Cookies and sessions

### `self.set_cookie(name, value, cookie_parameters={})`

Queues a cookie for the response. The dictionary's keys are appended as cookie attributes.

```python
self.set_cookie(
    "preference",
    "compact",
    {"Path": "/", "SameSite": "Lax"}
)
```

Cookie attributes are assembled as strings by this method. It does not validate attribute names or values. Set appropriate security attributes for your application and ensure cookies are used only over the intended transport.

### Session methods

Session data is stored in `HTTPHandler.active_sessions`, a process-local dictionary. Session methods use a shared re-entrant lock.

| Method | Behavior |
|---|---|
| `self.set_session()` | Reads the configured session cookie. If its session exists and is valid, refreshes its `set-date` and returns the ID. Otherwise creates a new session, initializes `authenticated` to `False`, queues the session cookie, and returns the new ID. |
| `self.validate_session(session_id)` | Returns whether the session age is less than its configured timeout. |
| `self.destroy_session(session_id)` | Removes the session if present. |
| `self.get_session_parameter(session_id, key)` | Returns the stored session value, or `None` if it cannot be retrieved. |
| `self.set_session_parameter(session_id, key, value)` | Stores a value in the session's `parameters` dictionary. |
| `self.session_authenticated(session_id)` | Returns the session's `authenticated` value, or `False` if unavailable. |
| `self.authenticate_session(session_id, username)` | Sets `authenticated=True` and stores `username` in session parameters. |
| `self.deauthenticate_session(session_id)` | Sets `authenticated=False`. |

Typical pattern:

```python
session_id = self.set_session()

if not self.validate_session(session_id):
    self.set_response("Session expired", status="401 Unauthorized")
else:
    if not self.session_authenticated(session_id):
        self.set_response("Authentication required", status="401 Unauthorized")
    else:
        username = self.get_session_parameter(session_id, "username")
        # Continue only after checking authorization for this operation.
```

Important implementation characteristics:

- Sessions are held in process memory, not a shared session store.
- Session data may be lost when the server process restarts.
- Session timeout is measured from the session's `set-date`; validation itself does not refresh that timestamp.
- `set_session()` refreshes the timestamp for an existing valid session and creates a new session if the cookie is missing, invalid, or expired.
- The current implementation uses a configured cookie name and sets attributes when creating a session cookie. Review those attributes for your domain and security requirements.
- Authentication state is not authorization. Check whether the authenticated user may perform the specific operation.
- Some session helper methods intentionally swallow errors and return defaults or do nothing. Do not treat a default return as proof that an operation succeeded.

## 6. Rendering templates

### `self.execute_template(path, parameters)`

Loads a template from the configured templates directory, executes embedded Python blocks, and appends the rendered HTML to the response.

```python
self.execute_template("example.html", {"title": "Example"})
```

The `parameters` dictionary is passed into the template execution context. Template code can use `self.template_print(...)` to add generated output.

### Template output helpers

| Method | Behavior |
|---|---|
| `self.template_print(string, end='\n')` | Appends generated text to the template execution output buffer. |
| `self.get_exec_stdout()` | Returns the current generated-output buffer. |
| `self.reset_exec_stdout()` | Clears that buffer. |

Template files use `<% ... %>` as embedded Python blocks. These blocks execute as Python code, not as a restricted template language. The framework does not automatically HTML-escape generated values.

Treat templates as trusted server-side code. Escape untrusted data for its HTML context, and never place client input into executable template blocks.

## 7. Database access

### `self.create_sqlite_connection(db_file)`

Attempts to open a SQLite file below the configured private-files database directory and returns the connection, or `None` if it cannot open it.

```python
connection = self.create_sqlite_connection("application.sqlite")
if connection is None:
    self.set_response("Database unavailable", status="500 Internal Server Error")
else:
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT display_name FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
    finally:
        connection.close()
```

The exact file location is formed from the configured root path, private-files path, and the `databases` subdirectory.

### Server-level `db_connection`

The web-server module exposes a `db_connection` proxy backed by a thread-local connection. It supports configured SQLite and MySQL backends. Each request worker thread obtains its own connection; the worker closes its connection after handling the request.

Existing action code can use it in a DB-API-like manner:

```python
cursor = db_connection.cursor()
try:
    cursor.execute(
        "SELECT display_name FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    db_connection.commit()  # needed after writes
finally:
    cursor.close()
```

Placeholder syntax differs by database driver. The example above uses SQLite-style `?` placeholders; use the placeholder style supported by the configured backend/driver. Do not assume one query string is portable between SQLite and MySQL.

Use parameterized queries for all client-derived values. Avoid assembling SQL statements by concatenating request input. Commit write transactions explicitly and handle database exceptions deliberately.

## 8. Static files and fallback behavior

If an action script cannot be found, `execute_action()` attempts to serve a file from the configured public-files directory using the requested path. The file extension is mapped through `content-types`. Text-like content types receive a UTF-8 charset suffix.

If the file cannot be read or its content type cannot be resolved, the handler dispatches the configured 404 error action. This fallback is part of the routing behavior; action authors generally do not need to call `get_file_bytes()` directly.

`self.get_file_bytes(path, method='get', status='200 OK')` is available on the handler if custom code needs to invoke the same configured public-file response path. It reads from the configured public-files directory and sets `Content-Type`, `Content-Length`, and the response body.

## 9. HTTP methods and dispatch

`handle_request()` dispatches these methods to dedicated methods:

| HTTP method | Handler method | Argument source |
|---|---|---|
| GET | `do_get(path, args)` | URL query string |
| HEAD | `do_head(path, args)` | URL query string; uses GET action behavior and strips the body |
| POST | `do_post(path, args)` | Request body |
| PUT | `do_put(path, args)` | Request body |
| DELETE | `do_delete(path, args)` | URL query string |
| CONNECT | `do_connect(path, args)` | URL query string |
| OPTIONS | `do_options(path, args)` | URL query string |
| TRACE | `do_trace(path, args)` | URL query string |
| PATCH | `do_patch(path, args)` | URL query string |

The root path `/` maps to the configured default location for GET and HEAD. Unsupported methods set an `Allow` header and invoke the configured 405 error action.

Although dispatch methods exist for all methods above, whether an action is present and routable depends on the configured method directories and files. HEAD currently executes the GET action and removes the response body afterward.

## 10. Web-server layer

The web-server modules provide the transport and process-level behavior around `HTTPHandler`.

### Request receiving

The server reads the request headers, then reads the body according to `Content-Length` or supported transfer encoding. It returns a complete HTTP/1.x request as bytes to the handler. The current implementation handles one request per TCP connection.

### Per-request worker

Each accepted client connection is handled in a worker thread. The worker creates a fresh `HTTPHandler`, calls `respond_to_request(...)`, sends the resulting bytes, then closes the client connection and releases the worker slot.

### Concurrency

A semaphore limits the number of concurrent request workers using the configured thread limit. `HTTPHandler` request/response state is per-instance, while session storage is class-level and synchronized. The database proxy provides thread-local database connections.

### HTTP and HTTPS entry points

The non-TLS server creates an IPv4 TCP socket, binds to the configured host and port, listens, and starts the listener loop. The TLS server uses the corresponding SSL entry point and certificate/key configuration. When HTTPS enforcement is enabled in the server configuration, the handler can rewrite the request to the configured secure-redirect action.

The server layer is responsible for socket acceptance, request framing, connection lifetime, and invoking the handler. Action scripts should focus on application behavior and should not create their own listening sockets.

### Server helpers

| Helper | Purpose |
|---|---|
| `timeout_to_seconds(hms_notation)` | Converts an `HH:MM:SS` duration string to seconds. |
| `is_blank(string)` | Returns whether the input contains no printable ASCII character according to the helper's implementation. |
| `ThreadLocalDatabaseConnection` | Lazily creates a per-thread connection for the configured SQLite or MySQL backend and delegates connection attributes/methods. |

## 11. Error and response behavior

- The dispatcher defaults action responses to `200 OK` unless an alternate status is passed.
- If action execution raises an exception, the handler invokes the configured 500 error action.
- If no action file exists, the handler tries the public-file fallback.
- If a public file cannot be served, the handler invokes the configured 404 error action.
- Error actions can themselves fail; a recursion guard prevents an infinite error-handler loop.
- The action dispatcher sets `Content-Length` after the action finishes, based on the encoded response body. If an action finalizes the response itself before that point, the normal dispatcher finalization may not replace it.
- `set_response()` accepts only `str` or `bytes` bodies.

Use explicit HTTP status codes for expected client errors and authentication failures. Keep application-level result fields separate from HTTP status codes.

## 12. Practical action pattern

This is a generic starting pattern, not a drop-in action for every request format:

```python
try:
    # Choose one input convention:
    # payload = json.loads(self.request["parameters"])  # raw JSON body
    # payload = json.loads(parameters["data"])          # URL-encoded data field

    payload = json.loads(self.request["parameters"])

    if not isinstance(payload, dict):
        self.set_response_header("Content-Type", "application/json; charset=utf-8")
        self.set_response(
            json.dumps({"error": "Expected a JSON object"}),
            status="400 Bad Request"
        )
    else:
        # Validate fields and authorization before performing work.
        result = {"ok": True}
        self.set_response_header("Content-Type", "application/json; charset=utf-8")
        self.print(json.dumps(result), end="")
except (ValueError, TypeError):
    self.set_response_header("Content-Type", "application/json; charset=utf-8")
    self.set_response(
        json.dumps({"error": "Invalid request body"}),
        status="400 Bad Request"
    )
```

Because `set_response()` finalizes the response immediately, use it for early exits. If you use `self.print()` instead, let the dispatcher finalize the response after the action completes.

## 13. Implementation limits to understand

These points describe the current source, not general HTTP recommendations:

- Action scripts and template blocks are executed with Python `exec`; they are trusted code and are not sandboxed.
- Request body parsing preserves the body as text. It does not automatically decode JSON or multipart form data.
- Query/form-style parameters are stored in a dictionary, so repeated keys are not preserved as lists.
- The handler constructs an HTTP/1.x response from a configured protocol version, status line, headers, cookies, and body.
- Session state is in memory and is not shared between separate server processes.
- The code's static-file fallback and route resolution use configured filesystem paths; keep those paths controlled by trusted configuration.
- Some existing application code may rely on globals imported by the server module. Treat undocumented globals as implementation details rather than a stable extension interface.

## 14. Scope of this guide

This guide covers the general capabilities and lifecycle of Python actions, `HTTPHandler`, and the server transport. It deliberately does not catalogue application-specific routes, document template contents, enumerate static assets, or reproduce environment-specific configuration values.
