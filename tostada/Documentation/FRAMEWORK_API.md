# Tostada Framework API

## Request lifecycle

1. The HTTP server receives a request and passes it to `HTTPHandler`.
2. `HTTPHandler` parses the request target, headers, and body.
3. The handler dispatches according to the HTTP method.
4. For action-backed routes, it resolves the action script using the configured action root and method-specific directory.
5. The action can set response headers, write a response, access session state, or render a template.

## Action routing

Action scripts are organized by HTTP method, for example:

- `web/actions/get/<action>.py`
- `web/actions/post/<action>.py`
- `web/actions/put/<action>.py`
- `web/actions/delete/<action>.py` (if configured and present)

The action name is derived from the request path and resolved under the configured method-specific action directory. The precise URL prefix depends on `http_config.json`; consult the active `paths.actions` values rather than assuming that the filesystem path is the public URL.

For GET and HEAD, query parameters are supplied to the action. For POST and PUT, the parsed request body is supplied. The handler parses query/form-style values using URL-encoded parameter parsing. Repeated parameter names collapse to one dictionary entry; a parameter without `=` can be represented as `None`.

## Action execution context

The action scripts in this application use these handler/application names:

- `self` — current `HTTPHandler` instance.
- `parameters` — parsed request parameters, represented as a dictionary.
- `HTTPHandler` — handler class; application scripts use it for shared session state.
- `json` — JSON parsing utility used by JSON-oriented actions.
- `timeout_to_seconds` — helper used by page actions to expose session timeout duration.
- `server_config` and `logger` are referenced by application scripts, but application-specific configuration and operational logging are outside this developer API reference.

An action that expects JSON commonly reads it with `json.loads(parameters["data"])`. Because the handler parses form-style fields, clients should send `data` as a JSON string inside a URL-encoded field unless the request parser is changed.

## Response helpers

The action scripts use the following handler methods:

| Method | Purpose |
|---|---|
| `self.print(text)` | Appends text to the response body. |
| `self.set_response_header(name, value)` | Sets a response header. |
| `self.execute_template(path, parameters)` | Renders a template with the provided parameter dictionary. |
| `self.redirect(location)` | Requests a redirect to the given location. |
| `self.set_session()` | Gets or creates a session identifier for the request. |
| `self.validate_session(session_id)` | Checks whether the session exists and is still valid. |
| `self.session_authenticated(session_id)` | Checks the session's authenticated state. |
| `self.authenticate_session(session_id, username)` | Marks the session authenticated and associates the username. |
| `self.deauthenticate_session(session_id)` | Clears the authenticated state. |
| `self.destroy_session(session_id)` | Removes the session. |
| `self.get_session_parameter(session_id, key)` | Reads an application value stored in session state. |
| `self.set_session_parameter(session_id, key, value)` | Stores an application value in session state. |
| `self.create_sqlite_connection(name)` | Opens a configured SQLite database file by name. |

## Templates

Templates are rendered by `execute_template(path, parameters)`. The current template engine supports embedded Python blocks and server-side output through `self.template_print(...)`. Template execution is trusted-code execution, not a sandbox. Escape HTML output explicitly and do not treat template variables as safe by default.

## Sessions and cookies

Session state is held by the running server process. Application actions use sessions for authentication and flags such as whether the user has completed security-question setup. A session is not a substitute for authorization checks: protected actions should validate both session validity and authentication before returning sensitive data or performing privileged operations.

## Security and correctness considerations

The source scripts directly construct SQL statements using request-derived values in several places and build JSON responses through string concatenation. Before exposing these actions to untrusted clients, use parameterized SQL, serialize responses with a JSON encoder, validate input types and lengths, and return consistent HTTP status codes. These notes describe source-observed risks; they are not claims that those improvements are already implemented.
