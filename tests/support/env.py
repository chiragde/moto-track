"""Configure process environment for isolated test runs."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def activate_test_mode() -> Path:
    """Point the app at the isolated test database before imports."""
    os.environ["MOTO_TRACK_TEST"] = "1"
    os.environ.pop("MOTO_TRACK_DB", None)

    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)

    return PROJECT_ROOT / "tests" / "data" / "moto_track_test.db"
