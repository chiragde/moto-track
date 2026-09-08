import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "moto_track.db"
TEST_DB_PATH = PROJECT_ROOT / "tests" / "data" / "moto_track_test.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "")


def is_test_mode() -> bool:
    if os.environ.get("MOTO_TRACK_DB", "").strip():
        return False
    return os.environ.get("MOTO_TRACK_TEST", "").strip().lower() in {"1", "true", "yes", "on"}


def resolve_db_path() -> Path:
    explicit = os.environ.get("MOTO_TRACK_DB", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    if is_test_mode():
        return TEST_DB_PATH
    return DEFAULT_DB_PATH


def get_db_path() -> Path:
    return resolve_db_path()


def get_db():
    if DATABASE_URL.startswith("postgres"):
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return _PostgresConn(conn)

    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class _PostgresConn:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        sql = sql.replace("?", "%s")
        sql = sql.replace("INSERT OR IGNORE", "INSERT")
        sql = sql.replace("AUTOINCREMENT", "")
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        return cur

    def executescript(self, sql):
        cur = self._conn.cursor()
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                cur.execute(statement.replace("?", "%s"))
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._conn.commit()
        self._conn.close()


def init_db():
    is_pg = DATABASE_URL.startswith("postgres")
    with get_db() as conn:
        if is_pg:
            _init_postgres(conn)
        else:
            _init_sqlite(conn)
        migrate_db(conn)


def _init_sqlite(conn):
    conn.executescript(_SCHEMA_SQLITE)


def _init_postgres(conn):
    for stmt in _SCHEMA_SQLITE.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        pg_stmt = (
            stmt.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            .replace("INSERT OR IGNORE", "INSERT")
            .replace("?", "%s")
        )
        try:
            conn.execute(pg_stmt)
        except Exception:
            pass


_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    currency TEXT NOT NULL DEFAULT 'INR',
    unit_system TEXT NOT NULL DEFAULT 'metric',
    theme TEXT NOT NULL DEFAULT 'system',
    email TEXT,
    notifications_enabled INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    make TEXT,
    model TEXT,
    year INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fuel_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    liters REAL NOT NULL,
    cost REAL NOT NULL,
    odometer REAL NOT NULL,
    notes TEXT,
    tag TEXT,
    receipt_image TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS maintenance_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    entry_type TEXT NOT NULL CHECK (entry_type IN ('service', 'adhoc')),
    description TEXT NOT NULL,
    cost REAL NOT NULL,
    odometer REAL,
    notes TEXT,
    receipt_image TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS odometer_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    reading_date TEXT NOT NULL,
    reading REAL NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS care_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    task_type TEXT NOT NULL,
    description TEXT NOT NULL,
    odometer REAL NOT NULL,
    cost REAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bike_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    reminder_type TEXT NOT NULL,
    interval_km INTEGER,
    interval_days INTEGER,
    last_done_date TEXT,
    last_done_odometer REAL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
);
"""


def migrate_db(conn):
    column_migrations = {
        "fuel_entries": {
            "receipt_image": "TEXT",
            "tag": "TEXT",
            "is_partial": "INTEGER DEFAULT 0",
            "station_name": "TEXT",
        },
        "maintenance_entries": {"receipt_image": "TEXT"},
        "bikes": {"photo": "TEXT"},
    }
    for table, columns in column_migrations.items():
        try:
            existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        except Exception:
            existing = set()
        for column, col_type in columns.items():
            if column not in existing:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                except Exception:
                    pass

    _ensure_table(
        conn,
        "expense_entries",
        """
        CREATE TABLE IF NOT EXISTS expense_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bike_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
        )
        """,
    )
    _ensure_table(
        conn,
        "bike_parts",
        """
        CREATE TABLE IF NOT EXISTS bike_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bike_id INTEGER NOT NULL,
            part_type TEXT NOT NULL,
            label TEXT NOT NULL,
            interval_km INTEGER,
            last_done_odometer REAL,
            last_done_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (bike_id) REFERENCES bikes(id) ON DELETE CASCADE
        )
        """,
    )
    _ensure_table(
        conn,
        "push_subscriptions",
        """
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL UNIQUE,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
    )

    _ensure_table(
        conn,
        "user_settings",
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            currency TEXT NOT NULL DEFAULT 'INR',
            unit_system TEXT NOT NULL DEFAULT 'metric',
            theme TEXT NOT NULL DEFAULT 'system',
            email TEXT,
            notifications_enabled INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
    )
    _ensure_table(
        conn,
        "password_reset_tokens",
        """
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
    )


def _ensure_table(conn, name, create_sql):
    try:
        conn.execute(f"SELECT 1 FROM {name} LIMIT 1")
    except Exception:
        conn.execute(create_sql)
