#!/usr/bin/env bash

set -u

TOSTADA_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$TOSTADA_ROOT" || exit 1

python3 "$TOSTADA_ROOT/webserver_ipv4.py" &
HTTP_PID=$!

python3 "$TOSTADA_ROOT/webserver_ipv4_ssl.py" &
HTTPS_PID=$!

# Stop both servers when either one exits.
set +e
wait -n "$HTTP_PID" "$HTTPS_PID"
STATUS=$?

kill "$HTTP_PID" "$HTTPS_PID" 2>/dev/null
wait 2>/dev/null

exit "$STATUS"