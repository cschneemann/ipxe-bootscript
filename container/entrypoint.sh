#!/bin/sh
set -e

# Initialize SQLite table if it does not exist yet
python3 -c "import admin; admin.init_db()"

# CGI server for the iPXE bootscript on port 8080 (background)
python3 -m http.server --cgi "${BOOT_PORT:-8080}" &

# Flask admin UI on port 5000 (foreground, receives SIGTERM)
exec python3 admin.py
