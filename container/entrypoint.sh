#!/bin/sh
set -e
exec python3 -m http.server --cgi "${BOOT_PORT:-8080}"
