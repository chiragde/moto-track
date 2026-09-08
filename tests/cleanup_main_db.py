#!/usr/bin/env python3
"""Remove automated test accounts from the production SQLite database."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.support.db import MAIN_DB_PATH, cleanup_main_database


def main() -> int:
    removed = cleanup_main_database()
    if not removed:
        print(f"No automated test accounts found in {MAIN_DB_PATH}.")
        return 0
    print(f"Removed {len(removed)} test account(s) from {MAIN_DB_PATH}:")
    for username in removed:
        print(f"  - {username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
