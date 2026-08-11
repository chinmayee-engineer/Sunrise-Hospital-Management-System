"""Append-only audit trail (spec section 36)."""
from __future__ import annotations

from datetime import datetime

from core.database.db import execute, query_all


def log_action(user_id: str | None, role_name: str | None, action: str,
                related_record: str = "", description: str = "") -> None:
    execute(
        """INSERT INTO audit_logs (user_id, role_name, action, related_record, description, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, role_name, action, related_record, description, datetime.now().isoformat(timespec="seconds")),
    )


def recent_logs(limit: int = 500, action_filter: str = "", user_filter: str = "") -> list[dict]:
    sql = "SELECT * FROM audit_logs WHERE 1=1"
    params: list = []
    if action_filter:
        sql += " AND action LIKE ?"
        params.append(f"%{action_filter}%")
    if user_filter:
        sql += " AND (user_id LIKE ? OR role_name LIKE ?)"
        params.extend([f"%{user_filter}%", f"%{user_filter}%"])
    sql += " ORDER BY audit_id DESC LIMIT ?"
    params.append(limit)
    return query_all(sql, tuple(params))
