#!/usr/bin/env python3
"""Reset the isolated test database and run HTTP smoke tests."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.support.db import reset_test_database
from tests.support.env import activate_test_mode


def main() -> int:
    test_db = activate_test_mode()
    reset_test_database()
    print(f"Using test database: {test_db}")

    from tests.smoke.test_routes import run_smoke_tests

    return run_smoke_tests()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1) from None
