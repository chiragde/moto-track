"""Database helpers for test runs and one-off production cleanup."""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN_DB_PATH = PROJECT_ROOT / "moto_track.db"

# Automated accounts created by smoke tests or ad-hoc QA scripts.
TEST_USERNAMES = {
    "qa_runner",
    "qa_manual_test",
    "qa_manual_test2",
    "brand_new_user_xyz",
    "test_8f740abb",
    "reg_f9e84e7c",
    "http_5e715532",
    "x_b124bc3d",
    "wrap_54aaf209",
}
TEST_USERNAME_RE = re.compile(
    r"^(qa_|brand_new_user_|test_[a-f0-9]{8}|reg_[a-f0-9]{8}|http_[a-f0-9]{8}|"
    r"x_[a-f0-9]{8}|wrap_[a-f0-9]{8})"
)


def reset_test_database() -> Path:
    """Delete and recreate the isolated SQLite database used for tests."""
    from database import init_db, resolve_db_path

    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    init_db()
    return db_path


def cleanup_main_database(db_path: Path | None = None) -> list[str]:
    """Remove automated test accounts from the production SQLite database."""
    if os.environ.get("MOTO_TRACK_TEST", "").strip().lower() in {"1", "true", "yes", "on"}:
        raise RuntimeError("Refusing to clean the main database while MOTO_TRACK_TEST is set.")

    path = db_path or MAIN_DB_PATH
    if not path.exists():
        return []

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        users = conn.execute("SELECT id, username FROM users").fetchall()
        removed: list[str] = []
        for user in users:
            username = user["username"]
            if username in TEST_USERNAMES or TEST_USERNAME_RE.match(username):
                conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
                removed.append(username)
        conn.commit()
        return removed
    finally:
        conn.close()
