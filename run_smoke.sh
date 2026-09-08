#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
elif [[ -x ".venv/Scripts/python.exe" ]]; then
  PY=".venv/Scripts/python.exe"
else
  echo "Virtual environment not found. Run: python3 -m venv .venv"
  exit 1
fi

exec "$PY" tests/run_smoke.py
