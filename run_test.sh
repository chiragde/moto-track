#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export MOTO_TRACK_TEST=1

if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
elif [[ -x ".venv/Scripts/python.exe" ]]; then
  PY=".venv/Scripts/python.exe"
else
  echo "Virtual environment not found. Run: python3 -m venv .venv"
  exit 1
fi

echo "Starting Moto Track in TEST mode at http://localhost:5000"
echo "Using database: tests/data/moto_track_test.db"
echo "Press Ctrl+C to stop the server."
echo
exec "$PY" app.py
