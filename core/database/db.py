"""SQLite connection management, schema initialization and small
row-mapping conveniences shared by both applications.

A single, small connection pool is unnecessary for a desktop app --
we open one connection per Database instance (SQLite handles
concurrent readers fine) with foreign keys and WAL journaling
enabled, and use context-managed transactions for writes.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from core.utils.paths import DATABASE_PATH, ensure_directories

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")

_lock = threading.Lock()
_connection: sqlite3.Connection | None = None


def _row_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))


def get_connection() -> sqlite3.Connection:
    """Return the process-wide SQLite connection, creating and
    initializing the database on first use."""
    global _connection
    with _lock:
        if _connection is None:
            ensure_directories()
            _connection = sqlite3.connect(
                str(DATABASE_PATH),
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            _connection.row_factory = _row_factory
            _connection.execute("PRAGMA foreign_keys = ON;")
            _connection.execute("PRAGMA journal_mode = WAL;")
            initialize_schema(_connection)
        return _connection


def initialize_schema(conn: sqlite3.Connection) -> None:
    script = _SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(script)
    conn.commit()


@contextmanager
def transaction():
    """Context manager giving a cursor; commits on success, rolls
    back on any exception. Use for every write operation."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def query_all(sql: str, params: tuple = ()) -> list[dict]:
    conn = get_connection()
    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def query_one(sql: str, params: tuple = ()) -> dict | None:
    conn = get_connection()
    cursor = conn.execute(sql, params)
    row = cursor.fetchone()
    cursor.close()
    return row


def execute(sql: str, params: tuple = ()) -> int:
    """Run a single INSERT/UPDATE/DELETE inside its own transaction.
    Returns lastrowid (useful for autoincrement PKs like audit_logs)."""
    with transaction() as cursor:
        cursor.execute(sql, params)
        return cursor.lastrowid


def next_numeric_id(table: str, id_column: str) -> int | None:
    """Find the highest numeric suffix currently used for an entity's
    ID column, e.g. patients.patient_id -> max numeric part of P-xxxxx."""
    rows = query_all(f"SELECT {id_column} AS id FROM {table}")
    if not rows:
        return None
    from core.utils.ids import numeric_part
    return max(numeric_part(row["id"]) for row in rows)


def close_connection() -> None:
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None
