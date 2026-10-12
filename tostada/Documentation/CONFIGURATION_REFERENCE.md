# Tostada Configuration Reference

This reference describes the framework configuration structure without copying any environment-specific values.

## `http_config.json`

Observed top-level keys:

| Key | Purpose |
|---|---|
| `version` | Configuration/schema version identifier. |
| `default-location` | Default route used for the root page. |
| `session-timeout` | Session expiration interval. |
| `session-cookie-name` | Cookie name used to identify a session. |
| `status-locations` | Mapping used for status/error destinations. |
| `status-codes` | HTTP status code definitions. |
| `root-path` | Base path used to resolve application files. |
| `paths.actions.actions-root` | Root directory for action scripts. |
| `paths.actions.get` | Directory for GET actions. |
| `paths.actions.post` | Directory for POST actions. |
| `paths.actions.put` | Directory for PUT actions. |
| `paths.actions.delete` | Directory for DELETE actions, when configured. |
| `paths.public-files` | Public static-file directory. |
| `paths.private-files` | Private application-file directory. |
| `paths.templates` | Template directory. |
| `content-types` | File-extension to content-type mapping. |
| `configured` | Configuration-state flag. |

The route path is derived from the HTTP request and the configured action directory. Do not assume that the directory name itself is the full public URL.

## `server_config.json`

The source references these general settings:

| Key | Purpose |
|---|---|
| `non-ssl-port` | Listener port for non-TLS HTTP. |
| `ssl-port` | Listener port for TLS HTTP. |
| `hostname` | Hostname used by server logic. |
| `server-host` | Host/address value used by the server. |
| `cert-location` | TLS certificate path. |
| `key-location` | TLS private-key path. |
| `enable-https.enabled` | Enables HTTPS-related behavior. |
| `enable-https.force-ssl.force` | Controls HTTP-to-HTTPS enforcement. |
| `enable-https.force-ssl.true-path` | Path/URL used for the secure redirect behavior. |
| `queue-limit` | Socket listen queue limit. |
| `socket-buffer-size` | Socket buffer size. |
| `max-threads` | Thread limit for request handling. |
| `database.type` | Database backend selection. |
| `database.sqlite-file` | SQLite database file setting. |
| `database.mysql.host` | MySQL host. |
| `database.mysql.port` | MySQL port. |
| `database.mysql.database` | MySQL database name. |
| `database.mysql.user` | MySQL username. |
| `database.mysql.password` | MySQL password setting; never publish its value. |

Keep actual server addresses, credential values, private key material, and environment-specific paths out of documentation committed to a public repository.
