#!/usr/bin/env bash
# Kartly -- security training target. Localhost only.
set -e
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python

echo "Installing dependencies..."
"$PY" -m pip install -r requirements.txt >/dev/null

echo "Starting Kartly on http://127.0.0.1:5000/  (Ctrl+C to stop)"
exec "$PY" app.py
